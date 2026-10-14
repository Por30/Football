---
task_id: "AGILE-V3-AIM035-20260928"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "docs/agilekickball_v3/README.md", "README.md", "agent/plan/agilekickball-v3-aim035.md", "agent/task/agilekickball-v3-aim035.md", "agent/report/agilekickball-v3-aim035.md", "agent/handoff/agilekickball-v3-aim035.md", "docs/agilekickball_v3/aim035_20260928/receipts.json", "docs/agilekickball_v3/aim035_20260928/artifacts.json"]
task_contract_sha256: "a86e79c5345af908383b7c97843323aadb8a606873f13663caca9af2464a7bde"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c2cdedcfd922b65a901ff9fbcdfea89ab151033175e669e47945355a8beed98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "1086fe56871dd4b3a11d9bed291a9a3204eaa69e51ac2144e2f132f97d52ada0", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

v3横向目标偏移终点由±0.75m改为±0.35m，保留±0.25m起点和60000平均来球曝光步；中点变为±0.30m。revision更新为wide_serve_aim035_20260928，checkpoint配置记录0.35m并拒绝旧分布。最远3m发球、机器人1.2m移动范围和v2速度课程保持。同步现有回归、smoke期望和当前说明。

冻结CPU回归PASS，git diff --check通过；此次未重跑真实仿真，历史validation属于±0.75m版本。未启动/停止/重启训练，也未修改历史checkpoint。查询时未发现scripts/rsl_rl/train.py进程。启动命令见docs/agilekickball_v3/README.md，新任务从零训练，旧v3存档不能直接resume。
