from pathlib import Path
import sys,json,hashlib,datetime
R=Path('/home/cao/perceptual_ball');D=Path(__file__).resolve().parent;slug='carrybox-wall5-stability-20261023'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
receipts=[]
for i in range(3):receipts.extend(json.loads((D/f'receipt_{i}.json').read_text())['tests'])
assert all(v['result']=='PASS' for v in receipts)
(D/'receipts.json').write_text(json.dumps({'schema_version':'robotics-engineering-test-receipts.v1','tests':receipts},indent=2)+'\n')
snap=json.loads((D/'snapshot.json').read_text());launch=json.loads((D/'launch.json').read_text());smoke=json.loads((D/'smoke.json').read_text());stop=json.loads((D/'stopped_run.json').read_text())
assert snap['status']=='PASS' and smoke['status']=='PASS'
cmd=[x.decode() for x in Path(f'/proc/{launch["pid"]}/cmdline').read_bytes().split(b'\0') if x];assert cmd==launch['command']
for p,h in launch['source_sha256'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
assert smoke['contract']['reward_weights']['alive']==3.
append=f'''\n## 验证与正式训练快照\n\nCPU 9项通过，包含固定配额/partial reset、配置覆盖、终止步归属、延迟及生存奖励正常/失败/timeout/并发失败边界。512环境{smoke['ground_reset_cases']}次reset接地检查通过，最低脚凸包离地{smoke['minimum_reset_clearance_m']:.6f}m，三pickup、配对支撑台、最终q填充延迟缓存及partial reset保持。\n\n最终512环境fresh 128次PPO/AMP更新均有限，实际四类控制步配额始终{smoke['transition_counts']}；actor、critic、CNN、pose head均更新，保存恢复输出一致，拒绝revision26完整恢复。weight1没有通过行为断言，原始FAIL回执和日志已完整保留；weight3通过相同断言，没有降低标准。\n\n{snap['checked_at']}：旧PID{stop['pid']}已退出，日志最后第{stop['last_log_iteration']}轮；最后保存{Path(stop['last_saved_checkpoint']).name}，旧模型及日志全部保留。新PID **{snap['pid']}**，4096环境，seed42，40000轮，**从零初始化，无resume/warm-start**。核验到第**{snap['iteration']}**轮，近10轮平均**{snap['mean_iteration_seconds']:.3f}s/轮**、最慢{snap['max_iteration_seconds']:.3f}s。\n\n新训练Sampling/loco（含default）={snap['metrics']['Sampling/loco_transition_fraction']:.4f}，default={snap['metrics']['Sampling/default_transition_fraction']:.4f}，pickup={snap['metrics']['Sampling/pickup_transition_fraction']:.4f}，hold={snap['metrics']['Sampling/hold_transition_fraction']:.4f}。最近25轮按累计已结束回合反算的各组平均步数约为{json.dumps(snap['recent25_completed_episode_steps'],ensure_ascii=False)}，仅作早期训练诊断。\n\nRun：`{snap['run']}`\n\n```bash\ntail -f {snap['log']}\n```\n\n新模型revision27/schema2，首轮policy/AMP及优化器有限，优化器step20、AMP统计计数61440符合fresh初始化，critic123、AMP60×10、完整15clips、自碰撞及roll0.5契约一致。当前确认正式训练持续推进和采样修复；尚未完成新正式checkpoint的独立行走/抓取评估。\n\n[短测](smoke.json)、[正式启动](launch.json)、[100轮以上快照](snapshot.json)、[最终测试回执](receipts.json)、[工件校验](artifact_validation.json)。\n'''
p=D/'README.md';text=p.read_text();assert '## 验证与正式训练快照' not in text;p.write_text(text+append)
summary=f"wall5 revision27修复随机reset采样偏置，四来源固定819/2185/546/546，空手控制步从4.38%恢复73.34%；修正终止步default标签。新增is_alive weight3（raw+.06/有效步），其他奖励、PD和终止保持。同初态旧rev22约10.83s、当前0.166s；同冻结AMP完整混合回报旧策略更高，不能称完整目标偏好倾倒。512×128短训末段默认/loco由8.185/6.55提高到24.985/19.525步，weight1失败已保留，尚未证明走路收敛。9项CPU、更新恢复通过。旧PID{stop['pid']}已停，新PID{snap['pid']}，4096 fresh，核验第{snap['iteration']}轮、近10轮平均{snap['mean_iteration_seconds']:.3f}s。"
for f,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
 p=R/f;head,tail=p.read_text().split('\n',1)
 p.write_text(head+'\n\n'+f'2026-10-23：[wall5空手倾倒诊断、采样/稳定反馈修复与重新训练]({prefix}docs/carrybox/wall5_stability_20261023/README.md)：'+summary+'\n'+tail)
plan=R/f'agent/plan/{slug}.md';tp=R/f'agent/task/{slug}.md';task,_=load_frontmatter(tp)
changed=json.loads((D/'scope_check.json').read_text())['changed_production_files']
changed += [str(p.relative_to(R)) for p in D.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
changed += [str(D.relative_to(R)/n) for n in ['artifact_validation.json','process_status.json']]
changed += [f'agent/{kind}/{slug}.md' for kind in ('plan','task','report','handoff')]+['projects/README.md','projects/findbox/README.md','tests/test_carrybox_wall5_stability.py']
changed += [str(Path(snap['log']).relative_to(R)),str(Path(snap['checkpoint']).relative_to(R))]
meta=dict(task_id=slug,language='zh-CN',axes=['E','C','L'],risk_tier='T2',status='DONE',changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=receipts,resume_command=None)
body=summary+'\n\n详见 docs/carrybox/wall5_stability_20261023/README.md 和同目录诊断/短训/正式启动证据。仅四个wall5生产文件改变；75个其他原训练启动来源哈希保持。固定分区只决定初始化，参考帧/扰动继续随机，技能标签不输入actor/critic；与PhysHSI物理reset保持，但来源抽样改为固定配额。新增survival是实质目标调整，也会奖励原地存活；它没有新姿态门控，不把空手短期存活改善当成走路或地面拾箱成功。\n\n验证记录：baseline诊断PASS；quota-only管线PASS但行为退化；alive1冻结validate命令FAIL，按原范围一次修正到alive3，同一行为断言PASS；最终正式启动验证PASS。未继续加权或降低断言。冻结成熟AMP判别器认可旧稳定策略，不能用raw task排序推断完整目标偏好倾倒；早期混合来源惩罚量级不是固定噪声成本或空手专属值。\n'
for kind in ('report','handoff'):
 tail=''
 if kind=='handoff':tail=f'\n当前正式训练PID{snap["pid"]}，run={snap["run"]}。后续先核对实际进程，勿因快照重复启动。Sampling/loco_transition_fraction应约0.7334，Reset比例是事件计数。下一步按空手首回合稳定性、接近及手箱接触评估；不能用持箱参考起点success当作地面拾箱。短训曲线仍从早期峰值下降，只是退化减轻，需核查正式训练是否持续改善。不要未经新证据继续放大alive或改相同力矩/PD。没有待恢复的工程步骤。\n'
 (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in {**meta,'artifact':kind.upper()}.items())+'\n---\n\n'+body+tail)
(D/'process_status.json').write_text(json.dumps({'checked_at':datetime.datetime.now().astimezone().isoformat(),'pid':snap['pid'],'command':cmd,'source_unchanged':True},indent=2)+'\n')
v=validate_paths(plan,tp,R/f'agent/report/{slug}.md',R/f'agent/handoff/{slug}.md');(D/'artifact_validation.json').write_text(json.dumps(v,indent=2)+'\n');assert v['valid'],v
print(json.dumps(snap,ensure_ascii=False,indent=2));print('ARTIFACTS_VALID')
