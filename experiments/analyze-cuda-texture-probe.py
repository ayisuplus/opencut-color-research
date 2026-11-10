"""Measure own CUDA sampler outputs and compare existing HDR observations posthoc."""
import ast
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(x):
    return {'values':int(x.size),'max_abs':float(np.abs(x).max()),
            'rmse':float(np.sqrt(np.mean(x*x)))}
manifest=json.loads((case/'cuda-texture-input.json').read_text(encoding='utf8'))
raw=(case/'cuda-texture-input.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()==manifest['input_sha256']
magic,n,t,k=struct.unpack_from('<4I',raw)
assert magic==0x31585448 and n==1024 and t==8 and k==manifest['coordinates']
tables=np.frombuffer(raw,dtype='<f4',count=n*t,offset=16).reshape(t,n)
coordinates=np.frombuffer(raw,dtype='<f4',count=k,offset=16+4*n*t)
assert len(raw)==16+4*n*t+4*k
output=(case/'cuda-texture-output.bin').read_bytes()
assert struct.unpack_from('<4I',output)==(magic,n,t,k) and len(output)==16+4*t*k
gpu=np.frombuffer(output,dtype='<f4',count=t*k,offset=16).reshape(t,k)
assert np.isfinite(gpu).all()
position=coordinates.astype(float)*n-.5
index=np.floor(position).astype(int)
fraction=position-index
alpha=np.floor(fraction*256+.5)/256
lo,hi=np.clip(index,0,n-1),np.clip(index+1,0,n-1)
ideal=tables[:,lo].astype(float)*(1-fraction)+tables[:,hi].astype(float)*fraction
nearest=tables[:,lo].astype(float)*(1-alpha)+tables[:,hi].astype(float)*alpha
ramp=gpu[manifest['ramp_table_index']]
assert np.array_equal(ramp.astype(float),nearest[manifest['ramp_table_index']])
tie_ids=[d['coordinate_index'] for d in manifest['diagnostics'] if d.get('tie_delta')==0.]
assert len(tie_ids)==768
tie_even=np.rint(fraction[tie_ids]*256)/256
tie_up=alpha[tie_ids]
ties_differ=int(np.count_nonzero(tie_even!=tie_up))
source=root/'experiments/evaluate-hdr-domain-candidates.py'
assert sha(source)==manifest['transfer_source_sha256']
tree=ast.parse(source.read_text(encoding='utf8'))
nodes=[v for v in tree.body if (isinstance(v,ast.FunctionDef) and v.name.startswith('bt709_')) or
       (isinstance(v,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='bt709_threshold' for a in v.targets))]
ns={'np':np}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
observations={
    'old':json.loads((root/'docs/experiments/resolve-hdr-global-grid-result.json').read_text(encoding='utf8')),
    'mixed':json.loads((root/'docs/experiments/hdr-mixed-result.json').read_text(encoding='utf8')),
}
comparisons=[]
for group in manifest['groups']:
    start,count=group['start'],group['count']
    linear=np.array(group['linear_RGB'])
    q=np.array(group['q_float64'])
    for e,name,table_index in [(-1,'minus1',0),(1,'plus1',6)]:
        sample_name='hdr-'+name if group['name']=='old' else name
        actual=np.array(observations[group['name']]['sample_RGB'][sample_name])
        for model,lookup in [('GPU_actual_texture',gpu[table_index,start:start+count].astype(float)),
                             ('same_f32_coordinate_ideal',ideal[table_index,start:start+count]),
                             ('same_f32_coordinate_nearest_half_up',nearest[table_index,start:start+count])]:
            predicted=ns['bt709_encode'](linear*2.**(lookup[:,None]-q[:,None]))
            comparisons.append({'dataset':group['name'],'stored_gainjz':e,'model':model,
                'residual':stats(predicted-actual),'predicted_RGB':predicted.tolist()})
run=json.loads((case/'cuda-texture-run.json').read_text(encoding='utf-8-sig'))
result={'scope':'actual_source_owned_CUDA_sampler; HDR comparisons posthoc conditional on frozen color/q/table assumptions',
    'new_resolve_frames':0,'formal_resolve_frames_total':48,'device_run':run,
    'input_sha256':sha(case/'cuda-texture-input.bin'),'output_sha256':sha(case/'cuda-texture-output.bin'),
    'source_sha256':sha(root/'experiments/cuda-texture-probe.cu'),
    'preparer_sha256':sha(root/'experiments/prepare-cuda-texture-probe.py'),
    'analysis_sha256':sha(Path(__file__)),'executable_sha256':sha(case/'cuda-texture-probe.exe'),
    'sampler':manifest['sampler'],'table_width':n,'tables':t,'coordinates':k,
    'ramp_nearest_half_up_exact':True,'halfway_coordinates':len(tie_ids),
    'half_up_differs_from_ties_even_cases':ties_differ,
    'exposure_tables_GPU_minus_ideal':stats(gpu[:7].astype(float)-ideal[:7]),
    'exposure_tables_GPU_minus_nearest':stats(gpu[:7].astype(float)-nearest[:7]),
    'exposure_tables_GPU_minus_nearest_f32':stats(gpu[:7].astype(float)-nearest[:7].astype(np.float32).astype(float)),
    'comparisons':comparisons,
    'source_bindings':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in
        [case/'cuda-texture-input.json',case/'cuda-texture-run.json',
         root/'docs/experiments/resolve-hdr-global-grid-result.json',root/'docs/experiments/hdr-mixed-result.json']],
    'primary_source':'https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html#linear-filtering',
    'limits':manifest['limits']+['No CUDA backend/resource or table content has been captured from a Resolve render.',
        'The ramp tie behavior is measured for this GPU/resource/configuration, not every hardware/API.',
        'Probe returns texture values only; following exp2 and color encoding are CPU conditional calculations.',
        'No pre-observation mixed predictions were changed.']}
out=root/'docs/experiments/cuda-texture-probe-result.json'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({key:result[key] for key in ['device_run','ramp_nearest_half_up_exact',
    'halfway_coordinates','half_up_differs_from_ties_even_cases',
    'exposure_tables_GPU_minus_ideal','exposure_tables_GPU_minus_nearest',
    'exposure_tables_GPU_minus_nearest_f32']},indent=2))
print(json.dumps([{key:r[key] for key in ['dataset','stored_gainjz','model','residual']} for r in comparisons],indent=2))
