"""Twenty-env revision23 task gates, PPO/AMP update and strict checkpoint restore."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import copy
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import (
    CarryBoxWalled5EnvCfg, CarryBoxWalled5PPORunnerCfg)
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import (
    CarryBoxWalled3EnvCfg, CarryBoxWalled4EnvCfg)
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as mdp
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards import reward_terms
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy

OUT = Path(__file__).resolve().parent


def verify_gates(env):
    from perceptual_ball.carrybox_wall5 import grasp_reward_geometry
    from self_collision_check import verify_self_collision
    check = verify_self_collision(env)
    assert env.cfg.grasp_geometry == grasp_reward_geometry()
    env.reset()
    robot, box = env.scene['robot'].data, env.scene['box'].data
    g = mdp.grasp_state(env)
    from isaaclab.utils.math import quat_apply_inverse
    ids = env.scene['robot'].find_bodies(['left_palm_link','right_palm_link'],preserve_order=True)[0]
    palms = quat_apply_inverse(box.root_quat_w[:,None].expand(-1,2,-1),
                              robot.body_link_pos_w[:,ids]-box.root_pos_w[:,None])
    surface = (palms.abs()-palms.new_tensor([.15,.15,.125])).clamp_min(0.).norm(dim=-1)
    torch.testing.assert_close(g['surface_distance'],surface)
    for name in ('carryup_task','stable_grasp','slow_pickup','arm_speed_pickup','arm_acc_pickup'):
        value = mdp.grasp_task_reward(env,name)
        assert value.shape == (20,) and torch.isfinite(value).all()
    return dict(self_collision=check,surface_distance_readback=True)


def verify_height_causes(env):
    """Read real G1 FK; diagnose simultaneous causes before a partial reset."""
    robot = env.scene['robot']
    ids = torch.arange(4, device=env.device)
    root = robot.data.root_state_w[ids].clone()
    root[:, :3] = env.scene.env_origins[ids]
    root[:, 2] += root.new_tensor([.2, .8, .1, .8])
    root[:, 3:7] = root.new_tensor([[1., 0., 0., 0.], [0., 0., 1., 0.],
                                  [0., 0., 1., 0.], [1., 0., 0., 0.]])
    root[:, 7:] = 0.
    robot.write_joint_state_to_sim(robot.data.default_joint_pos[ids],
                                  torch.zeros_like(robot.data.default_joint_pos[ids]), env_ids=ids)
    robot.write_root_link_state_to_sim(root, env_ids=ids)
    env.sim.forward()
    env.scene.update(env.physics_dt)
    pelvis, head = parent.fallen_pelvis(env)[ids], parent.fallen_head(env)[ids]
    heights = parent.head_height(env)[ids].tolist()
    assert pelvis.tolist() == [True, False, True, False], pelvis
    assert head.tolist() == [False, True, True, False], heights
    s = parent.state(env)
    assert s.skills[ids].tolist() == [0, 0, 0, 0]
    previous = {key: getattr(s, key).clone() for key in ('episode_counts', 'fell_counts', 'tipped_counts')}
    env.termination_manager.compute()
    env._carrybox_in_step = True
    try:
        env._reset_idx(ids[:3])
    finally:
        env._carrybox_in_step = False
    assert (s.episode_counts-previous['episode_counts']).tolist() == [3, 0, 0]
    assert (s.fell_counts-previous['fell_counts']).tolist() == [3, 0, 0]
    assert s.height_failure_counts['fell_pelvis'].tolist() == [2, 0, 0]
    assert s.height_failure_counts['fell_head'].tolist() == [2, 0, 0]
    # These intentionally forced episodes belong only to this diagnostic run.
    return dict(root_height_m=[.2, .8, .1, .8], head_com_height_m=heights,
                pelvis_flags=pelvis.tolist(), head_flags=head.tolist(),
                multi_cause_counts=[2, 2], aggregate_fell_count=3,
                pre_reset_accounting_verified=True)


def verify_depth_units(env):
    """Actual Warp capture is metres; deterministic clean capture isolates unit conversion."""
    cfg = env.cfg
    keys = ('depth_noise_std_m', 'depth_stereo_near_m', 'depth_stereo_far_m',
            'depth_edge_probability', 'depth_hole_probability',
            'depth_delay_probability', 'depth_freeze_probability')
    previous = {key: getattr(cfg, key) for key in keys}
    try:
        for key in keys: setattr(cfg, key, 0.)
        parent.state(env).paired = None
        camera = env.scene['depth_camera']
        raw = camera.data.output['distance_to_image_plane'][..., 0].clone()
        expected = torch.nan_to_num(raw, nan=3., posinf=3., neginf=3.).clamp(.1, 3.)
        depth, target = parent.captured_pair(env)
        torch.testing.assert_close(depth, expected, rtol=0, atol=0)
        assert depth.max() == 3. and depth.gt(1.).any()
        assert depth.min() >= .1
        hits = camera.data.output['mesh_id'][..., 0]
        box_id = next(i for i, mesh in enumerate(camera.mesh_manifest) if mesh['root'].endswith('/Box'))
        visible = ((hits == box_id) & (depth < 3.) & (depth >= .1)).flatten(1).any(-1)
        visible &= (target[:, 2] >= .1) & (target[:, 2] < 3.)
        torch.testing.assert_close(target[:, 9].bool(), visible)
        return dict(min_m=float(depth.min()), max_m=float(depth.max()),
                    raw_warp_capture_exact=True, above_one_metre_pixels=int(depth.gt(1.).sum()),
                    visible_box_count=int(visible.sum()), nearest_hit_visibility_matches=True)
    finally:
        for key, value in previous.items(): setattr(cfg, key, value)
        parent.state(env).paired = None

def main():
    torch.set_num_threads(2)
    cfg, agent = CarryBoxWalled5EnvCfg(), CarryBoxWalled5PPORunnerCfg()
    assert cfg.task_box_distance_3d is True
    assert cfg.depth_in_metres and cfg.depth_noise_std_m == .02
    assert cfg.depth_stereo_near_m == .008 and cfg.depth_stereo_far_m == .03
    assert agent.algorithm.pose_aux_coef == 1.0
    for cls in (CarryBoxWalled3EnvCfg, CarryBoxWalled4EnvCfg):
        assert not cls().scene.robot.spawn.articulation_props.enabled_self_collisions
        assert not getattr(cls(), 'task_box_distance_3d', False)
        assert not hasattr(cls(), 'reward_geometry')
        assert not getattr(cls(), 'depth_in_metres', False)
        assert cls().depth_noise_std_m == .06
        assert (cls().depth_stereo_near_m, cls().depth_stereo_far_m) == (.024, .09)
    cfg.scene.num_envs = 20
    cfg.seed = 42
    cfg.sim.device = args.device
    for name in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity',
                 'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, name, 262144)
    env = gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0', cfg=cfg)
    try:
        base = env.unwrapped
        assert 'locomotion_stability' not in base.reward_manager.active_terms
        assert 'early_failure' not in base.reward_manager.active_terms
        assert set(base.termination_manager.active_terms) == {'time_out', 'invalid', 'tipped', 'fell_pelvis', 'fell_head'}
        measured = json.loads((OUT.parent/'wall5_semantic_20261020/geometry.json').read_text())
        import hashlib
        assert hashlib.sha256(Path(cfg.scene.robot.spawn.usd_path).read_bytes()).hexdigest() == measured['asset_sha256']
        w = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        assert parent.state(base).library.metadata['manifest_sha256'] == measured['source_manifest_sha256']
        with torch.inference_mode():
            depth_check = verify_depth_units(base)
            geometry = verify_gates(base)
            height_causes = verify_height_causes(base)
            obs, _ = w.reset()
        shapes = {'proprio': (20, 372), 'perception': (20, 4, 27, 48), 'amp': (20, 600),
                  'box_pose_target': (20, 10), 'critic_state': (20, 123), 'action_bounds': (20, 58)}
        assert {k: tuple(v.shape) for k, v in obs.items()} == shapes
        # Read actual G1 link origins back from PhysX, independently check all 15 critic values.
        from isaaclab.utils.math import quat_apply
        robot = base.scene['robot']
        ids, names = robot.find_bodies(list(mdp.AMP_BODY_NAMES), preserve_order=True)
        assert names == list(mdp.AMP_BODY_NAMES)
        ends = obs['critic_state'][:, 108:].reshape(20, 5, 3)
        torch.testing.assert_close(
            quat_apply(robot.data.root_link_quat_w[:, None].expand(-1, 5, -1), ends),
            robot.data.body_link_pos_w[:, ids] - robot.data.root_link_pos_w[:, None], atol=2e-6, rtol=2e-5)
        assert all(torch.isfinite(v).all() for v in obs.values())
        assert obs['perception'].min() >= .1 and obs['perception'].max() == 3.
        assert obs['perception'].gt(1.).any()
        assert parent.state(base).skills.tolist() == [0] * 15 + [1] + [2] * 4
        runner = CarryBoxWall5OnPolicyRunner(w, agent.to_dict(), log_dir=None, device=args.device)

        def update(current):
            nonlocal obs
            with torch.inference_mode():
                for step in range(agent.num_steps_per_env):
                    if step == 0:
                        base.episode_length_buf[[0, 15, 16]] = base.max_episode_length - 1
                    action = current.alg.act(obs)
                    obs, reward, done, extra = w.step(action)
                    current.alg.process_env_step(obs, reward, done, extra)
                    assert torch.isfinite(reward).all()
                    assert 'Reward/loco_locomotion_stability_per_step' not in extra['log']
                    assert 'Reward/loco_carryup_task_per_step' in extra['log']
                    assert 'Reward/loco_early_failure_per_step' not in extra['log']
                    if step == 0:
                        for key in ('Episode_Termination/fell_pelvis', 'Episode_Termination/fell_head', 'Skill/loco_fell_pelvis_fraction', 'Skill/loco_fell_head_fraction'):
                            assert key in extra['log'], key
                    assert all(torch.isfinite(v).all() for v in obs.values())
                    # The generic distance metric now follows gates; XY is explicit.
                    r, b = base.scene['robot'].data, base.scene['box'].data
                    active = ((parent.state(base).skills == 0) & ~done).float()
                    delta = b.root_pos_w - r.root_link_pos_w
                    for key, distance in (('box_distance_m', delta.norm(dim=-1)),
                                          ('box_distance_xy_m', delta[:, :2].norm(dim=-1))):
                        expected = (distance * active).sum() / active.sum().clamp_min(1.)
                        torch.testing.assert_close(extra['log']['Motion/loco_survivor_' + key], expected)
                current.alg.compute_returns(obs)
            losses = current.alg.update()
            assert all(torch.isfinite(torch.tensor(v)) for v in losses.values())
            assert current.alg.pose_aux_coef == 1.0 and losses['box_supervised_fraction'] == 1.0
            assert abs(losses['box_aux_weighted'] - losses['box_position'] - losses['box_rotation']) < 1.e-6
            assert parent.state(base).skills.tolist() == [0] * 15 + [1] + [2] * 4
            return losses

        before = copy.deepcopy(runner.alg.policy.state_dict())
        losses = [update(runner), update(runner)]
        for prefix in ('actor.', 'critic.', 'perception_encoder.', 'pose_head.'):
            assert any(not torch.equal(before[k], v) for k, v in runner.alg.policy.state_dict().items()
                       if k.startswith(prefix)), prefix
        assert runner.alg.motion_metadata['clip_count'] == 15
        assert runner.alg.motion_metadata['total_frames'] == 4155
        assert runner.alg.motion_metadata['manifest_sha256'] != parent.state(base).library.metadata['manifest_sha256']
        assert runner.alg.optimizer.state and runner.alg.amp_optimizer.state
        runner.current_learning_iteration = 2
        path = OUT / 'smoke_model.pt'
        runner.save(path)
        restored = CarryBoxWall5OnPolicyRunner(w, agent.to_dict(), log_dir=None, device=args.device)
        restored.load(path)
        assert restored.current_learning_iteration == 2
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(obs),
                                       runner.alg.policy.act_inference(obs), rtol=0, atol=0)
            torch.testing.assert_close(restored.alg.policy.evaluate(obs),
                                       runner.alg.policy.evaluate(obs), rtol=0, atol=0)
        old_path = Path('/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_14-09-30_wall5_v22_critic123_aux1_fresh_20261021_140925/model_22800.pt')
        for load_optimizer in (True, False):
            try:
                restored.load(old_path, load_optimizer=load_optimizer)
            except ValueError as error:
                assert 'environment variant/contract' in str(error)
            else:
                raise AssertionError('Revision22 strict restore was not rejected')
        losses.append(update(restored))
        with torch.inference_mode():
            wrapper = export_depth_policy(restored.alg.policy, obs, OUT/'exported',
                                          {'depth_contract': base.depth_contract})
            expected = restored.alg.policy.act_inference(obs).cpu()
            flat, depth = obs['proprio'].cpu(), obs['perception'].cpu()
            torch.testing.assert_close(wrapper(flat, depth), expected, atol=2e-5, rtol=2e-5)
            loaded = torch.jit.load(str(OUT/'exported/policy.pt'))
            torch.testing.assert_close(loaded(flat, depth), expected, atol=2e-5, rtol=2e-5)
            assert not any(k.startswith(('critic.', 'pose_head.')) for k in loaded.state_dict())
        manifest = json.loads((OUT/'exported/manifest.json').read_text())
        assert manifest['metadata']['depth_contract'] == base.depth_contract
        assert manifest['flat_groups'] == ['proprio'] and manifest['depth_shape'] == [4, 27, 48]

        contract = base.checkpoint_contract()
        assert contract['migration_revision'] == 23
        assert contract['task_box_distance']['metric'] == 'xyz_l2'
        assert contract['reward_geometry'] == cfg.reward_geometry
        assert contract['reward_geometry']['body_frame'] == 'pelvis'
        assert contract['self_collisions'] is True
        assert contract['grasp_reward']['profile'] == 'bilateral_surface_contact_clearance_v23'
        result = dict(status='PASS',depth_units=depth_check,exported_metres_policy=True,critic_endpoints_readback=True,all_frames_aux_coef=1.0,height_causes=height_causes,geometry=geometry,shapes=shapes,contract=contract,losses=losses,
                      wall3_wall4_remain_xy=True,strict_restore=True,rev22_strict_restore_rejected=True,
                      optimizer_and_amp_updated=True,formal_training_restarted=False)
        (OUT / 'smoke.json').write_text(json.dumps(result, indent=2) + '\n')
        print('GRASP_SMOKE_PASS', flush=True)
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
