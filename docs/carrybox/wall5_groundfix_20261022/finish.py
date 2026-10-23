from pathlib import Path
import sys,json,hashlib,datetime
R=Path('/home/cao/perceptual_ball');D=Path(__file__).resolve().parent;slug='carrybox-wall5-groundfix-20261022'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
snap=json.loads((D/'snapshot.json').read_text());launch=json.loads((D/'launch.json').read_text());receipts=json.loads((D/'receipts.json').read_text())['tests']
assert snap['status']=='PASS' and all(v['result']=='PASS' for v in receipts)
cmd=[x.decode() for x in Path(f'/proc/{launch["pid"]}/cmdline').read_bytes().split(b'\0') if x];assert cmd==launch['command']
for p,h in launch['source_sha256'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
stop=json.loads((D/'stopped_run.json').read_text())
append=f'''\n## 正式训练验收快照\n\n{snap['checked_at']}：旧revision25 PID **{stop['pid']}** 已退出，日志最后第 **{stop['last_log_iteration']}** 轮；保存到 `{stop['last_saved_checkpoint']}`，所有旧文件保留。\n\n新 PID **{snap['pid']}**，4096环境、seed42、40000轮、**从零初始化**；首模型schema2/revision26、全新优化器step20与AMP计数61440、参数有限，环境契约与短测一致。核验到第 **{snap['iteration']}** 轮，近10轮平均 **{snap['mean_iteration_seconds']:.3f}s/轮**、最慢 **{snap['max_iteration_seconds']:.3f}s/轮**。\n\nRun：`{snap['run']}`\n\n```bash\ntail -f {snap['log']}\n```\n\n[正式启动快照](snapshot.json)、[来源身份](validated_sources.json)、[执行回执](receipts.json)。训练正在进行；目前未评估是否学会稳定行走或拾箱；本轮确认消除了采样初态足底穿地。\n'''
p=D/'README.md';text=p.read_text();assert '## 正式训练验收快照' not in text;p.write_text(text+append)
summary=f"wall5 revision26恢复PhysHSI严格abs roll>0.5/pitch>1.1终止，并在最终关节随机化FK后按实际脚凸包只上移至5mm，配对箱子/活动平台同步。640相同初态穿地>1mm由473个降至0，根COM/关节速度、延迟缓存和partial reset保持；CPU5项、64环境PPO/AMP更新及恢复通过。旧PID{stop['pid']}在{stop['last_log_iteration']}轮停止，新PID{snap['pid']}，4096 fresh，核验第{snap['iteration']}轮、近10轮平均{snap['mean_iteration_seconds']:.3f}s。训练进行中，尚未验证稳定行走或拾箱收敛。"
for f,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
 p=R/f;head,tail=p.read_text().split('\n',1)
 p.write_text(head+'\n\n'+f'2026-10-22：[wall5恢复PhysHSI终止与接地修复重启]({prefix}docs/carrybox/wall5_groundfix_20261022/README.md)：'+summary+'\n'+tail)
plan=R/f'agent/plan/{slug}.md';tp=R/f'agent/task/{slug}.md';task,_=load_frontmatter(tp)
changed=[p for p in task['allowed_paths'] if p.startswith('source/')]
changed += [str(p.relative_to(R)) for p in D.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
changed += [str(D.relative_to(R)/n) for n in ['artifact_validation.json','process_status.json']]
changed += [f'agent/{kind}/{slug}.md' for kind in ('plan','task','report','handoff')]+['projects/README.md','projects/findbox/README.md']
changed += [str(Path(snap['log']).relative_to(R)),str(Path(snap['checkpoint']).relative_to(R))]
meta=dict(task_id=slug,language='zh-CN',axes=['E','L'],risk_tier='T2',status='DONE',changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=receipts,resume_command=None)
body=summary+'\n\n详细阈值/测量点、同起点前后对照、精确日志命令与限制见 docs/carrybox/wall5_groundfix_20261022/README.md。原PhysHSI有角度终止，已恢复同样严格大于判据；脚部几何校正是当前G1适配，不称逐行一致。仅三个wall5生产文件变化，未修改共享helper/资产、奖励/PD、AMP/观测/数据。修复初态穿地不能证明全部失稳根因已解决。\n' 
for kind in ('report','handoff'):
 tail=''
 if kind=='handoff':tail=f'\n当前正式训练PID{snap["pid"]}，run={snap["run"]}。后续查看实时进程，不因历史快照重复启动。下一步按实际曲线/回放评估空手站稳、接近和拾箱；奖励尺度差异仍属未完成动态验证的线索。接地修正必须在最终随机q/clamp/FK之后，并同移参考箱子与活动台；动作缓冲和COM速度不可重置为参考值。没有待恢复工程步骤。\n' 
 m={**meta,'artifact':kind.upper()}
 (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in m.items())+'\n---\n\n'+body+tail)
(D/'process_status.json').write_text(json.dumps({'checked_at':datetime.datetime.now().astimezone().isoformat(),'pid':snap['pid'],'command':cmd,'source_unchanged':True},indent=2)+'\n')
v=validate_paths(plan,tp,R/f'agent/report/{slug}.md',R/f'agent/handoff/{slug}.md');(D/'artifact_validation.json').write_text(json.dumps(v,indent=2)+'\n');assert v['valid'],v
print(json.dumps(snap,ensure_ascii=False,indent=2));print('ARTIFACTS_VALID')
