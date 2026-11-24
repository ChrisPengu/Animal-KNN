"""Audit external provenance and, after freezing the study, evaluate all accepted photos."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

import numpy as np
import pandas as pd
from PIL import Image,ImageDraw,ImageOps
from scipy.fft import dctn
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix

from animal_knn.common import ROOT,CLASSES,VI,read_image,save_json
from animal_knn.data import load


def phash(image):
    gray=np.asarray(image.convert('L').resize((32,32)),dtype=float)
    values=dctn(gray,norm='ortho')[:8,:8].ravel()[1:]
    return values>np.median(values)


def audit(root=ROOT):
    root=Path(root)
    images,manifest=load(root)
    external=pd.read_csv(root/'data/external/manifest.csv')
    hashes=np.array([phash(Image.fromarray(p)) for p in images],dtype=np.uint8)
    queries=np.array([phash(read_image(root/name)) for name in external.filename],dtype=np.uint8)
    nn=NearestNeighbors(n_neighbors=1,metric='hamming',algorithm='brute',n_jobs=2).fit(hashes)
    distances,indices=nn.kneighbors(queries)
    rows=[]
    for i,(distance,index) in enumerate(zip(distances[:,0],indices[:,0])):
        if distance*63<=5:
            rows.append({'external_filename':external.iloc[i].filename,'stl_id':manifest.iloc[index].sample_id,
                         'stl_index':int(index),'hamming_bits':int(round(distance*63))})
    result=pd.DataFrame(rows,columns=['external_filename','stl_id','stl_index','hamming_bits'])
    result.to_csv(root/'data/external/stl_overlap_candidates.csv',index=False)
    save_json(root/'data/external/audit.json',{'count':len(external),'class_counts':external.class_name.value_counts().to_dict(),
        'all_visually_reviewed':bool(external.visual_review.fillna('').str.startswith('accepted').all()),
        'stl_near_duplicate_candidates':len(result),'hamming_threshold':5,
        'note':'Perceptual-hash candidate search is not a guarantee of zero semantic overlap.'})
    if rows:
        sheet=Image.new('RGB',(800,200*((len(rows)+1)//2)),'white')
        draw=ImageDraw.Draw(sheet)
        for k,row in enumerate(rows):
            x=(k%2)*400;y=(k//2)*200
            sheet.paste(ImageOps.contain(read_image(root/row['external_filename']),(190,160)),(x,y))
            sheet.paste(Image.fromarray(images[row['stl_index']]).resize((190,160)),(x+200,y))
            draw.text((x,y+164),Path(row['external_filename']).name,fill='black')
            draw.text((x+200,y+164),row['stl_id'],fill='black')
        sheet.save(root/'data/external/overlap_review.jpg')
    print(json.dumps({'external':len(external),'overlap_candidates':len(rows)}),flush=True)


def evaluate(root=ROOT):
    from animal_knn.inference import Predictor
    from animal_knn.evaluation import _confusion
    root=Path(root)
    if not (root/'results/test_access_receipt.json').exists():
        raise RuntimeError('Freeze and evaluate the main study before external evaluation')
    frame=pd.read_csv(root/'data/external/manifest.csv')
    if len(frame)!=60 or not frame.visual_review.fillna('').str.startswith('accepted').all():
        raise ValueError('External evaluation requires 60 visually accepted photographs')
    predictor=Predictor(root)
    predictor.predict(read_image(root/frame.iloc[0].filename))
    rows=[]
    for row in frame.itertuples():
        result=predictor.predict(read_image(root/row.filename))
        rows.append({'filename':row.filename,'truth':row.label,'prediction':result['label'],
                     'vote_score':max(result['vote_scores']),'elapsed_ms':result['elapsed_ms'],'source_page':row.source_page})
    result=pd.DataFrame(rows)
    result.to_csv(root/'results/external_predictions.csv',index=False)
    cm=confusion_matrix(result.truth,result.prediction,labels=range(6))
    metrics={'accuracy':accuracy_score(result.truth,result.prediction),
        'macro_f1':f1_score(result.truth,result.prediction,average='macro',labels=range(6),zero_division=0),
        'count':len(frame),'classification_report':classification_report(result.truth,result.prediction,labels=range(6),target_names=CLASSES,output_dict=True,zero_division=0),
        'confusion_matrix':cm,'median_ms':float(result.elapsed_ms.median()),'p95_ms':float(result.elapsed_ms.quantile(.95)),
        'protocol':'Fixed Wikimedia set, visually reviewed before model evaluation; no tuning on this set'}
    save_json(root/'results/external_metrics.json',metrics)
    _confusion(cm,'Wikimedia, 60 ảnh',root/'results/external_confusion.png')
    print(json.dumps({k:metrics[k] for k in ['accuracy','macro_f1','median_ms','p95_ms']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['audit','evaluate'])
    p.add_argument('--root',type=Path,default=ROOT)
    a=p.parse_args()
    audit(a.root) if a.action=='audit' else evaluate(a.root)
