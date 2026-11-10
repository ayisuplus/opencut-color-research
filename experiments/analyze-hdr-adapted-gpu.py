"""Compare fixed matrix correction against existing observations and GPU control."""
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

manifest=json.loads((case/'hdr-adapted-gpu-input.json').read_text(encoding='utf8'))
assert sha(case/'hdr-adapted-gpu-input.bin')==manifest['input_sha256']
assert sha(root/'experiments/prepare-hdr-adapted-gpu.py')==manifest['preparer_sha256']
assert sha(root/'experiments/hdr-transfer-gpu-probe.cu')==manifest['probe_source_sha256']
assert sha(case/'hdr-transfer-gpu-probe.exe')==manifest['executable_sha256']
old_path=root/'docs/experiments/hdr-transfer-gpu-result.json'
assert sha(old_path)=='4a1d103c3a3afdb97fe42c4a1603dfebdfb060ce1310f8c018c0f82af6690360'
old=json.loads(old_path.read_text(encoding='utf8'))
data=(case/'hdr-adapted-gpu-output.bin').read_bytes()
assert len(data)==15380 and struct.unpack_from('<5I',data)==(0x32584448,1024,2,48,10)
trace=np.frombuffer(data,dtype='<f4',offset=20).reshape(2,2,2,48,10)
previous_path=case/'hdr-transfer-gpu-output-v2.bin'
assert sha(previous_path)=='7af9e74fb026343de4d9f319d6b0b71c2229aa2baa97aee5bfb7d18d3ea0f3f0'
previous_data=previous_path.read_bytes()
assert len(previous_data)==15380 and struct.unpack_from('<5I',previous_data)==(0x32584448,1024,2,48,10)
previous=np.frombuffer(previous_data,dtype='<f4',offset=20).reshape(trace.shape)
assert np.isfinite(trace).all()
assert np.array_equal(trace[:,0].view('<u4'),previous[:,0].view('<u4'))
assert np.array_equal(trace[:,:,:,:,:3],previous[:,:,:,:,:3])
rows=[]
for g in manifest['groups']:
    p=root/g['path']; assert sha(p)==g['sha256']
    samples=json.loads(p.read_text(encoding='utf8'))['sample_RGB']
    for t,(e,name) in enumerate(zip([-1,1],[g['minus'],g['plus']])):
        actual=np.array(samples[name],dtype=np.float64)
        for m in range(2):
            for a in range(2):
                s,n=g['start'],g['count']
                rgb=trace[t,m,a,s:s+n,7:10].astype(float)
                error=rgb-actual
                prior_matrix=['rounded_Y_simple_RGB','public_xy_XYZ_forward_inverse'][m]
                prior=next(r for r in old['comparisons'] if r['dataset']==g['name'] and r['stored_gainjz']==e and
                           r['matrix_mode']==prior_matrix and r['interpolation']==manifest['interpolation'][a])
                rows.append({'dataset':g['name'],'stored_gainjz':e,'assumed_gamma_enum':g['assumed_gamma_enum'],
                    'matrix_mode':manifest['matrix_modes'][m],'interpolation':manifest['interpolation'][a],
                    'channels':int(error.size),'max_abs_error':float(np.abs(error).max()),
                    'RMSE':float(np.sqrt(np.mean(error*error))),'previous_max_abs_error':prior['max_abs_error'],
                    'predicted_RGB':rgb.tolist()})
run=json.loads((case/'hdr-adapted-gpu-run.json').read_text(encoding='utf-8-sig'))
assert run['pixels']==48 and run['models']==8 and run['trace_floats']==10
out={'scope':manifest['scope'],'fitted_parameters':0,'new_resolve_frames':0,
    'formal_resolve_frames_total':48,'device_run':run,'comparisons':rows,
    'matrix0_control_trace_bit_equal':True,'control_trace_values':int(trace[:,0].size),
    'work_trace_equal_across_matrix_change':True,'finite_trace_values':int(trace.size),
    'changed_input_region':manifest['changed_input_region'],
    'matrices_float32':manifest['matrices_float32'],'adaptation_matrix':manifest['adaptation_matrix'],
    'inverse_rounding_decimal_places':4,'primary_source':manifest['primary_source'],
    'bindings':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in [
        Path(__file__),root/'experiments/prepare-hdr-adapted-gpu.py',old_path,
        root/'experiments/hdr-transfer-gpu-probe.cu',case/'hdr-transfer-gpu-probe.exe',
        case/'hdr-transfer-gpu-input-v2.bin',case/'hdr-transfer-gpu-output-v2.bin',
        case/'hdr-adapted-gpu-input.bin',case/'hdr-adapted-gpu-input.json',
        case/'hdr-adapted-gpu-output.bin',case/'hdr-adapted-gpu-run.json']],
    'limits':manifest['limits']}
(root/'docs/experiments/hdr-adapted-gpu-result.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps([{k:v for k,v in r.items() if k!='predicted_RGB'} for r in rows if r['matrix_mode']==manifest['matrix_modes'][1]],indent=2))
