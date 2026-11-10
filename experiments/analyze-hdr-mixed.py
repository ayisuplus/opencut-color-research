"""Evaluate frozen HDR candidates on the unseen mixed input; never refit them."""
import ast
import hashlib
import json
import os
from pathlib import Path

os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2
import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-mixed-20261013'
def read(p):
    return json.loads(p.read_text(encoding='utf8'))
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(x):
    return {'channels':int(x.size),'max_abs':float(np.abs(x).max()),
            'rmse':float(np.sqrt(np.mean(x*x)))}

plan_path=case/'analysis/frozen-plan.json'
receipt_path=case/'analysis/native-results.json'
freeze_path=root/'docs/experiments/hdr-mixed-input-freeze.json'
plan,receipt,freeze=read(plan_path),read(receipt_path),read(freeze_path)
assert sha(plan_path)==receipt['plan_sha256'] and sha(freeze_path)==plan['freeze_sha256']
assert sha(root/freeze['fixture']['path'])==freeze['fixture']['sha256']
assert receipt['failure'] is None and len(receipt['completed'])==len(plan['rows'])==6
assert len({j['JobId'] for j in receipt['owned_jobs']})==6
assert [r['job_id'] for r in receipt['completed']]==[j['JobId'] for j in receipt['owned_jobs']]
assert receipt['baseline_input_gate']['exact_expected_normalization']
final=read(case/'runtime/finalize.json')
final=json.loads(final['content'][0]['text'])['result']
assert final['source_full_snapshot_match'] and final['source_jobs_preserved']==23 and not final['rendering']
assert final['completed_006_saved_exported'] and final['owned_jobs_complete']==6
pixels,samples,frames={},{},[]
for row,frozen,job in zip(receipt['completed'],plan['rows'],receipt['owned_jobs']):
    assert all(row[k]==v for k,v in frozen.items())
    assert Path(row['file']).resolve()==(Path(job['TargetDir'])/job['OutputFilename']).resolve()
    name=row['name']
    assert row['status']=={'JobStatus':'Complete','CompletionPercentage':100}
    raw=Path(row['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['image_sha256']
    measured=read(case/'analysis'/f'{name}-measured.json')
    assert measured['opencv_crosscheck_exact'] and measured['crosscheck_channels']==6220800
    rgb=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_UNCHANGED)[:,:,::-1].astype('<f4')
    assert rgb.shape==(1080,1920,3) and np.isfinite(rgb).all()
    assert hashlib.sha256(rgb.tobytes()).hexdigest()==row['RGB_sha256']==measured['rgb_pixels_sha256']
    validation=read(case/'analysis'/f'{name}-readback-validation.json')
    assert validation['passed'] and sha(Path(validation['readback']))==validation['readback_sha256']
    assert validation['source_sha256']==row['sha256'] and sha(Path(row['grade']))==row['sha256']
    assert sha(case/'analysis'/f'{name}-readback-validation.json')==row['validation_sha256']
    pixels[name]=rgb
    samples[name]=np.array([rgb[s['sample_xy'][1],s['sample_xy'][0]] for s in freeze['samples']],dtype=float)
    assert np.array_equal(samples[name],np.array([s['rgb'] for s in measured['samples']]))
    frames.append({'name':name,'stored_gainjz':row['stored_gainjz'],'tools':row['tools'],
                   'EXR_sha256':row['image_sha256'],'RGB_sha256':row['RGB_sha256'],
                   'source_grade_sha256':row['sha256'],'native_grade_sha256':validation['readback_sha256']})

controls={name:bool(np.array_equal(pixels['neutral-before'],pixels[name])) for name in ['zero','neutral-restored']}
controls['plus1_replay']=bool(np.array_equal(pixels['plus1'],pixels['plus1-replay']))
assert all(controls.values())
spatial={}
for name,rgb in pixels.items():
    pairs=[]
    for i in range(6):
        a,b=freeze['samples'][i],freeze['samples'][i+6]
        ax0,ay0,ax1,ay1=a['roi_xyxy']; bx0,by0,bx1,by1=b['roi_xyxy']
        delta=rgb[ay0:ay1,ax0:ax1].astype(float)-rgb[by0:by1,bx0:bx1].astype(float)
        pairs.append({'ids':[i,i+6],'center':stats(samples[name][i]-samples[name][i+6]),
                      'ROI':stats(delta),'ROI_exact':bool(np.all(delta==0))})
    spatial[name]=pairs

residuals={}
for name,e in [('minus1',-1),('zero',0),('plus1',1)]:
    residuals[name]={}
    for model,predicted in freeze['predictions'][str(e)].items():
        delta=np.array(predicted)-samples[name]
        residuals[name][model]={label:stats(delta[ids]) for label,ids in [
            ('all',list(range(16))),('mixed_unique',list(range(6))),('gray',list(range(12,15))),('black',[15])]}

source=root/'experiments/evaluate-hdr-domain-candidates.py'
assert sha(source)==freeze['transfer_source_sha256']
tree=ast.parse(source.read_text(encoding='utf8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name.startswith('bt709_')) or
       (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bt709_threshold' for t in n.targets))]
ns={'np':np}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
linear0=ns['bt709_decode'](samples['neutral-before'])
reference={}
for name,e in [('minus1',-1),('plus1',1)]:
    ratios=ns['bt709_decode'](samples[name][:15])/linear0[:15]
    b=np.log2(ratios)-e
    reference[name]={'B_RGB':b.tolist(),'within_mixed_patch_B_spread':stats(np.ptp(b[:6],axis=1)),
                     'within_gray_patch_B_spread':stats(np.ptp(b[12:15],axis=1))}
reference['plus_minus_B_difference']=stats(np.array(reference['plus1']['B_RGB'])-np.array(reference['minus1']['B_RGB']))

context=[]
codes=np.array([s['encoded_rgb_u16'] for s in freeze['samples']])
for channel in range(3):
    for level in sorted(set(codes[:6,channel].tolist())):
        ids=np.where(codes[:,channel]==level)[0].tolist()
        assert len(ids)==5
        mixed_ids=[i for i in ids if i<6]
        assert len(mixed_ids)==2
        context.append({'channel':'RGB'[channel],'input_u16':level,'ids':ids,
            'mixed_unique_ids':mixed_ids,
            'input_normalized_f64':level/65535.,
            'minus1_output_range':float(np.ptp(samples['minus1'][ids,channel])),
            'plus1_output_range':float(np.ptp(samples['plus1'][ids,channel])),
            'minus1_mixed_unique_output_range':float(np.ptp(samples['minus1'][mixed_ids,channel])),
            'plus1_mixed_unique_output_range':float(np.ptp(samples['plus1'][mixed_ids,channel]))})

result={'scope':'six native unseen mixed-input frames; frozen candidates, no refit',
    'native_frames_added':6,'formal_native_frames_total':48,
    'plan_sha256':sha(plan_path),'receipt_sha256':sha(receipt_path),
    'freeze_sha256':sha(freeze_path),'fixture_sha256':freeze['fixture']['sha256'],
    'analysis_sha256':sha(Path(__file__)),'finalize_sha256':sha(case/'runtime/finalize.json'),
    'manual_OpenCV_crosscheck_channels_per_frame':6220800,
    'baseline_input_gate':receipt['baseline_input_gate'],'source_005_full_snapshot_match':True,
    'frames':frames,'controls_exact':controls,'spatial_duplicates':spatial,
    'frozen_candidate_residuals':residuals,'BT709_arithmetic_reference':reference,
    'same_channel_input_different_context':context,
    'sample_RGB':{k:v.tolist() for k,v in samples.items()},
    'limits':freeze['limits']+["Only the six spatial pairs and fixed interior-table colors were tested.",
        "Common multipliers and B use frozen BT709 arithmetic; they do not identify the actual working domain.",
        "Main candidate inputs remain predeclared float64 PNG normalized codes; baseline float32 discrepancy is reported.",
        "No physical-EV, full-kernel/backend, endpoint, subnormal or arbitrary-image equivalence claim."]}
out=root/'docs/experiments/hdr-mixed-result.json'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'controls':controls,'spatial_all_ROIs_exact':all(p['ROI_exact'] for rows in spatial.values() for p in rows),
    'candidate_errors':{k:{m:v['all']['max_abs'] for m,v in values.items()} for k,values in residuals.items()},
    'context_max_output_range':max(v['plus1_output_range'] for v in context),
    'B_within_mixed_plus1':reference['plus1']['within_mixed_patch_B_spread'],
    'B_plus_minus_difference':reference['plus_minus_B_difference']},indent=2))
