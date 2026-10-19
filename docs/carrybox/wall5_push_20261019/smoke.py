"""Actual 4-env reset/timeout/PPO/AMP/restore/export check; artifacts are not formal training."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
import copy,json,time
from pathlib import Path
from unittest.mock import patch
import torch,gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import quat_apply
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as mdp
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy
from materials import inspect_materials
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent
OUT=Path(__file__).resolve().parent


def verify_physics(b):
    material=inspect_materials(b)
    (OUT/'materials_after.json').write_text(json.dumps(material,indent=2)+'\n')
    for path in ('/physicsScene/defaultMaterial','/World/ground/physicsMaterial'):
        m=next(x for x in material['materials'] if x['path']==path)
        assert m['static']==1. and m['dynamic']==1. and m['friction_combine']=='multiply'
    assert material['robot_unique']==[[1.,1.,0.]]
    assert all(x['material'] is None for x in material['bindings'] if '/Robot/' in x['collider'])
    assert next(x for x in material['bindings'] if '/ground/' in x['collider'])['material']=='/World/ground/physicsMaterial'
    assert material['box_coefficients']!=[[[1.,.8,0.]]]*4  # startup tensor randomization remains enabled
    robot=b.scene['robot'];shapes={}
    for name in ('left_ankle_roll_link','right_ankle_roll_link','left_rubber_hand','right_rubber_hand'):
        view=robot._physics_sim_view.create_rigid_body_view('/World/envs/env_0/Robot/'+name)
        props=view.get_material_properties().cpu();assert props.shape[1]>0
        torch.testing.assert_close(props[...,:2],torch.ones_like(props[...,:2]))
        shapes[name]=props.tolist()
    event=b.event_manager.get_term_cfg('push_robot');ranges=event.params['velocity_range']
    limits=torch.tensor([ranges[k] for k in ('x','y','z','roll','pitch','yaw')],device=b.device)
    ids=torch.tensor([0,2],device=b.device)
    initial=torch.tensor([[.85,.2,-.1,.3,-.4,.5]],device=b.device).repeat(4,1)
    curriculum=parent.state(b).curriculum;old=copy.deepcopy(curriculum)
    checks=[]
    with torch.inference_mode():
        for mode,iteration,scale in (('increment',0,0.),('increment',1000,0.),('increment',3000,.5),('increment',5000,1.),('set',5000,1.),('none',5000,0.)):
            curriculum.anchor=0;curriculum.iteration=iteration
            robot.write_root_velocity_to_sim(initial)
            torch.testing.assert_close(robot.root_physx_view.get_root_velocities(),initial)
            torch.manual_seed(730)
            delta=limits[:,0]+torch.rand(2,6,device=b.device)*(limits[:,1]-limits[:,0])
            torch.manual_seed(730)
            if mode=='increment':mdp.push_velocity_increment(b,ids,ranges)
            elif mode=='set':parent.push_velocity(b,ids,ranges)
            actual=robot.root_physx_view.get_root_velocities().clone()
            expected=initial.clone()
            expected[ids]=delta if mode=='set' else initial[ids]+scale*delta
            torch.testing.assert_close(actual,expected,atol=1e-6,rtol=1e-6)
            torch.testing.assert_close(robot.data.root_vel_w,actual,atol=1e-6,rtol=1e-6)
            checks.append(dict(mode=mode,iteration=iteration,scale=scale,before=initial.tolist(),sample=delta.tolist(),after_physx=actual.tolist()))
    parent.state(b).curriculum=old
    b.reset()
    return dict(materials_verified=True,foot_hand_shapes=shapes,push_physx_readback=checks)

def main():
    torch.set_num_threads(2);cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
    assert cfg.reset_skill_probabilities==(.8,0.,.2) and cfg.scene.platform is None
    assert agent.obs_groups=={'policy':['proprio','perception'],'critic':['critic_state']}
    assert agent.policy.class_name=='CarryBoxWall5ActorCritic'
    old=CarryBoxWalled4EnvCfg();old_agent=CarryBoxWalled4PPORunnerCfg()
    assert not hasattr(old.observations,'critic_state') and old_agent.policy.class_name=='CarryBoxActorCritic'
    assert old_agent.obs_groups['critic']==['proprio','perception']
    assert cfg.events.push_robot.func is mdp.push_velocity_increment
    assert old.events.push_robot.func is parent.push_velocity
    for material in (old.sim.physics_material,old.scene.ground.spawn.physics_material):
        assert material.static_friction==.5 and material.dynamic_friction==.5 and material.friction_combine_mode=='average'
    cfg.scene.num_envs=4;cfg.seed=42;cfg.sim.device=args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
    try:
        b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        physical_checks=verify_physics(b)
        runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
        with torch.inference_mode():
            obs,_=w.reset();robot=b.scene['robot'].data;box=b.scene['box'].data
            expected_shapes={'proprio':(4,372),'perception':(4,4,27,48),'amp':(4,600),'box_pose_target':(4,10),'critic_state':(4,108)}
            assert {k:tuple(v.shape) for k,v in obs.items()}==expected_shapes
            assert all(torch.isfinite(v).all() for v in obs.values())
            torch.testing.assert_close(obs['critic_state'],mdp.critic_state(b))
            torch.testing.assert_close(quat_apply(robot.root_link_quat_w,obs['critic_state'][:,93:96]),robot.root_link_lin_vel_w,atol=1e-5,rtol=1e-5)
            torch.testing.assert_close(quat_apply(robot.root_link_quat_w,obs['critic_state'][:,96:99]),box.root_pos_w-robot.root_link_pos_w,atol=1e-5,rtol=1e-5)
            torch.testing.assert_close(obs['critic_state'][:,105:],torch.tensor(cfg.scene.box.spawn.size,device=b.device).expand(4,-1))
            before=mdp.critic_state(b).clone();b._reset_idx(torch.tensor([0],device=b.device))
            torch.testing.assert_close(mdp.critic_state(b)[1:],before[1:]);obs,_=w.reset()
        terminal_checks=[];losses=[];original_reset=b._reset_idx
        def checked_reset(ids):
            active=getattr(b,'_carrybox_in_step',False)
            before=mdp.critic_state(b)[ids].clone() if active else None
            original_reset(ids)
            if active:
                torch.testing.assert_close(b._carrybox_terminal['obs']['critic_state'],before)
                terminal_checks.append(len(ids))
        b._reset_idx=checked_reset
        def update(runner,force_timeout=False):
            nonlocal obs
            with torch.inference_mode():
                for step in range(agent.num_steps_per_env):
                    if force_timeout and step==0:b.episode_length_buf[[0,2]]=b.max_episode_length-1
                    action=runner.alg.act(obs);obs,reward,done,extra=w.step(action)
                    expected=None
                    if extra['time_outs'].any():
                        terminal=extra['terminal_observations'];ids=terminal['env_ids']
                        value=runner.alg.policy.evaluate(terminal['obs']).squeeze(-1)
                        raw=reward.clone();motion=obs['amp'].clone();motion[ids]=terminal['obs']['amp']
                        # _process_amp initializes normalization before scoring its first transition.
                        runner.alg._ensure_motion_library()
                        expected=.75*raw+.25*.5*runner.alg.amp.predict_reward(motion)
                        expected[ids]+=runner.alg.gamma*value*extra['time_outs'][ids]
                    runner.alg.process_env_step(obs,reward,done,extra)
                    if expected is not None:torch.testing.assert_close(runner.alg.storage.rewards[step,:,0],expected,atol=1e-5,rtol=1e-5)
                runner.alg.compute_returns(obs)
            result=runner.alg.update();assert all(torch.isfinite(torch.tensor(x)) for x in result.values());return result
        before=copy.deepcopy(runner.alg.policy.state_dict())
        losses.append(update(runner,True));losses.append(update(runner,True))
        assert terminal_checks and runner.alg.motion_metadata['clip_count']==13
        for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
            assert any(not torch.equal(before[k],v) for k,v in runner.alg.policy.state_dict().items() if k.startswith(prefix)),prefix
        assert runner.alg.optimizer.state and runner.alg.amp_optimizer.state
        runner.current_learning_iteration=2;checkpoint=OUT/'smoke_model.pt';runner.save(checkpoint)
        restored=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device);restored.load(checkpoint)
        assert restored.current_learning_iteration==2
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(obs),runner.alg.policy.act_inference(obs),rtol=0,atol=0)
            torch.testing.assert_close(restored.alg.policy.evaluate(obs),runner.alg.policy.evaluate(obs),rtol=0,atol=0)
        # Only physical contract differs: even weights-only load through strict loader must reject it.
        incompatible=torch.load(checkpoint,weights_only=False);incompatible['environment_contract']['migration_revision']=14
        old_checkpoint=OUT/'old_contract_model.pt';torch.save(incompatible,old_checkpoint)
        for load_optimizer in (True,False):
            try:restored.load(old_checkpoint,load_optimizer=load_optimizer)
            except ValueError as error:assert 'environment variant/contract' in str(error)
            else:raise AssertionError('old physical contract accepted')
        losses.append(update(restored,True))
        with torch.inference_mode():
            wrapper=export_depth_policy(restored.alg.policy,obs,OUT/'exported',{'environment_contract':b.checkpoint_contract()})
            torch.testing.assert_close(wrapper(obs['proprio'].cpu(),obs['perception'].cpu()),restored.alg.policy.act_inference(obs).cpu(),atol=2e-5,rtol=2e-5)
        manifest=json.loads((OUT/'exported/manifest.json').read_text());assert manifest['flat_groups']==['proprio']
        contract=b.checkpoint_contract();assert contract['migration_revision']==15 and contract['critic_shape']==108
        result=dict(status='PASS',physical_checks=physical_checks,old_physical_contract_rejected=True,shapes=expected_shapes,contract=contract,terminal_checks=terminal_checks,losses=losses,
                    strict_restore=True,actor_export_without_privileged=True,wall4_unchanged=True,optimizer_and_amp_updated=True)
        (OUT/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('PUSH_SMOKE_PASS',flush=True)
    finally:env.close()
try:main()
finally:app.close(wait_for_replicator=False)
