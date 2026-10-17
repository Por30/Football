"""Fixed-window, read-only analysis; no simulator imports."""
from pathlib import Path
import datetime, hashlib, json, math, re, statistics as st
import torch

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RUN = ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a'
LOG = RUN.parent/'launch_20261016_134504.log'
text = re.sub(r'\x1b\[[0-9;]*m', '', LOG.read_text(errors='replace'))
parts = re.split(r'Learning iteration\s+(\d+)/\d+', text)
rows = []
for i in range(1, len(parts), 2):
    if int(parts[i]) > 7249 or 'Iteration time:' not in parts[i+1]:
        continue
    row = {'iteration': int(parts[i])}
    for line in parts[i+1].splitlines():
        m = re.match(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)(?:s)?\s*$', line)
        if m:
            row[m[1].strip()] = float(m[2])
    rows.append(row)
assert len(rows) == 7250 and rows[-1]['iteration'] == 7249
keys = [k for k in rows[-1] if k != 'iteration' and not k.startswith('Skill/')]
windows = {}
for low, high in [(0,99),(500,599),(1000,1099),(2000,2099),(3000,3099),(4000,4099),(5000,5099),(6000,6099),(7150,7249)]:
    selected = rows[low:high+1]
    mean = {k:st.mean(r[k] for r in selected if k in r) for k in keys}
    mean['amp_net_mixed_reward_fraction'] = mean['Reward/amp_per_step']/mean['Reward/mixed_per_step']
    windows[f'{low}-{high}'] = mean
skill_windows = {}
for low in (6249,6749):
    before, after = rows[low], rows[-1]
    by_skill = {}
    for skill in ('loco','pickup','hold'):
        p = 'Skill/'+skill+'_'
        n0,n1 = before[p+'episodes'], after[p+'episodes']
        n = n1-n0
        by_skill[skill] = {'completed_episodes_approx':n,
            'completed_mean_steps_approx':(n1*after[p+'mean_steps']-n0*before[p+'mean_steps'])/n,
            'success_count_delta_approx':after[p+'successes']-before[p+'successes']}
    skill_windows[f'{low}-7249'] = by_skill
c = torch.load(RUN/'model_7200.pt', map_location='cpu', weights_only=False)
assert c['carrybox_schema'] == 2 and c['environment_contract']['migration_revision'] == 9
assert all(torch.isfinite(v).all() for v in c['model_state_dict'].values())
summary = dict(checked_at=datetime.datetime.now().isoformat(), last_iteration=7249,
    log=str(LOG), checkpoint=str(RUN/'model_7200.pt'),
    checkpoint_sha256=hashlib.sha256((RUN/'model_7200.pt').read_bytes()).hexdigest(),
    windows=windows, skill_windows=skill_windows,
    ppo_lr=[g['lr'] for g in c['optimizer_state_dict']['param_groups']],
    action_std=c['model_state_dict']['log_std'].exp().tolist(), pose_aux_coef=c['pose_aux_coef'],
    amp_config=c['amp']['config'],
    caveats=['Mean episode length is last100 completed episodes per log line',
             'Termination scalars are retained last labels averaged over environments, not completed-episode fractions',
             'Skill counters are lifetime; log snapshots averaged over24 rollout steps; differences are approximate',
             'Mean reward is raw task reward, not PPO mixed reward; AMP fraction is reward magnitude, not gradient share'])
(OUT/'training_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'training_rows.json').write_text(json.dumps(rows)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2,2,figsize=(11,7))
chunks = [rows[i:i+100] for i in range(0,len(rows),100)]
x = [st.mean(r['iteration'] for r in a) for a in chunks]
for ax, names in zip(axes.flat, [['Mean episode length'],['Episode_Termination/tipped','Episode_Termination/fell','Episode_Termination/time_out'],['AMP/style_reward'],['Reward/task_weighted_per_step','Reward/amp_per_step']]):
    for name in names:
        ax.plot(x,[st.mean(r[name] for r in a) for a in chunks],label=name)
    ax.axvline(1000,color='grey',ls=':',alpha=.6)
    ax.axvline(5000,color='grey',ls=':',alpha=.6)
    ax.set_xlabel('Iteration'); ax.grid(alpha=.2); ax.legend(fontsize=7)
fig.suptitle('Wall5: 100-iteration averages; dotted lines: push ramp start/end')
fig.tight_layout(); fig.savefig(OUT/'training_curves.png',dpi=150)
print('WALL5_LOG_ANALYSIS_PASS',json.dumps(windows['7150-7249']))
