"""Package evidence after manual review; preserve live training and sources."""
from pathlib import Path
import datetime,hashlib,json,sys
D=Path(__file__).resolve().parent;R=D.parents[2];slug='carrybox-wall5-amp-reward-audit-20261023'
S=json.loads((D/'selection.json').read_text());a=json.loads((D/'analysis.json').read_text());p=json.loads((D/'probe_summary.json').read_text());receipts=json.loads((D/'receipts.json').read_text())['tests']
assert a['status']==p['status']=='PASS' and all(t['result']=='PASS' for t in receipts)
for name,digest in S['source_sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
for k in ('checkpoint','baseline_checkpoint','latest_checkpoint'):
 assert hashlib.sha256(Path(S[k]).read_bytes()).hexdigest()==S[k+'_sha256']
pid=S['training_pid'];cmd=[x.decode() for x in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if x]
assert cmd==S['training_command']
assert Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]==S['training_start_ticks']
status=dict(checked_at=datetime.datetime.now().astimezone().isoformat(),pid=pid,same_process_running=True,source_checkpoint_training_unchanged=True)
(D/'formal_status.json').write_text(json.dumps(status,indent=2)+'\n')
review=(D/'findings.md').read_text().strip();assert review
(D/'README.md').write_text(review+'\n\n'+f'正式训练PID {pid} 于 {status["checked_at"]} 仍运行，本次没有修改生产代码、数据、模型或训练进程。\n\n'+
 '[日志/检查点/奖励曲线核验](analysis.json) · [同初态回放汇总](probe_summary.json) · [执行回执](receipts.json) · [专家审查](expert_brief.json) · [诊断脚本兼容修复记录](repair.md)\n')
summary='rev22对照只读诊断：AMP实际更新/混合已核验；当前空手接近停滞、膝目标饱和和奖励衔接问题见证据。未改参数或重启，未将单项认定为唯一训练根因。'
for name,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
 f=R/name;title,body=f.read_text().split('\n',1);link=prefix+'docs/carrybox/'+D.name+'/README.md';assert link not in body
 f.write_text(title+'\n\n2026-10-23：[wall5 AMP与奖励衔接排查]('+link+')：'+summary+'\n'+body)
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
task,_=load_frontmatter(R/f'agent/task/{slug}.md')
changed=[str(f.relative_to(R)) for f in D.rglob('*') if f.is_file() and '__pycache__' not in f.parts]
changed+=['projects/README.md','projects/findbox/README.md',str((D/'artifact_validation.json').relative_to(R))]+[f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')]
meta=dict(task_id=slug,language='zh-CN',axes=['L','C','E'],risk_tier='T2',status='DONE',changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=receipts,resume_command=None)
for kind in ('report','handoff'):
 fields={**meta,'artifact':kind.upper()}
 (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in fields.items())+'\n---\n\n'+summary+'\n\n'+review+'\n\n所有诊断已完成；无待恢复进程。后续优化需要单独任务，保留此处原始证据。\n')
validation=validate_paths(*(R/f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')))
(D/'artifact_validation.json').write_text(json.dumps(validation,indent=2)+'\n');assert validation['valid'],validation
print('ARTIFACTS_VALID; PRODUCTION_UNCHANGED')
