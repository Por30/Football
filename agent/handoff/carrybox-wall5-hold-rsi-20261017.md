---
task_id: "carrybox-wall5-hold-rsi-20261017"
language: "zh-CN"
axes: ["E"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-hold-rsi-20261017.md", "agent/plan/carrybox-wall5-hold-rsi-20261017.md", "agent/report/carrybox-wall5-hold-rsi-20261017.md", "agent/task/carrybox-wall5-hold-rsi-20261017.md", "docs/carrybox/wall5_hold_rsi_20261017/README.md", "docs/carrybox/wall5_hold_rsi_20261017/carrybox_wall5.py.before", "docs/carrybox/wall5_hold_rsi_20261017/carrybox_wall5_env_cfg.py.before", "docs/carrybox/wall5_hold_rsi_20261017/carrybox_walled.py.before", "docs/carrybox/wall5_hold_rsi_20261017/check.sh", "docs/carrybox/wall5_hold_rsi_20261017/cpu.log", "docs/carrybox/wall5_hold_rsi_20261017/receipts.json", "docs/carrybox/wall5_hold_rsi_20261017/smoke.json", "docs/carrybox/wall5_hold_rsi_20261017/smoke.log", "docs/carrybox/wall5_hold_rsi_20261017/smoke.py", "docs/carrybox/wall5_hold_rsi_20261017/smoke.sh", "docs/carrybox/wall5_hold_rsi_20261017/test_carrybox_ground.py.before", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_ground.py"]
task_contract_sha256: "bfd7521310fcc4f2276b4c7d59b426f2dc381d4862609793eea60c75d1012ddb"
tests: [{"command": "bash docs/carrybox/wall5_hold_rsi_20261017/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "79badaf4a435680bcae86b22e3e3a875da63f7a689d781b782e860ec6954b993", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_hold_rsi_20261017/smoke.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "f63b3610370240179adb195ec477ac906a11a3c78307751d2b88805eb5e43b95", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

已将wall5 RSI默认改为loco80%、pickup0%、hold20%，hold保持真实参考箱高，其余loco贴地。仅wall5显式开放hold例外，旧ground拒绝规则保留；数据/PPO/深度/AMP权重不变。revision13契约和项目入口已同步。14CPU与4env reset短测通过，覆盖原始hold各帧与重复尾帧、partial和自动reset；首20ms接触瞬态最高1.64m/s，未验证持箱稳定或收敛。没有启动/停止正式训练，football PID3429618保留。
