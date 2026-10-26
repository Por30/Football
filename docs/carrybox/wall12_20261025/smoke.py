"""Actual wall12 capture pairing, joint update, strict resume and actor export."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args()
app=AppLauncher(args).app
from pathlib import Path
import copy
import json
import torch
import gymnasium as gym
import onnx
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import matrix_from_quat
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall12_env_cfg import CarryBoxWalled12EnvCfg, CarryBoxWalled12PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall11_env_cfg import CarryBoxWalled11EnvCfg, CarryBoxWalled11PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall12 as task
from perceptual_ball.rsl_rl_extensions.carrybox_wall12 import CarryBoxWall12OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.carrybox_wall10 import CarryBoxWall10OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy

OUT=Path(__file__).resolve().parent
N=16


def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [p for k in a.keys()|b.keys() for p in differences(a.get(k),b.get(k),path+'.'+k)]
    return [] if a==b else [path.lstrip('.')]


def expected_target(env):
    camera=env.scene['depth_camera'].data
    box=env.scene['box'].data
    inverse=matrix_from_quat(camera.quat_w_ros).transpose(-1,-2)
    xyz=(inverse @ (box.root_pos_w-camera.pos_w).unsqueeze(-1)).squeeze(-1)
    rotation=inverse @ matrix_from_quat(box.root_quat_w)
    return torch.cat((xyz,rotation[...,:2].transpose(-1,-2).flatten(-2),
                      env.scene['depth_camera'].box_sizes),-1)


def capture_checks(env):
    ids=torch.arange(N,device=env.device)
    for label_first in (True,False):
        env._wall11_depth.reset(ids)
        env._wall12_pose_step[ids]=-1
        if label_first:
            label=task.box_pose_target(env).clone();depth=task.depth_image(env).clone()
        else:
            depth=task.depth_image(env).clone();label=task.box_pose_target(env).clone()
        torch.testing.assert_close(label,expected_target(env),atol=2.e-6,rtol=1.e-5)
        rng=torch.cuda.get_rng_state(env.device).clone()
        torch.testing.assert_close(task.depth_image(env),depth,atol=0,rtol=0)
        torch.testing.assert_close(task.box_pose_target(env),label,atol=0,rtol=0)
        assert torch.equal(rng,torch.cuda.get_rng_state(env.device))
    keep=torch.arange(1,N-1,device=env.device)
    reset=torch.tensor([0,N-1],device=env.device)
    env._reset_idx(reset)
    assert (env._wall12_pose_step[reset]==-1).all()
    fresh=task.box_pose_target(env)
    torch.testing.assert_close(fresh[keep],label[keep],atol=0,rtol=0)
    torch.testing.assert_close(task.depth_image(env)[keep],depth[keep],atol=0,rtol=0)
    torch.testing.assert_close(fresh,expected_target(env),atol=2.e-6,rtol=1.e-5)
    history=env.observation_manager.compute_group('perception',update_history=True)
    torch.testing.assert_close(history[reset],task.depth_image(env)[reset,None].expand(-1,4,-1,-1),atol=0,rtol=0)
    return dict(both_read_orders=True,repeated_reads_rng_unchanged=True,partial_reset=True,
                independent_camera_frame_transform=True,labels_detached=not fresh.requires_grad)


def main():
    torch.set_num_threads(2)
    cfg,agent=CarryBoxWalled12EnvCfg(),CarryBoxWalled12PPORunnerCfg()
    prior,prior_agent=CarryBoxWalled11EnvCfg(),CarryBoxWalled11PPORunnerCfg()
    env_differences=differences(cfg.to_dict(),prior.to_dict())
    assert set(env_differences)=={'walled_variant','events.reset_box.func',
        'observations.perception.image.func','observations.box_pose_target.pose.func'},env_differences
    runner_differences=differences(agent.to_dict(),prior_agent.to_dict())
    assert set(runner_differences)=={'class_name','experiment_name','run_name',
        'algorithm.class_name','algorithm.pose_aux_coef'},runner_differences
    assert (agent.num_steps_per_env,agent.algorithm.num_learning_epochs,agent.algorithm.num_mini_batches)==(24,5,4)
    assert agent.algorithm.pose_aux_coef==1. and prior_agent.algorithm.pose_aux_coef==0.
    cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled12-v0',cfg=cfg)
    try:
        b=env.unwrapped
        wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        obs,_=wrapped.reset()
        expected={'proprio':[N,558],'perception':[N,4,27,48],'critic_state':[N,123],
                  'box_pose_target':[N,12],'amp':[N,600]}
        assert {k:list(v.shape) for k,v in obs.items()}==expected
        assert b.scene['depth_camera'].cfg.object_names==('Wall','Platform','Cylinder0','Cylinder1','Cylinder2')
        assert not torch.equal(obs['perception'][:,-1],b.scene['depth_camera'].data.output['distance_to_image_plane'][...,0])
        checks=capture_checks(b)
        original=b.terminal_frame
        probe={}
        def capture(group):
            frame=original(group)
            if group=='perception':
                probe['depth']=frame.clone()
                probe['target']=task.box_pose_target(b).clone()
                torch.testing.assert_close(probe['target'],expected_target(b),atol=2.e-6,rtol=1.e-5)
            return frame
        b.terminal_frame=capture
        obs,_=wrapped.reset()
        model=CarryBoxWall12OnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
        initial=copy.deepcopy(model.alg.policy.state_dict())
        initial_d=copy.deepcopy(model.alg.amp.state_dict())
        losses=[];cnn_calls=[]
        def update(runner):
            nonlocal obs
            with torch.inference_mode():
                for step in range(24):
                    if step==0:b.episode_length_buf[[0,N-1]]=b.max_episode_length-1
                    before=obs['box_pose_target'].clone()
                    obs,reward,done,extra=wrapped.step(runner.alg.act(obs))
                    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
                    torch.testing.assert_close(obs['perception'][:,-1],task.depth_image(b),atol=0,rtol=0)
                    torch.testing.assert_close(obs['box_pose_target'],expected_target(b),atol=3.e-6,rtol=1.e-5)
                    if step==0:
                        assert done[[0,N-1]].all()
                        assert any(k.startswith('Wall12/') for k in extra['log'])
                        assert not any(k.startswith(('Wall10/','Wall11/')) for k in extra['log'])
                        terminal=extra['terminal_observations'];ids=terminal['env_ids']
                        torch.testing.assert_close(terminal['obs']['perception'][:,-1],probe['depth'][ids],atol=0,rtol=0)
                        assert not torch.equal(obs['box_pose_target'][[0,N-1]],probe['target'][[0,N-1]])
                    runner.alg.process_env_step(obs,reward,done,extra)
                    torch.testing.assert_close(runner.alg.storage.observations['box_pose_target'][step],before,atol=0,rtol=0)
                runner.alg.compute_returns(obs)
            calls=[]
            handle=runner.alg.policy.perception_encoder.register_forward_hook(lambda module,inputs,output:calls.append(len(inputs[0])))
            try: loss=runner.alg.update()
            finally:handle.remove()
            assert calls==[184]*20,calls  # 92 samples/current + mixed, one CNN call/update.
            cnn_calls.append(len(calls))
            assert all(torch.isfinite(torch.tensor(v)) for v in loss.values())
            assert loss['pose_position']>0 and loss['pose_rotation']>0
            assert loss['pose_samples']==16*23*5
            return loss
        losses.extend([update(model),update(model)])
        changed_modules={}
        for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
            changed_modules[prefix]=any(not torch.equal(v,initial[k]) for k,v in model.alg.policy.state_dict().items() if k.startswith(prefix))
            assert changed_modules[prefix],prefix
        assert any(not torch.equal(v,initial_d[k]) for k,v in model.alg.amp.state_dict().items())
        assert model.alg.optimizer is model.alg.amp_optimizer
        assert {int(v['step']) for v in model.alg.optimizer.state.values()}=={40}
        assert all(p in model.alg.optimizer.state for p in model.alg.policy.pose_head.parameters())
        model.current_learning_iteration=2;model.save(OUT/'smoke_model.pt')
        restored=CarryBoxWall12OnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
        restored.load(OUT/'smoke_model.pt')
        assert restored.alg.learning_rate==model.alg.learning_rate
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(obs),model.alg.policy.act_inference(obs),atol=0,rtol=0)
            torch.testing.assert_close(restored.alg.policy.predict_box_pose(obs),model.alg.policy.predict_box_pose(obs),atol=0,rtol=0)
        for a,p in zip(model.alg.policy.pose_head.parameters(),restored.alg.policy.pose_head.parameters()):
            for key,value in model.alg.optimizer.state[a].items():
                actual=restored.alg.optimizer.state[p][key]
                # map_location may move Adam's scalar step; moments retain the
                # parameter device. Require exact numerical state in both cases.
                if key=='step':
                    torch.testing.assert_close(value.cpu(),actual.cpu(),atol=0,rtol=0)
                else:
                    torch.testing.assert_close(value,actual,atol=0,rtol=0)
        checkpoint=torch.load(OUT/'smoke_model.pt',map_location='cpu',weights_only=False)
        for field in ('variant','auxiliary'):
            broken=copy.deepcopy(checkpoint)
            if field=='variant':broken['environment_contract']['variant']='walled11'
            else:broken['amp']['config']['auxiliary']['frame']='world'
            path=OUT/f'incompatible_{field}.pt';torch.save(broken,path)
            try:restored.load(path)
            except ValueError:pass
            else:raise AssertionError('Incompatible wall12 checkpoint accepted')
        wall11=Path('logs/rsl_rl/g1_carrybox_depth/walled11/2026-10-24_12-34-49_wall11_24step_fresh_20261024_123445/model_19999.pt')
        assert wall11.is_file()
        try:restored.load(wall11)
        except ValueError as error:assert 'environment variant/contract' in str(error)
        else:raise AssertionError('Actual wall11 checkpoint accepted as wall12')
        # The shared runner/actor continues loading wall11's original objective.
        legacy=CarryBoxWall10OnPolicyRunner(wrapped,prior_agent.to_dict(),log_dir=None,device=args.device)
        legacy.environment_contract=lambda:torch.load(wall11,map_location='cpu',weights_only=False)['environment_contract']
        legacy.load(wall11,load_optimizer=False)
        assert all(not p.requires_grad for p in legacy.alg.policy.pose_head.parameters())
        losses.append(update(restored))
        assert {int(v['step']) for v in restored.alg.optimizer.state.values()}=={60}
        changed=obs.clone()
        for key in ('amp','box_pose_target','critic_state'):changed[key]+=1000
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(changed),restored.alg.policy.act_inference(obs),atol=0,rtol=0)
        exported=export_depth_policy(restored.alg.policy,obs,OUT/'exported',metadata=b.checkpoint_contract())
        with torch.inference_mode():
            torch.testing.assert_close(exported(obs['proprio'].cpu(),obs['perception'].cpu()),
                restored.alg.policy.act_inference(obs).cpu(),atol=2.e-5,rtol=1.e-5)
        assert not any('pose' in k or 'critic' in k for k in exported.state_dict())
        graph=onnx.load(OUT/'exported/policy.onnx');onnx.checker.check_model(graph)
        assert [x.name for x in graph.graph.input]==['flat','depth']
        report=dict(status='PASS',num_envs=N,iterations='2+1',rollout_steps=24,shapes=expected,
            contract=b.checkpoint_contract(),config_differences=env_differences,runner_differences=runner_differences,
            capture_checks=checks,losses=losses,changed_modules=changed_modules,cnn_forward_calls_per_update=cnn_calls,
            joint_optimizer_steps=60,pose_optimizer_resume=True,actual_wall11_rejected=True,
            legacy_wall11_weights_load=True,terminal_pairing=True,actor_export_privilege_boundary=True,
            full_scale_performance_measured=False,convergence_evaluated=False)
        (OUT/'smoke.json').write_text(json.dumps(report,indent=2)+'\n')
        print('WALL12_SMOKE_PASS',flush=True)
    finally:env.close()


try:main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:app.close(wait_for_replicator=False)
