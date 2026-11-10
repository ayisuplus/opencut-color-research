"""Freeze a public Bradford-form, four-decimal-inverse candidate; no fitting."""
import hashlib
import json
from pathlib import Path

import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-reference-origin-20261013/analysis'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

original=case/'hdr-transfer-gpu-input-v2.bin'
old_manifest=json.loads((case/'hdr-transfer-gpu-input-v2.json').read_text(encoding='utf8'))
assert sha(original)==old_manifest['input_sha256']
assert sha(case/'hdr-transfer-gpu-probe.exe')=='4534207287f355203465a52697b175c5f9303745e12572aacf56834e6cf1dce0'
assert sha(root/'experiments/hdr-transfer-gpu-probe.cu')==old_manifest['probe_source_sha256']
raw=bytearray(original.read_bytes())
assert len(raw)==9052

xy=np.array([[.64,.30,.15],[.33,.60,.06]])
white_xy=np.array([.3127,.329])
p=np.vstack((xy[0]/xy[1],np.ones(3),(1-xy[0]-xy[1])/xy[1]))
ws=np.array([white_xy[0]/white_xy[1],1.,(1-white_xy.sum())/white_xy[1]])
m=p*np.linalg.solve(p,ws)
# Bradford cone matrix from ICC Technical Note 02-2003.
c=np.array([[.8951,.2664,-.1614],[-.7502,1.7135,.0367],[.0389,-.0685,1.0296]])
b=np.round(np.linalg.inv(c),4)
# Fixed target literals match truncation to eight decimal places in this case.
wt=np.trunc(ws*1e8)/1e8
assert np.array_equal(wt,np.array([.95045592,1.,1.08905775]))
a=b@np.diag((c@wt)/(c@ws))@c
adapted=a@m
matrices=np.concatenate(((100*adapted).ravel(),(np.linalg.inv(adapted)/100).ravel())).astype('<f4')
start=20+2048*4
raw[start:start+72]=matrices.tobytes()
assert bytes(raw[:start])==original.read_bytes()[:start]
assert bytes(raw[start+72:])==original.read_bytes()[start+72:]
manifest={**old_manifest,'scope':'posthoc conditional Bradford-form matrix correction in unchanged own CUDA probe',
    'input_sha256':hashlib.sha256(raw).hexdigest(),'preparer_sha256':sha(Path(__file__)),
    'matrices_float32':matrices.reshape(2,3,3).tolist(),
    'matrix_modes':['rounded_Y_simple_RGB_control','Bradford_form_four_decimal_inverse_XYZ'],
    'matrix_derivation':'double public xy -> B4*diag((C*Wt)/(C*Ws))*C -> forward*100, inverse/100 -> F32',
    'source_white':ws.tolist(),'target_white':wt.tolist(),'public_cone_matrix':c.tolist(),
    'inverse_rounding_decimal_places':4,'rounded_cone_inverse':b.tolist(),
    'adaptation_matrix':a.tolist(),'max_adaptation_minus_identity':float(np.abs(a-np.eye(3)).max()),
    'original_input_sha256':sha(original),'executable_sha256':sha(case/'hdr-transfer-gpu-probe.exe'),
    'primary_source':'https://www.color.org/chadtag/',
    'changed_input_region':[start,start+72],
    'limits':old_manifest['limits']+[
        'Only the 18 stored matrix values change; source, executable, tables, RGB and hypotheses remain fixed.',
        'Four-decimal inverse and target white are fixed static candidates; actual render matrix is not captured.',
        'NumPy double matrix arithmetic does not prove exact imported-library or host execution bits.',
        'The previous matrix0 traces are a required unchanged control, not additional native evidence.']}
path=case/'hdr-adapted-gpu-input.bin'
assert not path.exists(), 'Preserve frozen inputs; use a new case for a new run.'
path.write_bytes(raw)
(case/'hdr-adapted-gpu-input.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'input_sha256':manifest['input_sha256'],'bytes':len(raw),
                  'max_adaptation_minus_identity':manifest['max_adaptation_minus_identity']}))
