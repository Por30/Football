"""Verify revision26 ground correction, remaining boundaries, PPO/AMP and restore."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser);args=parser.parse_args();app=AppLauncher(args).app
import copy,json,hashlib
from pathlib import Path
import torch,gymnasium as gym
import perceptual_ball.tasks
from isaaclab.utils.math import quat_from_euler_xyz,quat_apply,quat_conjugate,yaw_quat
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5 import tipped
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as common,carrybox_physhsi as phy
from perceptual_ball.carrybox_physhsi import interpolate
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
D=Path(__file__).resolve().parent;R=D.parents[2]

def check_ground(b,w):
 s=common.state(b);robot=b.scene['robot'];all_ids=torch.arange(b.num_envs,device=b.device)
 term=b.action_manager.get_term('joint_pos');box=b.scene['box'];platform=b.scene['platform']
 original=common.reference_ground_correction;capture={}
 def clearance(ids):
  heights=[]
  for body,points in zip(s.feet,s.foot_support_points):
   q=robot.data.body_link_quat_w[ids,body,None].expand(-1,len(points),-1)
   z=quat_apply(q,points[None].expand(len(ids),-1,-1))[:,:,2]+robot.data.body_link_pos_w[ids,body,None,2]
   heights.append(z.amin(-1)-b.scene.env_origins[ids,2])
  return torch.stack(heights,-1).amin(-1)
 def measured(e,ids):
  result=original(e,ids)
  capture.update(ids=ids.clone(),before=clearance(ids).clone(),root=robot.data.root_state_w[ids].clone(),
                 joint=robot.data.joint_pos[ids].clone(),joint_velocity=robot.data.joint_vel[ids].clone())
  return result
 common.reference_ground_correction=measured
 rows=[];seen=set()
 try:
  for batch in range(10):
   w.reset();after=clearance(all_ids);before=capture['before'];shift=s.reset_ground_correction
   assert torch.isfinite(after).all() and torch.isfinite(shift).all()
   assert (shift>=0).all() and (after>=.005-2e-5).all(),(batch,float(after.min()))
   torch.testing.assert_close(after,before+shift,atol=2e-5,rtol=0)
   expected=capture['root'].clone();expected[:,2]+=shift
   torch.testing.assert_close(robot.data.root_state_w,expected,atol=2e-5,rtol=1e-5)
   torch.testing.assert_close(robot.data.root_vel_w,s.reset_root_velocity,atol=2e-5,rtol=1e-5)
   torch.testing.assert_close(robot.data.joint_pos,capture['joint'])
   torch.testing.assert_close(robot.data.joint_vel,capture['joint_velocity'])
   q=robot.data.joint_pos[:,term._joint_ids]
   torch.testing.assert_close(term.delay.buffer,q[None].expand(5,-1,-1))
   torch.testing.assert_close(term.processed_actions,q)
   # Verify final paired box and support geometry, after parent clamps.
   loco=s.skills==0;z=b.scene.env_origins[:,2]
   from isaaclab.utils.math import matrix_from_quat
   # Fetch actual box dimensions rather than guessing from the visible mesh.
   from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox import BOX_SIZE
   extent=(matrix_from_quat(box.data.root_quat_w)[:,2].abs()*box.data.root_pos_w.new_tensor(BOX_SIZE)/2).sum(-1)
   torch.testing.assert_close(box.data.root_pos_w[loco,2]-z[loco]-extent[loco],torch.full_like(z[loco],.005),atol=2e-5,rtol=0)
   for clip in s.reference_clip.unique().tolist():
    if clip<0:continue
    ids=((s.reference_clip==clip)&~loco).nonzero().flatten()
    if not len(ids):continue
    data=s.references[clip];times=s.reference_time[ids]
    if int(s.skills[ids[0]])==1:seen.add(clip)
    nativeq=interpolate(data['base_quat'].float()[:,[3,0,1,2]],times,True)
    offset=quat_apply(quat_conjugate(yaw_quat(nativeq)),interpolate(data['box_pos_local'].float(),times))
    rawbox=capture['root'][ids,:3]+offset
    expected_box=rawbox.clone();expected_box[:,2]+=shift[ids]
    expected_box[:,2]=torch.maximum(expected_box[:,2],z[ids]+extent[ids]+.005)
    torch.testing.assert_close(box.data.root_pos_w[ids],expected_box,atol=2e-5,rtol=1e-5)
    active=s.support_active[ids]
    if active.any():
     top=(rawbox[:,2]-z[ids]-.125-.005).clamp_min(0.)+shift[ids]
     top=torch.minimum(top,box.data.root_pos_w[ids,2]-z[ids]-extent[ids]-.005).clamp_min(0.)
     actual_top=platform.data.root_pos_w[ids,2]-z[ids]+.4
     torch.testing.assert_close(actual_top[active],top[active],atol=2e-5,rtol=0)
     assert (actual_top[active]<=box.data.root_pos_w[ids[active],2]-z[ids[active]]-extent[ids[active]]+2e-5).all()
   inactive=~s.support_active
   torch.testing.assert_close(platform.data.root_pos_w[inactive,2]-z[inactive],torch.full_like(z[inactive],-5.),atol=2e-5,rtol=0)
   immediate={k:int(getattr(b.cfg.terminations,k).func(b).sum()) for k in ('tipped','fell_pelvis','fell_head','fell_hip','box_speed')}
   assert not any(immediate.values()),immediate
   for i in range(b.num_envs):
    rows.append(dict(batch=batch,env_id=i,kind='default' if bool(s.default_reset[i]) else ('loco','pickup','hold')[int(s.skills[i])],clip=int(s.reference_clip[i]),frame=float(s.reference_time[i]),before_m=float(before[i]),after_m=float(after[i]),shift_m=float(shift[i]),support=bool(s.support_active[i])))
  assert len(seen)==3,seen
  ids=torch.tensor([61,3,29,5,47,12,31],device=b.device)
  survivors=torch.tensor([0,1,2,4,6],device=b.device)
  oldroot=robot.data.root_state_w[survivors].clone();oldq=robot.data.joint_pos[survivors].clone()
  oldv=robot.data.joint_vel[survivors].clone();oldbuf=term.delay.buffer[:,survivors].clone()
  oldbox=box.data.root_state_w[survivors].clone();oldplatform=platform.data.root_state_w[survivors].clone()
  b._reset_idx(ids)
  for a,c in [(robot.data.root_state_w[survivors],oldroot),(robot.data.joint_pos[survivors],oldq),(robot.data.joint_vel[survivors],oldv),(term.delay.buffer[:,survivors],oldbuf),(box.data.root_state_w[survivors],oldbox),(platform.data.root_state_w[survivors],oldplatform)]:torch.testing.assert_close(a,c,atol=2e-5,rtol=1e-5)
  assert (clearance(ids)>=.005-2e-5).all()
  print('GROUND_CHECK_PASS',len(rows),'minimum',min(r['after_m'] for r in rows),flush=True)
 finally:common.reference_ground_correction=original
 return rows


def main():
 # Exact scalar thresholds independently of quaternion round-off.
 import ast,types
 tree=ast.parse((R/'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py').read_text())
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='tipped')
 roll=torch.tensor([.5,-.5,.500001,-.500001,0.,0.,0.,0.],dtype=torch.float64)
 pitch=torch.tensor([0.,0.,0.,0.,1.1,-1.1,1.100001,-1.100001],dtype=torch.float64)
 ns={'euler_xyz_from_quat':lambda _: (roll,pitch,torch.zeros_like(roll)),'wrap_to_pi':lambda x:x}
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'tipped-boundary','exec'),ns)
 fake=types.SimpleNamespace(scene={'robot':types.SimpleNamespace(data=types.SimpleNamespace(root_quat_w=None))})
 assert ns['tipped'](fake).tolist()==[False,False,True,True,False,False,True,True]
 torch.set_num_threads(2)
 cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg()
 assert cfg.terminations.tipped is not None and cfg.episode_length_s==20.
 for cls in (CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg):assert cls().terminations.tipped is not None
 cfg.scene.num_envs=64;cfg.seed=42;cfg.sim.device=args.device
 for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
  setattr(cfg.sim.physx,name,262144)
 env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
 try:
  b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset()
  terms=set(b.termination_manager.active_terms)
  assert terms=={'time_out','invalid','fell_pelvis','fell_head','fell_hip','box_speed','tipped'},terms
  robot=b.scene['robot'];box=b.scene['box'];manager=b.termination_manager
  with torch.inference_mode():
   reset_rows=check_ground(b,w)
   # Lift the whole robot clear of height/contact thresholds to isolate angles.
   root=robot.data.root_state_w.clone();root[:,:3]=b.scene.env_origins;root[:,2]+=2.
   roll=torch.zeros(64,device=b.device);pitch=roll.clone();zero=roll.clone()
   roll[:4]=torch.tensor([.49,.51,-.49,-.51],device=b.device);pitch[4:8]=torch.tensor([1.09,1.11,-1.09,-1.11],device=b.device)
   root[:,3:7]=quat_from_euler_xyz(roll,pitch,zero);root[:,7:]=0.
   robot.write_root_state_to_sim(root);box.write_root_velocity_to_sim(torch.zeros(64,6,device=b.device))
   b.sim.forward();b.episode_length_buf.zero_()
   expected=torch.zeros(64,device=b.device,dtype=torch.bool);expected[[1,3,5,7]]=True
   assert torch.equal(tipped(b),expected)
   assert torch.equal(manager.compute(),expected),'Angle boundary does not match PhysHSI'
   # Zero quaternion angles and change only the whole-robot height.
   root[:,3:7]=torch.tensor([1.,0.,0.,0.],device=b.device);root[:,2]=b.scene.env_origins[:,2]-2.
   robot.write_root_state_to_sim(root);b.sim.forward()
   for key in ('fell_pelvis','fell_head','fell_hip'):
    term=getattr(b.cfg.terminations,key);assert term.func(b,**term.params).all(),key
   assert manager.compute().all() and manager.terminated.all()
   # Each existing strict boundary remains covered by its existing unit test;
   # isolate box speed and timeout here in the live termination manager.
   root[:,2]=b.scene.env_origins[:,2]+2.;robot.write_root_state_to_sim(root);b.sim.forward()
   vel=torch.zeros(64,6,device=b.device);vel[:2,0]=torch.tensor([3.01,2.99],device=b.device)
   box.write_root_velocity_to_sim(vel)
   done=manager.compute();assert done[0] and not done[1:].any()
   box.write_root_velocity_to_sim(torch.zeros_like(vel));b.episode_length_buf[:]=b.max_episode_length
   assert manager.compute().all() and manager.time_outs.all() and not manager.terminated.any()
   obs,_=w.reset();b.episode_length_buf.zero_()
  shapes={k:list(v.shape) for k,v in obs.items()}
  assert shapes=={'proprio':[64,372],'perception':[64,4,27,48],'amp':[64,600],'box_pose_target':[64,10],'critic_state':[64,123],'action_bounds':[64,58]},shapes
  contract=b.checkpoint_contract();assert contract['migration_revision']==26
  oldrun=Path(json.loads((D/'before.json').read_text())['old_run']);oldpath=oldrun/'model_0.pt'
  old=torch.load(oldpath,map_location='cpu',weights_only=False)['environment_contract']
  changed={k for k in contract.keys()|old.keys() if contract.get(k)!=old.get(k)}
  assert changed=={'migration_revision','roll_termination','roll_limit','termination_profile','failure_diagnostics','reference_ground_clearance','paired_reference_ground_shift'},changed
  profile_delta={k for k in contract['termination_profile'] if contract['termination_profile'][k]!=old['termination_profile'][k]}
  assert profile_delta=={'roll_rad','pitch_rad'} and contract['roll_limit']==.5
  runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
  before=copy.deepcopy(runner.alg.policy.state_dict())
  with torch.inference_mode():
   for step in range(agent.num_steps_per_env):
    if step==0:b.episode_length_buf[[0,3]]=b.max_episode_length-1
    action=runner.alg.act(obs);obs,reward,done,extra=w.step(action)
    runner.alg.process_env_step(obs,reward,done,extra)
    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
    if step==0:
     assert done[[0,3]].all()
     assert extra['terminal_observations']['obs']['critic_state'].shape[-1]==123
     assert 'Skill/loco_tilt_at_episode_end_fraction' in extra['log']
     assert 'Skill/loco_tipped_fraction' not in extra['log']
   runner.alg.compute_returns(obs)
  loss=runner.alg.update();assert all(torch.isfinite(torch.tensor(v)) for v in loss.values()),loss
  for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
   assert any(not torch.equal(before[k],v) for k,v in runner.alg.policy.state_dict().items() if k.startswith(prefix)),prefix
  runner.current_learning_iteration=1;path=D/'smoke_model.pt';runner.save(path)
  saved=torch.load(path,map_location='cpu',weights_only=False)
  assert saved['amp']['dataset']['clip_count']==15
  for opt in (saved['optimizer_state_dict'],saved['amp']['optimizer']):
   assert {int(v['step']) for v in opt['state'].values()}=={20}
  restored=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device);restored.load(path)
  with torch.inference_mode():
   torch.testing.assert_close(restored.alg.policy.act_inference(obs),runner.alg.policy.act_inference(obs),atol=0,rtol=0)
  try:restored.load(oldpath)
  except ValueError as error:assert 'environment variant/contract' in str(error)
  else:raise AssertionError('Revision25 strict restore was accepted')
  before_hash=json.loads((D/'before.json').read_text())['source_sha256']
  allowed={'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py','source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py','source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py'}
  actual={p for p,h in before_hash.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h}
  assert actual==allowed,actual
  result=dict(status='PASS',num_envs=64,active_terminations=sorted(terms),isolated_angle_cases_rad={'roll':[.49,.51,-.49,-.51],'pitch':[1.09,1.11,-1.09,-1.11]},angle_cases_reset=True,reset_rows=reset_rows,height_conditions_active=True,box_speed_boundary=True,timeout_steps=b.max_episode_length,shapes=shapes,contract=contract,contract_changed_keys=sorted(changed),loss=loss,ppo_amp_updates=1,restore=True,revision25_restore_rejected=True,other_sources_unchanged=True)
  (D/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('GROUNDFIX_SMOKE_PASS',flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
