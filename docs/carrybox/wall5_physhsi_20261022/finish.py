from pathlib import Path
import sys,json,hashlib,datetime,subprocess
R=Path('/home/cao/perceptual_ball');D=Path(__file__).resolve().parent;slug='carrybox-wall5-physhsi-20261022'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
snap=json.loads((D/'snapshot.json').read_text());launch=json.loads((D/'launch.json').read_text());receipts=json.loads((D/'receipts.json').read_text())['tests']
assert snap['status']=='PASS' and all(v['result']=='PASS' for v in receipts)
cmd=[x.decode() for x in Path(f'/proc/{launch["pid"]}/cmdline').read_bytes().split(b'\0') if x];assert cmd==launch['command']
for p,h in launch['source_sha256'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
stop=json.loads((D/'stopped_run.json').read_text())
append=f'''\n## 正式训练验收快照\n\n{snap['checked_at']}：原revision23 PID {stop['pid']}已停止，最后日志迭代{stop['last_log_iteration']}，保留模型`{stop['last_saved_checkpoint']}`及全部旧日志。中间PID1759807已退出，其初始化日志归档。\n\n最终PID **{snap['pid']}**，4096环境、seed42、40000轮、**fresh**；首模型schema2/revision24、全新优化器step20与AMP统计计数61440、参数有限，完整环境契约与短测一致。检查到**第{snap['iteration']}轮**，最近10轮平均**{snap['mean_iteration_seconds']:.3f}s**、最慢**{snap['max_iteration_seconds']:.3f}s**，满足每轮6秒要求。\n\nRun：`{snap['run']}`\n\n```bash\ntail -f {snap['log']}\n```\n\n[最终执行回执](receipts.json)、[正式启动快照](snapshot.json)、[源身份](validated_sources.json)。训练进行中，尚未验证稳定行走或从地面拾箱成功率。\n'''
p=D/'README.md';text=p.read_text();assert '## 正式训练验收快照' not in text;p.write_text(text+append)
summary=f"wall5 revision24按PhysHSI G1恢复原碰撞/肩胶囊并取消髋膝接触扣分；20%默认+80% RSI（条件2/3、1/6、1/6），完整三pickup连续起点/支撑台、根速度覆盖、90%软限位关节扰动、0–20ms物理步动作延迟及原失败终止。保留普通FindBox前方地面箱、网络/AMP/奖励核心。24项CPU、64环境更新恢复导出通过；旧PID{stop['pid']}已停，最终PID{snap['pid']}，4096 fresh，检查第{snap['iteration']}轮，平均{snap['mean_iteration_seconds']:.3f}s/轮。正式训练进行中，尚未验证行走或拾箱收敛。"
for f,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
 p=R/f;head,tail=p.read_text().split('\n',1)
 entry=f'2026-10-22：[wall5 PhysHSI碰撞与reset迁移]({prefix}docs/carrybox/wall5_physhsi_20261022/README.md)：'+summary
 p.write_text(head+'\n\n'+entry+'\n'+tail)
plan=R/f'agent/plan/{slug}.md';tp=R/f'agent/task/{slug}.md';task,_=load_frontmatter(tp)
changed=[p for p in task['allowed_paths'] if p.startswith('source/') or p.startswith('tests/')]
changed += [str(p.relative_to(R)) for p in D.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
changed += [str(D.relative_to(R)/'artifact_validation.json'),str(D.relative_to(R)/'process_status.json')]
changed += [f'agent/{kind}/{slug}.md' for kind in ('plan','task','report','handoff')]+['projects/README.md','projects/findbox/README.md']
changed += [str(Path(snap['log']).relative_to(R)),str(Path(snap['checkpoint']).relative_to(R))]
meta=dict(task_id=slug,language='zh-CN',axes=['E','C','L'],risk_tier='T2',status='DONE',changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=receipts,resume_command=None)
body=summary+'\n\n详细范围、保留差异、验证和精确日志命令见 docs/carrybox/wall5_physhsi_20261022/README.md。原始G1 USD/URDF及15段AMP不变；wall3/wall4与football配置行为未改。revision23 checkpoint严格恢复拒绝，最终run从零初始化。\n\n首次验收空Xform判定错误已修正为实际CollisionAPI/形状集合核对；第二次补齐PhysHSI 90%软限位reset，短暂启动的PID1759807已停，失败回执和日志均保留。最终三项冻结命令PASS，非删测或放宽阈值。\n'
for kind in ('report','handoff'):
 m={**meta,'artifact':kind.upper()};tail=''
 if kind=='handoff':tail=f'\n当前正式训练PID{snap["pid"]}，run={snap["run"]}。后续只读查看日志/模型；不要因历史文档状态再次自动重启。评估须区分默认/loco与pickup/hold参考起点，持箱RSI不能当作从地面抓起成功。动作队列在物理步更新；actor导出仅输入本体与米制深度。当前无待恢复执行。\n'
 (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in m.items())+'\n---\n\n'+body+tail)
(D/'process_status.json').write_text(json.dumps({'checked_at':datetime.datetime.now().astimezone().isoformat(),'pid':snap['pid'],'command':cmd,'source_unchanged':True},indent=2)+'\n')
v=validate_paths(plan,tp,R/f'agent/report/{slug}.md',R/f'agent/handoff/{slug}.md');(D/'artifact_validation.json').write_text(json.dumps(v,indent=2)+'\n');assert v['valid'],v
print(json.dumps(snap,ensure_ascii=False,indent=2));print('ARTIFACTS_VALID')
