"""Clean wall5 depth, delayed push onset, finite PPO/AMP and strict restore."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
from pathlib import Path
from unittest.mock import patch
import copy,json,hashlib
import torch,gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import convert_camera_frame_orientation_convention
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
from perceptual_ball.carrybox_walled import PairedDepthBuffer

D=Path(__file__).resolve().parent;R=D.parents[2];N=64
ZERO_FIELDS=('depth_noise_std_m','depth_stereo_near_m','depth_stereo_far_m',
    'depth_edge_probability','depth_hole_probability','depth_delay_probability',
    'depth_freeze_probability','camera_position_error_m','camera_rotation_error_deg')

def depth_check(env,obs):
    camera=env.scene['depth_camera'];s=parent.state(env)
    raw=camera.data.output['distance_to_image_plane'][...,0]
    expected=raw.nan_to_num(nan=3.,posinf=3.,neginf=3.).clamp(.1,3.)
    depth,target=parent.captured_pair(env)
    torch.testing.assert_close(depth,expected,atol=0,rtol=0)
    torch.testing.assert_close(obs['perception'][:,-1],expected,atol=0,rtol=0)
    torch.testing.assert_close(target[:,:9],parent.base.box_pose_target(env),atol=0,rtol=0)
    torch.testing.assert_close(obs['box_pose_target'],target,atol=0,rtol=0)
    assert s.paired.depth.shape[1]==1 and not s.paired.freeze_left.any()
    offset=env.cfg.scene.depth_camera.offset
    torch.testing.assert_close(camera._offset_pos,raw.new_tensor(offset.pos).repeat(N,1),atol=0,rtol=0)
    q=convert_camera_frame_orientation_convention(raw.new_tensor(offset.rot).repeat(N,1),origin=offset.convention,target='world')
    torch.testing.assert_close(camera._offset_quat,q,atol=2e-6,rtol=0)
    return dict(min_m=float(depth.min()),max_m=float(depth.max()),raw_capture_exact=True,current_pose_paired=True)

def push_check(env):
    robot=env.scene['robot'];s=parent.state(env);saved=copy.deepcopy(s.curriculum)
    ids=torch.tensor([0,3],device=env.device);ranges=env.cfg.events.push_robot.params['velocity_range']
    bounds=torch.tensor([ranges[k] for k in ('x','y','z','roll','pitch','yaw')],device=env.device)
    draw=torch.full((2,6),.75,device=env.device);delta=bounds[:,0]+draw*(bounds[:,1]-bounds[:,0]);rows=[]
    # Inspect the exact write arguments without applying an artificial test push.
    try:
        for iteration,anchor,scale in ((0,None,0.),(100,None,0.),(70000,70000,0.),
                (74999,70000,0.),(75000,70000,0.),(80000,70000,.5),(85000,70000,1.),(90000,70000,1.)):
            s.curriculum.anchor=anchor;s.curriculum.iteration=iteration
            before=robot.data.root_vel_w.clone()
            with patch.object(torch,'rand',return_value=draw),patch.object(robot,'write_root_velocity_to_sim') as write:
                task.push_velocity_increment(env,ids,ranges)
                if scale==0.:write.assert_not_called()
                else:
                    write.assert_called_once();torch.testing.assert_close(write.call_args.args[0],before[ids]+scale*delta)
                    torch.testing.assert_close(write.call_args.kwargs['env_ids'],ids)
            torch.testing.assert_close(robot.data.root_vel_w,before,atol=0,rtol=0)
            rows.append(dict(iteration=iteration,anchor=anchor,expected_scale=scale))
    finally:s.curriculum=saved
    return rows

def single_slot_check():
    x=torch.ones(2,2,3);y=torch.ones(2,10);z=torch.zeros(2,dtype=torch.long)
    buffer=PairedDepthBuffer(x,y,0)
    for step in range(4):
        a,b=buffer.update(step,x+step,y+step,z,z)
        torch.testing.assert_close(a,x+step);torch.testing.assert_close(b,y+step)
    a,b=buffer.update(3,x+99,y+99,z,z)
    torch.testing.assert_close(a,x+3);torch.testing.assert_close(b,y+3)
    buffer.reset(torch.tensor([0]));a,b=buffer.update(3,x+9,y+9,z,z)
    torch.testing.assert_close(a[0],x[0]+9);torch.testing.assert_close(a[1],x[1]+3)
    torch.testing.assert_close(b[0],y[0]+9);torch.testing.assert_close(b[1],y[1]+3)

def main():
    torch.set_num_threads(2);single_slot_check()
    cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg()
    assert all(getattr(cfg,k)==0 for k in ZERO_FIELDS)
    assert cfg.depth_max_delay_steps==0 and cfg.depth_freeze_max_steps==1
    assert (cfg.push_warmup_iterations,cfg.push_ramp_iterations)==(5000,10000)
    for cls in (CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg):
        other=cls();assert other.depth_noise_std_m==.06 and other.depth_max_delay_steps==1
        assert other.camera_position_error_m==.01
        assert (other.push_warmup_iterations,other.push_ramp_iterations)==(1000,4000)
    cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
    for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
    try:
        b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset()
        c=b.checkpoint_contract();oldpath=json.loads((D/'before.json').read_text())['checkpoint']
        old=torch.load(oldpath,map_location='cpu',weights_only=False)['environment_contract']
        changed={k for k in c.keys()|old.keys() if c.get(k)!=old.get(k)}
        expected={'migration_revision','push_curriculum','noise','depth_edge','depth_holes','depth_stereo',
            'latency_probability','delay','freeze','freeze_steps','mount_pos','depth_observation'}
        assert changed==expected,changed
        assert c['migration_revision']==28 and c['depth_observation']['units']=='metres'
        camera=b.scene['depth_camera'];roots={m['root'] for m in camera.mesh_manifest}
        assert '/World/ground' in roots and any('/Robot/' in x for x in roots)
        for name in ('Box','Wall','Cylinder0','Cylinder1','Cylinder2','Platform'):assert any(x.endswith('/'+name) for x in roots),name
        shapes={k:list(v.shape) for k,v in obs.items()}
        assert shapes=={'proprio':[N,372],'perception':[N,4,27,48],'amp':[N,600],'box_pose_target':[N,10],'critic_state':[N,123],'action_bounds':[N,58]}
        with torch.inference_mode():
            depth_rows=[depth_check(b,obs)];push=push_check(b)
        runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
        initial=copy.deepcopy(runner.alg.policy.state_dict());losses=[]
        def update(current,iteration):
            nonlocal obs
            b.set_training_iteration(iteration)
            with torch.inference_mode():
                for step in range(agent.num_steps_per_env):
                    if step==0:b.episode_length_buf[[0,N-1]]=b.max_episode_length-1
                    obs,reward,done,extra=w.step(current.alg.act(obs));current.alg.process_env_step(obs,reward,done,extra)
                    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
                    depth_rows.append(depth_check(b,obs))
                    if step==0:assert done[[0,N-1]].all() and extra['terminal_observations']['obs']['critic_state'].shape[-1]==123
                current.alg.compute_returns(obs)
            loss=current.alg.update();assert all(torch.isfinite(torch.tensor(v)) for v in loss.values())
            for model in (current.alg.policy,current.alg.amp):assert all(torch.isfinite(v).all() for v in model.state_dict().values())
            return loss
        losses.extend([update(runner,0),update(runner,1)])
        for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
            assert any(not torch.equal(initial[k],v) for k,v in runner.alg.policy.state_dict().items() if k.startswith(prefix)),prefix
        runner.current_learning_iteration=2;path=D/'smoke_model.pt';runner.save(path)
        model=torch.load(path,map_location='cpu',weights_only=False)
        assert model['amp']['dataset']['clip_count']==15
        for opt in (model['optimizer_state_dict'],model['amp']['optimizer']):assert {int(v['step']) for v in opt['state'].values()}=={40}
        restored=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device);restored.load(path)
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(obs),runner.alg.policy.act_inference(obs),atol=0,rtol=0)
            torch.testing.assert_close(restored.alg.policy.evaluate(obs),runner.alg.policy.evaluate(obs),atol=0,rtol=0)
        for load_optimizer in (True,False):
            try:restored.load(oldpath,load_optimizer=load_optimizer)
            except ValueError as error:assert 'environment variant/contract' in str(error)
            else:raise AssertionError('rev27 strict restore accepted')
        losses.append(update(restored,2))
        result=dict(status='PASS',num_envs=N,contract=c,contract_changed_keys=sorted(changed),shapes=shapes,
            depth_checks=len(depth_rows),depth_example=depth_rows[0],single_slot_partial_reset=True,
            push_boundaries=push,mesh_roots=sorted(roots),losses=losses,restore_identical=True,
            revision27_strict_restore_rejected=True,wall3_wall4_unchanged=True,convergence_evaluated=False)
        (D/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('CLEAN_CAMERA_SMOKE_PASS',flush=True)
    finally:env.close()
try:main()
except BaseException:
    import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
