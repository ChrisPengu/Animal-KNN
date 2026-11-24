from pathlib import Path
import importlib.metadata as metadata
import json
import platform
import subprocess
import sys
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT=Path(__file__).resolve().parents[1]
lines=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True).splitlines()
# Lock only this project's dependency closure; omit retired web UI/build tools.
pending=[Requirement(s).name for s in (ROOT/'requirements.txt').read_text().splitlines() if s.strip() and not s.startswith('#')]
pending += ['torch','torchvision','agent-reach']
needed=set()
while pending:
    name=canonicalize_name(pending.pop())
    if name in needed: continue
    needed.add(name)
    for value in metadata.requires(name) or []:
        req=Requirement(value)
        if req.marker is None or req.marker.evaluate({'extra':''}): pending.append(req.name)
filtered=[]
for line in lines:
    if line.startswith('# Editable') or line.startswith('-e ') or line.lower().startswith('animal-knn'):
        continue
    if canonicalize_name(line.split(' @ ')[0].split('==')[0]) not in needed:
        continue
    if line.lower().startswith('agent-reach @'):
        distribution=metadata.distribution('agent-reach')
        direct=json.loads(distribution.read_text('direct_url.json'))
        digest=direct['archive_info']['hashes']['sha256']
        source_url=direct['url']
        if source_url=='https://github.com/Panniantong/Agent-Reach/releases/latest/download/agent-reach.zip':
            source_url=f'https://github.com/Panniantong/Agent-Reach/releases/download/v{metadata.version("agent-reach")}/agent-reach.zip'
        line='agent-reach @ '+source_url+'#sha256='+digest
    filtered.append(line)
(ROOT/'requirements.lock.txt').write_text('--extra-index-url https://download.pytorch.org/whl/cu126\n'+'\n'.join(filtered)+'\n',encoding='utf-8')
result={'python':sys.version,'platform':platform.platform(),'ui':'Tkinter/ttk, Tcl/Tk 8.6', 'versions':{d:metadata.version(d) for d in ['torch','torchvision','numpy','scikit-learn','scikit-image','opencv-python-headless','agent-reach']}}
import torch
result.update({'cuda_available':torch.cuda.is_available(),'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None})
(ROOT/'reports/environment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Locked',len(filtered),'packages')
