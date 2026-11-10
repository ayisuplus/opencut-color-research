"""Paired ideal CPU diagnostic; vary only Y clamp, without modifying GPU freeze."""
import hashlib
import json
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-near-black-20261014/analysis'
freeze=root/'docs/experiments/hdr-near-black-prediction-freeze.json'
assert hashlib.sha256(freeze.read_bytes()).hexdigest()=='24298e00d3b8b25d3d11c85a7105b3817e33aeea7634a09da1b71d27d628e61c'
manifest=json.loads((case/'input-freeze.json').read_text('utf8'))
raw=(case/'near-black-input.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()==manifest['GPU_input_sha256']
trace_raw=(case/'near-black-output.bin').read_bytes()
bindings=json.loads(freeze.read_text('utf8'))['bindings']
assert hashlib.sha256(trace_raw).hexdigest()==next(b['sha256'] for b in bindings if b['path'].endswith('near-black-output.bin'))
trace=np.frombuffer(trace_raw,dtype='<f4',offset=20).reshape(2,2,2,16,10)
matrices=np.frombuffer(raw,dtype='<f4',count=18,offset=8212).astype(float).reshape(2,3,3)
tables=np.frombuffer(raw,dtype='<f4',count=2048,offset=20).astype(float).reshape(2,1024)
rows=[]
for t,gain in enumerate([-1.,1.]):
    xyz=trace[t,1,0,:,:3].astype(float)@matrices[0].T
    y=xyz[:,1]; nz=y>0; versions=[]
    for clamp in [True,False]:
        selected=np.clip(y[nz],.0703125,4608) if clamp else y[nz]
        q=np.log2(selected/18); position=(q+8)/16*1024-.5
        index=np.floor(position).astype(int); alpha=position-index
        value=tables[t,np.clip(index,0,1023)]*(1-alpha)+tables[t,np.clip(index+1,0,1023)]*alpha
        returned=(xyz[nz]*np.exp2(value-q)[:,None])@matrices[1].T
        rgb=np.zeros((16,3))
        rgb[nz]=np.where(returned<=.018,returned*4.5,1.099*np.maximum(returned,0)**.45-.099)
        assert np.isfinite(rgb).all(); versions.append(rgb)
    delta=np.max(np.abs(versions[0]-versions[1]),axis=1)
    assert np.all(delta[7:]==0) and delta[0]==0
    rows.append({'stored_gainjz':gain,'ideal_clamped_RGB':versions[0].tolist(),
        'ideal_unclamped_RGB':versions[1].tolist(),'difference_per_patch':delta.tolist(),
        'patches_above_1e_6':[int(i) for i in np.flatnonzero(delta>1e-6)],'ideal_work_Y':y.tolist()})
out={'scope':'Paired double CPU ideal diagnostic differing only in Y clamp; neither branch is the GPU acceptance model',
    'prediction_freeze_sha256':hashlib.sha256(freeze.read_bytes()).hexdigest(),
    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rows':rows,
    'limits':['Gamma0 return exponent cancellation, ideal matrix/709/interpolation and black-zero convention shared by both branches.',
        'Distinguishes mathematical candidate semantics; does not prove actual Resolve implementation.',
        'Ordinary-color precision residuals in the original GPU-versus-CPU diagnostic are not attributed to clamp.']}
path=root/'docs/experiments/hdr-near-black-clamp-diagnostic.json'; assert not path.exists()
path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'paired_separable_patches':rows[1]['patches_above_1e_6'],'old_controls_delta':rows[1]['difference_per_patch'][13:]}))
