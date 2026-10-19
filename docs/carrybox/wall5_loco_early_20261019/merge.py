from pathlib import Path
import json
p=Path(__file__).resolve().parent
modes=('policy','hold_reference','default_pose','follow_reference','hold_reference_zero_velocity')
result=None
for mode in modes:
 r=json.loads((p/('case_'+mode+'.json')).read_text());assert r['status']=='PASS' and r['initial_states_equal'] and r['initial_observations_equal']
 if result is None:result=r
 else:
  assert r['checkpoint_sha256']==result['checkpoint_sha256'] and r['original_contract']==result['original_contract']
  result['cases'].update(r['cases'])
result['independent_process_per_condition']=True
(p/'replay_result.json').write_text(json.dumps(result)+'\n')
print('ALL_FIVE_CASES_PASS')
