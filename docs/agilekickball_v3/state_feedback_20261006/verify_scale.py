"""Validate production-sized bounded training from checkpoint and event evidence."""
import json
from pathlib import Path
import re
import torch
import yaml
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

out = Path(__file__).resolve().parent
root = out.parents[2]
log = (out / 'train_launch.log').read_text(errors='replace')
assert 'Traceback (most recent call last)' not in log and 'CUDA out of memory' not in log
assert 'revision=state_feedback_20261006' in log
match = re.search(r'Exact experiment name requested from command line: (\S+)', log)
assert match
run = root / 'logs/rsl_rl/agilekickball_v3_smoke' / (match.group(1) + '_state_feedback_scale_smoke')
agent = yaml.safe_load((run / 'params/agent.yaml').read_text())
assert agent['max_iterations'] == 1 and agent['resume'] is False
assert agent['algorithm']['num_learning_epochs'] == 5
assert agent['algorithm']['num_mini_batches'] == 4
assert agent['policy']['class_name'] == 'StateFeedbackActorCritic'
assert agent['algorithm']['class_name'] == 'StateFeedbackPPO'
assert re.search(r'num_envs:\s+4096\b', (run / 'params/env.yaml').read_text())
state = torch.load(run / 'model_0.pt', map_location='cpu', weights_only=False)
assert all(torch.isfinite(v).all() for v in state['model_state_dict'].values())
assert state['agile_v3_state_feedback_curriculum']['config']['revision'] == 'state_feedback_20261006'
assert state['state_feedback']['aux_updates'] > 0
assert state['ball_aux_optimizer_state_dict']['state']
events = EventAccumulator(str(run)).Reload()
scalars = {tag: events.Scalars(tag)[-1].value for tag in events.Tags()['scalars']}
assert scalars['Loss/aux/encoder_updates'] > 0
assert scalars['Loss/state_feedback/residual_abs_mean_raw'] > 0
assert scalars['Loss/aux/stage_monitor_kl'] <= .01
assert all(torch.isfinite(torch.tensor(value)) for value in scalars.values())
report = dict(run_dir=str(run), num_envs=4096, rollout_steps=24, ppo_epochs=5,
              ppo_minibatches=4, scratch_updates=1, finite_checkpoint=True,
              state_feedback=state['state_feedback'], scalars=scalars)
(out / 'scale_smoke.json').write_text(json.dumps(report, indent=2) + '\n')
print('V3_SCALE_SMOKE_PASS', json.dumps(report))
