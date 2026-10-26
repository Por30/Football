"""Sixteen real environments: depth, terminal pairs, joint updates, resume/export."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
from pathlib import Path
import copy
import json
import torch
import gymnasium as gym
import onnx
import perceptual_ball.tasks
from isaaclab.utils.math import quat_apply
from isaaclab.managers import SceneEntityCfg
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.kickball_v11_env_cfg import KickballV11EnvCfg, KickballV11PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall11_env_cfg import CarryBoxWalled11EnvCfg, CarryBoxWalled11PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import kickball_v11 as task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.amp import amp_features, END_EFFECTOR_BODY_NAMES
from perceptual_ball.rsl_rl_extensions.kickball_v11 import KickballV11OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy

OUT = Path(__file__).resolve().parent
N = 16


def main():
    torch.set_num_threads(2)
    cfg, agent = KickballV11EnvCfg(), KickballV11PPORunnerCfg()
    assert CarryBoxWalled11EnvCfg().scene.cylinder0 is not None
    assert CarryBoxWalled11PPORunnerCfg().algorithm.pose_aux_coef == 0.
    assert agent.num_steps_per_env == 24 and agent.algorithm.num_learning_epochs == 5
    assert agent.algorithm.num_mini_batches == 4 and agent.algorithm.pose_aux_coef == 1.
    cfg.scene.num_envs, cfg.seed, cfg.sim.device = N, 42, args.device
    for name in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity', 'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, name, 262144)
    env = gym.make('Template-Perceptual-Ball-Kickball-v11', cfg=cfg)
    try:
        b = env.unwrapped
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        obs, _ = wrapped.reset()
        expected = dict(proprio=[N,558], perception=[N,4,27,48], critic_state=[N,124],
                        ball_target=[N,6], amp=[N,600])
        assert {k:list(v.shape) for k,v in obs.items()} == expected
        assert set(b.scene.rigid_objects) == {'ball'}
        assert b._kickball.rsi_probability == 0 and b._kickball.serve_speed_range == (.4, 1.1)
        robot = b.scene['robot']
        torch.testing.assert_close(robot.data.joint_pos, robot.data.default_joint_pos, atol=0, rtol=0)
        assert torch.count_nonzero(robot.data.joint_vel) == 0
        assert torch.count_nonzero(robot.data.root_link_lin_vel_w) == 0
        ee = SceneEntityCfg('robot', body_names=END_EFFECTOR_BODY_NAMES, preserve_order=True)
        ee.resolve(b.scene)
        assert [robot.body_names[i] for i in ee.body_ids] == END_EFFECTOR_BODY_NAMES
        torch.testing.assert_close(task.amp_frame(b), amp_features(b, ee_cfg=ee), atol=1.e-6, rtol=0)
        assert torch.count_nonzero(task.amp_frame(b)[:,57:]) == 0
        torch.testing.assert_close(obs['ball_target'], task.ball_target(b))
        torch.testing.assert_close(obs['critic_state'][:,111:117], obs['ball_target'])

        # Ball contributes to the same live geometry depth as robot and ground.
        camera, ball = b.scene['depth_camera'], b.scene['ball']
        saved = ball.data.root_state_w.clone()
        far = saved.clone(); far[:, :3] = b.scene.env_origins + saved.new_tensor([50.,0.,.11]); far[:,7:] = 0
        ball.write_root_state_to_sim(far)
        camera.update(b.step_dt, force_recompute=True)
        absent = camera.data.output['distance_to_image_plane'][...,0].clone()
        near = far.clone()
        near[:, :3] = camera.data.pos_w + quat_apply(camera.data.quat_w_world, far.new_tensor([.8,0.,0.]).expand(N,-1))
        ball.write_root_state_to_sim(near)
        camera.update(b.step_dt, force_recompute=True)
        visible = camera.data.output['distance_to_image_plane'][...,0].clone()
        pixels = (absent - visible > .05).flatten(1).sum(-1)
        assert (pixels > 0).all(), pixels
        assert (visible >= .1).all() and (visible <= 3.).all()
        ball.write_root_state_to_sim(saved)
        obs, _ = wrapped.reset()
        noisy = task.depth_image(b).clone()
        rng = torch.cuda.get_rng_state()
        torch.testing.assert_close(task.depth_image(b), noisy, atol=0, rtol=0)
        assert torch.equal(torch.cuda.get_rng_state(), rng)

        # Partial reset does not mutate any surviving history, state, or noise.
        keep = torch.arange(1, N-1, device=b.device)
        ids = torch.tensor([0,N-1], device=b.device)
        previous_ball = ball.data.root_state_w.clone()
        hist = b.observation_manager.compute_group('perception').clone()
        b._reset_idx(ids)
        torch.testing.assert_close(ball.data.root_state_w[keep], previous_ball[keep], atol=0, rtol=0)
        torch.testing.assert_close(task.depth_image(b)[keep], noisy[keep], atol=0, rtol=0)
        torch.testing.assert_close(b.observation_manager.compute_group('perception')[keep], hist[keep], atol=0, rtol=0)
        action = b.action_manager.get_term('joint_pos')
        target = robot.data.joint_pos[ids][:,action._joint_ids]
        torch.testing.assert_close(action.delay.buffer[:,ids], target[None].expand(5,-1,-1))
        obs, _ = wrapped.reset()
        terminal_probes = {}
        original_reset = b._reset_idx
        def probe_reset(reset_ids):
            if getattr(b, '_carrybox_in_step', False):
                terminal_probes['depth'] = task.depth_image(b).clone()
                terminal_probes['target'] = task.ball_target(b).clone()
                terminal_probes['critic'] = task.critic_state(b).clone()
            return original_reset(reset_ids)
        b._reset_idx = probe_reset
        model = KickballV11OnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        initial = copy.deepcopy(model.alg.policy.state_dict())
        initial_d = model.alg.amp.amp_linear.weight.detach().clone()
        losses = []
        def update(runner):
            nonlocal obs
            with torch.inference_mode():
                for step in range(24):
                    if step == 0:
                        b.episode_length_buf[ids] = b.max_episode_length - 1
                    current_target = obs['ball_target'].clone()
                    obs, reward, done, extra = wrapped.step(runner.alg.act(obs))
                    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
                    torch.testing.assert_close(obs['ball_target'], task.ball_target(b))
                    torch.testing.assert_close(obs['perception'][:,-1], task.depth_image(b), atol=0, rtol=0)
                    if step == 0:
                        assert done[ids].all()
                        terminal = extra['terminal_observations']; rows = terminal['env_ids']
                        torch.testing.assert_close(terminal['obs']['perception'][:,-1], terminal_probes['depth'][rows], atol=0, rtol=0)
                        torch.testing.assert_close(terminal['obs']['ball_target'], terminal_probes['target'][rows])
                        torch.testing.assert_close(terminal['obs']['critic_state'], terminal_probes['critic'][rows])
                        torch.testing.assert_close(obs['perception'][ids], obs['perception'][ids,-1:].expand(-1,4,-1,-1), atol=0, rtol=0)
                    for actuator in robot.actuators.values():
                        assert (actuator.applied_effort.abs() <= actuator.effort_limit + 1.e-5).all()
                    runner.alg.process_env_step(obs, reward, done, extra)
                    torch.testing.assert_close(runner.alg.storage.observations['ball_target'][step], current_target)
                runner.alg.compute_returns(obs)
            loss = runner.alg.update()
            assert all(torch.isfinite(torch.tensor(v)) for v in loss.values())
            return loss
        losses.extend([update(model), update(model)])
        for prefix in ('actor.', 'critic.', 'perception_encoder.', 'ball_head.'):
            assert any(not torch.equal(v, initial[k]) for k,v in model.alg.policy.state_dict().items() if k.startswith(prefix)), prefix
        assert not torch.equal(initial_d, model.alg.amp.amp_linear.weight)
        assert model.alg.optimizer is model.alg.amp_optimizer
        assert {int(v['step']) for v in model.alg.optimizer.state.values()} == {40}
        model.current_learning_iteration = 2
        b._kickball.extension_unlocked = True
        b._kickball.extension_steps = b._kickball.course_config['extension_steps']
        b._kickball.direction_steps = 120000.
        model.save(OUT/'smoke_model.pt')
        saved_course = b._kickball.curriculum_state_dict()
        restored = KickballV11OnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        restored.load(OUT/'smoke_model.pt')
        obs = wrapped.get_observations()
        assert b._kickball.curriculum_state_dict() == saved_course
        assert b._kickball.serve_speed_range == (.4, 5.)
        assert torch.allclose(b._kickball.round_half_width, torch.full_like(b._kickball.round_half_width,.2))
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(obs), model.alg.policy.act_inference(obs), atol=0, rtol=0)
        assert restored.alg.learning_rate == model.alg.learning_rate
        incompatible = torch.load(OUT/'smoke_model.pt', map_location='cpu', weights_only=False)
        incompatible['environment_contract']['variant'] = 'walled11'
        torch.save(incompatible, OUT/'incompatible_model.pt')
        try:
            restored.load(OUT/'incompatible_model.pt')
        except ValueError:
            pass
        else:
            raise AssertionError('wall11 contract accepted as kickballv11')
        losses.append(update(restored))
        changed = obs.clone()
        for key in ('amp', 'ball_target', 'critic_state'):
            changed[key] += 1000
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(changed), restored.alg.policy.act_inference(obs), atol=0, rtol=0)
        exported = export_depth_policy(restored.alg.policy, obs, OUT/'exported', metadata=b.checkpoint_contract())
        with torch.inference_mode():
            torch.testing.assert_close(exported(obs['proprio'].cpu(), obs['perception'].cpu()),
                restored.alg.policy.act_inference(obs).cpu(), atol=2.e-5, rtol=1.e-5)
        graph = onnx.load(OUT/'exported/policy.onnx')
        assert [x.name for x in graph.graph.input] == ['flat','depth']
        assert not any('ball_head' in x.name or 'critic' in x.name for x in graph.graph.initializer)
        restored.load(OUT/'smoke_model.pt', load_optimizer=False)
        assert not b._kickball.curriculum_training
        report = dict(status='PASS', num_envs=N, iterations='2+1', rollout_steps=24,
            contract=b.checkpoint_contract(), shapes=expected, losses=losses,
            ball_depth_changed_pixels=pixels.tolist(), kick_end_effectors=END_EFFECTOR_BODY_NAMES,
            standing_only_reset=True, partial_reset=True, terminal_pairs=True, torque_limits=True,
            actor_export_privilege_boundary=True, curriculum_resume=True, convergence_evaluated=False)
        (OUT/'smoke.json').write_text(json.dumps(report, indent=2)+'\n')
        print('KICKBALL_V11_SMOKE_PASS', flush=True)
    finally:
        env.close()


try:
    main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    app.close(wait_for_replicator=False)
