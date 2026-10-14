"""Read-only validation of the specifically authorized detached v3 run."""
import json
import os
from pathlib import Path
import re
import torch
import yaml

root = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
meta = json.loads((out / 'launch.json').read_text())
pid = meta['pid']
proc = Path('/proc') / str(pid)
args = proc.joinpath('cmdline').read_bytes().split(b'\0')
assert b'scripts/rsl_rl/train.py' in args and b'Template-Perceptual-Ball-AgileKickball-v3' in args
stat = proc.joinpath('stat').read_text().split(') ', 1)[1].split()
assert int(stat[19]) == meta['start_ticks'], 'PID has been reused'
assert os.getsid(pid) == pid, 'Training must be in an independent session'
log = Path(meta['log']).read_text(errors='replace')
assert 'Traceback (most recent call last)' not in log
assert 'CUDA out of memory' not in log
iterations = re.findall(r'Learning iteration\s+(\d+)/(\d+)', log)
assert iterations and int(iterations[-1][0]) >= 49 and int(iterations[-1][1]) == 50000
match = re.search(r'Exact experiment name requested from command line: (\S+)', log)
assert match
run = root / 'logs/rsl_rl/agilekickball_v3' / (match.group(1) + '_feedback_stable_20261008_v2init')
agent = yaml.safe_load((run / 'params/agent.yaml').read_text())
assert (agent['max_iterations'], agent['seed'], agent['resume']) == (50000, 42, False)
assert agent['num_steps_per_env'] == 24 and agent['experiment_name'] == 'agilekickball_v3'
assert agent['policy']['class_name'] == 'StateFeedbackActorCritic'
assert agent['algorithm']['class_name'] == 'StateFeedbackPPO'
assert agent['algorithm']['num_learning_epochs'] == 5 and agent['algorithm']['num_mini_batches'] == 4
assert '--num_envs' in [a.decode() for a in args]
assert args[args.index(b'--num_envs') + 1] == b'4096'
assert args[args.index(b'--device') + 1] == b'cuda:0'
checkpoint = run / 'model_0.pt'
state = torch.load(checkpoint, weights_only=False, map_location='cpu')
assert state['soccer_schema_version'] == 3
assert all(torch.isfinite(v).all() for v in state['model_state_dict'].values())
course = state['agile_v3_state_feedback_curriculum']
assert course['schema'] == 5 and course['config']['revision'] == 'feedback_stable_20261008'
assert state['state_feedback']['config']['schema'] == 2
assert state['state_feedback']['aux_updates'] > 0
assert state['ball_aux_optimizer_state_dict']['state']
assert any('actor.residual' in key for key in state['model_state_dict'])
assert 'revision=feedback_stable_20261008' in log
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
events = EventAccumulator(str(run)).Reload()
metrics = {tag: events.Scalars(tag)[-1].value for tag in events.Tags()['scalars']}
assert metrics['Loss/state_feedback/residual_abs_mean_raw'] > 0
assert metrics['Loss/aux/encoder_updates'] == 0
assert metrics['Loss/aux/predictor_updates'] > 0
assert metrics['AgileKickball/recovered_serves'] > 0
assert state['initialization']['kind'] == 'v2_weights_only'
assert agent['algorithm']['ball_aux_update_encoder'] is False
assert agent['algorithm']['learning_rate'] == 1.e-5
assert agent['algorithm']['ball_aux_max_kl'] == .001
assert agent['algorithm']['ball_aux_lr'] == .0001
assert '--warm_start_v2' in [a.decode() for a in args]
assert metrics['Loss/aux/stage_monitor_kl'] <= .001
assert all(torch.isfinite(torch.tensor(value)) for value in metrics.values())
report = dict(pid=pid, independent_session=True, num_envs=4096, max_iterations=50000,
              seed=42, resume=False, revision=course['config']['revision'],
              latest_iteration_at_check=int(iterations[-1][0]),
              run_dir=str(run), log=meta['log'], first_checkpoint=str(checkpoint),
              finite_first_checkpoint=True, ball_aux_optimizer_present=True, state_feedback=state['state_feedback'], initialization=state['initialization'], metrics=metrics)
(out / 'verified_start.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
