"""Publish engineering receipts only after the real restart verification passed."""
import json,statistics,sys,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];slug='carrybox-wall5-perf-20261018'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
receipts=json.loads((OUT/'receipts.json').read_text())['tests'];assert all(r['result']=='PASS' for r in receipts)
status=json.loads((OUT/'snapshot.json').read_text());assert status['status']=='PASS'
base=json.loads((OUT/'baseline.json').read_text());candidate=json.loads((OUT/'candidate.json').read_text())
def means(d):
    rows=[r for r in d['iterations'] if 2<=r['it']<=5]
    c=statistics.mean(r['collection_time'] for r in rows);l=statistics.mean(r['learn_time'] for r in rows)
    return c,l,c+l,max(r['collection_time']+r['learn_time'] for r in rows)
a,b=means(base),means(candidate)
summary=dict(baseline=dict(zip(('collection','learning','total','max'),a)),candidate=dict(zip(('collection','learning','total','max'),b)),speedup=a[2]/b[2],reduction_fraction=1-b[2]/a[2],formal_mean=status['mean_iteration_seconds'],formal_max=status['max_iteration_seconds'])
(OUT/'comparison.json').write_text(json.dumps(summary,indent=2))
rsi=candidate['rsi_equivalence'];assert rsi['rng_equal'] and rsi['partial_reset_unchanged']
body=f'''# Wall5 revision13性能排查与正式恢复（2026-10-18）

已完成等价优化、31项CPU检查、4096环境8轮完整更新/严格恢复与真实RSI对照；正式4096 wall5已恢复，检查时间{status['checked_at']}，PID **{status['pid']}**，实际迭代{status['progress_from']}→{status['progress_to']}。尚未完成正式长训或证明收敛。

| 同revision13、model0/seed42、4096×24 | 采样 s | 学习 s | 合计 s |
|---|---:|---:|---:|
| 修改前，第2–5轮 | {a[0]:.3f} | {a[1]:.3f} | {a[2]:.3f} |
| 修改后，第2–5轮 | {b[0]:.3f} | {b[1]:.3f} | {b[2]:.3f} |

耗时下降{100*(1-b[2]/a[2]):.1f}%，吞吐约{a[2]/b[2]:.2f}倍。正式运行最近10轮平均 **{status['mean_iteration_seconds']:.3f}s**、最慢 **{status['max_iteration_seconds']:.3f}s**，达到6秒目标。表格为未插入同步计时的完整训练轮；0–1轮预热排除，第6–7轮另开同步profile。两进程均使用24个PyTorch CPU线程、相同控制/仿真/学习配置，GPU单进程。环境创建和物理初始化约5分钟，单独于每轮训练时间。

## 原因与改动

基线细分每轮RSI初始化2.430s、全部reset2.943s、物理步1.456s、深度相机更新0.187s（嵌套阶段不可相加）。48次reset调用了576次root-link写入，反复读取全体连杆质心；624次get_coms共4.20s/两轮。主要新增开销来自RSI逐片段写入，不是深度光线投射。

1. Wall5 RSI保留原随机片段/帧采样顺序，填好所有待reset行后一次提交root-link和joint状态，保留link→COM速度转换、两次kinematics刷新及实际足部接地修正。
2. Wall5 AMP拼接native raw张量，批量gather和插值，再计算旋转/末端/0.7m距离封顶。保留shortest-arc nlerp、连续采样、边界检查和RNG；未用插值后的特征替代原始状态插值。
3. PPO每minibatch只编码一次深度latent，actor/critic/pose head在同一次optimizer step联合反传，保留原act采样的RNG消耗和KL调度、有效标签掩码。

未改变4096环境、24步、5epochs×4minibatches、512/256/256网络、std/entropy、AMP权重和Normalizer、80/0/20 RSI、奖励/终止、全身碰撞、深度分辨率/50Hz/自遮挡/障碍遮挡或数据manifest。actor/critic仍只接收本体与深度；箱子真值只进入AMP/辅助监督。checkpoint仍schema2/environment revision13/AMP config3，严格兼容本次原正式model0。足球使用独立BallRegression/SkillAMP算法，DepthCNNEncoder及足球文件未改；wall3/4默认分支仍按原状态写入和三次CNN forward工作。

## 验证与边界

31项CPU测试覆盖AMP样本/边界/四元数符号/RNG，CNN输出、总loss、各参数梯度和一次Adam更新，以及原CarryBox/walled/ground/AMP契约。4096实际PhysX对512个部分reset环境执行旧/新写入：root/COM/link速度、joint、足部和box/障碍状态最大差值记录于candidate.json；loco {rsi['loco_count']}、hold {rsi['hold_count']}，未reset行保持、RNG一致、脚底未穿地，loco箱底5mm。完整PPO/AMP更新和验证model7严格恢复通过。

首轮验收在训练后的RSI检查处因缺少inference_mode失败；这是检查上下文错误，正式重启被门控阻止。64环境复现了具体PyTorch异常，补上与训练采样一致的inference_mode后通过，并重新完成4096验收。保留attempt1_receipts.json、attempt1_candidate.log和rsi_debug日志。最初计时入口profile.py与标准库重名，已改为benchmark_profile.py，startup失败日志保留。最终3条冻结测试均由run_engineering_tests.py执行，见receipts.json。

旧PID3804340日志止于70轮，但仅model_0.pt写盘，1–70轮未保存更新无法恢复。新正式运行从原正式model_0.pt完整恢复网络、PPO/AMP优化器、Normalizer与RNG；物理在途状态/回合不在checkpoint中，课程照既有规则重新建立进程锚点。原run/log/checkpoint保留，docs下模型仅验证，不作为正式训练或成功率证据。

## 当前正式运行

- PID：{status['pid']}
- Run：`{status['run']}`
- 日志：`{status['log']}`
- 恢复来源：`{status['source_checkpoint']}`

```bash
tail -f '{status['log']}'
```

baseline.json/candidate.json提供同配置计时，两个profile.txt提供分项分析；snapshot.json记录正式契约、有限值与持续推进；unchanged_scope.json记录未改共享/配置/相机文件哈希。所有PID/轮次为带时间的快照，下次查看需核对实时状态。
'''
(OUT/'README.md').write_text(body)
short=f"{status['checked_at'][:16].replace('T',' ')} JST：[wall5性能优化与正式恢复]({{link}})：RSI合并写入、AMP批量native插值及同批CNN复用，4096同配置平均{a[2]:.3f}→{b[2]:.3f}秒/轮；31项CPU与4096完整更新/部分reset/恢复通过。新PID{status['pid']}，正式最近10轮平均{status['mean_iteration_seconds']:.3f}秒、最慢{status['max_iteration_seconds']:.3f}秒，检查迭代{status['progress_from']}→{status['progress_to']}。保持revision13/RSI80-0-20/全部遮挡与学习配置，从原正式model0恢复；旧70轮中未落盘部分无法恢复。训练进行中，未证明收敛。"
for file,link in [('projects/README.md','../docs/carrybox/wall5_perf_20261018/README.md'),('projects/findbox/README.md','../../docs/carrybox/wall5_perf_20261018/README.md')]:
 p=ROOT/file;s=p.read_text();heading,rest=s.split('\n',1);p.write_text(heading+'\n\n'+short.format(link=link)+'\n'+rest)
task,_=load_frontmatter(ROOT/f'agent/task/{slug}.md')
changed=[p for p in task['allowed_paths'] if p.endswith('.py') or p in ('projects/README.md','projects/findbox/README.md')]
changed=[p for p in changed if p!='scripts/rsl_rl/train.py']
changed += [str(p.relative_to(ROOT)) for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pt','.prof') and 'events.out.tfevents' not in p.name]
changed += [f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')]
changed=sorted(set(changed))
common={k:task[k] for k in ('task_id','language','axes','risk_tier')}
common.update(status='DONE',changed_files=changed,task_contract_sha256=task_contract_sha256(task),tests=receipts)
for kind,text in [('report',body),('handoff',f"等价性能优化与用户授权的正式恢复已完成。PID{status['pid']}，核验{status['checked_at']}、迭代{status['progress_to']}。正式日志`{status['log']}`；来源为原正式model0，不含旧run未保存的1–70轮。31项CPU、4096完整更新/RSI状态对照/恢复及正式持续推进通过。见docs/carrybox/wall5_perf_20261018/README.md与snapshot.json。后续请求先只读核对PID/log/checkpoint，再按用户意图操作；当前任务无待办，长训未结束，尚无收敛/成功率结论。")]:
 data=dict(common,artifact=kind.upper())
 if kind=='handoff':data['resume_command']=None
 (ROOT/f'agent/{kind}/{slug}.md').write_text('---\n'+''.join(f'{k}: {json.dumps(v,ensure_ascii=False)}\n' for k,v in data.items())+'---\n\n'+text+'\n')
result=validate_paths(*(ROOT/f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')))
(OUT/'artifact_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));assert result['valid'],result
print(json.dumps(dict(validation=result,comparison=summary,pid=status['pid'],iteration=status['progress_to'],log=status['log']),ensure_ascii=False,indent=2))
