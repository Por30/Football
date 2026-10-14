"""Read existing Wall4 measurements; never launch a simulator or touch training."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import pstats
import re
import statistics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=Path('docs/carrybox/render6s_20261014'))
    parser.add_argument('--output', type=Path, default=Path('docs/carrybox/depth_timing_20261014/timing.json'))
    args = parser.parse_args()
    hashes = json.loads((args.evidence / 'source_hashes.json').read_text())
    mismatches = [p for p, h in hashes.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != h]
    if mismatches:
        raise RuntimeError(f'Profile source mismatch: {mismatches}')
    profile_path = args.evidence / 'scale4096/sample.prof'
    profile = pstats.Stats(str(profile_path))
    targets = {
        'env_step': ('/envs/manager_based_rl_env.py', 'step'),
        'render': ('/isaaclab/sim/simulation_context.py', 'render'),
        'physics': ('/physics_context/physics_context.py', '_step'),
        'camera_buffer': ('/camera/tiled_camera.py', '_update_buffers_impl'),
        'camera_pose': ('/perceptual_ball/carrybox_camera.py', '_update_poses'),
        'depth_normalization': ('/mdp/carrybox.py', 'depth_image'),
        'depth_label_pair_and_corruption': ('/mdp/carrybox_walled.py', 'captured_pair'),
    }
    stages = {}
    for name, (suffix, func) in targets.items():
        matches = [v for (file, _, fn), v in profile.stats.items() if file.endswith(suffix) and fn == func]
        if len(matches) != 1:
            raise RuntimeError(f'Expected exactly one profiler entry for {name}, got {len(matches)}')
        _, calls, own, cumulative, _ = matches[0]
        stages[name] = dict(calls=calls, self_s=own, cumulative_s=cumulative)
    steps = stages['env_step']['calls']
    for stage in stages.values():
        stage['cumulative_s_per_control_step'] = stage['cumulative_s'] / steps
    launch = json.loads((args.evidence / 'launch.json').read_text())
    log_path = Path(launch['train_log'])
    log = log_path.read_text()
    measurements = re.findall(r'Learning iteration (\d+)/\d+.*?collection: ([\d.]+)s, learning ([\d.]+)s', log, re.S)
    # Warmup iteration zero is reported separately, not mixed into the recent mean.
    recent = [(int(i), float(c), float(l)) for i, c, l in measurements if int(i) > 0][-10:]
    if not recent:
        raise RuntimeError('No completed nonzero formal iteration available')
    pid_path = Path('/proc') / str(launch['pid'])
    running = pid_path.exists() and (pid_path / 'stat').read_text().split()[21] == launch['start_ticks']
    report = dict(
        checked_at=datetime.datetime.now().astimezone().isoformat(),
        measurement='existing cProfile replay plus read-only current formal log; no new GPU timing',
        backend='FabricTiledCamera(TiledCamera): RTX distance_to_image_plane',
        profile_path=str(profile_path), profile_sha256=hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        source_hashes_match=True, control_steps=steps, stages=stages,
        render_share=stages['render']['cumulative_s'] / stages['env_step']['cumulative_s'],
        formal=dict(pid=launch['pid'], process_identity_matches=running, log=str(log_path),
                    recent=recent, mean_collection_s=statistics.mean(r[1] for r in recent),
                    mean_learning_s=statistics.mean(r[2] for r in recent),
                    mean_iteration_s=statistics.mean(r[1]+r[2] for r in recent)),
        limitations=['Nested cumulative entries overlap; do not sum camera, depth and pair rows.',
                     'cProfile measures host call duration. CUDA work is asynchronous; GPU kernel attribution is unavailable.',
                     'Benchmark synchronized CUDA after each env step, not after every substage.',
                     'Render includes scene/Fabric updates and synchronization, not only GPU ray traversal.',
                     'Only four profiled control steps; full PPO timings come from independent unprofiled logs.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
