"""G1 FK of all three complete pickups; self-collision contact readback, no training."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import json,hashlib
from pathlib import Path
import torch,gymnasium as gym
import perceptual_ball.tasks
import omni.physics.tensors as physics
from pxr import PhysxSchema,Usd,UsdPhysics
from isaaclab.utils.math import quat_apply,quat_apply_inverse,quat_mul,quat_conjugate,yaw_quat
from perceptual_ball.carrybox_amp import FindBoxMotionLibrary,DEFAULT_DATASET_PATH,joint_mapping
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
D=Path(__file__).resolve().parent

def main():
 torch.set_num_threads(2);cfg=CarryBoxWalled5EnvCfg();cfg.scene.num_envs=4;cfg.seed=42;cfg.sim.device=args.device
 cfg.scene.robot.spawn.articulation_props.enabled_self_collisions=True
 for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
 env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg);b=env.unwrapped
 try:
  env.reset();r=b.scene['robot'];s=task.state(b);ids=torch.arange(4,device=b.device)
  lib=FindBoxMotionLibrary(DEFAULT_DATASET_PATH,device=b.device);mapping=torch.argsort(torch.tensor(joint_mapping(r.joint_names),device=b.device))
  hands=r.find_bodies(['left_palm_link','right_palm_link'],preserve_order=True)[0];rows=[]
  data=[torch.load(lib.root/n,weights_only=True,map_location=b.device) for n in lib.clip_names]
  specs=[(i,f) for i,g in enumerate(lib.clip_groups) if g=='pickUp' for f in range(len(lib.clips[i][0]))]
  with torch.inference_mode():
   for start in range(0,len(specs),4):
    batch=specs[start:start+4];count=len(batch);batch += [batch[-1]]*(4-count)
    root=r.data.default_root_state.clone();root[:,:3]=b.scene.env_origins;root[:,7:]=0
    joints=r.data.default_joint_pos.clone();box_delta=torch.empty(4,3,device=b.device)
    for j,(i,f) in enumerate(batch):
     q=lib.clips[i][2][f:f+1];unyaw=quat_conjugate(yaw_quat(q));root[j,2]+=data[i]['base_height'][f]+.05
     root[j,3:7]=quat_mul(unyaw,q)[0];joints[j]=lib.clips[i][0][f,mapping];box_delta[j]=quat_apply(unyaw,data[i]['box_pos_local'][f:f+1].float())[0]
    r.write_root_link_state_to_sim(root);r.write_joint_state_to_sim(joints,torch.zeros_like(joints));b.sim.forward();b.scene.update(b.physics_dt)
    corr=task.reference_ground_correction(b,ids);root[:,2]+=corr;r.write_root_link_state_to_sim(root);b.sim.forward();b.scene.update(b.physics_dt)
    box=root[:,:3]+box_delta;palms=r.data.body_link_pos_w[:,hands];rubber=r.data.body_pos_w[:,s.hands]
    relative=palms-box[:,None];surf=(relative.abs()-relative.new_tensor([.15,.15,.125])).clamp_min(0).norm(dim=-1)
    for j,(i,f) in enumerate(batch[:count]):
     rows.append(dict(clip=lib.clip_names[i],frame=f,contact_index=int(data[i]['contact_index']),root_box_xy=float(box_delta[j,:2].norm()),root_box_3d=float(box_delta[j].norm()),box_height=float(box[j,2]-b.scene.env_origins[j,2]),pelvis_height=float(root[j,2]-b.scene.env_origins[j,2]),head_height=float(task.head_height(b)[j]),palm_to_surface=surf[j].tolist(),rubber_center_to_box=(rubber[j]-box[j]).norm(dim=-1).tolist(),hand_center_to_box=float((rubber[j].mean(0)-box[j]).norm()),palms_relative_box=relative[j].tolist(),source_palm_fk_max_error=float((palms[j]-root[j,None,:3]-quat_apply(quat_conjugate(yaw_quat(lib.clips[i][2][f:f+1])).expand(2,-1),data[i]['link_position'][f,:2].float())).abs().max())))
   # All robot-on-robot contacts, excluding ground and box. Suspended pose probes.
   pv=physics.create_simulation_view('torch');pv.set_subspace_roots('/')
   contacts=pv.create_rigid_contact_view('/World/envs/env_0/Robot/*',filter_patterns=['/World/envs/env_0/Robot/'+n for n in r.body_names],max_contact_data_count=4096)
   probes={}
   for mode in ('default','pickup_prefix','hold','crossed_arms'):
    root=r.data.default_root_state.clone();root[:,:3]=b.scene.env_origins;root[:,2]+=3.;root[:,7:]=0
    q=r.data.default_joint_pos.clone()
    if mode in ('pickup_prefix','hold'):
     i=lib.clip_names.index('pick_up/pick_up_03.pt' if mode=='pickup_prefix' else 'hold/hold_box_01.pt');f=16 if mode=='pickup_prefix' else 150;q[:]=lib.clips[i][0][f,mapping]
    if mode=='crossed_arms':
     for name,value in [('left_shoulder_pitch_joint',-.7),('right_shoulder_pitch_joint',-.7),('left_shoulder_roll_joint',-.7),('right_shoulder_roll_joint',.7),('left_elbow_joint',1.8),('right_elbow_joint',1.8)]:q[:,r.joint_names.index(name)]=value
    r.write_root_link_state_to_sim(root);r.write_joint_state_to_sim(q,torch.zeros_like(q));r.set_joint_position_target(q);b.scene.write_data_to_sim();b.sim.forward()
    peak=None
    for _ in range(12):
     b.sim.step(render=False);b.scene.update(b.physics_dt);force=contacts.get_contact_force_matrix(b.physics_dt).norm(dim=-1)
     peak=force if peak is None else torch.maximum(peak,force)
     assert torch.isfinite(r.data.root_state_w).all() and torch.isfinite(r.data.joint_vel).all()
    sensors=list(contacts.sensor_paths) if hasattr(contacts,'sensor_paths') else []
    ix=(peak>.1).nonzero().tolist();probes[mode]=dict(shape=list(peak.shape),sensor_paths=sensors,peak_n=float(peak.max()),contacts=[dict(sensor=sensors[a] if sensors else a,other=r.body_names[c],force=float(peak[a,c])) for a,c in ix],joint_velocity_max=float(r.data.joint_vel.abs().max()))
  stage=b.sim.get_initial_stage();art=[str(p.GetPath()) for p in Usd.PrimRange(stage.GetPrimAtPath('/World/envs/env_0/Robot')) if p.HasAPI(PhysxSchema.PhysxArticulationAPI)]
  result=dict(status='PASS',rows=rows,self_contact_probes=probes,articulations={p:PhysxSchema.PhysxArticulationAPI(stage.GetPrimAtPath(p)).GetEnabledSelfCollisionsAttr().Get() for p in art},manifest_sha256=lib.metadata['manifest_sha256'])
  (D/'geometry_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('AUDIT_PASS',json.dumps(probes),flush=True)
 finally:env.close()
try:main()
finally:app.close(wait_for_replicator=False)
