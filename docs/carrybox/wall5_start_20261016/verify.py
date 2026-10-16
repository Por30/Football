"""Read-only startup receipt for the user's existing Wall5 training process."""
import datetime
import json
from pathlib import Path
import re
import time
import torch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PID = 2996727
LOG = ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled5/launch_20261016_134504.log'
RUN = ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a'
deadline = time.monotonic() + 600
while True:
    command = Path(f'/proc/{PID}/cmdline').read_bytes().replace(b'\0', b' ').decode()
    assert 'CarryBox-Walled5-v0' in command and '--num_envs 4096' in command, command
    text = LOG.read_text(errors='replace')
    assert 'Traceback (most recent call last)' not in text
    assert 'out of memory' not in text.lower()
    blocks = re.split(r'Learning iteration\s+(\d+)/40000', text)
    iterations = []
    for i in range(1, len(blocks), 2):
        match = re.search(r'Iteration time:\s+([\d.]+)s', blocks[i+1])
        if match:
            iterations.append((int(blocks[i]), float(match[1])))
    if iterations and iterations[-1][0] >= 11 and (RUN/'model_0.pt').is_file():
        break
    if time.monotonic() > deadline:
        raise TimeoutError('No completed startup verification within 600 seconds')
    time.sleep(5)
state = torch.load(RUN/'model_0.pt', map_location='cpu', weights_only=False)
contract = state['environment_contract']
assert state['carrybox_schema'] == 2 and contract['variant'] == 'walled5'
assert contract['migration_revision'] == 9 and contract['depth_backend'] == 'warp'
assert contract['amp_shape'] == [10, 35]
assert state['amp']['config']['frame_dim'] == 35
assert state['amp']['config']['reward_scale'] == .5
assert state['amp']['config']['reward_time_scale'] == 'per_policy_step_no_dt'
assert state['amp']['dataset']['clip_count'] == 15
assert state['amp']['statistics_initialized']
for values in (state['model_state_dict'], state['amp']['model']):
    assert all(torch.isfinite(v).all() for v in values.values())
assert state['optimizer_state_dict']['state'] and state['amp']['optimizer']['state']
assert all(g['lr'] == 5e-5 for g in state['amp']['optimizer']['param_groups'])
assert all(g['lr'] == 3e-4 for g in state['optimizer_state_dict']['param_groups'])
valid = [float(v) for v in re.findall(r'AMP/valid_fraction:\s+([\d.]+)', text)]
assert valid and all(v == 1. for v in valid)
recent = [(i,t) for i,t in iterations if i >= 2][-10:]
report = dict(status='PASS', checked_at=datetime.datetime.now().astimezone().isoformat(),
              pid=PID, command=command.strip(), log=str(LOG.relative_to(ROOT)), run=str(RUN.relative_to(ROOT)),
              completed_iteration=iterations[-1][0], num_envs=4096, max_iterations=40000,
              checkpoint=str((RUN/'model_0.pt').relative_to(ROOT)), schema=2, revision=9,
              amp_frame_dim=35, amp_clip_count=15, amp_valid_fraction=valid[-1],
              finite_policy_and_amp=True, nonempty_optimizers=True,
              timing_iterations=recent, average_seconds=sum(t for _,t in recent)/len(recent),
              maximum_seconds=max(t for _,t in recent), under_6_seconds=all(t<6 for _,t in recent),
              training_finished=False, convergence='not_evaluated')
(OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
