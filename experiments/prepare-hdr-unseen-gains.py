"""Freeze unseen stored-Global predictions inputs; do not call Resolve."""
import ast
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

root=Path(__file__).resolve().parents[1]
prior=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'
case=root/'evidence/local/resolve-hdr-unseen-gains-20261013/analysis'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

manifest_path=prior/'hdr-adapted-gpu-input.json'
assert sha(manifest_path)=='8550d2c87b38121876c3896fd6453ebdbb3d6aa356d2c97a90e1941641e1a4ad'
manifest=json.loads(manifest_path.read_text(encoding='utf8'))
previous=prior/'hdr-adapted-gpu-input.bin'
assert sha(previous)=='108e14d94158ed1b49ca9c0d3f5cbe21563d92fce68ede6fb550db4096a4d780'
assert sha(prior/'hdr-transfer-gpu-probe.exe')==manifest['executable_sha256']
assert sha(root/'experiments/hdr-transfer-gpu-probe.cu')==manifest['probe_source_sha256']
raw=previous.read_bytes()
group=next(g for g in manifest['groups'] if g['name']=='mixed')
assert group['start']==16 and group['count']==16 and group['assumed_gamma_enum']==0
fixture_path=root/'docs/experiments/hdr-mixed-input-freeze.json'
assert sha(fixture_path)=='9cb32be3c50b6e0f5342259fa18669f6dcc745439eb8cccb5b9dabc490b892aa'
fixture=json.loads(fixture_path.read_text(encoding='utf8'))
assert sha(root/fixture['fixture']['path'])==fixture['fixture']['sha256']
pixels=bytearray()
for sample in fixture['samples']:
    rgb=np.float32(sample['encoded_rgb_u16'])*np.float32(1/65535)
    pixels.extend(struct.pack('<3fI',*rgb,0))
assert bytes(pixels)==raw[8284+16*16:8284+32*16]
table_source=root/'experiments/evaluate-hdr-transfer-chain.py'
assert sha(table_source)==manifest['table_source_sha256']
nodes=[n for n in ast.parse(table_source.read_text(encoding='utf8')).body
       if isinstance(n,ast.FunctionDef) and n.name=='exposure_table']
assert len(nodes)==1
ns={'np':np}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(table_source),'exec'),ns)
batches=[('half',[-.5,.5]),('two-control',[2.,1.])]
case.mkdir(parents=True,exist_ok=True)
assert not any((case/f'{name}-input.bin').exists() for name,_ in batches)
records=[]
for name,exposures in batches:
    tables=np.array([ns['exposure_table'](e) for e in exposures],dtype='<f4')
    if name=='two-control':
        assert tables[1].tobytes()==raw[20+1024*4:20+2048*4]
    data=struct.pack('<5I',0x32584448,1024,2,16,10)+tables.tobytes()+raw[8212:8284]+pixels
    path=case/f'{name}-input.bin'; path.write_bytes(data)
    records.append({'name':name,'stored_gainjz':exposures,'path':path.relative_to(root).as_posix(),
        'bytes':len(data),'sha256':sha(path),
        'table_sha256':[hashlib.sha256(t.tobytes()).hexdigest() for t in tables]})
out={'scope':'prospective fixed stored Global -0.5/+0.5/+2; no new native output observed',
    'preparer_sha256':sha(Path(__file__)),'fixture_sha256':sha(fixture_path),
    'matrix_manifest_sha256':sha(manifest_path),'source_input_sha256':sha(previous),
    'probe_source_sha256':manifest['probe_source_sha256'],'executable_sha256':manifest['executable_sha256'],
    'table_source_sha256':sha(table_source),'batches':records,'primary_model':[1,0],
    'fitted_parameters':0,'native_actions_attempted':False,'new_resolve_frames':0,
    'normalization':'float32(code) * float32(1/65535), frozen before new baseline',
    'primary_max_absolute_error_limit':1e-6,
    'limit_scope':'prospective finite sampled/ROI RGB comparison, not full-formula acceptance',
    'native_rows':['neutral-before','minus-half','plus-half','plus-two','plus-half-replay','neutral-restored'],
    'controls':['baseline and restored neutral match fixed input over full image',
        'plus-half replay full image bit-equal','owned plus1 GPU control matches prior mixed trace bits'],
    'limits':['Stored values are not new UI/physical-EV calibration.',
        'Gamma0, class1, adapted default matrix, own height0 CUDA texture remain conditional.',
        'Actual Resolve backend and resource not captured; current user reply is Auto.',
        'Same mixed fixture; only exposure settings are unseen. Stop on failed identity/readback/baseline gates.']}
(case/'input-freeze.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'batches':records,'new_frames':0}))
