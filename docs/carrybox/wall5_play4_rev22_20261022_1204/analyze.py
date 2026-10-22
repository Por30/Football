"""Describe this recorded rollout only; exclude states after automatic reset."""
from pathlib import Path
import json
import numpy as np
p=Path(__file__).resolve().parent
r=json.loads((p/'recording.json').read_text())
a=json.loads((p/'trajectory.json').read_text())
origins=np.array(r['env_origins']);rows=[]
for i in range(4):
    samples=[s for s in a if s['episode_steps'][i]>0]
    robot=np.array([s['robot'][i] for s in samples])
    box=np.array([s['box'][i] for s in samples])
    distance=np.linalg.norm((robot-box)[:,:2],axis=1)
    hands=np.array([s['hand_box_distance'][i] for s in samples])
    contacts=np.array([s['hand_contacts'][i] for s in samples])
    bottom=np.array([s['box_bottom_clearance'][i] for s in samples])
    head=np.array([s['head_height'][i] for s in samples])
    rows.append(dict(robot=i+1,initial_skill=r['initial_skills'][i],
        samples_excluding_post_reset=len(samples),
        first_xy_distance=float(distance[0]),last_xy_distance=float(distance[-1]),
        xy_distance_min=float(distance.min()),hand_box_min=float(hands.min()),hand_box_mean=float(hands.mean()),
        box_center_height_min=float(box[:,2].min()-origins[i,2]),box_center_height_max=float(box[:,2].max()-origins[i,2]),
        box_bottom_clearance_max=float(bottom.max()),head_height_min=float(head.min()),
        pelvis_height_min=float(robot[:,2].min()-origins[i,2]),
        either_hand_contact_steps=int(contacts.any(-1).sum()),both_hand_contact_steps=int(contacts.all(-1).sum()),
        strict_success=any(s['success'][i] for s in samples) or any(e['success'] for e in r['episodes'] if e['env_id']==i)))
result=dict(checkpoint=r['checkpoint'],policy_mode=r['policy_mode'],duration_s=20,
    not_success_rate_evaluation=True,robots=rows,episodes=r['episodes'])
(p/'behavior.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
