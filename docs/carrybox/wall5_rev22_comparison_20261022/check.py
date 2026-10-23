from pathlib import Path
import json, yaml, statistics, hashlib, datetime

D = Path(__file__).resolve().parent
R = D.parents[2]
old_run = R/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_14-09-30_wall5_v22_critic123_aux1_fresh_20261021_140925'
new_run = R/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-22_22-13-48_wall5_v26_groundfix_fresh_20261022_221344'
video = json.loads((R/'docs/carrybox/wall5_play4_rev22_20261021/selection.json').read_text())
assert Path(video['checkpoint']) == old_run/'model_6400.pt'
launches = [json.loads((R/p).read_text()) for p in (
    'docs/carrybox/wall5_critic123_aux_20261021/launch.json',
    'docs/carrybox/wall5_groundfix_20261022/launch.json')]
source_same = {}
for name,h in launches[0]['source_sha256'].items():
    if name in launches[1]['source_sha256']:
        source_same[name] = h == launches[1]['source_sha256'][name]
assert source_same['source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py']
for name,h in launches[1]['source_sha256'].items():
    assert hashlib.sha256((R/name).read_bytes()).hexdigest() == h, name
old,new = [yaml.load((p/'params/env.yaml').read_text(),Loader=yaml.BaseLoader) for p in (old_run,new_run)]
oa,na = [yaml.load((p/'params/agent.yaml').read_text(),Loader=yaml.BaseLoader) for p in (old_run,new_run)]
same = dict(torques=old['rewards']['torques']==new['rewards']['torques'],
    action_rate=old['rewards']['action_rate']==new['rewards']['action_rate'],
    actuators=old['scene']['robot']['actuators']==new['scene']['robot']['actuators'],
    physics_dt=old['sim']['dt']==new['sim']['dt'], decimation=old['decimation']==new['decimation'],
    action_scale=old['actions']['joint_pos']['scale']==new['actions']['joint_pos']['scale'])
assert all(same.values()),same
agent_diff = {k:dict(old=oa[k],new=na[k]) for k in oa if oa[k]!=na.get(k)}
keys = ['Mean episode length','AMP/style_reward','Reward/loco_task_per_step',
    'Reward/loco_walk_task_per_step','Reward/loco_action_rate_per_step','Reward/loco_torques_per_step']
curves = {}
for tag,path in [('rev22','docs/carrybox/wall5_walk_diagnosis_20261022/rev22_curve.json'),
                 ('rev26','docs/carrybox/wall5_status_20261022_2338/curve.json')]:
    rows=json.loads((R/path).read_text());by={r['iteration']:r for r in rows};curves[tag]={}
    for end in (100,400,1200,6400):
        if end not in by:continue
        window=[r for r in rows if end-100<=r['iteration']<end];assert len(window)==100
        a,b=by[end-100],by[end];n=b['Skill/loco_episodes']-a['Skill/loco_episodes']
        metrics={k:statistics.mean(r[k] for r in window) for k in keys}
        metrics['recent_loco_steps_estimate']=(b['Skill/loco_mean_steps']*b['Skill/loco_episodes']-
            a['Skill/loco_mean_steps']*a['Skill/loco_episodes'])/n
        curves[tag][str(end)]=metrics
pid=launches[1]['pid']
assert [x.decode() for x in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if x]==launches[1]['command']
result=dict(status='PASS',checked_at=datetime.datetime.now().astimezone().isoformat(),
    old_run=str(old_run),new_run=str(new_run),video_checkpoint=video['checkpoint'],same=same,
    torque_config=old['rewards']['torques'],agent_diff=agent_diff,source_same=source_same,curves=curves,
    current_training_pid=pid,production_unchanged=True,
    differences={k:dict(old=old.get(k),new=new.get(k)) for k in ('reward_geometry','grasp_geometry',
        'reset_skill_probabilities','reference_motion_dataset','height_termination_terms')})
(D/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print('COMPARISON_PASS',json.dumps(dict(same=same,curves=curves),ensure_ascii=False))
