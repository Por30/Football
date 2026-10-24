"""Read-only checkpoint, source, video and logged reward audit."""
from pathlib import Path
import ast,datetime,hashlib,json,math,re,statistics
import torch
import imageio.v2 as imageio
from PIL import Image
D=Path(__file__).resolve().parent;R=D.parents[2]
S=json.loads((D/'selection.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name,digest in S['source_sha256'].items():assert sha(R/name)==digest,name
models={}
for name,key in [('current','checkpoint'),('old','baseline_checkpoint'),('latest','latest_checkpoint')]:
 assert sha(S[key])==S[key+'_sha256']
 models[name]=torch.load(S[key],map_location='cpu',weights_only=False)
 assert all(torch.isfinite(v).all() for v in models[name]['model_state_dict'].values())
 assert all(torch.isfinite(v).all() for v in models[name]['amp']['model'].values())
assert models['current']['environment_contract']['migration_revision']==28
assert models['old']['environment_contract']['migration_revision']==22
a,b=models['current']['amp'],models['latest']['amp']
steps=lambda x:sorted(set(float(v['step']) for v in x['optimizer']['state'].values()))
amp=dict(config=a['config'],dataset=a['dataset'],first_iter=models['current']['iter'],last_iter=models['latest']['iter'],
 optimizer_steps_before=steps(a),optimizer_steps_after=steps(b),normalizer_count_before=float(a['model']['running_count']),normalizer_count_after=float(b['model']['running_count']),
 parameter_change_l2=math.sqrt(sum(float((a['model'][k]-b['model'][k]).square().sum()) for k in a['model'] if k.endswith(('weight','bias')))))
assert amp['parameter_change_l2']>0 and max(steps(b))>max(steps(a))
def read_log(path):
 raw=Path(path).read_bytes();parts=re.split(r'Learning iteration\s+(\d+)/40000',raw.decode(errors='replace'));rows=[]
 for i in range(1,len(parts),2):
  row={'iteration':int(parts[i])}
  for line in parts[i+1].splitlines():
   m=re.match(r'\s*([^:\x1b]+):\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)s?\s*$',line)
   if m:row[m[1].strip()]=float(m[2])
  if 'Iteration time' in row:rows.append(row)
 return rows,sha(path)
keys=['Mean episode length','Mean action noise std','AMP/style_reward','AMP/valid_fraction','Reward/task_raw_per_step','Reward/task_weighted_per_step','Reward/amp_per_step','Reward/mixed_per_step',
 'Reward/loco_walk_task_per_step','Reward/loco_carryup_task_per_step','Reward/loco_standup_task_per_step','Reward/loco_task_per_step','Reward/loco_alive_per_step','Reward/loco_torques_per_step','Reward/loco_action_rate_per_step',
 'Mean amp_expert_loss loss','Mean amp_policy_loss loss','Mean box_aux_weighted loss','Mean ppo_learning_rate loss','Motion/loco_survivor_box_distance_xy_m','Grasp/loco_both_contact_fraction']
logs={}
for name,path in [('current',S['training_log']),('old',S['baseline_log'])]:
 rows,digest=read_log(path);(D/f'{name}_curve.json').write_text(json.dumps(rows)+'\n')
 windows={}
 for lo,hi in [(1100,1200),(4700,4800),(6300,6400),(rows[-1]['iteration']-99,rows[-1]['iteration']+1)]:
  sub=[x for x in rows if lo<=x['iteration']<hi]
  if sub:windows[f'{lo}:{hi}']={k:statistics.mean(x[k] for x in sub if k in x) for k in keys if any(k in x for x in sub)}
 logs[name]=dict(last_iteration=rows[-1]['iteration'],source_sha256=digest,windows=windows)
# Execute the exact pure tensor functions from the production file without simulator imports.
path=R/'source/perceptual_ball/perceptual_ball/carrybox_wall5.py';tree=ast.parse(path.read_text())
nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('grasp_reward_geometry','grasp_components')]
ns={'torch':torch};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
g=ns['grasp_reward_geometry']();curves=[]
for xy in [.45,.52,.60,.65,.70,.735,.75,.80,1.,1.5]:
 for v in [0.,.25,.5,.85]:
  delta=torch.tensor([[xy,0.,-.648]])
  palms=torch.tensor([[[.05-xy,.15,.425],[.05-xy,-.15,.425]]])
  comp=ns['grasp_components'](delta,torch.tensor([v]),torch.zeros(1),palms,torch.tensor([.2,.2,.125]),torch.zeros(1,2),torch.zeros(1),g)
  old=1.5 if float(delta.norm())<models['old']['environment_contract']['reward_geometry']['near_distance'] else math.exp(-5*(.85-v)**2)+.5
  assert torch.isfinite(comp['walk_task']).all() and torch.isfinite(comp['carryup_task']).all()
  curves.append(dict(xy_m=xy,towards_mps=v,current_walk=float(comp['walk_task'])*.02,old_walk=old*.02,current_reach=float(comp['reach'])*.02,travel=max(0.,min(1.,(xy-.6)/.2)),reach_gate=max(0.,min(1.,(.98-float(delta.norm()))/.08))))
videos={}
for name,folder in [('old','wall5_play4_rev22_20261021'),('current','wall5_play4_rev28_20261023_2223')]:
 src=R/'docs/carrybox'/folder;r=json.loads((src/'recording.json').read_text());v=json.loads((src/'video_validation.json').read_text());t=json.loads((src/'trajectory.json').read_text())
 assert sha(r['video'])==v['video_sha256']
 with imageio.get_reader(r['video']) as reader:
  im=Image.new('RGB',(1920,1080))
  for i,idx in enumerate([0,49,249,498]):im.paste(Image.fromarray(reader.get_data(idx)).resize((960,540)),((i%2)*960,(i//2)*540))
  im.save(D/f'{name}_video_frames.jpg')
 robots=[]
 for i in range(4):
  # Rev22 recorded terminal events separately, without a per-step reset field.
  reset_steps={e['end_step'] for e in r['episodes'] if e['env_id']==i}
  rows=[x for x in t if x['step'] not in reset_steps];dist=lambda x:math.dist(x['robot'][i][:2],x['box'][i][:2])
  spans={}
  for start,end in [(0,2),(2,20)]:
   z=[x for x in rows if start<x['step']*.02<=end]
   spans[f'{start}:{end}']=dict(start_xy=dist(z[0]),end_xy=dist(z[-1]),distance_reduction=dist(z[0])-dist(z[-1]))
  robots.append(dict(env=i,spans=spans,min_xy=min(map(dist,rows)),contacts=sum(any(x['hand_contacts'][i]) for x in rows)))
 videos[name]=dict(path=r['video'],sha256=v['video_sha256'],robots=robots)
contracts={k:dict(old=models['old']['environment_contract'].get(k),current=models['current']['environment_contract'].get(k)) for k in models['old']['environment_contract'].keys()|models['current']['environment_contract'].keys() if models['old']['environment_contract'].get(k)!=models['current']['environment_contract'].get(k)}
out=dict(status='PASS',checked_at=datetime.datetime.now().astimezone().isoformat(),amp=amp,logs=logs,walk_sweep=curves,contract_differences=contracts,videos=videos)
(D/'analysis.json').write_text(json.dumps(out,indent=2)+'\n')
print('ANALYSIS_PASS',json.dumps(dict(amp_parameter_delta=amp['parameter_change_l2'],optimizer_steps=[steps(a),steps(b)],latest_log=logs['current']['last_iteration'])))
