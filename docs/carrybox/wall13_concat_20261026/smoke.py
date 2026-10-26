"""Wall13 revision3 paired PPO/AMP/pose updates, strict resume and deployment."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args()
app=AppLauncher(args).app

import copy
import json
from pathlib import Path
import torch
import onnx
import onnxruntime as ort
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall12_env_cfg import CarryBoxWalled12EnvCfg,CarryBoxWalled12PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.carrybox_wall13 import CarryBoxWall13OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy

OUT=Path(__file__).resolve().parent
N=16


def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [p for k in a.keys()|b.keys() for p in differences(a.get(k),b.get(k),path+'.'+k)]
    return [] if a==b else [path.lstrip('.')]


def main():
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32=True
    torch.backends.cudnn.allow_tf32=True
    task='Template-Perceptual-Ball-CarryBox-Walled13-v0'
    cfg=load_cfg_from_registry(task,'env_cfg_entry_point')
    agent=load_cfg_from_registry(task,'rsl_rl_cfg_entry_point')
    env_diff=differences(cfg.to_dict(),CarryBoxWalled12EnvCfg().to_dict())
    agent_diff=differences(agent.to_dict(),CarryBoxWalled12PPORunnerCfg().to_dict())
    assert env_diff==['walled_variant'],env_diff
    assert set(agent_diff)=={'class_name','experiment_name','run_name','policy.class_name','algorithm.class_name'},agent_diff
    assert (cfg.scene.num_envs,agent.num_steps_per_env,agent.algorithm.num_learning_epochs,
            agent.algorithm.num_mini_batches,agent.algorithm.pose_aux_coef)==(4096,24,5,4,1.)
    cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
    env=gym.make(task,cfg=cfg)
    try:
        b=env.unwrapped
        wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        obs,_=wrapped.reset()
        expected={'proprio':[N,558],'perception':[N,4,27,48],'critic_state':[N,123],
                  'box_pose_target':[N,12],'amp':[N,600]}
        assert {k:list(v.shape) for k,v in obs.items()}==expected
        runner=CarryBoxWall13OnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
        initial=copy.deepcopy(runner.alg.policy.state_dict())
        assert runner.alg.policy.actor[0].weight.shape==(512,695)
        assert not any('fusion' in k for k in initial)
        with torch.no_grad():
            f=runner.alg.policy._features(obs)
            z=runner.alg.policy.perception_encoder(obs['perception'])
            torch.testing.assert_close(f[:,:558],obs['proprio'],atol=0,rtol=0)
            torch.testing.assert_close(f[:,558:686],z,atol=0,rtol=0)
            torch.testing.assert_close(f[:,686:],runner.alg.policy.pose_head(z),atol=0,rtol=0)
        initial_amp=copy.deepcopy(runner.alg.amp.state_dict())
        calls_by_update=[]
        def update(model):
            nonlocal obs
            with torch.inference_mode():
                for step in range(24):
                    if step==0:b.episode_length_buf[[0,N-1]]=b.max_episode_length-1
                    obs,reward,done,extra=wrapped.step(model.alg.act(obs))
                    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
                    if step==0:assert done[[0,N-1]].all() and any(k.startswith('Wall13/') for k in extra['log'])
                    model.alg.process_env_step(obs,reward,done,extra)
                model.alg.compute_returns(obs)
            calls=[]
            hook=model.alg.policy.perception_encoder.register_forward_hook(lambda m,i,o:calls.append(len(i[0])))
            try:loss=model.alg.update()
            finally:hook.remove()
            assert calls==[184]*20,calls
            assert all(torch.isfinite(torch.tensor(v)) for v in loss.values())
            assert loss['pose_samples']==N*23*5
            assert model.alg._pose_prediction is None
            calls_by_update.append(len(calls))
            return loss
        losses=[update(runner),update(runner)]
        for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
            assert any(not torch.equal(v,initial[k]) for k,v in runner.alg.policy.state_dict().items() if k.startswith(prefix)),prefix
        assert any(not torch.equal(v,initial_amp[k]) for k,v in runner.alg.amp.state_dict().items())
        ids=[id(p) for group in runner.alg.optimizer.param_groups for p in group['params']]
        assert len(ids)==len(set(ids)) and runner.alg.optimizer is runner.alg.amp_optimizer
        runner.current_learning_iteration=2;runner.save(OUT/'smoke_model.pt')
        restored=CarryBoxWall13OnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
        restored.load(OUT/'smoke_model.pt')
        assert restored.alg.learning_rate==runner.alg.learning_rate
        with torch.no_grad():
            torch.testing.assert_close(restored.alg.policy.act_inference(obs),runner.alg.policy.act_inference(obs),atol=0,rtol=0)
        for (name,a),(other_name,p) in zip(runner.alg.policy.named_parameters(),restored.alg.policy.named_parameters()):
            assert name==other_name
            for key,value in runner.alg.optimizer.state[a].items():
                torch.testing.assert_close(value.cpu(),restored.alg.optimizer.state[p][key].cpu(),atol=0,rtol=0)
        rejected=[]
        for old in (Path('docs/carrybox/wall13_20261026/smoke_model.pt'),
            Path('docs/carrybox/wall13_feedback_20261026/smoke_model.pt'),
            Path('logs/rsl_rl/g1_carrybox_depth/walled12/2026-10-25_12-32-53_wall12_24step_pose_aux_fresh_20261025_123249/model_19999.pt')):
            assert old.is_file()
            try:restored.load(old)
            except ValueError as e:
                assert 'environment variant/contract' in str(e)
                rejected.append(str(old))
            else:raise AssertionError('Old checkpoint accepted')
        losses.append(update(restored))
        assert {int(s['step']) for s in restored.alg.optimizer.state.values()}=={60}
        contract=b.checkpoint_contract()
        assert contract['migration_revision']==3 and contract['pose_supervision']['actor_feedback']
        assert restored.alg.amp_config['auxiliary']['actor_feedback']
        assert restored.alg.amp_config['visual_feedback']==contract['visual_feedback']
        # Compare deployment in FP32; training above uses normal TF32 settings.
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        p=restored.alg.policy.eval()
        inputs={k:v.cpu() for k,v in obs.items()}
        # A trained policy retains a transient distribution with non-leaf
        # tensors. Rebuild a CPU reference from weights, not that cached graph.
        settings=agent.policy.to_dict()
        settings.pop('class_name')
        cpu=type(p)(inputs,agent.obs_groups,29,**settings).eval()
        cpu.load_state_dict(p.state_dict())
        with torch.no_grad():
            reference=cpu.act_inference(inputs)
            torch.testing.assert_close(p.act_inference(obs).cpu(),reference,atol=2.e-5,rtol=1.e-5)
            base_action=p.act_inference(obs)
            delta=torch.zeros(9,device=args.device);delta[0]=1.
            hook=p.pose_head.register_forward_hook(lambda m,i,o:o+delta)
            try:action_delta=float((p.act_inference(obs)-base_action).abs().max())
            finally:hook.remove()
            assert action_delta>1.e-6
            changed={k:v.clone() for k,v in obs.items()}
            for key in ('critic_state','box_pose_target','amp'):changed[key]+=1000
            torch.testing.assert_close(p.act_inference(changed),base_action,atol=0,rtol=0)
        export_depth_policy(cpu,inputs,OUT/'exported',metadata=contract)
        jit=torch.jit.load(str(OUT/'exported/policy.pt'))
        graph=onnx.load(OUT/'exported/policy.onnx');onnx.checker.check_model(graph)
        assert [x.name for x in graph.graph.input]==['flat','depth']
        assert any('pose_head' in x.name for x in graph.graph.initializer)
        assert not any('fusion' in x.name for x in graph.graph.initializer)
        options=ort.SessionOptions();options.intra_op_num_threads=1
        session=ort.InferenceSession(str(OUT/'exported/policy.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        errors={}
        for n in (1,N):
            with torch.no_grad():
                wanted=cpu.act_inference({k:v[:n] for k,v in inputs.items()})
                scripted=jit(inputs['proprio'][:n],inputs['perception'][:n])
            result=torch.from_numpy(session.run(None,{'flat':inputs['proprio'][:n].numpy(),
                'depth':inputs['perception'][:n].numpy()})[0])
            torch.testing.assert_close(scripted,wanted,atol=2.e-5,rtol=1.e-5)
            torch.testing.assert_close(result,wanted,atol=2.e-5,rtol=1.e-5)
            errors[str(n)]=float((result-wanted).abs().max())
        (OUT/'smoke.json').write_text(json.dumps(dict(status='PASS',num_envs=N,iterations='2+1',
            rollout_steps=24,updates=60,shapes=expected,env_differences=env_diff,agent_differences=agent_diff,
            actor_input_dim=695,fusion_parameters=0,contract=contract,losses=losses,cnn_calls_per_update=calls_by_update,
            pose_intervention_max_action_delta=action_delta,privileged_actor_isolation=True,
            optimizer_exact_resume=True,rejected_checkpoints=rejected,onnx_max_errors=errors,
            formal_training_started=False,performance_or_success_evaluated=False),indent=2)+'\n')
        print('WALL13_CONCAT_SMOKE_PASS',flush=True)
    finally:env.close()


try:main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:app.close(wait_for_replicator=False)
