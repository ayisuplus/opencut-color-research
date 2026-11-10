"""Freeze a tiny source-owned CUDA sampler input, separate from Resolve execution."""
import ast
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'
source=root/'experiments/evaluate-hdr-domain-candidates.py'
tree=ast.parse(source.read_text(encoding='utf8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name.startswith('bt709_')) or
       (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bt709_threshold' for t in n.targets))]
ns={'np':np}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
inputs=[('old',root/'docs/experiments/resolve-hdr-global-grid-result.json','neutral-before'),
        ('mixed',root/'docs/experiments/hdr-mixed-result.json','neutral-before')]
coordinates=[]
groups=[]
weights=np.array([.2126,.7152,.0722])
for label,path,name in inputs:
    observed=np.array(json.loads(path.read_text(encoding='utf8'))['sample_RGB'][name])
    linear=ns['bt709_decode'](observed)
    q=np.log2(np.clip(linear@weights/.18,2.**-8,2.**8))
    u=((q+8)/16).astype('<f4')
    start=len(coordinates)
    coordinates.extend(u.tolist())
    groups.append({'name':label,'start':start,'count':len(u),'q_float64':q.tolist(),
                   'linear_RGB':linear.tolist(),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

# Known ramp interpolation near every half-way alpha bucket, plus clamped boundaries.
diagnostics=[]
for index in [10,511,900]:
    for bucket in range(256):
        for delta in [-2.**-12,0.,2.**-12]:
            position=index+(bucket+.5)/256+delta
            u=np.float32((position+.5)/1024)
            diagnostics.append({'coordinate_index':len(coordinates),'base_index':index,
                                'bucket':bucket,'tie_delta':delta,'u_float32':float(u)})
            coordinates.append(float(u))
for u in [-.1,0.,.5/1024,1./1024,.5,1-.5/1024,1.,1.1]:
    diagnostics.append({'coordinate_index':len(coordinates),'boundary':True,'u_float32':float(np.float32(u))})
    coordinates.append(float(np.float32(u)))

exposures=[-1.,-2.**-10,-2.**-14,0.,2.**-14,2.**-10,1.]
tables=[]
for e in exposures:
    table=np.float32(np.float32(np.arange(1024,dtype=np.float32)*np.float32(16/1023))-np.float32(8))
    table=np.float32(table+np.float32(e))
    original=table.copy()
    left=float(original[0]); right=float(original[-1])
    for i in range(1,52):
        left=(left+float(original[2*i-1]))+float(original[2*i])
        right=(right+float(original[1024-2*i]))+float(original[1023-2*i])
        table[i]=np.float32(left/float(2*i+1)); table[1023-i]=np.float32(right/float(2*i+1))
    for i in range(52,973):
        left=(float(original[i+51])-float(original[i-52]))+left
        table[i]=np.float32(left/103.)
    tables.append(table)
tables.append(np.arange(1024,dtype=np.float32))
coordinates=np.array(coordinates,dtype='<f4')
tables=np.array(tables,dtype='<f4')
header=struct.pack('<4I',0x31585448,1024,len(tables),len(coordinates))
data=header+tables.tobytes()+coordinates.tobytes()
path=case/'cuda-texture-input.bin'
path.write_bytes(data)
manifest={'scope':'source_owned_sampler_probe_not_target_runtime_or_texture_capture',
    'input_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
    'table_width':1024,'exposures':exposures,'ramp_table_index':7,
    'tables_sha256':[hashlib.sha256(t.tobytes()).hexdigest() for t in tables],
    'coordinates':len(coordinates),'groups':groups,'diagnostics':diagnostics,
    'probe_source_sha256':hashlib.sha256((root/'experiments/cuda-texture-probe.cu').read_bytes()).hexdigest(),
    'preparer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'transfer_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'sampler':{'resource':'CUDA 1D array FLOAT channel','normalized':True,'filter':'linear','address':'clamp','read':'element'},
    'limits':['These generated tables are not read from Resolve.',
        'Coordinates use frozen BT709 decode and rounded Y weights with float32 conversion.',
        'GPU probe excludes actual input/output color transforms and log2/exp2 kernel arithmetic.',
        'The zero table is sampled for diagnostics; an actual gain-disabled branch would bypass it.',
        'Mixed input has already been observed; later comparisons are posthoc, not new blind predictions.']}
(case/'cuda-texture-input.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'input_sha256':manifest['input_sha256'],'bytes':len(data),'tables':len(tables),'coordinates':len(coordinates)}))
