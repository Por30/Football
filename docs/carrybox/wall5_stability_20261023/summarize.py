from pathlib import Path
import json,numpy as np,re
D=Path(__file__).resolve().parent
d=json.loads((D/'diagnosis.json').read_text());current=d['runs']['current']['lengths'];rows={}
for name,r in d['runs'].items():
 returns=np.zeros(64);prefix=np.zeros(64);parts=[]
 for item in r['rewards']:
  values=np.asarray(item['values']);ids=np.asarray(item['live_ids']);discount=.99**(item['step']-1)
  returns[ids]+=values.sum(-1)*discount
  common=np.asarray(current)[ids]>=item['step'];prefix[ids[common]]+=values[common].sum(-1)*discount
  parts.append(values)
 values=np.concatenate(parts)
 rows[name]={'groups':r['groups'],'mean_first_episode_seconds':float(np.mean(r['lengths'])*.02),
  'mean_raw_task_reward_per_step':float(values.sum(-1).mean()),'mean_raw_task_discounted_return':float(returns.mean()),
  'mean_raw_task_discounted_common_prefix_return':float(prefix.mean()),
  'raw_reward_terms_per_step':dict(zip(r['reward_names'],values.mean(0).tolist()))}
text=(D/'before_training.log').read_text();metrics={}
for key in ('Sampling/default_transition_fraction','Sampling/loco_transition_fraction','Sampling/pickup_transition_fraction','Sampling/hold_transition_fraction','Reset/default_fraction','Reset/loco_rsi_fraction','Reset/pickup_rsi_fraction','Reset/hold_rsi_fraction'):
 metrics[key]=float(re.findall(re.escape(key)+r':\s*([-+\d.eE]+)',text)[-1])
result=dict(modes=rows,before_training_metrics=metrics,
 reward_limitation='Raw task only; full PPO uses .75*task+.125*style. Frozen discriminator comparison was not recorded. Do not infer mixed-return ordering.',
 interpretation='Current learned actions accelerate failure. Four-source random-reset duration bias removes most empty-hand transitions. Rev23 regression predates this sampler; not a single-cause proof.')
(D/'diagnosis_summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
