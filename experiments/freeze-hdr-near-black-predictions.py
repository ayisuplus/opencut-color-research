"""Freeze one unchanged GPU-model run and a labelled ideal no-Y-clamp diagnostic."""
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-near-black-20261014/analysis'
prior=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest_path=case/'input-freeze.json'; manifest=json.loads(manifest_path.read_text('utf8'))
assert sha(root/'experiments/prepare-hdr-near-black.py')==manifest['preparer_sha256']
fixture_path=root/'docs/experiments/hdr-near-black-input-freeze.json'
assert sha(fixture_path)==manifest['fixture_sha256']
fixture=json.loads(fixture_path.read_text('utf8'))
assert sha(root/fixture['fixture']['path'])==fixture['fixture']['sha256']
assert sha(root/'experiments/hdr-transfer-gpu-probe.cu')==manifest['probe_source_sha256']
assert sha(prior/'hdr-transfer-gpu-probe.exe')==manifest['executable_sha256']
input_path=case/'near-black-input.bin'; assert sha(input_path)==manifest['GPU_input_sha256']
raw=input_path.read_bytes(); assert len(raw)==8540 and struct.unpack_from('<5I',raw)==(0x32584448,1024,2,16,10)
output_path=case/'near-black-output.bin'; data=output_path.read_bytes()
assert len(data)==5140 and data[:20]==raw[:20]
trace=np.frombuffer(data,dtype='<f4',offset=20).reshape(2,2,2,16,10)
assert np.isfinite(trace).all()
run_path=case/'near-black-run.json'
assert json.loads(run_path.read_text('utf8'))=={'device':'NVIDIA GeForce RTX 5090','compute':[12,0],
    'runtime':12080,'driver':13040,'pixels':16,'models':8,'trace_floats':10}
old=prior/'hdr-adapted-gpu-output.bin'
assert sha(old)=='00202ae11882bfd3e55dfd9e6802ece05f66316c7b71fd51a8d25031c6291805'
previous=np.frombuffer(old.read_bytes(),dtype='<f4',offset=20).reshape(2,2,2,48,10)
for new,old_index in fixture['controls_new_to_old_input_indices']:
    assert np.array_equal(trace[:,:,:,new,:].view('<u4'),previous[:,:,:,old_index,:].view('<u4'))
rows=[]; diagnostics=[]
matrices=np.frombuffer(raw,dtype='<f4',count=18,offset=8212).astype(float).reshape(2,3,3)
tables=np.frombuffer(raw,dtype='<f4',count=2048,offset=20).astype(float).reshape(2,1024)
for t,gain in enumerate([-1.,1.]):
    for m in range(2):
        for a in range(2):
            rows.append({'stored_gainjz':gain,'matrix_mode':m,'interpolation':a,'primary':(m,a)==(1,0),
                'predicted_RGB':trace[t,m,a,:,7:10].astype(float).tolist()})
    work=trace[t,1,0,:,:3].astype(float)
    xyz=work@matrices[0].T; y=xyz[:,1]
    result=np.zeros_like(work); nonzero=y>0
    q=np.log2(y[nonzero]/18)
    position=(q+8)/16*1024-.5; index=np.floor(position).astype(int); alpha=position-index
    value=tables[t,np.clip(index,0,1023)]*(1-alpha)+tables[t,np.clip(index+1,0,1023)]*alpha
    adjusted=(xyz[nonzero]*np.exp2(value-q)[:,None])@matrices[1].T
    result[nonzero]=np.where(adjusted<=.018,adjusted*4.5,1.099*np.maximum(adjusted,0)**.45-.099)
    assert np.isfinite(result).all()
    delta=np.max(np.abs(result-trace[t,1,0,:,7:10]),axis=1)
    diagnostics.append({'stored_gainjz':gain,'ideal_no_Y_clamp_RGB':result.tolist(),
        'delta_from_primary_per_patch':delta.tolist(),'patches_above_error_gate':[int(i) for i in np.flatnonzero(delta>1e-6)]})
out={**manifest,'scope':'Prospective near-black new-color GPU predictions; no new native render observed',
    'freezer_sha256':sha(Path(__file__)),'prediction_rows':rows,'diagnostics':diagnostics,
    'controls_trace_bits_equal':240,'primary_center_channels':96,'predicted_RGB_channels':384,
    'own_GPU_executions_reported_by_parent':1,'new_resolve_frames_at_freeze':0,'formal_resolve_frames_total_at_freeze':54,
    'diagnostic_scope':'CPU float64 with GPU work RGB, ideal matrix arithmetic/interpolation/709 return and Gamma0 ideal exponent cancellation; only a discrimination aid, not a GPU alternative acceptance model. Black defined as zero separately.',
    'limits':fixture['limits']+['Own height0 texture is not an actual Resolve backend/resource witness.'],
    'bindings':[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in
        [manifest_path,fixture_path,input_path,output_path,run_path,old,case/'GPU-execution-record.json']]}
assert len(rows)==8 and len([r for r in rows if r['primary']])==2
path=root/'docs/experiments/hdr-near-black-prediction-freeze.json'; assert not path.exists()
path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'freeze_sha256':sha(path),'old_control_trace_values':240,'separable_patches':diagnostics[1]['patches_above_error_gate']}))
