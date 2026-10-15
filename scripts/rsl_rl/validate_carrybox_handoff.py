"""Actual wall4 event/reward/AMP integration and unchanged-scale throughput gate."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser()
parser.add_argument('--num-envs',type=int,required=True)
parser.add_argument('--output',required=True)
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args()
app=AppLauncher(args).app
import copy
import json
from pathlib import Path
import torch
import gymnasium as gym
from pxr import UsdPhysics
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,CarryBoxWalled4PPORunnerCfg,CarryBoxWalled3EnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_env_cfg import CarryBoxEnvCfg,CarryBoxPPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards import reward_terms
from perceptual_ball.carrybox_amp import FindBoxMotionLibrary,joint_mapping
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy


def audit_events(env,wrapped,cfg,report):
    robot=env.scene['robot'];box=env.scene['box'];n=env.num_envs
    ids=torch.arange(n,device=args.device)
    obs,_=wrapped.reset()
    assert obs['proprio'].shape==(n,372) and obs['perception'].shape==(n,4,27,48)
    assert obs['amp'].shape==(n,640) and obs['box_pose_target'].shape==(n,9)
    assert all(torch.isfinite(v).all() for v in obs.values())
    assert (task.state(env).skills!=1).all()
    actual=robot.data.default_joint_pos.clone()
    nominal=actual.clone()
    import re
    for i,name in enumerate(robot.joint_names):
        nominal[:,i]=next(value for pattern,value in cfg.scene.robot.init_state.joint_pos.items() if re.fullmatch(pattern,name))
    assert ((actual-nominal).abs()<=.010001).all()
    assert (actual-nominal).abs().sum()>0
    torch.testing.assert_close(env.action_manager.get_term('joint_pos')._offset,actual)
    # Inspect actual PhysX mass/material/COM, including repeat reset without compounding.
    samples=[]
    for _ in range(4):
        wrapped.reset()
        mass=box.root_physx_view.get_masses()
        assert ((mass>=.08-1e-6)&(mass<=1.2+1e-6)).all(),mass
        samples.append(mass.flatten().tolist())
    material=box.root_physx_view.get_material_properties()
    assert ((material[...,0]>=.3)&(material[...,0]<=2.)).all()
    assert ((material[...,1]>=.4)&(material[...,1]<=1.5)).all()
    assert ((material[...,2]>=0.)&(material[...,2]<=.2)).all()
    torso=task.state(env).torso
    prim=env.sim.get_initial_stage().GetPrimAtPath('/World/envs/env_0/Robot/torso_link')
    nominal_com=torch.tensor(list(UsdPhysics.MassAPI(prim).GetCenterOfMassAttr().Get()))
    com=robot.root_physx_view.get_coms()[:,torso,:3].cpu()
    assert ((com-nominal_com).abs()<=torch.tensor([.025,.05,.05])+1e-6).all(),(com,nominal_com)
    for _ in range(3):task.push_velocity(env,ids,cfg.events.push_robot.params['velocity_range'])
    velocity=robot.data.root_vel_w
    assert (velocity.abs()<=torch.tensor([.5,.5,.2,.52,.52,.78],device=args.device)+1e-6).all()
    # Action range includes every motion and startup offset; physical limits unchanged.
    library=FindBoxMotionLibrary(device=args.device)
    mapping=torch.tensor(joint_mapping(robot.joint_names),device=args.device)
    default=actual[:,mapping]
    coverage={}
    for name,(joints,_,_,_) in zip(library.clip_names,library.clips):
        required=((joints[None]-default[:,None]).abs()/.25).max().item()
        assert required<=9.,(name,required)
        coverage[name]=required
    # Reward manager has one exact set, not inherited duplicate approach/lift bonuses.
    expected={'dof_acc','action_rate','torques','dof_vel','dof_pos_limits','dof_vel_limits','undesired_contacts',
        'walk_task','carryup_task','standup_task','slow_pickup','stable_grasp','arm_speed_pickup','arm_acc_pickup',
        'grip_force_cap','held_hand_speed','held_hand_acc','waist_yaw_penalty','search_turn'}
    assert set(env.reward_manager.active_terms)==expected,env.reward_manager.active_terms
    assert cfg.terminations.success is None
    assert env.scene['body_contacts'].num_bodies>0
    # Both wall variants share new recipe; baseline and football registration remain independent.
    wall3=CarryBoxWalled3EnvCfg();baseline=CarryBoxEnvCfg()
    assert wall3.reset_skill_probabilities==(.8,0.,.2) and not hasattr(wall3.rewards,'search_turn')
    assert hasattr(baseline.rewards,'approach') and baseline.scene.box.spawn.mass_props.mass==1.125
    assert CarryBoxPPORunnerCfg().clip_actions==5.
    assert 'agilekickball_v4_env_cfg' in gym.spec('Template-Perceptual-Ball-AgileKickball-v4').kwargs['env_cfg_entry_point']
    wrapped.reset()
    obs=env.observation_manager.compute()
    a=task.depth_image(env).clone();p=task.box_pose_target(env).clone()
    torch.testing.assert_close(a,task.depth_image(env));torch.testing.assert_close(p,task.box_pose_target(env))
    for v in reward_terms(env).values():assert torch.isfinite(v).all()
    report.update(mass_samples=samples,materials=material.tolist(),torso_com=com.tolist(),
                  action_coverage=coverage,obs_shapes={k:list(v.shape) for k,v in obs.items()},reward_terms=sorted(expected))


def main():
    torch.set_num_threads(2)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    cfg=CarryBoxWalled4EnvCfg();agent=CarryBoxWalled4PPORunnerCfg()
    cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.seed=42
    assert agent.clip_actions==9. and agent.num_steps_per_env==24
    assert agent.algorithm.num_learning_epochs==4 and agent.algorithm.num_mini_batches==4
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0',cfg=cfg)
    b=env.unwrapped;wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
    report=dict(num_envs=args.num_envs,contract=b.checkpoint_contract(),status='RUNNING')
    try:
        assert not b.sim.has_rtx_sensors()
        assert cfg.scene.depth_camera.update_period==.02
        assert len(b.scene['depth_camera'].mesh_manifest)==43
        with torch.inference_mode():
            if args.num_envs==4:audit_events(b,wrapped,cfg,report)
            else:wrapped.reset()
        runner=CarryBoxOnPolicyRunner(wrapped,agent.to_dict(),log_dir=str(out/'train'),device=args.device)
        source=json.loads(Path('docs/carrybox/handoff_20261014/stopped_run.json').read_text())['checkpoint']
        try:runner.load(source)
        except ValueError as error:assert 'environment' in str(error)
        else:raise AssertionError('Old contract silently accepted')
        runner.warm_start(source)
        assert not runner.alg.optimizer.state and not runner.alg.amp_optimizer.state
        assert not runner.alg.amp_statistics_initialized and runner.current_learning_iteration==0
        old_amp=copy.deepcopy(runner.alg.amp.state_dict())
        times=[];log=runner.log
        def capture(locs,*a,**kw):
            times.append(dict(collection=locs['collection_time'],learning=locs['learn_time'],
                              total=locs['collection_time']+locs['learn_time']))
            return log(locs,*a,**kw)
        runner.log=capture
        runner.learn(6 if args.num_envs==4096 else 3,init_at_random_ep_len=True)
        assert runner.alg.motion_metadata['clip_count']==15
        assert runner.alg.motion_metadata==task.state(b).library.metadata
        assert any(not torch.equal(old_amp[k],v) for k,v in runner.alg.amp.state_dict().items())
        checkpoint=out/'validation_model.pt';runner.save(str(checkpoint))
        # New runner exercises complete new-contract restore; physics state is intentionally fresh.
        fresh=CarryBoxOnPolicyRunner(wrapped,agent.to_dict(),log_dir=str(out/'resumed'),device=args.device)
        fresh.load(str(checkpoint));assert fresh.alg.optimizer.state and fresh.alg.amp_optimizer.state
        fresh_log=fresh.log
        def capture_resume(locs,*a,**kw):
            times.append(dict(collection=locs['collection_time'],learning=locs['learn_time'],
                              total=locs['collection_time']+locs['learn_time']))
            return fresh_log(locs,*a,**kw)
        fresh.log=capture_resume
        fresh.learn(4 if args.num_envs==4096 else 2)
        for model in (fresh.alg.policy,fresh.alg.amp):
            assert all(torch.isfinite(v).all() for v in model.state_dict().values())
        with torch.inference_mode():
            obs=wrapped.get_observations()
            changed=obs.clone();changed['box_pose_target']+=100.;changed['amp']+=100.
            torch.testing.assert_close(fresh.alg.policy.act_inference(obs),fresh.alg.policy.act_inference(changed))
            torch.testing.assert_close(fresh.alg.policy.evaluate(obs),fresh.alg.policy.evaluate(changed))
        report.update(timings=times,amp_dataset=fresh.alg.motion_metadata,full_resume=True,
                      warm_start_source=source,initialization=runner.warm_start_info)
        if args.num_envs==4096:
            report['warm_max_seconds']=max(t['total'] for t in times[2:])
            report['warm_mean_seconds']=sum(t['total'] for t in times[2:])/len(times[2:])
            (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
            assert report['warm_max_seconds']<=6.,report['timings']
        else:
            export_depth_policy(fresh.alg.policy,obs,str(out/'export'))
            report['export']=True
        report['status']='PASS';(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print('CARRYBOX_HANDOFF_PASS',flush=True)
    finally:env.close()


try:main()
finally:app.close(wait_for_replicator=False)
