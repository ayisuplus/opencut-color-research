"""Check the frozen GPU probe and compare fixed previous native observations."""
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

manifest=json.loads((case/'hdr-transfer-gpu-input-v2.json').read_text(encoding='utf8'))
assert sha(case/'hdr-transfer-gpu-input-v2.bin')==manifest['input_sha256']
assert sha(root/'experiments/hdr-transfer-gpu-probe.cu')==manifest['probe_source_sha256']
assert sha(case/'hdr-transfer-gpu-probe.cu')==manifest['probe_source_sha256']
assert sha(root/'experiments/prepare-hdr-transfer-gpu.py')==manifest['preparer_sha256']
assert sha(root/'experiments/evaluate-hdr-transfer-chain.py')==manifest['table_source_sha256']
raw=(case/'hdr-transfer-gpu-input-v2.bin').read_bytes()
header=struct.unpack_from('<5I',raw)
assert header==(0x32584448,1024,2,48,10) and len(raw)==9052
output=(case/'hdr-transfer-gpu-output-v2.bin').read_bytes()
assert struct.unpack_from('<5I',output)==header and len(output)==15380
trace=np.frombuffer(output,dtype='<f4',offset=20).reshape(2,2,2,48,10)
assert np.isfinite(trace).all()
assert np.array_equal(trace[0,:,:,:,:5],trace[1,:,:,:,:5])
assert np.array_equal(trace[:,:,0,:,:5],trace[:,:,1,:,:5])
assert np.array_equal(trace[:,0,:,:,0:3],trace[:,1,:,:,0:3])
previous_path=root/'docs/experiments/hdr-transfer-chain-posthoc-result.json'
previous=json.loads(previous_path.read_text(encoding='utf8'))
rows=[]
for g in manifest['groups']:
    p=root/g['path']
    assert sha(p)==g['sha256']
    samples=json.loads(p.read_text(encoding='utf8'))['sample_RGB']
    s,n=g['start'],g['count']
    for t,(e,name) in enumerate(zip(manifest['exposures'],[g['minus'],g['plus']])):
        actual=np.array(samples[name],dtype=np.float64)
        for m in range(2):
            for a in range(2):
                predicted=trace[t,m,a,s:s+n,7:10].astype(np.float64)
                error=predicted-actual
                old=next(r for r in previous['comparisons'] if r['dataset']==g['name'] and
                         r['stored_gainjz']==e and r['interpolation']=='ideal')
                rows.append({'dataset':g['name'],'assumed_gamma_enum':g['assumed_gamma_enum'],
                    'stored_gainjz':e,'matrix_mode':manifest['matrix_modes'][m],
                    'interpolation':manifest['interpolation'][a],'channels':int(error.size),
                    'max_abs_error':float(np.abs(error).max()),'RMSE':float(np.sqrt(np.mean(error*error))),
                    'prior_float64_ideal_max_abs_error':old['max_abs_error'],
                    'max_prediction_delta_from_prior_float64_ideal':float(np.abs(predicted-np.array(old['predicted_RGB'])).max()),
                    'predicted_RGB':predicted.tolist()})
run=json.loads((case/'hdr-transfer-gpu-run-v2.json').read_text(encoding='utf-8-sig'))
assert run['pixels']==48 and run['models']==8 and run['trace_floats']==10
result={'scope':manifest['scope'],'fitted_parameters':0,'new_resolve_frames':0,
    'formal_resolve_frames_total':48,'device_run':run,'compile_flags':manifest['compile_flags'],
    'groups':manifest['groups'],'matrices_float32':manifest['matrices_float32'],
    'model_order':manifest['model_order'],'trace_order':manifest['trace_order'],
    'comparisons':rows,'finite_trace_values':int(trace.size),
    'stage_invariants':['work/q/u equal across exposure and interpolation','work equal across matrix mode'],
    'bindings':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in [
        root/'experiments/hdr-transfer-gpu-probe.cu',root/'experiments/prepare-hdr-transfer-gpu.py',
        Path(__file__),previous_path,case/'hdr-transfer-gpu-input-v2.bin',case/'hdr-transfer-gpu-input-v2.json',
        case/'hdr-transfer-gpu-output-v2.bin',case/'hdr-transfer-gpu-run-v2.json',case/'hdr-transfer-gpu-probe.exe',
        case/'build-hdr-transfer-gpu.cmd',case/'hdr-transfer-gpu-build-v2.log',case/'hdr-transfer-gpu-probe.cu']],
    'limits':manifest['limits']}
out=root/'docs/experiments/hdr-transfer-gpu-result.json'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps([{k:v for k,v in r.items() if k!='predicted_RGB'} for r in rows],indent=2))
