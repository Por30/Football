"""Four-env revision19 task gates, PPO/AMP update and strict checkpoint restore."""
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
    r[:, 2] += r.new_tensor([.7731534838676453, .7731534838676453, .55, .55])
    r[:, 3:7] = r.new_tensor([1., 0., 0., 0.])
    r[:, 7:] = 0.
    b[:, :3] = env.scene.env_origins
    b[:, 0] += b.new_tensor([.5, .4, .7, .6])
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
    assert (d3 < env.cfg.reward_geometry['near_distance']).tolist() == [False, True, False, True]
    parent.state(env).reward_step = None
    terms = reward_terms(env)
    assert (terms['carryup_task'] > 0).tolist() == [False, True, False, True]
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
    assert (search > 0).tolist() == [True, False, True, False]
    result['search_turn'] = search.tolist()
    return result


def main():
    torch.set_num_threads(2)
    cfg, agent = CarryBoxWalled5EnvCfg(), CarryBoxWalled5PPORunnerCfg()
    assert cfg.task_box_distance_3d is True
    for cls in (CarryBoxWalled3EnvCfg, CarryBoxWalled4EnvCfg):
        assert not getattr(cls(), 'task_box_distance_3d', False)
        assert not hasattr(cls(), 'reward_geometry')
    cfg.scene.num_envs = 4
    cfg.seed = 42
    cfg.sim.device = args.device
    for name in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity',
                 'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, name, 262144)
    env = gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0', cfg=cfg)
    try:
        base = env.unwrapped
        assert 'locomotion_stability' not in base.reward_manager.active_terms
        w = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        with torch.inference_mode():
            geometry = verify_gates(base)
            obs, _ = w.reset()
        shapes = {'proprio': (4, 372), 'perception': (4, 4, 27, 48), 'amp': (4, 600),
                  'box_pose_target': (4, 10), 'critic_state': (4, 108), 'action_bounds': (4, 58)}
        assert {k: tuple(v.shape) for k, v in obs.items()} == shapes
        assert all(torch.isfinite(v).all() for v in obs.values())
        assert parent.state(base).skills.tolist() == [0, 0, 0, 2]
        runner = CarryBoxWall5OnPolicyRunner(w, agent.to_dict(), log_dir=None, device=args.device)

        def update(current):
            nonlocal obs
            with torch.inference_mode():
                for step in range(agent.num_steps_per_env):
                    if step == 0:
                        base.episode_length_buf[[0, 2]] = base.max_episode_length - 1
                    action = current.alg.act(obs)
                    obs, reward, done, extra = w.step(action)
                    current.alg.process_env_step(obs, reward, done, extra)
                    assert torch.isfinite(reward).all()
                    assert 'Reward/loco_locomotion_stability_per_step' not in extra['log']
                    assert 'Reward/loco_carryup_task_per_step' in extra['log']
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
            assert parent.state(base).skills.tolist() == [0, 0, 0, 2]
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
        old_path = Path('logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-20_12-48-36_wall5_v18_distance3d_fresh_20261020_124832/model_0.pt')
        for load_optimizer in (True, False):
            try:
                restored.load(old_path, load_optimizer=load_optimizer)
            except ValueError as error:
                assert 'environment variant/contract' in str(error)
            else:
                raise AssertionError('Revision18 strict restore was not rejected')
        losses.append(update(restored))
        contract = base.checkpoint_contract()
        assert contract['migration_revision'] == 19
        assert contract['task_box_distance']['metric'] == 'xyz_l2'
        assert contract['reward_geometry'] == cfg.reward_geometry
        assert contract['reward_geometry']['body_frame'] == 'pelvis'
        result = dict(status='PASS',geometry=geometry,shapes=shapes,contract=contract,losses=losses,
                      wall3_wall4_remain_xy=True,strict_restore=True,rev18_strict_restore_rejected=True,
                      optimizer_and_amp_updated=True,formal_training_restarted=False)
        (OUT / 'smoke.json').write_text(json.dumps(result, indent=2) + '\n')
        print('SEMANTIC_SMOKE_PASS', flush=True)
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
