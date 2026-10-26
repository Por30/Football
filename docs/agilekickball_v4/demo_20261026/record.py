"""Render the requested v4 checkpoint using the normal play runner and curriculum."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import hashlib
import json
from pathlib import Path
import gymnasium as gym
import imageio.v2 as imageio
import numpy as np
import torch
from PIL import Image
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v4_env_cfg import (
    AgileKickballV4EnvCfg, AgileKickballV4PPORunnerCfg,
)

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
SELECTION = json.loads((DOC / 'selection.json').read_text())
CKPT = Path(SELECTION['checkpoint'])
VIDEO = Path(SELECTION['video'])


def main():
    torch.set_num_threads(2)
    assert not VIDEO.exists(), 'Preserve prior recordings'
    digest = hashlib.sha256(CKPT.read_bytes()).hexdigest()
    assert digest == SELECTION['checkpoint_sha256']
    for name, expected in SELECTION['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    checkpoint = torch.load(CKPT, map_location='cpu', weights_only=False)
    assert checkpoint['iter'] == 49999 and checkpoint['soccer_schema_version'] == 3
    course = checkpoint['agile_v4_return_curriculum']
    assert course['config']['revision'] == 'return_to_sender_20261012'
    assert all(torch.isfinite(x).all() for x in checkpoint['model_state_dict'].values())
    cfg, agent = AgileKickballV4EnvCfg(), AgileKickballV4PPORunnerCfg()
    cfg.scene.num_envs, cfg.seed, cfg.sim.device = 1, 42, args.device
    agent.seed, agent.device = 42, args.device
    cfg.viewer.resolution = (1920, 1080)
    cfg.viewer.eye, cfg.viewer.lookat = (3.6, -4.5, 2.6), (.65, 0., .65)
    cfg.sim.render.enable_direct_lighting = True
    # Only reduce oversized broadphase buffers for this one-environment recording.
    for key in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity',
                'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, key, 262144)
    env = gym.make(SELECTION['task'], cfg=cfg, render_mode='rgb_array')
    raw = env.unwrapped
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    try:
        runner = BallRegressionOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        runner.load(str(CKPT), load_optimizer=False)
        policy = runner.get_inference_policy(device=args.device)
        network = runner.alg.policy
        saved = {name: value.detach().clone() for name, value in network.state_dict().items()}
        kb = raw._kickball
        assert not kb.curriculum_training and kb.serve_speed_override is None
        assert abs(raw.step_dt - .02) < 1.e-9
        samples, episodes = [], []
        active, step = False, 0
        original_reset = raw._reset_idx

        def capture_reset(ids):
            if active:
                for i in ids.tolist():
                    causes = {name: bool(raw.termination_manager.get_term(name)[i])
                              for name in raw.termination_manager.active_terms}
                    episodes.append(dict(step=step + 1, causes=causes,
                                         episode_steps=int(raw.episode_length_buf[i])))
            original_reset(ids)

        raw._reset_idx = capture_reset
        counts = ('serves', 'recovered_serves', 'foot_strike_rounds', 'target_hits',
                  'strict_hits', 'completed_rounds', 'completed_target_hits')

        def read_counts():
            return {name: int(getattr(kb, name)[0]) for name in counts}

        def frame():
            before = raw.scene['robot'].data.root_pos_w.clone()
            physics_time, counter = raw.sim.current_time, raw.common_step_counter
            rgb = np.asarray(raw.render()).copy()[..., :3]
            assert rgb.shape == (1080, 1920, 3) and rgb.std() > 5.
            assert raw.sim.current_time == physics_time and raw.common_step_counter == counter
            assert torch.equal(before, raw.scene['robot'].data.root_pos_w)
            return rgb

        with torch.inference_mode():
            # Match play.py: reset once after restoring the checkpoint course.
            obs, _ = wrapped.reset()
            initial = read_counts()
            initial_course = dict(speed=list(kb.serve_speed_range), distance=list(kb.serve_distance_range),
                                  target_half_width=kb.target_half_width)
            print('PLAY_COURSE', initial_course, flush=True)
            # render() creates its RGB annotator lazily; create it before warmup.
            raw.render()
            for _ in range(16):
                raw.sim.render()
            Image.fromarray(frame()).save(VIDEO.parent / 'initial_scene.png')
            active = True
            with imageio.get_writer(str(VIDEO), fps=25, codec='libx264', quality=8,
                                   pixelformat='yuv420p', macro_block_size=2,
                                   ffmpeg_params=['-threads', '2', '-movflags', '+faststart']) as writer:
                nframes = 0
                for step in range(SELECTION['steps']):
                    actions = policy(obs)
                    assert torch.isfinite(actions).all()
                    obs, reward, done, _ = wrapped.step(actions)
                    assert torch.isfinite(reward).all() and all(torch.isfinite(x).all() for x in obs.values())
                    robot, ball = raw.scene['robot'].data, raw.scene['ball'].data
                    samples.append(dict(step=step + 1, robot=robot.root_pos_w[0].tolist(),
                                        ball=ball.root_pos_w[0].tolist(), ball_velocity=ball.root_lin_vel_w[0].tolist(),
                                        active=bool(kb.ball_active[0]), reset=bool(done[0]),
                                        return_hit=bool(kb.return_hit[0]), counts=read_counts()))
                    if (step + 1) % 2 == 0:
                        rgb = frame()
                        writer.append_data(rgb)
                        nframes += 1
                        if nframes in (1, 25, 50, 125, 250, 375, 500, 625, 749, 750):
                            Image.fromarray(rgb).save(VIDEO.parent / f'frame_{nframes:04d}.png')
                    if (step + 1) % 100 == 0:
                        print('RECORD_PROGRESS', step + 1, 'frames', nframes,
                              'resets', len(episodes), 'counts', read_counts(), flush=True)
        assert nframes == 750 and all(torch.equal(v, saved[k]) for k, v in network.state_dict().items())
        assert hashlib.sha256(CKPT.read_bytes()).hexdigest() == digest
        assert not kb.curriculum_training and list(kb.serve_speed_range) == initial_course['speed']
        result = dict(status='PASS', **SELECTION, strict_load=True, weights_unchanged=True,
                      frames=nframes, resolution=[1920, 1080], duration=30., control_dt=raw.step_dt,
                      action_mode='deterministic_mean', course=initial_course,
                      viewer_eye=list(cfg.viewer.eye), viewer_lookat=list(cfg.viewer.lookat),
                      rendering_advances_physics=False, initial_counts=initial,
                      final_counts=read_counts(), episodes=episodes, reset_count=len(episodes),
                      task_overrides=[], visual_overrides=['spectator_camera', 'direct_lighting'],
                      raw_continuous=True, finite_inference=True)
        (DOC / 'trajectory.json').write_text(json.dumps(samples) + '\n')
        (DOC / 'recording.json').write_text(json.dumps(result, indent=2) + '\n')
        print('RECORD_PASS', str(VIDEO), flush=True)
    finally:
        wrapped.close()


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        import traceback
        traceback.print_exc()
        raise
    finally:
        app.close()
