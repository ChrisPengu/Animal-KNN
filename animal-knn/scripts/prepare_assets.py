from pathlib import Path
import shutil
import json
import numpy as np
import pandas as pd
from PIL import Image
from animal_knn.common import ROOT,CLASSES,VI,save_json


def main():
    root=ROOT
    external=pd.read_csv(root/'data/external/manifest.csv')
    examples=root/'assets/examples'
    examples.mkdir(parents=True,exist_ok=True)
    sources=[]
    for name in CLASSES:
        row=external[external.class_name==name].iloc[0]
        shutil.copyfile(root/row.filename,examples/(name+'.jpg'))
        sources.append({'asset':f'assets/examples/{name}.jpg','source_file':row.filename,
                        'source_page':row.source_page,'author':row.author,'license':row.license,'license_url':row.license_url})
    save_json(examples/'sources.json',sources)
    selection=root/'models/selection.json'
    if not selection.exists():
        return
    feature=json.loads(selection.read_text(encoding='utf-8'))['config']['feature']
    data=pd.read_csv(root/'results'/f'{feature}_test_predictions.csv')
    data=data[data.label!=data.prediction].sort_values('vote_score',ascending=False)
    chosen=data.groupby('label',sort=False).head(1).head(3)
    images=np.load(root/'data/processed/images.npy',mmap_mode='r')
    manifest=pd.read_csv(root/'data/processed/manifest.csv').set_index('sample_id')
    records=[]
    errors=root/'assets/deck_errors'
    errors.mkdir(exist_ok=True)
    for i,row in enumerate(chosen.itertuples()):
        index=manifest.index.get_loc(row.sample_id)
        filename=errors/f'error_{i}.png'
        Image.fromarray(images[index]).save(filename)
        records.append({'path':filename.relative_to(root).as_posix(),'sample_id':row.sample_id,
                        'truth_vi':VI[row.label],'pred_vi':VI[row.prediction],'vote_score':row.vote_score})
    save_json(root/'assets/deck_errors.json',records)
    print('Prepared six demo examples and presentation evidence')


if __name__=='__main__':main()
