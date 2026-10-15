"""G1 reset/camera audit and complete wall4 training smoke; no formal model reuse."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--num_envs',type=int,default=16);AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import ast,copy,json,statistics,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,torch,trimesh,gymnasium as gym
from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import quat_apply,quat_apply_inverse,quat_mul,quat_conjugate,euler_xyz_from_quat,wrap_to_pi,quat_from_euler_xyz
from perceptual_ball.tasks.manager_based.perceptual_ball import carrybox_walled_env_cfg as config
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task,carrybox as base_task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy
from perceptual_ball.carrybox_amp import joint_mapping
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent/str(args.num_envs);OUT.mkdir(exist_ok=True)
# Reuse previously validated actual collider/depth protocol, using wall4 scene.
src=(ROOT/'scripts/rsl_rl/smoke_carrybox_walled.py').read_text();node=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='geometry');geometry_src=ast.get_source_segment(src,node)
# Isolate obstacle probes from randomly placed robots in the enlarged 16-env sample.
# Production-mounted camera/body occlusion are audited separately after restoring RSI.
geometry_src=geometry_src.replace('        origin = b.scene.env_origins', '''        robot = b.scene['robot']
        parked = robot.data.root_state_w.clone()
        parked[:, :3] = b.scene.env_origins + torch.tensor([-10., -10., 1.], device=args.device)
        parked[:, 7:] = 0.
        robot.write_root_state_to_sim(parked)
        b.sim.forward()
        origin = b.scene.env_origins''')
exec(compile(geometry_src,'geometry_audit','exec'));args.variant=4

def main():
 torch.set_num_threads(2);cfg=config.CarryBoxWalled4EnvCfg();agent=config.CarryBoxWalled4PPORunnerCfg();cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.seed=42
 env=gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0',cfg=cfg);b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);report=dict(num_envs=args.num_envs,contract=b.checkpoint_contract(),rsi={},depth_changes={})
 try:
  robot=b.scene['robot'];s=task.state(b)
  if args.num_envs==16:
   geometry(b,w,cfg,report);print("GEOMETRY_PASS",flush=True)
   cfg.reference_init=True;cfg.search_prob=.02;cfg.camera_position_error_m=0.
   feet=robot.find_bodies(['left_ankle_roll_link','right_ankle_roll_link'],preserve_order=True)[0]
   verts=[]
   urdf=Path('/home/cao/PhysHSI/legged_gym/resources/robots/g1/urdf/g1_29dof.urdf');xml=ET.parse(urdf).getroot()
   for side in ['left','right']:
    mesh=trimesh.load(urdf.parent/'../meshes'/f'{side}_ankle_roll_link.STL',process=False)
    verts.append(torch.tensor(np.asarray(mesh.vertices).copy(),device=b.device,dtype=torch.float32))
   request={};original_write=robot.write_root_state_to_sim
   def capture(root_state,env_ids=None):
    ids=torch.arange(b.num_envs,device=b.device) if env_ids is None else env_ids
    request['ids']=ids.clone();request['state']=root_state.clone();return original_write(root_state,env_ids=env_ids)
   robot.write_root_state_to_sim=capture
   def snapshot():
    bottoms=[]
    for i,v in enumerate(verts):
     q=robot.data.body_link_quat_w[:,feet[i],None].expand(-1,len(v),-1);pos=robot.data.body_link_pos_w[:,feet[i],None]
     bottoms.append((pos+quat_apply(q.reshape(-1,4),v[None].expand(b.num_envs,-1,-1).reshape(-1,3)).reshape(b.num_envs,-1,3))[:,:,2].min(-1).values-b.scene.env_origins[:,2])
    roll,pitch,_=euler_xyz_from_quat(robot.data.root_quat_w)
    return dict(root=robot.data.root_state_w.tolist(),head_height=task.head_height(b).tolist(),foot_bottom=torch.stack(bottoms,-1).tolist(),gravity=robot.data.projected_gravity_b.tolist(),roll=wrap_to_pi(roll).tolist(),pitch=wrap_to_pi(pitch).tolist(),fell=task.fallen(b).tolist(),tipped=task.tipped(b).tolist())
   with torch.inference_mode():
    report['reset_audit']={}
    for skill in range(3):
     cfg.reset_skill_probabilities=tuple(float(i==skill) for i in range(3));obs,_=w.reset();read=robot.data.root_state_w[request['ids']]
     torch.testing.assert_close(read[:,:7],request['state'][:,:7],atol=2e-5,rtol=0)
     report['reset_audit'][str(skill)]=dict(request=request['state'].tolist(),actual=snapshot())
     assert not task.fallen(b).any() and not task.tipped(b).any()
     assert min(min(v) for v in report['reset_audit'][str(skill)]['actual']['foot_bottom']) >= .0049
    saved_root=robot.data.root_state_w.clone();saved_joints=robot.data.joint_pos.clone();saved_targets=robot.data.joint_pos_target.clone()
    b._reset_idx(torch.tensor([0],device=b.device))
    torch.testing.assert_close(robot.data.root_state_w[1:],saved_root[1:])
    torch.testing.assert_close(robot.data.joint_pos[1:],saved_joints[1:])
    torch.testing.assert_close(robot.data.joint_pos_target[1:],saved_targets[1:])
    report['partial_reset_preserves_other_states_and_targets']=True
    cam=b.scene['depth_camera'];cam.update(.02,force_recompute=True);with_body=cam.data.output['distance_to_image_plane'].clone()
    saved_views=cam._views[:]
    try:
     for idx,m in enumerate(cam.mesh_manifest):
      if '/Robot/' in m['root']:
       pose=cam._views[idx].get_transforms().clone();pose[:,:3]+=1000.;cam._views[idx]=pose
     cam._is_outdated[:]=True;without_body=cam.data.output['distance_to_image_plane'].clone()
     blocked=(without_body-with_body)>.001
     report['body_occlusion_pixels']=blocked.flatten(1).sum(-1).tolist()
     assert blocked.any(), 'No body pixels detected in held-reference pose'
    finally:
     cam._views=saved_views;cam._is_outdated[:]=True
    # G1 nominal D435 mount: actual parent transforms after root translation + yaw.
    ids=torch.arange(b.num_envs,device=b.device);root=robot.data.root_state_w.clone();root[:,:3]+=torch.tensor([.3,-.2,.1],device=b.device);a=torch.full((b.num_envs,),.6,device=b.device);z=torch.zeros_like(a)
    root[:,3:7]=quat_mul(quat_from_euler_xyz(z,z,a),root[:,3:7]);robot.write_root_state_to_sim(root,env_ids=ids);b.sim.forward();robot.update(0.)
    cam=b.scene['depth_camera'];cam.update(.02,force_recompute=True);data=cam.data
    q=robot.data.body_link_quat_w[:,s.torso];pos=robot.data.body_link_pos_w[:,s.torso];offset=torch.tensor(cfg.scene.depth_camera.offset.pos,device=b.device).expand(b.num_envs,3)
    torch.testing.assert_close(data.pos_w,pos+quat_apply(q,offset),atol=2e-5,rtol=0)
    mount=torch.tensor(cfg.scene.depth_camera.offset.rot,device=b.device).expand(b.num_envs,4);forward=torch.tensor([1.,0.,0.],device=b.device).expand(b.num_envs,3)
    torch.testing.assert_close(quat_apply(data.quat_w_world,forward),quat_apply(quat_mul(q,mount),forward),atol=3e-5,rtol=0)
    joint=xml.find("joint[@name='d435_joint']");assert joint.find('parent').get('link')=='torso_link';xyz=[float(v) for v in joint.find('origin').get('xyz').split()];assert np.allclose(xyz,cfg.scene.depth_camera.offset.pos,atol=1e-7)
    report['camera']=dict(parent=cfg.scene.depth_camera.prim_path,pos=xyz,rpy=joint.find('origin').get('rpy'),intrinsics=data.intrinsic_matrices[0].tolist(),mesh_count=len(cam.mesh_manifest),body_meshes=[m['root'] for m in cam.mesh_manifest if '/Robot/' in m['root']],max_parent_transform_error=float((data.pos_w-pos-quat_apply(q,offset)).abs().max()))
   robot.write_root_state_to_sim=original_write
   (OUT/'audit.json').write_text(json.dumps(report,indent=2));print('G1_AUDIT_PASS',flush=True)
   cfg.camera_position_error_m=.01
  cfg.reference_init=True;cfg.reset_skill_probabilities=(.6,.3,.1);cfg.search_prob=.02
  with torch.inference_mode():w.reset()
  runner=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'train'),device=args.device)
  if args.num_envs==16:
   with torch.inference_mode():
    cfg.reset_skill_probabilities=(1.,0.,0.);obs,_=w.reset();report['fresh_first_steps']=[]
    for step in range(4):
     action=runner.alg.policy.act_inference(obs);entry=dict(step=step,roll=wrap_to_pi(euler_xyz_from_quat(robot.data.root_quat_w)[0]).tolist(),raw_action=action.tolist(),root_z=robot.data.root_pos_w[:,2].tolist(),head_z=task.head_height(b).tolist());obs,_,done,_=w.step(action);term=b.action_manager.get_term('joint_pos');entry.update(done=done.tolist(),targets=term.processed_actions.tolist(),saturation=term.target_saturation.tolist());report['fresh_first_steps'].append(entry)
    assert not any(any(row['done']) for row in report['fresh_first_steps']),report['fresh_first_steps']
    cfg.reset_skill_probabilities=(.6,.3,.1);w.reset()
  old=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_21-08-12_wall4_handoff_v6_amp15_20261014_210808/model_14000.pt'
  try:runner.load(str(old));raise AssertionError('old contract accepted')
  except ValueError:pass
  times=[];log=runner.log
  def capture(locs,*a,**kw):
   times.append(dict(collection=locs['collection_time'],learning=locs['learn_time'],total=locs['collection_time']+locs['learn_time']));return log(locs,*a,**kw)
  runner.log=capture;before=copy.deepcopy(runner.alg.amp.state_dict());runner.learn(8 if args.num_envs==4096 else 3,init_at_random_ep_len=True)
  assert runner.alg.motion_metadata['clip_count']==15 and runner.alg.motion_metadata==s.library.metadata
  assert any(not torch.equal(before[k],v) for k,v in runner.alg.amp.state_dict().items())
  runner.save(str(OUT/'model.pt'));fresh=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'resumed'),device=args.device);fresh.load(str(OUT/'model.pt'));fresh.learn(2)
  for model in [fresh.alg.policy,fresh.alg.amp]:assert all(torch.isfinite(v).all() for v in model.state_dict().values())
  with torch.inference_mode():
   obs=w.get_observations();changed=obs.clone();changed['box_pose_target']+=100.;changed['amp']+=100.;torch.testing.assert_close(fresh.alg.policy.act_inference(obs),fresh.alg.policy.act_inference(changed));torch.testing.assert_close(fresh.alg.policy.evaluate(obs),fresh.alg.policy.evaluate(changed))
  if args.num_envs==16:export_depth_policy(fresh.alg.policy,obs,str(OUT/'export'))
  report['skill_completed_episodes']=s.episode_counts.tolist();report['skill_valid_window_steps']=s.valid_amp_steps.tolist()
  assert int(s.valid_amp_steps[0])>0, 'loco never formed a complete AMP history'
  report.update(timings=times,amp_dataset=fresh.alg.motion_metadata,restore=True,finite=True,updates=10 if args.num_envs==4096 else 5,initialization='fresh',status='PASS')
  if args.num_envs==4096:
   report.update(warm_mean_seconds=statistics.mean(t['total'] for t in times[2:]),warm_max_seconds=max(t['total'] for t in times[2:]));assert report['warm_max_seconds']<=6.,times
  (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('G1_RESET_PASS',flush=True)
 finally:env.close()
try:main()
except Exception:
 import traceback
 traceback.print_exc()
 raise
finally:app.close(wait_for_replicator=False)
