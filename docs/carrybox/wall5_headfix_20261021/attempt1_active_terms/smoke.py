"""Twenty-env revision20 task gates, PPO/AMP update and strict checkpoint restore."""
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

OUT = Path(__file__).resolve().parent


def verify_gates(env):
    """Controlled simulator states, read back before stepping; not a contact test."""
    robot, box = env.scene['robot'], env.scene['box']
    r = robot.data.root_state_w.clone()
    b = box.data.root_state_w.clone()
    r[:, :3] = env.scene.env_origins
    r[:, 2] += r.new_tensor([.7731534838676453, .7731534838676453, .55, .55] * 5)
    r[:, 3:7] = r.new_tensor([1., 0., 0., 0.])
    r[:, 7:] = 0.
    b[:, :3] = env.scene.env_origins
    b[:, 0] += b.new_tensor([.5, .4, .7, .6] * 5)
    b[:, 2] += .125
    b[:, 3:7] = b.new_tensor([1., 0., 0., 0.])
    b[:, 7:] = 0.
    # Explicit link-state setter also refreshes the already-read link velocity
    # cache; the generic COM setter alone leaves it stale until the next step.
    robot.write_root_link_state_to_sim(r)
    box.write_root_state_to_sim(b)
    torch.testing.assert_close(robot.data.root_pos_w, robot.data.root_link_pos_w)
    torch.testing.assert_close(robot.data.root_link_lin_vel_w, torch.zeros_like(r[:, :3]))
    delta = box.data.root_pos_w - robot.data.root_link_pos_w
    d3 = parent.task_box_distance(env, delta)
    torch.testing.assert_close(d3, delta.norm(dim=-1))
    assert (d3 < env.cfg.reward_geometry['near_distance']).tolist() == [False, True, False, True] * 5
    parent.state(env).reward_step = None
    terms = reward_terms(env)
    assert (terms['carryup_task'] > 0).tolist() == [False, True, False, True] * 5
    walk = mdp.walk_task(env)
    torch.testing.assert_close(walk[[1, 3]], torch.full_like(walk[[1, 3]], 1.5))
    assert walk[0] < .53 and walk[2] < .53
    result = dict(distance_xyz=d3.tolist(), distance_xy=delta[:, :2].norm(dim=-1).tolist(),
                  carryup=terms['carryup_task'].tolist(), walk=walk.tolist())
    # Same geometry, bearing pi/2: search remains active outside the calibrated XYZ threshold.
    b[:, 1] = env.scene.env_origins[:, 1] + (b[:, 0] - env.scene.env_origins[:, 0])
    b[:, 0] = env.scene.env_origins[:, 0]
    box.write_root_state_to_sim(b)
    parent.state(env).search[:] = True
    search = parent.search_turn(env)
    assert (search > 0).tolist() == [True, False, True, False] * 5
    result['search_turn'] = search.tolist()
    return result



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

def main():
    torch.set_num_threads(2)
    cfg, agent = CarryBoxWalled5EnvCfg(), CarryBoxWalled5PPORunnerCfg()
    assert cfg.task_box_distance_3d is True
    for cls in (CarryBoxWalled3EnvCfg, CarryBoxWalled4EnvCfg):
        assert not getattr(cls(), 'task_box_distance_3d', False)
        assert not hasattr(cls(), 'reward_geometry')
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
        assert set(base.termination_manager.active_terms) == {'time_out', 'tipped', 'fell_pelvis', 'fell_head'}
        measured = json.loads((OUT.parent/'wall5_semantic_20261020/geometry.json').read_text())
        import hashlib
        assert hashlib.sha256(Path(cfg.scene.robot.spawn.usd_path).read_bytes()).hexdigest() == measured['asset_sha256']
        w = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        assert parent.state(base).library.metadata['manifest_sha256'] == measured['source_manifest_sha256']
        with torch.inference_mode():
            geometry = verify_gates(base)
            height_causes = verify_height_causes(base)
            obs, _ = w.reset()
        shapes = {'proprio': (20, 372), 'perception': (20, 4, 27, 48), 'amp': (20, 600),
                  'box_pose_target': (20, 10), 'critic_state': (20, 108), 'action_bounds': (20, 58)}
        assert {k: tuple(v.shape) for k, v in obs.items()} == shapes
        assert all(torch.isfinite(v).all() for v in obs.values())
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
            assert parent.state(base).skills.tolist() == [0] * 15 + [1] + [2] * 4
            return losses

        before = copy.deepcopy(runner.alg.policy.state_dict())
        losses = [update(runner), update(runner)]
        for prefix in ('actor.', 'critic.', 'perception_encoder.', 'pose_head.'):
            assert any(not torch.equal(before[k], v) for k, v in runner.alg.policy.state_dict().items()
                       if k.startswith(prefix)), prefix
        assert runner.alg.motion_metadata['clip_count'] == 13
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
        old_path = Path('logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_12-57-08_wall5_v19_rsi75_5_20_fresh_20261021_125703/model_0.pt')
        for load_optimizer in (True, False):
            try:
                restored.load(old_path, load_optimizer=load_optimizer)
            except ValueError as error:
                assert 'environment variant/contract' in str(error)
            else:
                raise AssertionError('Revision19 strict restore was not rejected')
        losses.append(update(restored))
        contract = base.checkpoint_contract()
        assert contract['migration_revision'] == 20
        assert contract['task_box_distance']['metric'] == 'xyz_l2'
        assert contract['reward_geometry'] == cfg.reward_geometry
        assert contract['reward_geometry']['body_frame'] == 'pelvis'
        result = dict(status='PASS',height_causes=height_causes,geometry=geometry,shapes=shapes,contract=contract,losses=losses,
                      wall3_wall4_remain_xy=True,strict_restore=True,rev19_strict_restore_rejected=True,
                      optimizer_and_amp_updated=True,formal_training_restarted=False)
        (OUT / 'smoke.json').write_text(json.dumps(result, indent=2) + '\n')
        print('HEADFIX_SMOKE_PASS', flush=True)
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
