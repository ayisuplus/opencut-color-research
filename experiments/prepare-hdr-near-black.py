"""Freeze owned near-black PNG16 and unchanged-model GPU inputs before Resolve."""
import ast
import hashlib
import json
from pathlib import Path
import struct
import zlib

import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-near-black-20261014'
analysis=case/'analysis'; analysis.mkdir(parents=True,exist_ok=True)
prior=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest_path=prior/'hdr-adapted-gpu-input.json'
assert sha(manifest_path)=='8550d2c87b38121876c3896fd6453ebdbb3d6aa356d2c97a90e1941641e1a4ad'
manifest=json.loads(manifest_path.read_text('utf8'))
old=prior/'hdr-adapted-gpu-input.bin'
assert sha(old)=='108e14d94158ed1b49ca9c0d3f5cbe21563d92fce68ede6fb550db4096a4d780'
assert sha(prior/'hdr-transfer-gpu-probe.exe')==manifest['executable_sha256']
assert sha(root/'experiments/hdr-transfer-gpu-probe.cu')==manifest['probe_source_sha256']
data=old.read_bytes()
levels=[0,1,8,64,128,200,207,208,209,211,256,512,1024,11262,25944]
colors=[[v,v,v] for v in levels]+[[11262,25944,45967]]
pixels=np.empty((1080,1920,3),dtype='>u2'); samples=[]; records=bytearray()
for i,color in enumerate(colors):
    row,col=divmod(i,4); x,y=col*480,row*270
    pixels[y:y+270,x:x+480]=color
    rgb=np.float32(color)*np.float32(1/65535)
    records.extend(struct.pack('<3fI',*rgb,0))
    samples.append({'id':i,'encoded_rgb_u16':color,'sample_xy':[x+240,y+135],
                    'roi_xyxy':[x+208,y+103,x+272,y+167],'normalized_F32_RGB':rgb.astype(float).tolist()})
def chunk(kind,payload):
    return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1920,1080,16,2,0,0,0))
png+=chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r.tobytes() for r in pixels)))+chunk(b'IEND',b'')
folder=root/'experiments/output/hdr-near-black-input'; folder.mkdir(parents=True,exist_ok=True)
image=folder/'near-black-srgb16.png'
freeze=root/'docs/experiments/hdr-near-black-input-freeze.json'
gpu_input=analysis/'near-black-input.bin'; input_freeze=analysis/'input-freeze.json'
assert all(not p.exists() for p in [image,freeze,gpu_input,input_freeze])
table_source=root/'experiments/evaluate-hdr-transfer-chain.py'
assert sha(table_source)==manifest['table_source_sha256']
nodes=[n for n in ast.parse(table_source.read_text('utf8')).body if isinstance(n,ast.FunctionDef) and n.name=='exposure_table']
assert len(nodes)==1
ns={'np':np}; exec(compile(ast.Module(body=nodes,type_ignores=[]),str(table_source),'exec'),ns)
tables=np.array([ns['exposure_table'](g) for g in [-1.,1.]],dtype='<f4')
assert tables.tobytes()==data[20:8212]
for new_index,old_index in [(13,28),(14,29),(15,16)]:
    assert records[new_index*16:(new_index+1)*16]==data[8284+old_index*16:8284+(old_index+1)*16]
image.write_bytes(png)
fixture={'scope':'Prospective new near-black colors; stored gains -1/+1 previously observed',
    'generator_sha256':sha(Path(__file__)),'source_owned':True,'dimensions':[1920,1080],
    'encoding':'RGB16 full-range PNG with sRGB intent0; same metadata as old fixture',
    'normalization':'float32(code) * float32(1/65535)',
    'fixture':{'path':image.relative_to(root).as_posix(),'bytes':len(png),'sha256':sha(image)},
    'samples':samples,'controls_new_to_old_input_indices':[[13,28],[14,29],[15,16]],
    'native_rows':['neutral-before','minus1','plus1','plus1-replay','minus1-replay','neutral-restored'],
    'new_resolve_frames_at_freeze':0,'formal_resolve_frames_total_at_freeze':54,
    'primary_model':[1,0],'primary_max_absolute_error_limit':1e-6,
    'limits':['No new native output observed. No physical-EV or arbitrary-image validation.',
        'Gamma0/class1/empty zones/zero black offset/default adapted matrix remain conditional.',
        'Upper clamp4608 and negative float inputs are outside this PNG16 protocol.']}
freeze.write_text(json.dumps(fixture,indent=2)+'\n',encoding='utf8',newline='\n')
gpu_input.write_bytes(struct.pack('<5I',0x32584448,1024,2,16,10)+tables.tobytes()+data[8212:8284]+records)
out={'scope':fixture['scope'],'preparer_sha256':sha(Path(__file__)),'fixture_sha256':sha(freeze),
    'source_input_sha256':sha(old),'matrix_manifest_sha256':sha(manifest_path),
    'probe_source_sha256':manifest['probe_source_sha256'],'executable_sha256':manifest['executable_sha256'],
    'table_source_sha256':sha(table_source),'GPU_input_sha256':sha(gpu_input),'GPU_input_bytes':gpu_input.stat().st_size,
    'stored_gains':[-1.,1.],'primary_model':[1,0],'max_abs_error_gate':1e-6,
    'max_GPU_executions':1,'max_native_frames':6,'fitted_parameters':0}
input_freeze.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'PNG_sha256':sha(image),'input_freeze_sha256':sha(freeze),'GPU_input_sha256':sha(gpu_input)}))
