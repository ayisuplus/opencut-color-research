"""Freeze source-owned GPU transfer inputs against already observed native data."""
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

source=root/'experiments/evaluate-hdr-transfer-chain.py'
tree=ast.parse(source.read_text(encoding='utf8'))
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='exposure_table']
assert len(nodes)==1
ns={'np':np}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
tables=np.array([ns['exposure_table'](e) for e in [-1,1]],dtype='<f4')

# Fixed public Rec709 chromaticities; these are not a Resolve matrix capture.
primaries=np.array([[.64,.30,.15],[.33,.60,.06]])
white=np.array([.3127,.3290])
columns=np.vstack((primaries[0]/primaries[1],np.ones(3),
                   (1-primaries[0]-primaries[1])/primaries[1]))
w=np.array([white[0]/white[1],1.,(1-white.sum())/white[1]])
m=columns*np.linalg.solve(columns,w)
matrices=np.concatenate(((100*m).ravel(),(np.linalg.inv(m)/100).ravel())).astype('<f4')

datasets=[('old','docs/experiments/resolve-hdr-global-grid-result.json',0,
           'neutral-before','hdr-minus1','hdr-plus1'),
          ('mixed','docs/experiments/hdr-mixed-result.json',0,
           'neutral-before','minus1','plus1'),
          ('configured_srgb','docs/experiments/resolve-hdr-srgb-pair-result.json',5,
           'pair-srgb-neutral','pair-srgb-minus1','pair-srgb-plus1')]
previous=json.loads((root/'docs/experiments/hdr-transfer-chain-posthoc-result.json').read_text(encoding='utf8'))
expected={b['path']:b['sha256'] for b in previous['bindings']}
pixels=bytearray()
groups=[]
for label,path,gamma,neutral,minus,plus in datasets:
    p=root/path
    assert sha(p)==expected[path], path
    observed=np.array(json.loads(p.read_text(encoding='utf8'))['sample_RGB'][neutral],dtype='<f4')
    assert observed.shape==(16,3) and np.isfinite(observed).all() and (observed>=0).all()
    start=len(pixels)//16
    for rgb in observed:
        pixels.extend(struct.pack('<3fI',*rgb,gamma))
    groups.append({'name':label,'path':path,'sha256':sha(p),'start':start,'count':16,
                   'assumed_gamma_enum':gamma,'neutral':neutral,'minus':minus,'plus':plus})
data=struct.pack('<5I',0x32584448,1024,2,len(pixels)//16,10)+tables.tobytes()+matrices.tobytes()+pixels
manifest={'scope':'posthoc source-owned full-float32 conditional GPU model',
    'input_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'pixels':len(pixels)//16,
    'exposures':[-1,1],'table_sha256':[hashlib.sha256(t.tobytes()).hexdigest() for t in tables],
    'matrices_float32':matrices.reshape(2,3,3).tolist(),'matrix_derivation':'fixed Rec709 xy, D65; forward*100, inverse/100',
    'groups':groups,'probe_source_sha256':sha(root/'experiments/hdr-transfer-gpu-probe.cu'),
    'preparer_sha256':sha(Path(__file__)),'table_source_sha256':sha(source),
    'compile_flags':['-arch=sm_120','-O2','--fmad=false','--ftz=true'],
    'model_order':'((exposure_index*2+matrix_mode)*2+interpolation)',
    'matrix_modes':['rounded_Y_simple_RGB','public_xy_XYZ_forward_inverse'],
    'interpolation':['own_FLOAT1D_linear_clamp_texture','software_float32_ideal_weight'],
    'trace_order':['work_R','work_G','work_B','q','u','table_t','gain','output_R','output_G','output_B'],
    'fitted_parameters':0,'new_resolve_frames':0,
    'limits':['Inputs are existing observations; this is posthoc, not an unseen prediction.',
        'Gamma 0/0/5 assignment, class multiplier 1 and default direction are conditional.',
        'Both matrix paths and generated tables are fixed mathematical hypotheses, not target captures.',
        'CUDA intrinsics, explicit FMA and FTZ approximate the mathematical stages; instruction equivalence is not claimed.',
        'The stages run in one own kernel; compiler optimization and per-pass target rounding remain unbound.',
        'Own texture resource and CUDA backend do not establish the Resolve render backend or resource.',
        'Only finite nonnegative input RGB and exposures -1/+1 are compared; exact-zero bypass is excluded.']}
assert not (case/'hdr-transfer-gpu-input-v2.bin').exists(), 'Preserve frozen input; use a new case for a new run.'
(case/'hdr-transfer-gpu-input-v2.bin').write_bytes(data)
(case/'hdr-transfer-gpu-input-v2.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'bytes':len(data),'pixels':manifest['pixels'],'input_sha256':manifest['input_sha256']}))
