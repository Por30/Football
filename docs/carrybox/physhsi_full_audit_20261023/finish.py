"""Finalize this read-only audit's evidence and engineering records."""
from pathlib import Path
import datetime, hashlib, json, re, sys

D = Path(__file__).resolve().parent
R = D.parents[2]
slug = 'carrybox-physhsi-full-audit-20261023'
sys.path.insert(0, '/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256, validate_paths

identity = json.loads((D/'source_identity.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in identity.items())
perf = R/'docs/carrybox/wall10_perf_20261023'
perf_sources = json.loads((perf/'validated_sources.json').read_text())
assert all(identity[str(R/p)] == digest for p,digest in perf_sources.items())
perf_receipts = json.loads((perf/'receipts.json').read_text())
assert all(x['result'] == 'PASS' and x['exit_code'] == 0 for x in perf_receipts['tests'])
(D/'wall10_supplement.json').write_text(json.dumps(dict(
    recorded_at=datetime.datetime.now().astimezone().isoformat(),
    provenance='Read existing independent performance task; not executed by this audit',
    matched_sources=perf_sources, receipts=perf_receipts,
    source_report=str(perf/'README.md')),ensure_ascii=False,indent=2)+'\n')

taskpath = R/'agent/task'/f'{slug}.md'
task,taskbody = load_frontmatter(taskpath)
# Record the received expert's bounded conclusions; test commands/scope stay frozen.
brief = dict(
    affected_call_path=[
        'PhysHSI G1 carrybox config/env -> motionlib -> explicit PD/PhysX -> post-step reward/reset -> HIMPPO/AMP',
        'wall5 config -> PhysHSI reset/delay helper -> implicit actuator -> inherited X2/grasp rewards -> independent PPO/AMP',
        'Independent wall10 config -> explicit PD -> source-style regularization/joint PPO/AMP; inspect as separate variant'],
    critical_interfaces=[
        '29 named joints; 5 ms physics/20 ms policy; source xyzw and Lab wxyz; link-origin positions versus COM velocities',
        '60D AMP order/frame; actor depth/proprio only; privileged critic/pose/AMP training-only',
        'Default/RSI reference selection, final joint pose, foot clearance, paired box/platform, terminal data before reset'],
    invariants=[
        'Keep original files/weights, checkpoint schemas and unrelated football changes',
        'Do not equate nominal Kp/Kd with implicit/explicit control equivalence',
        'Do not count held-box RSI as a successful ground pickup; separate effective terms from inactive declarations'],
    smallest_change_locus=['Read-only audit artifacts and project index entries; no production change'],
    mandatory_safeguards=task['safeguards'],
    minimal_tests=[x['command'] for x in task['tests']],
    blockers=task['stop_conditions'])
(D/'expert_brief.json').write_text(json.dumps(dict(
    reviewer='/root/physhsi_controls_audit_20261023',
    role='Read-only controls/physics/reset expert; findings integrated in README, no code changes',
    brief=brief),ensure_ascii=False,indent=2)+'\n')
task['expert_brief'] = brief

def write_artifact(path, meta, body):
    path.write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in meta.items())+'\n---\n\n'+body.strip()+'\n')
taskbody = taskbody.replace('resources资产/数据/部署模型','resources资产/数据/训练checkpoint')
write_artifact(taskpath,task,taskbody)
planpath = R/'agent/plan'/f'{slug}.md'
plan,planbody = load_frontmatter(planpath)
write_artifact(planpath,plan,planbody.replace('resources资产/数据/部署模型','resources资产/数据/训练checkpoint'))

summary = ('完成wall5 rev28对本地PhysHSI G1 carrybox/resume全链路只读审计：47个文件身份、1719个展开参数叶项、'
           '19/15段数据及14段字节同源、URDF/USD质量、网络CPU前向与全部有效奖励/AMP/PPO/reset/控制比较。'
           '源actor使用箱子/goal状态而当前使用深度；显式/隐式PD、力矩定义、100/24步rollout、时序平滑、'
           '数据采样与任务成功语义存在实质差异。同步独立wall10现状与性能证据，不将差异当作已证实失稳根因。'
           '未修改生产或操作训练；重构尚未实施。')
for board,prefix in [('projects/README.md','../docs'),('projects/findbox/README.md','../../docs')]:
    path=R/board
    content=path.read_text()
    marker='physhsi_full_audit_20261023/README.md'
    if marker not in content:
        first,rest=content.split('\n',1)
        entry=f'2026-10-24：[wall5与PhysHSI完整对照及重构边界]({prefix}/carrybox/{marker})：{summary}'
        path.write_text(first+'\n\n'+entry+'\n'+rest)

# Document-only path validation, not an extra training/physics test.
missing=[]
links=0
for path in [D/'README.md',D/'reconstruction.md',D/'appendix.md']:
    for dest in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if dest.startswith(('http:','https:','#')):
            continue
        target=dest.split('#')[0]
        target=re.sub(r':\d+$','',target)
        p=Path(target)
        if not p.is_absolute():p=path.parent/p
        links+=1
        if not p.exists():missing.append([str(path),dest])
assert not missing,missing
(D/'document_checks.json').write_text(json.dumps(dict(
    local_links_checked=links, missing=missing, sources_unchanged=True,
    matched_wall10_performance_files=len(perf_sources)),indent=2)+'\n')

artifacts = [f'agent/{kind}/{slug}.md' for kind in ('plan','task','report','handoff')]
changed=sorted(set(artifacts+['projects/README.md','projects/findbox/README.md']+
                   [str(p.relative_to(R)) for p in D.iterdir() if p.is_file()]+
                   [str((D/'artifact_validation.json').relative_to(R))]))
metadata=dict(task_id=slug,language='zh-CN',axes=task['axes'],risk_tier=task['risk_tier'],
              status='NO_CODE_CHANGE',changed_files=changed,
              task_contract_sha256=task_contract_sha256(task),
              tests=json.loads((D/'receipts.json').read_text())['tests'],resume_command=None)
reportbody=summary+'\n\n'+(
    '完整结果见 docs/carrybox/physhsi_full_audit_20261023/README.md，逐关节/碰撞体/片段见appendix.md，'
    '后续实施边界见reconstruction.md。两条冻结CPU命令均PASS；没有新GPU仿真。'
    '独立wall10性能任务回执和源码一致性另存wall10_supplement.json，不能归入本轮执行。\n\n'
    '限制：资源model65000无完整run配方；未验证跨引擎接触/惯量响应等价，未证明某项差异是失稳唯一原因，'
    '未验证新任务收敛。生产文件hash与审计初始快照一致，其他工作区修改均保留。')
handoffbody=summary+'\n\n'+(
    '无待恢复命令或本任务GPU进程。后续重构以reconstruction.md为依据，不能自动把此审计解释为启动训练。'
    '本轮主对照是wall5 rev28 model5600与正式params；wall10是已有独立任务，不能混用checkpoint。'
    '两条CPU命令和源文件hash分别见receipts.json/source_identity.json。'
    '注意源actor真值、显式PD、源reward尺度、100步与24步预算、static hold数据改造，以及源history/feet缓存顺序问题。')
reportpath=R/'agent/report'/f'{slug}.md'
handoffpath=R/'agent/handoff'/f'{slug}.md'
write_artifact(reportpath,dict(metadata,artifact='REPORT'),reportbody)
write_artifact(handoffpath,dict(metadata,artifact='HANDOFF'),handoffbody)
validation=validate_paths(planpath,taskpath,reportpath,handoffpath)
(D/'artifact_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(validation,ensure_ascii=False))
assert validation['valid']
