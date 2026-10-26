import json
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
SEEDS = (12345, 67890)
torch.set_num_threads(1)
initial_checks = {}
episodes = {11:[],12:[]}
for seed in SEEDS:
    initial = {v:torch.load(OUT/f'wall{v}_seed{seed}_initial.pt',weights_only=True) for v in (11,12)}
    assert initial[11].keys() == initial[12].keys()
    differences = {}
    for key in initial[11]:
        a,b = initial[11][key],initial[12][key]
        if a.is_floating_point():
            torch.testing.assert_close(a,b,atol=1.e-6,rtol=1.e-6)
            differences[key] = float((a-b).abs().max())
        else:
            assert torch.equal(a,b), key
            differences[key] = 0.
    initial_checks[str(seed)] = differences
    for variant in (11,12):
        report = json.loads((OUT/f'wall{variant}_seed{seed}.json').read_text())
        assert report['status'] == 'PASS' and report['num_envs'] == 64
        rows = report['rows']
        for i in range(64):
            episodes[variant].append(dict(seed=seed, env=i, **{k:v[i] for k,v in rows.items()}))


def stats(rows):
    n = len(rows)
    if not n:
        return dict(n=0)
    return dict(n=n, lifted_any=sum(r['max_held_steps']>0 for r in rows),
        held_0p5s=sum(r['max_held_steps']>=25 for r in rows),
        success_2s=sum(r['success'] for r in rows),
        tipped=sum(r['tipped'] for r in rows),terminated=sum(r['terminated'] for r in rows),
        timeout=sum(r['timeout'] for r in rows),
        mean_lifetime_s=float(np.mean([r['steps']*.02 for r in rows])),
        mean_longest_hold_s=float(np.mean([r['max_held_steps']*.02 for r in rows])),
        median_longest_hold_s=float(np.median([r['max_held_steps']*.02 for r in rows])),
        mean_longest_strict_s=float(np.mean([r['max_strict_steps']*.02 for r in rows])),
        mean_held_s=float(np.mean([r['held_frames']*.02 for r in rows])),
        held_frame_fraction=sum(r['held_frames'] for r in rows)/sum(r['steps'] for r in rows))


summary = {}
for v, rows in episodes.items():
    summary[str(v)] = dict(all=stats(rows),ground=stats([r for r in rows if r['ground']]),
        reference_airborne=stats([r for r in rows if not r['ground']]),
        by_seed={str(s):stats([r for r in rows if r['ground'] and r['seed']==s]) for s in SEEDS},
        by_source={name:stats([r for r in rows if r['source']==i])
            for i,name in enumerate(('default','loco_rsi','pickup_rsi','hold_rsi'))})
paired = {}
for key, threshold in [('max_held_steps',25),('max_strict_steps',100)]:
    counts = {'both':0,'wall11_only':0,'wall12_only':0,'neither':0}
    for a,b in zip(episodes[11],episodes[12]):
        assert (a['seed'],a['env'],a['ground'],a['source']) == (b['seed'],b['env'],b['ground'],b['source'])
        if not a['ground']:
            continue
        x,y = a[key]>=threshold,b[key]>=threshold
        counts['both' if x and y else 'wall11_only' if x else 'wall12_only' if y else 'neither'] += 1
    paired[key] = counts

data = np.load(OUT/'curves.npz')
fig,axes = plt.subplots(2,2,figsize=(11,7),layout='constrained')
for ax,(tag,title,scale) in zip(axes.ravel(),[
    ('Train/mean_reward','Training episode reward',1.),
    ('Train/mean_episode_length','Training episode duration (s)',.02),
    ('Task/hold_fraction','Frames satisfying strict hold conditions (%)',100.),
    ('Episode_Termination/tipped','Training tipped termination fraction (%)',100.)]):
    for v,color in [(11,'#276FBF'),(12,'#DC6B2F')]:
        y=data[f'wall{v}::{tag}']*scale
        ax.plot(np.arange(499,len(y)),np.convolve(y,np.ones(500)/500,mode='valid'),
                color=color,label=f'wall{v} (aux={int(v==12)})',lw=1.7)
    ax.set_title(title);ax.set_xlabel('Training iteration');ax.grid(alpha=.22)
axes[0,0].legend()
fig.suptitle('Wall11 vs Wall12 | seed 42, 4096 x 24 | trailing 500-iteration mean')
fig.savefig(OUT/'training_comparison.png',dpi=160)
plt.close(fig)
result = dict(status='PASS',initial_pairing_checks=initial_checks,summary=summary,paired_ground=paired,
    evaluation_seeds=list(SEEDS),first_episodes_per_model=128,training_runs_per_condition=1,
    interpretation='Snapshot engineering comparison of these two final models. Identical initial state/RNG checked; divergent reset times can change later RNG streams. Original noise and dynamics retained. Not multi-training-seed causal evidence.')
(OUT/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(OUT/'episodes.json').write_text(json.dumps(episodes,indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True)
print('SUMMARY_PASS',flush=True)
