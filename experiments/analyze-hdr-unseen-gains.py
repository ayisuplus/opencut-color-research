"""Compare immutable prospective predictions to admitted native float EXRs."""
import hashlib
import json
import os
from pathlib import Path

os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2
import numpy as np

root=Path(__file__).resolve().parents[1]
case=root/'evidence/local/resolve-hdr-unseen-gains-20261013'

def read(p): return json.loads(p.read_text('utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(x):
    return {'channels':int(x.size),'max_abs':float(np.abs(x).max()),
            'RMSE':float(np.sqrt(np.mean(x*x)))}

prediction_path=root/'docs/experiments/hdr-unseen-gains-prediction-freeze.json'
assert sha(prediction_path)=='13b8f6c48c87dc6406fc4d904a79d9e16fd0732dba12392b078a470d9b353862'
prediction=read(prediction_path)
plan_path=case/'analysis/frozen-plan.json'; plan=read(plan_path)
receipt_path=case/'analysis/native-results.json'; receipt=read(receipt_path)
assert sha(plan_path)==receipt['plan_sha256'] and receipt['failure'] is None
assert len(receipt['completed'])==len(receipt['owned_jobs'])==len(plan['rows'])==6
assert plan['prediction_freeze_sha256']==sha(prediction_path)
owned_ids=[j['JobId'] for j in receipt['owned_jobs']]
assert len(set(owned_ids))==6 and not set(owned_ids)&{j['JobId'] for j in plan['expected']['jobs']}
assert [r['job_id'] for r in receipt['completed']]==owned_ids
assert all(sha(case/p)==value for p,value in plan['source_snapshot_hashes'].items())
assert receipt['baseline_input_gate']['exact_expected_normalization']
assert len(receipt['baseline_input_gate']['full_patches_exact'])==16 and all(receipt['baseline_input_gate']['full_patches_exact'])
assert receipt['baseline_input_gate']['EXR_sha256']==receipt['completed'][0]['image_sha256']
fixture_path=root/'docs/experiments/hdr-mixed-input-freeze.json'; fixture=read(fixture_path)
assert sha(fixture_path)==plan['freeze_sha256']==receipt['fixture_freeze_sha256']==prediction['fixture_sha256']
assert sha(root/fixture['fixture']['path'])==fixture['fixture']['sha256']
assert [s['id'] for s in fixture['samples']]==list(range(16))
export_path=case/'analysis/completed-007-export-evidence.json'; export=read(export_path)
assert export['export_returned_true_before_source_assertion']
archive=Path(export['archive']['path'])
assert archive.resolve()==(case/'completed-007.drp').resolve()
assert archive.stat().st_size==export['archive']['bytes'] and sha(archive)==export['archive']['sha256']
assert all(sha(case/b['path'])==b['sha256'] for b in export['bindings'])
final_path=case/'runtime/finalize-recovery.json'
final=json.loads(read(final_path)['content'][0]['text'])['result']
assert final['source_full_snapshot_match'] and final['source_jobs_preserved']==23
assert final['project']=='EXPO_005_HDR_CONTEXT' and not final['rendering']
pixels={}; frames=[]; samples={}
for done,row,job in zip(receipt['completed'],plan['rows'],receipt['owned_jobs']):
    assert all(done[k]==v for k,v in row.items()) and done['job_id']==job['JobId']
    assert done['status']=={'JobStatus':'Complete','CompletionPercentage':100}
    path=Path(done['file']); assert path.resolve()==(Path(job['TargetDir'])/job['OutputFilename']).resolve()
    assert sha(path)==done['image_sha256']
    measured=read(case/'analysis'/f"{row['name']}-measured.json")
    assert measured['opencv_crosscheck_exact'] and measured['crosscheck_channels']==6220800
    validation=read(case/'analysis'/f"{row['name']}-readback-validation.json")
    assert validation['passed'] and validation['source_sha256']==row['sha256']==sha(Path(row['grade']))
    assert sha(Path(validation['readback']))==validation['readback_sha256']
    assert sha(case/'analysis'/f"{row['name']}-readback-validation.json")==done['validation_sha256']
    rgb=cv2.imdecode(np.frombuffer(path.read_bytes(),dtype=np.uint8),cv2.IMREAD_UNCHANGED)[:,:,::-1].astype('<f4')
    assert rgb.shape==(1080,1920,3) and np.isfinite(rgb).all()
    assert hashlib.sha256(rgb.tobytes()).hexdigest()==done['RGB_sha256']==measured['rgb_pixels_sha256']
    name=row['name']; pixels[name]=rgb
    samples[name]=np.array([rgb[s['sample_xy'][1],s['sample_xy'][0]] for s in fixture['samples']],dtype=float)
    assert np.array_equal(samples[name],np.array([s['rgb'] for s in measured['samples']]))
    frames.append({'name':name,'stored_gainjz':row['stored_gainjz'],'EXR_sha256':done['image_sha256'],
                   'RGB_sha256':done['RGB_sha256'],'native_grade_sha256':validation['readback_sha256'],
                   'source_grade_sha256':row['sha256'],'min_RGB':float(rgb.min()),'max_RGB':float(rgb.max())})
for s in fixture['samples']:
    r,c=divmod(s['id'],4)
    expected=np.float32(s['encoded_rgb_u16'])*np.float32(1/65535)
    assert np.all(pixels['neutral-before'][r*270:(r+1)*270,c*480:(c+1)*480].view('<u4')==expected.view('<u4'))
rgb_hashes={r['name']:r['RGB_sha256'] for r in frames}
controls={'neutral_restored':rgb_hashes['neutral-before']==rgb_hashes['neutral-restored'],
          'plus_half_replay':rgb_hashes['plus-half']==rgb_hashes['plus-half-replay']}
assert all(controls.values())
comparisons=[]
for name,gain in [('minus-half',-.5),('plus-half',.5),('plus-two',2.)]:
    for model in [p for p in prediction['prediction_rows'] if p['stored_gainjz']==gain]:
        expected=np.array(model['predicted_RGB'],dtype=float); roi_stats=[]
        for i,s in enumerate(fixture['samples']):
            x0,y0,x1,y1=s['roi_xyxy']
            assert x1-x0==y1-y0==64
            roi_stats.append(stats(pixels[name][y0:y1,x0:x1].astype(float)-expected[i]))
        center=stats(samples[name]-expected); max_roi=max(s['max_abs'] for s in roi_stats)
        comparisons.append({k:model[k] for k in ['stored_gainjz','matrix_mode','interpolation','primary']}|
            {'center':center,'ROI_max_abs':max_roi,'ROI_channels':sum(s['channels'] for s in roi_stats),
             'passed_prespecified_error_gate':max(center['max_abs'],max_roi)<=prediction['primary_max_absolute_error_limit']})
assert len(comparisons)==12 and len([r for r in comparisons if r['primary']])==3
assert sum(r['center']['channels'] for r in comparisons if r['primary'])==144
out={'scope':'prospective three stored gains on existing mixed fixture; no fitted parameters or backend capture',
    'new_resolve_frames':6,'formal_resolve_frames_total':54,'fitted_parameters':0,
    'prediction_freeze_sha256':sha(prediction_path),'frames':frames,'controls':controls,
    'sample_RGB':{k:v.tolist() for k,v in samples.items()},'comparisons':comparisons,
    'primary_all_pass':all(r['passed_prespecified_error_gate'] for r in comparisons if r['primary']),
    'max_error_gate':prediction['primary_max_absolute_error_limit'],
    'bindings':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in
        [Path(__file__),prediction_path,plan_path,receipt_path,fixture_path,export_path,final_path]],
    'limits':prediction['limits']+['A passing finite prospective test does not prove every input or actual implementation path.']}
path=root/'docs/experiments/hdr-unseen-gains-result.json'
assert not path.exists(); path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'primary':[r for r in comparisons if r['primary']],'controls':controls,'new_frames':6},indent=2))
