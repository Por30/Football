---
task_id: "carrybox-wall4-restart-20261014"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
status: "DONE"
changed_files: ["README.md", "projects/README.md", "projects/findbox/README.md", "docs/carrybox/restart_20261014/README.md", "docs/carrybox/restart_20261014/health.json", "docs/carrybox/restart_20261014/launch.json", "docs/carrybox/restart_20261014/provenance.json", "docs/carrybox/restart_20261014/test_receipts.json", "agent/plan/carrybox-wall4-restart-20261014.md", "agent/task/carrybox-wall4-restart-20261014.md", "agent/report/carrybox-wall4-restart-20261014.md", "agent/handoff/carrybox-wall4-restart-20261014.md", "logs/rsl_rl/g1_carrybox_depth/walled4/restart_20261014_125408/status.json"]
task_contract_sha256: "8bc5a1fcf4b59e02d1c07c3ff7434a1027cac833af7f479590f16d0203f96384"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_convergence.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "fba75ac136727a58d4f451acf516032c5314d1b13303edf011eabe022ffe2b53", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "1da81c3aa47c6ab48c0ec42bcc5ee5f7ab6ce34c1678fc222c01951289aa9bd2", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

2026-10-14 12:55 JST：用户重新授权后，修正跌倒奖励的wall4已从头启动，PID2322385；128环境、seed42、40000轮，AMP/RSI使用根findbox。检查到iteration24，平均回合32.92步、AMP有效比例77.47%，model_0.pt的schema2/revision4及有限值已核验。拾取动作目标范围问题未调整，未证明收敛。

新正式run：/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_12-54-15_wall4_rewardfix_20261014_125408。日志：/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/restart_20261014_125408/train.log。旧队列未恢复；不重复启动。用户最新启动指令覆盖之前停止要求。

无生产代码变更，沿用已通过21项CPU/真实回放的revision4；本轮冻结跌倒回归2项通过，并人工核验当前进程身份、日志连续更新、checkpoint有限值/环境契约/数据身份。启动登记时系统Python3.8不支持dict union，登记副本已补齐，未重复创建进程；首次健康快照解析因时间字段带s未匹配，修正只读解析后通过。未修改控制目标范围或PD，成功统计仍0；启动验收不能证明训练将收敛。
