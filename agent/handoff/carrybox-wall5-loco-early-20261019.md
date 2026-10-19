---
task_id: "carrybox-wall5-loco-early-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["docs/carrybox/wall5_loco_early_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-loco-early-20261019.md", "agent/task/carrybox-wall5-loco-early-20261019.md", "agent/report/carrybox-wall5-loco-early-20261019.md", "agent/handoff/carrybox-wall5-loco-early-20261019.md"]
task_contract_sha256: "87548590359d8097a0bda4ded3999f966f7bde5af01dc2ab6c4db11d006ac184"
tests: [{"command": "bash docs/carrybox/wall5_loco_early_20261019/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8198c07aa11c94f072a149ab8f993818c3696551f7a601cc4d7c570a581d23d3", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_loco_early_20261019/replay.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1b0b8e7a6770289545588f99b03448d45f2c77914a02160eaaaa2b9eb79e517c", "stdout_sha256": "25f5e73642fa370d1b40b0005e49c24c8d96f192ba7f317d0e54e3a911e76afe", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

model11200没有学会从loco起点稳定站立/移动。同初态16环境五组100步回放全部验收通过；策略16/16在9–11步pitch超限且均在push前。保持参考/默认/参考轨迹/参考清初速分别平均44.56/41.81/40.00/52.94步，全部也未稳定2秒，不能把控制适配宣布正常。首步左膝16/16、右膝14/16目标被物理下限裁剪，支持策略动作加速倾倒；未做单关节干预，不声称唯一根因。

正式近期日志loco约10.60步、hold936.38步，已完成回合步数约4.3%/95.7%；80%loco reset不能保证80%loco训练量。AMP占净混合约3.93%，辅助loss0.00209，不沿用旧版AMP主导的解释。完整证据、图、限制与后续最小修复顺序见docs/carrybox/wall5_loco_early_20261019/README.md。

最初单进程重置配对存在约0.18mm深度差异，两次范围内修复分别补异常可见性、改独立进程；保持全部断言，最后PASS，失败记录保留。仅新增诊断工件并更新项目入口。生产配置/RSI/数据/权重无改动；本次未停止重启训练。检查时原PID4038923已退出，正式日志止于11304轮，原因未知。诊断完成不代表训练问题修复。

后续先审计G1参考初态/PD/足端支撑的闭环可跟踪性及实际loco训练步数保障，再接回拾箱hold；仅调整rev15推扰/摩擦不足以解释首push前倾倒。现有生产RSI80/0/20不可因本次诊断自行改变。正式旧模型与当前rev15环境不完全兼容，后续先决定具体训练方案；不恢复/启动当前短测。冻结检查复现命令见Task，完成态无需自动恢复。
