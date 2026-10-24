"""Wall10 real-physics geometry/control, PPO+AMP, resume and actor export acceptance."""
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
import warp as wp
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.carrybox_raycast import optical_depth
from perceptual_ball.carrybox_warp_camera import visual_mesh
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall10_env_cfg import CarryBoxWalled10EnvCfg, CarryBoxWalled10PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg, CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall10 as task
from perceptual_ball.rsl_rl_extensions.carrybox_wall10 import CarryBoxWall10OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy

OUT = Path(__file__).resolve().parent
N = 16


def geometry_check(env):
    camera = env.scene['depth_camera']
    depth = camera.data.output['distance_to_image_plane'][..., 0]
    sizes = camera.box_sizes
    assert len(torch.unique(sizes, dim=0)) > 1
    assert (sizes[:, :2] >= .21 - 1.e-6).all() and (sizes[:, :2] <= .39 + 1.e-6).all()
    assert (sizes[:, 2] >= .15 - 1.e-6).all() and (sizes[:, 2] <= .35 + 1.e-6).all()
    mass = env.scene['box'].root_physx_view.get_masses().flatten().to(env.device)
    density = mass / sizes.prod(-1)
    assert (density >= 10 - .001).all() and (density <= 100 + .001).all()
    # Independent triangle-BVH renderer uses the actual spawned box geometry.
    errors = []
    poses = torch.stack([v if isinstance(v, torch.Tensor) else v.get_transforms() for v in camera._views], 1)
    poses = torch.cat((poses, camera._box_view.get_transforms()[:, None]), 1).contiguous()
    camera_pose = torch.cat((camera._data.pos_w, camera._data.quat_w_world[:, [1,2,3,0]]), -1).contiguous()
    baseline = torch.full_like(camera._depth, 3.)
    for i in range(N):
        vertices, faces, _ = visual_mesh(camera.stage, f'/World/envs/env_{i}/Box')
        mesh = wp.Mesh(points=wp.array(vertices, dtype=wp.vec3, device=env.device),
                       indices=wp.array(faces, dtype=wp.int32, device=env.device))
        mesh_ids = wp.array([m.id for m in camera._meshes] + [mesh.id], dtype=wp.uint64, device=env.device)
        with wp.ScopedStream(wp.stream_from_torch(torch.cuda.current_stream(env.device))):
            wp.launch(optical_depth, dim=(1, 48*27), inputs=[
                wp.from_torch(torch.tensor([i], device=env.device, dtype=torch.int32)),
                wp.from_torch(camera_pose, dtype=wp.transform), wp.from_torch(camera._rays, dtype=wp.vec3),
                mesh_ids, wp.from_torch(poses, dtype=wp.transform), .1, 3., wp.from_torch(baseline)], device=env.device)
        torch.cuda.synchronize()
        errors.append(float((baseline[i] - camera._depth[i]).abs().max()))
    assert max(errors) < .001, errors
    return dict(box_sizes=sizes.tolist(), density=density.tolist(), per_env_depth_error_m=errors)


def main():
    torch.set_num_threads(2)
    cfg, agent = CarryBoxWalled10EnvCfg(), CarryBoxWalled10PPORunnerCfg()
    assert (agent.num_steps_per_env, agent.max_iterations, agent.save_interval) == (100, 20000, 500)
    assert agent.algorithm.num_learning_epochs == 5 and agent.algorithm.learning_rate == .001
    assert agent.algorithm.pose_aux_coef == 0 and cfg.terminations.success is None
    old, old_agent = CarryBoxWalled5EnvCfg(), CarryBoxWalled5PPORunnerCfg()
    assert old_agent.num_steps_per_env == 24 and old_agent.algorithm.learning_rate == .0003
    assert old.scene.robot.actuators['legs'].class_type.__name__ == 'ImplicitActuator'
    cfg.scene.num_envs = N
    cfg.seed = 42
    cfg.sim.device = args.device
    for name in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity', 'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, name, 262144)
    env = gym.make('Template-Perceptual-Ball-CarryBox-Walled10-v0', cfg=cfg)
    try:
        b = env.unwrapped
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        obs, _ = wrapped.reset()
        expected = {'proprio': [N,558], 'perception': [N,4,27,48], 'critic_state': [N,123],
                    'box_pose_target': [N,9], 'amp': [N,600]}
        assert {k:list(v.shape) for k,v in obs.items()} == expected
        geometry = geometry_check(b)
        for actuator in b.scene['robot'].actuators.values():
            assert isinstance(actuator, task.Wall10Actuator)
            assert (actuator.effort_limit > 0).all() and (actuator.effort_limit < 500).all()
            for tensor in (actuator.kp_factor, actuator.kd_factor, actuator.motor_strength):
                assert (tensor >= .9).all() and (tensor <= 1.1).all()
            assert (actuator.effort_offset.abs() <= .05 * actuator.effort_limit).all()
        mat = b.scene['robot'].root_physx_view.get_material_properties()
        torch.testing.assert_close(mat[:,:,0], mat[:,:,1], atol=0, rtol=0)
        assert (mat[:,:,0] >= .1).all() and (mat[:,:,0] <= 1.5).all()
        # A partial reset affects selected physics, action queues and histories only.
        ids = torch.tensor([N-1, 0], device=b.device)
        keep = torch.arange(1, N-1, device=b.device)
        saved_pose = b.scene['robot'].data.root_state_w.clone()
        saved_hist = b.observation_manager.compute_group('proprio').clone()
        b._reset_idx(ids)
        torch.testing.assert_close(b.scene['robot'].data.root_state_w[keep], saved_pose[keep], atol=1.e-6, rtol=0)
        torch.testing.assert_close(b.observation_manager.compute_group('proprio')[keep], saved_hist[keep], atol=0, rtol=0)
        action = b.action_manager.get_term('joint_pos')
        target = b.scene['robot'].data.joint_pos[ids][:, action._joint_ids]
        torch.testing.assert_close(action.delay.buffer[:, ids], target[None].expand(5,-1,-1))
        obs, _ = wrapped.reset()
        model = CarryBoxWall10OnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        initial = copy.deepcopy(model.alg.policy.state_dict())
        initial_d = model.alg.amp.amp_linear.weight.detach().clone()
        losses = []
        def update(runner):
            nonlocal obs
            with torch.inference_mode():
                for step in range(100):
                    if step == 0:
                        b.episode_length_buf[[0,N-1]] = b.max_episode_length - 1
                    old_delay = action.delay.steps
                    obs, reward, done, extra = wrapped.step(runner.alg.act(obs))
                    assert action.delay.steps - old_delay == 4
                    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
                    torch.testing.assert_close(obs['perception'][:,-1], task.depth_image(b), atol=0, rtol=0)
                    for actuator in b.scene['robot'].actuators.values():
                        assert (actuator.applied_effort.abs() <= actuator.effort_limit + 1.e-5).all()
                    if step == 0:
                        assert done[[0,N-1]].all()
                        terminal = extra['terminal_observations']
                        assert terminal['obs']['critic_state'].shape[-1] == 123
                        assert terminal['obs']['proprio'].shape[-1] == 558
                    runner.alg.process_env_step(obs, reward, done, extra)
                runner.alg.compute_returns(obs)
            loss = runner.alg.update()
            assert all(torch.isfinite(torch.tensor(v)) for v in loss.values())
            return loss
        losses.extend([update(model), update(model)])
        for prefix in ('actor.', 'critic.', 'perception_encoder.'):
            assert any(not torch.equal(v, initial[k]) for k,v in model.alg.policy.state_dict().items() if k.startswith(prefix)), prefix
        assert not torch.equal(initial_d, model.alg.amp.amp_linear.weight)
        assert model.alg.optimizer is model.alg.amp_optimizer
        assert {int(v['step']) for v in model.alg.optimizer.state.values()} == {40}
        model.current_learning_iteration = 2
        model.save(OUT/'smoke_model.pt')
        restored = CarryBoxWall10OnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        restored.load(OUT/'smoke_model.pt')
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(obs), model.alg.policy.act_inference(obs), atol=0, rtol=0)
        assert restored.alg.learning_rate == model.alg.learning_rate
        incompatible = torch.load(OUT/'smoke_model.pt', map_location='cpu', weights_only=False)
        incompatible['environment_contract']['variant'] = 'walled5'
        torch.save(incompatible, OUT/'incompatible_model.pt')
        try:
            restored.load(OUT/'incompatible_model.pt')
        except ValueError as error:
            assert 'environment variant/contract' in str(error)
        else:
            raise AssertionError('wall5 checkpoint accepted as wall10')
        losses.append(update(restored))
        changed = obs.clone()
        for key in ('amp', 'box_pose_target', 'critic_state'):
            changed[key] += 1000
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(changed), restored.alg.policy.act_inference(obs), atol=0, rtol=0)
        exported = export_depth_policy(restored.alg.policy, obs, OUT/'exported', metadata=b.checkpoint_contract())
        with torch.inference_mode():
            torch.testing.assert_close(exported(obs['proprio'].cpu(), obs['perception'].cpu()),
                                       restored.alg.policy.act_inference(obs).cpu(), atol=2.e-5, rtol=1.e-5)
        report = dict(status='PASS', num_envs=N, iterations='2+1', rollout_steps=100,
            checkpoint_schema=2, contract=b.checkpoint_contract(), shapes=expected, geometry=geometry,
            losses=losses, reset_counts=task.state(b).reset_counts.tolist(),
            old_task_defaults_unchanged=True, partial_reset=True, torque_limits=True,
            actor_export_privilege_boundary=True, resume=True, convergence_evaluated=False)
        (OUT/'smoke.json').write_text(json.dumps(report, indent=2)+'\n')
        print('WALL10_SMOKE_PASS', flush=True)
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
