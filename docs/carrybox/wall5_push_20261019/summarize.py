"""Derive replay metrics without filtering failures or censored episodes."""
import json,statistics as st
from pathlib import Path
p=Path(__file__).resolve().parent
r=json.loads((p/'replay_result.json').read_text());assert r['status']=='PASS'
result={}
for mode,c in r['cases'].items():
    skills={}
    for skill,name in enumerate(('loco','pickup','hold')):
        done=[e for e in c['episodes'] if e['skill']==skill]
        censored=[e for e in c['censored'] if e['skill']==skill]
        steps=sum(e['steps'] for e in done+censored)
        skills[name]=dict(**c['by_skill'][name],total_sampled_steps=steps,sampled_fraction=steps/(r['num_envs']*r['steps']),
            positive_pitch_termination=sum(e['pitch']>1.1 for e in done),roll_exceeded=sum(abs(e['roll'])>.8 for e in done))
    max_error=0.
    for event in c['push_events']:
        expected=event['sample'] if mode=='set' else ([a+d for a,d in zip(event['before'],event['sample'])] if mode=='increment' else event['before'])
        max_error=max(max_error,max(abs(a-b) for a,b in zip(event['after'],expected)))
    assert max_error<1e-5
    assert sum(v['total_sampled_steps'] for v in skills.values())==19200
    result[mode]=dict(by_skill=skills,completed=c['done_count'],mean_completed_steps=c['mean_completed_steps'],
        scheduled_pushes=len(c['push_events']),applied_pushes=sum(e['applied'] for e in c['push_events']),
        cached_velocity_max_formula_error=max_error)
(p/'replay_summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
