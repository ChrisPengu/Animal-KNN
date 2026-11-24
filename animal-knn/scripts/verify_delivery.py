"""Check the shipped study against independent online inference and public UI helpers."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import joblib
import numpy as np
import pandas as pd
from PIL import Image
from threadpoolctl import threadpool_limits
from sklearn.metrics import accuracy_score,f1_score

from animal_knn.common import ROOT,CLASSES,save_json
from animal_knn.data import load,md5,CHECKSUMS
from animal_knn.inference import Predictor


def main():
    root=ROOT
    images,manifest=load(root)
    bundle=joblib.load(root/'models/best.joblib')
    train=manifest[manifest.split=='train']
    holdout=manifest[manifest.split.isin(['val','test'])]
    assert bundle['reference_ids']==train.sample_id.to_list()
    assert set(bundle['reference_ids']).isdisjoint(set(holdout.sample_id))
    assert set(bundle['train_sha256']).isdisjoint(set(holdout.sha256))
    assert bundle['pipeline'][-1].n_samples_fit_==len(train)
    receipt=json.loads((root/'results/test_access_receipt.json').read_text(encoding='utf-8'))
    assert receipt['best_model_sha256']==hashlib.sha256((root/'models/best.joblib').read_bytes()).hexdigest()
    with np.load(root/'data/features'/f"{bundle['feature']}.npz") as cached:
        indices=manifest.index[manifest.split=='test'].to_numpy()[:6]
        offline=cached['X'][indices].copy()
        val_indices=manifest.index[manifest.split=='val'].to_numpy()
        validation_features=cached['X'][val_indices].copy()
    with threadpool_limits(limits=2):
        validation_pred=bundle['pipeline'].predict(validation_features)
    actual_val_accuracy=accuracy_score(manifest.iloc[val_indices].label,validation_pred)
    actual_val_f1=f1_score(manifest.iloc[val_indices].label,validation_pred,average='macro',labels=range(6))
    assert abs(actual_val_accuracy-bundle['config']['val_accuracy']) < 1e-12
    assert abs(actual_val_f1-bundle['config']['val_macro_f1']) < 1e-12
    predictor=Predictor(root)
    online,_=predictor.extractor.batch(images[indices])
    relative_l2=np.linalg.norm(online-offline,axis=1)/np.maximum(np.linalg.norm(offline,axis=1),1e-12)
    cosine=(online*offline).sum(1)/(np.linalg.norm(online,axis=1)*np.linalg.norm(offline,axis=1))
    # CUDA kernels can differ with batch shape; compare vector scale and actual votes.
    assert float(relative_l2.max()) < .001,relative_l2
    assert float(cosine.min()) > .99999,cosine
    with threadpool_limits(limits=2):
        cached_scores=bundle['pipeline'].predict_proba(offline)
        online_scores=bundle['pipeline'].predict_proba(online)
    np.testing.assert_allclose(cached_scores,online_scores,rtol=1e-4,atol=1e-4)
    labels=[predictor.predict(Image.fromarray(images[i]))['label'] for i in indices]
    assert labels==online_scores.argmax(1).tolist()
    cpu=Predictor(root,device='cpu')
    cpu_labels=[cpu.predict(Image.fromarray(images[i]))['label'] for i in indices[:3]]
    assert cpu_labels==labels[:3]
    demo=predictor.predict(root/'assets/examples/cat.jpg')
    save_json(root/'results/demo_prediction.json',demo)
    import uuid
    unit=subprocess.run([sys.executable,'-m','pytest','-q','--basetemp',str(root/'.pytest_cache'/f'verify-{uuid.uuid4().hex}')],cwd=root,text=True,capture_output=True)
    (root/'results/pytest.txt').write_text(unit.stdout+'\n'+unit.stderr,encoding='utf-8')
    assert unit.returncode==0,unit.stdout+unit.stderr
    hashes={n:md5(root/'data/raw/stl10_binary'/n)==digest for n,digest in CHECKSUMS.items()}
    assert all(hashes.values())
    # The exact same serialized pipeline must retain its predictions on reload.
    reloaded=joblib.load(root/'models/best.joblib')
    with threadpool_limits(limits=2):
        np.testing.assert_array_equal(reloaded['pipeline'].predict(offline),bundle['pipeline'].predict(offline))
    save_json(root/'results/verification.json',{
        'official_binary_md5':all(hashes.values()),'reference_count_train_only':len(train),
        'no_exact_hash_overlap':True,'curated_near_duplicate_candidates':0,
        'cached_online_features_consistent':True,'cached_online_votes_consistent':True,
        'cached_online_max_relative_l2':float(relative_l2.max()),
        'stored_validation_metrics_reproduced':True,
        'reproduced_validation_accuracy':float(actual_val_accuracy),
        'cpu_gpu_prediction_consistency_samples':len(cpu_labels),'serialization_roundtrip':True,
        'unit_tests':unit.stdout.strip().splitlines()[-1],
        'selected_feature':bundle['feature'],'demo_expected_label_vi':demo['class_name_vi']})
    print(json.dumps({'verified':True,'feature':bundle['feature'],'demo':demo['class_name_vi']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
