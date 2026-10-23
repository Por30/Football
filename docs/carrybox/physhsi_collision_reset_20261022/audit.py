"""CPU-only source/config/URDF audit. Never imports either simulator."""
import ast
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).resolve().parent
P=Path('/home/cao/PhysHSI/legged_gym')
B=P/'legged_gym/envs/base';G=P/'legged_gym/envs/g1'
PKG=ROOT/'source/perceptual_ball/perceptual_ball';TASK=PKG/'tasks/manager_based/perceptual_ball'
inputs=[B/'base_config.py',B/'legged_robot_config.py',G/'carrybox_config.py',G/'carrybox_resume_config.py',G/'carrybox.py',
 P/'legged_gym/envs/motionlib/motionlib_carrybox.py',P/'legged_gym/envs/__init__.py',P/'resources/config/carrybox.yaml',
 P/'resources/robots/g1/urdf/g1_29dof.urdf',PKG/'carrybox_fullbody_collision.py',PKG/'carrybox_wall5.py',PKG/'carrybox_reward_geometry.py',
 PKG/'assets/robots/g1_29dof.py',PKG/'assets/robots/g1_29dof/config.yaml',TASK/'carrybox_wall5_env_cfg.py',TASK/'carrybox_walled_env_cfg.py',
 TASK/'mdp/carrybox_wall5.py',TASK/'mdp/carrybox_walled.py',PKG/'assets/motions/findbox/amp_manifest.json']
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}

def config(file):
 ns={'__name__':'cpu_config_audit'}
 for p in (B/'base_config.py',B/'legged_robot_config.py',file):
  tree=ast.parse(p.read_text());tree.body=[n for n in tree.body if not isinstance(n,ast.ImportFrom)]
  # Resolve the original config classes in one namespace; only package-relative
  # imports are omitted, avoiding the package's Isaac Gym initialization.
  exec(compile(tree,str(p),'exec'),ns)
 return ns['G1Cfg']()

cfg=config(G/'carrybox_config.py');resume=config(G/'carrybox_resume_config.py')
scales={k:getattr(cfg.rewards.scales,k) for k in dir(cfg.rewards.scales) if not k.startswith('_') and isinstance(getattr(cfg.rewards.scales,k),(int,float))}
assert 'collision' not in scales and 'termination' not in scales
assert cfg.asset.self_collisions==resume.asset.self_collisions==0
assert cfg.asset.terminate_after_contacts_on==[]
assert cfg.asset.box.reset_mode=='hybrid' and cfg.asset.box.hybrid_init_prob==.8
weights=np.array(cfg.asset.box.skill_init_prob);conditional=weights/weights.sum()
assert np.allclose(conditional,[2/3,1/6,1/6,0])

urdf=ET.parse(P/'resources/robots/g1/urdf/g1_29dof.urdf').getroot()
colliders={}
for link in urdf.findall('link'):
 shapes=[]
 for c in link.findall('collision'):
  g=list(c.find('geometry'))[0];o=c.find('origin')
  shapes.append(dict(type=g.tag,parameters=dict(g.attrib),origin=dict(o.attrib) if o is not None else {}))
 colliders[link.attrib['name']]=shapes
assert len([v for v in colliders.values() if v])==28 and sum(map(len,colliders.values()))==30
assert not colliders['pelvis'] and len(colliders['pelvis_contour_link'])==1
assert [x['type'] for x in colliders['left_knee_link']]==['box','box']
assert colliders['left_shoulder_pitch_link'][0]['type']=='cylinder'
constants={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse((PKG/'carrybox_fullbody_collision.py').read_text()).body
           if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
added=constants['ADDED_COLLISION_LINKS'];replaced=constants['REPLACED_COLLISION_LINKS']
assert all(not colliders[k] for k in added)
shape_count=30+len(added)+sum(1-len(colliders[k]) for k in replaced)
assert shape_count==35

manifest=json.loads((PKG/'assets/motions/findbox/amp_manifest.json').read_text())
clips=[];samples=[];sample_weights=[]
for clip in manifest['clips']:
 if clip['group']!='loco_direction':continue
 here=PKG/'assets/motions/findbox'/clip['file'];there=P/'resources/dataset/dataset_carrybox'/clip['source_file']
 h=hashlib.sha256(here.read_bytes()).hexdigest();other=hashlib.sha256(there.read_bytes()).hexdigest()
 assert h==other==clip['sha256']
 hashes[str(here)]=h;hashes[str(there)]=other
 data=torch.load(here,map_location='cpu',weights_only=True)
 v=torch.diff(data['base_position'].float(),dim=0)*60
 speed=v[:,:2].norm(dim=-1).numpy();assert np.isfinite(speed).all()
 clips.append(dict(file=clip['file'],frames=len(speed),mean_speed_mps=float(speed.mean()),sha256=h))
 samples.extend(speed.tolist());sample_weights.extend([1/len(speed)]*len(speed))
assert len(clips)==11
a=np.array(samples);w=np.array(sample_weights)/len(clips);idx=np.argsort(a)
stats=dict(equal_clip_mean_mps=float(np.sum(a*w)),p95_mps=float(a[idx][np.searchsorted(np.cumsum(w[idx]),.95)]),max_mps=float(a.max()))
phy=(G/'carrybox.py').read_text()
assert 'self.root_states[curr_env_ids, 7:13] = torch_rand_float(-0.2, 0.2' in phy
assert 'self.delay_buffer[:, env_ids, :] = self.dof_pos[env_ids] - self.default_dof_pos' in phy
assert 'self.gravity_termination_buf' not in '\n'.join(l for l in phy.splitlines() if 'self.reset_buf |=' in l)
assert 'self.success_buf' not in '\n'.join(l for l in phy.splitlines() if 'self.reset_buf |=' in l)
physics_dt=cfg.sim.dt;max_delay=(cfg.domain_rand.max_delay_timesteps-1)*physics_dt
assert abs(max_delay-.02)<1.e-12
current=(TASK/'carrybox_wall5_env_cfg.py').read_text();assert 'reset_skill_probabilities: tuple = (.75, .05, .2)' in current
assert 'ground_pickup_reset_frame_range: tuple = (0, 32)' in current
assert 'enabled_self_collisions = True' in current and 'self.rewards.early_failure = None' in current

result=dict(status='PASS',mode='CPU source/config/URDF only; no PhysHSI simulation',
 physhsi=dict(self_collisions_enabled=True,collision_reward_registered=False,active_rewards=scales,
  contact_termination_bodies=cfg.asset.terminate_after_contacts_on,collision_links=28,urdf_collision_elements=30,
  collider_shapes=colliders,replace_cylinder_with_capsule=cfg.asset.replace_cylinder_with_capsule,
  rsi_fraction=.8,default_fraction=.2,conditional_rsi_weights=weights.tolist(),conditional_rsi_probabilities=conditional.tolist(),
  total_reset_probabilities=dict(default=.2,**{k:float(v*.8) for k,v in zip(cfg.asset.box.skill,conditional)}),
  rsi_root_linear_each_axis_mps=[-.2,.2],rsi_root_angular_each_axis_radps=[-.2,.2],rsi_root_xy_max_mps=math.sqrt(2)*.2,
  default_root_velocity_each_axis=[-.5,.5],reference_joint_noise_rad=cfg.domain_rand.initial_joint_pos_offset,
  action_delay_seconds=[0,max_delay],delay_updates_per_policy_step=cfg.control.decimation,
  box_termination_carrybox=cfg.asset.box.box_termination,box_termination_resume=resume.asset.box.box_termination,
  velocity_push_enabled=cfg.domain_rand.push_robots,disturbance_enabled=cfg.domain_rand.disturbance,
  force_disturbance_interval_policy_steps=cfg.domain_rand.disturbance_interval,force_disturbance_each_axis_n=cfg.domain_rand.disturbance_range),
 wall5=dict(self_collisions_enabled=True,derived_collision_shapes=shape_count,added_links=added,replaced_links=replaced,
  collision_filter_pairs=constants['SELF_COLLISION_FILTER_PAIRS'],reset_probs=[.75,.05,.2],fixed_env_quota=True,
  pickup_reset_frames=[0,32],reference_root_xy_speed=stats,action_delay=False,ground_correction_clearance_m=.005),
 matching_loco_clips=clips,source_sha256=hashes)
for p,h in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
(D/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('AUDIT_PASS',json.dumps(dict(physhsi_shapes=30,wall5_shapes=shape_count,physhsi_reset=result['physhsi']['total_reset_probabilities'],wall5_speed=stats,max_delay_s=max_delay)))
