"""Read-only verification of the explicitly authorized background training launch."""
import json
import math
import re
import time
from pathlib import Path
import torch
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

folder = Path(__file__).resolve().parent
meta = json.loads((folder / 'launch.json').read_text())
proc = Path('/proc') / str(meta['pid'])
root = Path('/home/cao/perceptual_ball')
for attempt in range(75):
    assert proc.exists(), 'Training process exited'
    assert proc.joinpath('stat').read_text().split(') ', 1)[1][0] != 'Z', 'Training process is a zombie'
    log = Path(meta['stdout_log']).read_text(errors='replace')
    assert 'Traceback (most recent call last)' not in log, 'Training raised an exception; inspect stdout'
    match = re.search(r'Exact experiment name requested from command line: (\S+)', log)
    if match:
        run = root / 'logs/rsl_rl/agilekickball_v2' / (match[1] + '_v1_speed_only_20260925_scratch')
        events = list(run.glob('events*'))
        if events and (run / 'model_0.pt').exists():
            acc = EventAccumulator(str(run), size_guidance={'scalars': 20}).Reload()
            tags = acc.Tags()['scalars']
            if 'Train/mean_reward' in tags and 'AgileV2/schema' in tags:
                rewards = acc.Scalars('Train/mean_reward')
                if rewards[-1].step >= 2:
                    break
    time.sleep(2)
else:
    raise RuntimeError('No verified learning iterations within 150 seconds')
assert '[AgileKickball-v2] revision=v1_speed_only_20260925; schema=5' in log
assert 'Loading model checkpoint from:' not in log
cfg = (run / 'params/env.yaml').read_text()
agent = (run / 'params/agent.yaml').read_text()
assert 'num_envs: 4096' in cfg and 'revision: v1_speed_only_20260925' in cfg
assert 'resume: false' in agent and 'max_iterations: 50000' in agent and 'seed: 42' in agent
assert all(math.isfinite(x.value) for x in rewards)
assert acc.Scalars('AgileV2/schema')[-1].value == 5
checkpoint = torch.load(run / 'model_0.pt', map_location='cpu', weights_only=False)
course = checkpoint['agile_v2_recovery_curriculum']
assert checkpoint['iter'] == 0 and course['schema'] == 5
assert course['config']['revision'] == meta['revision']
assert course['control_steps'] <= 48 and course['exposure_steps'] <= 48
assert not course['extension_unlocked']
result = dict(pid=meta['pid'],run_directory=str(run),stdout_log=meta['stdout_log'],
              last_verified_iteration=rewards[-1].step,revision=meta['revision'],schema=5,
              num_envs=4096,max_iterations=50000,seed=42,device='cuda:0',resume=False,
              checkpoint_0_control_steps=course['control_steps'],tensorboard_scalars_written=True)
(folder / 'verified_start.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
