"""Summarize the recorded first episodes; never include post-reset frames."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

doc = Path(__file__).resolve().parent
data = json.loads((doc / 'replay_result.json').read_text())
assert data['status'] == 'PASS'
summary = {'checkpoint_sha256': data['checkpoint_sha256'], 'cases': {}}
labels = {'policy': 'Policy mean', 'hold_reference': 'Hold reference q',
          'default_pose': 'Default q', 'follow_reference': 'Follow reference q',
          'hold_reference_zero_velocity': 'Hold reference, zero initial velocity'}
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
for name, case in data['cases'].items():
    episodes = case['first_episodes']
    ends = np.array([x['steps'] if x else 101 for x in episodes])
    completed = [x['steps'] for x in episodes if x]
    total = np.zeros(16)
    terms = np.zeros((16, len(data['reward_names'])))
    for frame in case['frames']:
        alive = np.array(frame['alive_before_step'])
        total += np.array(frame['task_reward']) * alive
        terms += np.array(frame['weighted_task_terms']) * alive[:, None]
    row = dict(completed=len(completed), censored_100_steps=len(case['censored']),
               mean_completed_steps=float(np.mean(completed)),
               min_completed_steps=min(completed), max_completed_steps=max(completed),
               survivors_after_20_steps=int((ends > 20).sum()),
               first_episodes_with_push=sum(x and x['push_count'] > 0 for x in episodes),
               raw_task_return_mean=float(total.mean()),
               mean_raw_task_return_terms=dict(zip(data['reward_names'], terms.mean(0).tolist())))
    if name == 'follow_reference':
        endpoint = [i for i, x in enumerate(episodes) if x and x['steps'] * 1.2 > case['references'][i]['remaining_source_frames']]
        row.update(reference_end_before_first_termination=endpoint,
                   mean_steps_excluding_endpoints=float(np.mean([x['steps'] for i, x in enumerate(episodes) if x and i not in endpoint])))
    summary['cases'][name] = row
    time = np.arange(101) * .02
    survival = np.array([(ends > step).sum() for step in range(101)])
    axes[0].step(time, survival, where='post', label=labels[name])
    # Pitch from identical initial state env 1 (stand_to_walk, frame 26),
    # stop at its first reset. No averaging across changing survivor sets.
    env_id = 1
    length = min(ends[env_id], 100)
    pitch = [case['initial']['pitch'][env_id]] + [f['pitch'][env_id] for f in case['frames'][:length]]
    axes[1].plot(np.arange(len(pitch)) * .02, pitch, label=labels[name])
axes[0].set(xlabel='Time (s)', ylabel='First episodes still running (of 16)', ylim=(-.5, 16.5), title='Same initial states; mean-action policy fails earliest')
axes[1].axhline(1.1, color='black', ls='--', lw=1, label='Pitch termination (+1.1 rad)')
axes[1].set(xlabel='Time (s)', ylabel='Body pitch (rad)', xlim=(0, 1.2), title='Example: stand_to_walk_01, source frame 26')
for ax in axes:
    ax.grid(alpha=.25)
axes[0].legend(fontsize=8, loc='upper right')
axes[1].legend(fontsize=7, loc='upper left')
fig.savefig(doc / 'first_episode_comparison.png', dpi=160)
plt.close(fig)

case = data['cases']['policy']
initial = case['initial']
frame = case['frames'][0]
summary['initial'] = dict(tipped=sum(initial['tipped']), fell=sum(initial['fell']),
                        pitch_min=min(initial['pitch']), pitch_max=max(initial['pitch']),
                        lowest_foot_z_min=float(np.min(initial['foot_lowest_z'])),
                        lowest_foot_z_max=float(np.min(initial['foot_lowest_z'], axis=1).max()))
summary['policy_first_action'] = {}
for name in ('left_knee_joint', 'right_knee_joint', 'left_ankle_pitch_joint', 'right_ankle_pitch_joint', 'waist_pitch_joint'):
    j = data['joint_names'].index(name)
    summary['policy_first_action'][name] = dict(
        initial_q_mean=float(np.array(initial['joint_pos'])[:, j].mean()),
        raw_policy_mean=float(np.array(frame['raw_policy'])[:, j].mean()),
        requested_q_mean=float(np.array(frame['target_before_limits'])[:, j].mean()),
        applied_q_mean=float(np.array(frame['physical_target'])[:, j].mean()),
        physical_limit_clipped_count=int(np.array(frame['target_saturation'])[:, j].sum()))
summary['limits'] = data['limits'] + [
    'Open-loop reference tracking is not a balancing controller or a dynamic-feasibility proof.',
    'Equal initial observations use unchanged atol/rtol=1e-5; conditions run in fresh processes.',
    'Only first episodes analyzed; follow-reference endpoint effects are separated.',
    'No learned policy or production configuration changed.']
(doc / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
