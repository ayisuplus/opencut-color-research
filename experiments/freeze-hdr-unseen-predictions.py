"""Freeze own-GPU predictions before any new Resolve render observation."""
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-unseen-gains-20261013/analysis'
prior=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

manifest_path=case/'input-freeze.json'
manifest=json.loads(manifest_path.read_text(encoding='utf8'))
assert sha(root/'experiments/prepare-hdr-unseen-gains.py')==manifest['preparer_sha256']
assert sha(root/'experiments/hdr-transfer-gpu-probe.cu')==manifest['probe_source_sha256']
assert sha(prior/'hdr-transfer-gpu-probe.exe')==manifest['executable_sha256']
previous_path=prior/'hdr-adapted-gpu-output.bin'
assert sha(previous_path)=='00202ae11882bfd3e55dfd9e6802ece05f66316c7b71fd51a8d25031c6291805'
previous=np.frombuffer(previous_path.read_bytes(),dtype='<f4',offset=20).reshape(2,2,2,48,10)
rows=[]; bindings=[]; controls=[]
for batch in manifest['batches']:
    input_path=root/batch['path']; assert sha(input_path)==batch['sha256']
    output_path=case/(batch['name']+'-output.bin')
    data=output_path.read_bytes()
    assert len(data)==5140 and struct.unpack_from('<5I',data)==(0x32584448,1024,2,16,10)
    trace=np.frombuffer(data,dtype='<f4',offset=20).reshape(2,2,2,16,10)
    assert np.isfinite(trace).all()
    receipt_path=case/(batch['name']+'-run.json')
    receipt=json.loads(receipt_path.read_text(encoding='utf-8-sig'))
    assert receipt=={'device':'NVIDIA GeForce RTX 5090','compute':[12,0],'runtime':12080,
                    'driver':13040,'pixels':16,'models':8,'trace_floats':10}
    for t,gain in enumerate(batch['stored_gainjz']):
        if gain==1.:
            assert np.array_equal(trace[t].view('<u4'),previous[1,:,:,16:32].view('<u4'))
            controls.append({'name':'old_plus1_all_trace_bits','values':int(trace[t].size),'passed':True})
            continue
        for m in range(2):
            for a in range(2):
                rows.append({'stored_gainjz':gain,'matrix_mode':m,'interpolation':a,
                    'primary':(m,a)==(1,0),'predicted_RGB':trace[t,m,a,:,7:10].astype(float).tolist()})
    for p in [input_path,output_path,receipt_path]:
        bindings.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
assert len(controls)==1 and controls[0]['values']==640 and len(rows)==12
path=root/'docs/experiments/hdr-unseen-gains-prediction-freeze.json'
assert not path.exists(), 'Never replace prospective predictions after observing native output.'
out={**manifest,'scope':'own-GPU predictions frozen before new native observation; only exposure settings unseen',
    'freezer_sha256':sha(Path(__file__)),'input_manifest_sha256':sha(manifest_path),
    'prediction_rows':rows,'GPU_control_checks':controls,'own_GPU_executions':2,
    'formal_resolve_frames_total_at_freeze':48,'new_resolve_frames_at_freeze':0,
    'bindings':bindings+[{'path':manifest_path.relative_to(root).as_posix(),'bytes':manifest_path.stat().st_size,
        'sha256':sha(manifest_path)}]}
path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'prediction_rows':len(rows),'predicted_RGB_channels':576,'primary_channels':144,
                  'GPU_control_values':640,'new_resolve_frames':0,'freeze_sha256':sha(path)}))
