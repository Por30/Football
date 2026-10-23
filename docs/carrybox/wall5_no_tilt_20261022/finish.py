from pathlib import Path
import sys,json,hashlib,datetime
R=Path('/home/cao/perceptual_ball');D=Path(__file__).resolve().parent;slug='carrybox-wall5-no-tilt-20261022'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
snap=json.loads((D/'snapshot.json').read_text());launch=json.loads((D/'launch.json').read_text());receipts=json.loads((D/'receipts.json').read_text())['tests']
assert snap['status']=='PASS' and all(v['result']=='PASS' for v in receipts)
cmd=[x.decode() for x in Path(f'/proc/{launch["pid"]}/cmdline').read_bytes().split(b'\0') if x];assert cmd==launch['command']
for p,h in launch['source_sha256'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
stop=json.loads((D/'stopped_run.json').read_text())
append=f'''\n## 正式训练验收快照\n\n{snap['checked_at']}：旧revision24 PID **{stop['pid']}** 已退出，日志最后第 **{stop['last_log_iteration']}** 轮；保存到 `{stop['last_saved_checkpoint']}`，所有旧文件保留。\n\n新 PID **{snap['pid']}**，4096环境、seed42、40000轮、**从零初始化**；首模型schema2/revision25、全新优化器step20与AMP计数61440、参数有限，环境契约与短测一致。核验到第 **{snap['iteration']}** 轮，近10轮平均 **{snap['mean_iteration_seconds']:.3f}s/轮**、最慢 **{snap['max_iteration_seconds']:.3f}s/轮**。\n\nRun：`{snap['run']}`\n\n```bash\ntail -f {snap['log']}\n```\n\n[正式启动快照](snapshot.json)、[来源身份](validated_sources.json)、[执行回执](receipts.json)。训练正在进行；目前未评估是否学会稳定行走或拾箱，也未修复之前诊断的接地缺陷。\n'''
p=D/'README.md';text=p.read_text();assert '## 正式训练验收快照' not in text;p.write_text(text+append)
summary=f"wall5 revision25取消roll/pitch直接终止，其余PhysHSI高度/箱速及20s超时保持；倾斜日志改为回合结束姿态诊断。注意本地PhysHSI也含角度终止，本次按用户明确要求作例外。32环境角度隔离、保留条件、PPO/AMP更新与恢复检查通过；旧PID{stop['pid']}在{stop['last_log_iteration']}轮停止，新PID{snap['pid']}，4096 fresh，核验第{snap['iteration']}轮，近10轮平均{snap['mean_iteration_seconds']:.3f}s。训练进行中，未证明稳定性或拾箱收敛，足底穿地未在本轮修复。"
for f,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
 p=R/f;head,tail=p.read_text().split('\n',1)
 p.write_text(head+'\n\n'+f'2026-10-22：[wall5取消倾斜reset并从头重启]({prefix}docs/carrybox/wall5_no_tilt_20261022/README.md)：'+summary+'\n'+tail)
plan=R/f'agent/plan/{slug}.md';tp=R/f'agent/task/{slug}.md';task,_=load_frontmatter(tp)
changed=[p for p in task['allowed_paths'] if p.startswith('source/')]
changed += [str(p.relative_to(R)) for p in D.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
changed += [str(D.relative_to(R)/n) for n in ['artifact_validation.json','process_status.json']]
changed += [f'agent/{kind}/{slug}.md' for kind in ('plan','task','report','handoff')]+['projects/README.md','projects/findbox/README.md']
changed += [str(Path(snap['log']).relative_to(R)),str(Path(snap['checkpoint']).relative_to(R))]
meta=dict(task_id=slug,language='zh-CN',axes=['L'],risk_tier='T1',status='DONE',changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=receipts,resume_command=None)
body=summary+'\n\n详细来源与测量点、验证和精确日志命令见 docs/carrybox/wall5_no_tilt_20261022/README.md。本轮仅两个wall5生产文件变化：注册配置、checkpoint与倾斜诊断语义。新旧环境契约只变化五个预期字段，其余源码/数据hash保持。未修改PhysHSI、foot接地、RSI分布、奖励、网络或AMP。取消角度终止后的回合长度不可直接与旧版比较为稳定性提升。\n'
for kind in ('report','handoff'):
 tail=''
 if kind=='handoff':tail=f'\n当前正式训练PID{snap["pid"]}，run={snap["run"]}。后续查看实际进程和日志，不因历史快照重复启动。未完成长训或独立行为评估。回合结束的tilt_at_episode_end_fraction不是reset原因，低高度才是相关真实终止；接地缺陷与负任务奖励待后续授权修复。没有待恢复的工程步骤。\n'
 m={**meta,'artifact':kind.upper()}
 (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in m.items())+'\n---\n\n'+body+tail)
(D/'process_status.json').write_text(json.dumps({'checked_at':datetime.datetime.now().astimezone().isoformat(),'pid':snap['pid'],'command':cmd,'source_unchanged':True},indent=2)+'\n')
v=validate_paths(plan,tp,R/f'agent/report/{slug}.md',R/f'agent/handoff/{slug}.md');(D/'artifact_validation.json').write_text(json.dumps(v,indent=2)+'\n');assert v['valid'],v
print(json.dumps(snap,ensure_ascii=False,indent=2));print('ARTIFACTS_VALID')
