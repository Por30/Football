"""Describe this video only, separating empty-hand and reference-held episodes."""
from pathlib import Path
import json, statistics

D = Path(__file__).resolve().parent
r = json.loads((D/'recording.json').read_text())
samples = json.loads((D/'trajectory.json').read_text())
groups = {}
for kind,name in enumerate(('default','loco','pickup','hold')):
    episodes = [e for e in r['episodes'] if e['kind']==kind]
    points = [(row,i) for row in samples for i in range(4)
              if not row['reset'][i] and row['kinds'][i]==kind]
    counters = {name:sum(e['causes'][name] for e in episodes)
                for name in r['episodes'][0]['causes']} if r['episodes'] else {}
    groups[name] = dict(completed_episodes=len(episodes),
        mean_completed_seconds=statistics.mean(e['steps']*.02 for e in episodes) if episodes else None,
        max_completed_seconds=max((e['steps']*.02 for e in episodes),default=None),
        completed_successes=sum(e['success'] for e in episodes),termination_counts=counters,
        nonreset_samples=len(points),
        bilateral_contact_samples=sum(all(row['hand_contacts'][i]) for row,i in points),
        any_hand_contact_samples=sum(any(row['hand_contacts'][i]) for row,i in points),
        success_samples=sum(row['success'][i] for row,i in points),
        max_box_bottom_clearance_m=max((row['box_bottom_clearance'][i] for row,i in points),default=None),
        min_hand_center_box_distance_m=min((row['hand_box_distance'][i] for row,i in points),default=None))
result=dict(initial_kinds=r['initial_kinds'],reset_counts=r['reset_counts'],groups=groups,
    final_censored=r['final_censored'],limitations=[
        'One seed, four environments, 20 seconds; not a success-rate evaluation.',
        'Reset rows excluded from contact/height samples; those terminal frames are not included.',
        'Pickup/hold can start with the box lifted; do not count them as ground pickup.',
        'Termination causes may overlap; durations exclude unfinished final episodes.'])
(D/'behavior.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
