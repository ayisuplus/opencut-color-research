"""Posthoc, fixed transfer-chain candidates against previously captured native frames."""
import hashlib
import json
from pathlib import Path

import numpy as np

root=Path(__file__).resolve().parents[1]

def signed_power(v,p):
    return np.copysign(np.abs(v)**p,v)

def decode709(v):
    return np.where(v<=.081,v/4.5,((np.maximum(v,-.099)+.099)/1.099)**(1/.45))

def encode709(v):
    return np.where(v<=.018,v*4.5,1.099*np.maximum(v,0)**.45-.099)

def decode_srgb(v):
    return np.where(v<=.04045,v/12.92,((np.maximum(v,-.055)+.055)/1.055)**2.4)

def encode_srgb(v):
    return np.where(v<=.0031308,v*12.92,1.055*np.maximum(v,0)**(1/2.4)-.055)

def exposure_table(e):
    raw=np.float32(np.float32(np.arange(1024,dtype=np.float32)*np.float32(16/1023))-np.float32(8))
    raw=np.float32(raw+np.float32(e))
    table=raw.copy()
    for i in range(1024):
        radius=min(51,i,1023-i)
        values=raw[i-radius:i+radius+1]
        table[i]=np.float32(float(np.sum(values,dtype=np.float64))/float(len(values)))
    return table

datasets=[('old','docs/experiments/resolve-hdr-global-grid-result.json',0,
           'neutral-before','hdr-minus1','hdr-plus1'),
          ('mixed','docs/experiments/hdr-mixed-result.json',0,
           'neutral-before','minus1','plus1'),
          ('configured_srgb','docs/experiments/resolve-hdr-srgb-pair-result.json',5,
           'pair-srgb-neutral','pair-srgb-minus1','pair-srgb-plus1')]
rows=[]
bindings=[]
for label,path,gamma,neutral,minus,plus in datasets:
    p=root/path
    source=json.loads(p.read_text(encoding='utf8'))
    bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    x=np.array(source['sample_RGB'][neutral],dtype=np.float64)
    decode=(lambda v:signed_power(v,2.4)) if gamma==0 else decode_srgb
    encode=(lambda v:signed_power(v,1/2.4)) if gamma==0 else encode_srgb
    linear=decode709(signed_power(decode(x),1/2.4))
    q=np.log2(np.clip(linear@np.array([.2126,.7152,.0722])/.18,2.**-8,2.**8))
    u=((q+8)/16).astype(np.float32)
    position=u.astype(np.float64)*1024-.5
    index=np.floor(position).astype(int)
    fraction=position-index
    for e,name in [(-1,minus),(1,plus)]:
        table=exposure_table(e).astype(np.float64)
        actual=np.array(source['sample_RGB'][name],dtype=np.float64)
        for model,alpha in [('exp2_only',None),('ideal',fraction),
                            ('nearest_1_256_half_up',np.floor(fraction*256+.5)/256)]:
            t=q+e if alpha is None else table[np.clip(index,0,1023)]*(1-alpha)+table[np.clip(index+1,0,1023)]*alpha
            adjusted=linear*2.**(t[:,None]-q[:,None])
            predicted=encode(signed_power(encode709(adjusted),2.4))
            error=predicted-actual
            rows.append({'dataset':label,'assumed_gamma_enum':gamma,'stored_gainjz':e,'interpolation':model,
                'channels':int(error.size),'max_abs_error':float(np.abs(error).max()),
                'RMSE':float(np.sqrt(np.mean(error*error))),'predicted_RGB':predicted.tolist()})
out={'scope':'posthoc conditional transfer chain, not actual enum/backend binding',
     'new_resolve_frames':0,'formal_resolve_frames_total':48,'fitted_parameters':0,
     'formula':'GammaEncode(pow_signed(BT709Encode(HDR(BT709Decode(pow_signed(GammaDecode(x),1/2.4)))),2.4))',
     'coefficient_scope':'ideal decimal standard constants, native .081 decode join; float64 except table/coordinate storage',
     'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'bindings':bindings,'comparisons':rows,
     'limits':['Gamma enum0/5 assignment to these observations is a conditional hypothesis, not a getter/runtime capture.',
               'The default gamma-direction fallback and equal physical-class scaling are assumed.',
               'Rounded Rec709 Y weights and endpoint-smoothed first table are conditional; actual matrix/table not read.',
               'Exact inverse matrices cancel under a common XYZ multiplier in this real-arithmetic model.',
               'No approximate GPU transcendental/FMA/FTZ or per-pass float32 rounding is emulated.',
               'Nearest interpolation here is CPU arithmetic, not a new GPU sampler measurement.',
               'Only existing finite nonnegative RGB samples are compared; negative/NaN/Inf/boundaries not validated.',
               'Original prospective mixed predictions and all historical results are unchanged.']}
p=root/'docs/experiments/hdr-transfer-chain-posthoc-result.json'
p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps([{k:v for k,v in r.items() if k!='predicted_RGB'} for r in rows],indent=2))
