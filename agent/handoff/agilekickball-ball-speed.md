---
task_id: "agilekickball-ball-speed"
language: "zh-CN"
axes: ["C"]
risk_tier: "T1"
status: "DONE"
changed_files: ["scripts/sim2sim/kickball_mujoco.py", "scripts/sim2sim/depth_visualization.py", "tests/test_kickball_ball_speed.py", "docs/agilekickball_v4/sim2sim_20261014/README.md", "projects/football/README.md", "projects/README.md", "docs/agilekickball_v4/sim2sim_20261014/ball_speed_20261015/gui_smoke.json", "docs/agilekickball_v4/sim2sim_20261014/ball_speed_20261015/gui_smoke.xml", "docs/agilekickball_v4/sim2sim_20261014/ball_speed_20261015/receipts.json", "agent/plan/agilekickball-ball-speed.md", "agent/task/agilekickball-ball-speed.md", "agent/report/agilekickball-ball-speed.md", "agent/handoff/agilekickball-ball-speed.md"]
task_contract_sha256: "852634b18b4d843c0dee5e8e770c1d692f1cd6d6c01a6f08038baad6cecdd4fe"
tests: [{"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e285bbaef756008edc846cd4a06c7d45d16f544eb95777d67efe56c4fafd767f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e05fd941d4906d3582c95434c0cb8ecc4813ef8eb422b5520622cd4ddacc0953", "runner": "run_engineering_tests.py"}, {"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_ball_speed.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "7be3e6b197e04277349cc0af63f1fa72f016179e771f379bb1aba84b7898cdfd", "stdout_sha256": "b89b3c99ac3b8b24475bdaa41d3050fb109cdcc6bda33d59b25ca89d3957ac7c", "stderr_sha256": "d8b5fdae8a6dd1806cf811de113949a89fa8c113c9a24742ad9db2791cc35fa4", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

已完成；沿用原s2s图形命令即可看到Ball speed滑块及Apply now/Re-serve，--speed设置初值；--no-depth-window或--headless关闭控件。设置作用于后续发球，即时应用是一次速度修改，正常碰撞/摩擦和回合恢复仍继续。控制回调只入队，观测前消费；Free-joint角速度由世界系转换为球局部系；单位检查用MuJoCo实测角速度验证。原8项检查和新增4项（含真实桌面100步交互）PASS；证据位于ball_speed_20261015。机器人状态与策略历史不被手动操作重置。
