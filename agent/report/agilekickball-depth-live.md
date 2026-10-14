---
task_id: "agilekickball-depth-live"
language: "zh-CN"
axes: ["P"]
risk_tier: "T1"
status: "DONE"
changed_files: ["scripts/sim2sim/kickball_mujoco.py", "scripts/sim2sim/depth_visualization.py", "projects/football/README.md", "projects/README.md", "docs/agilekickball_v4/sim2sim_20261014/README.md", "docs/agilekickball_v4/sim2sim_20261014/depth_live_receipts.json", "docs/agilekickball_v4/sim2sim_20261014/depth_live_smoke.json", "docs/agilekickball_v4/sim2sim_20261014/depth_live_smoke.xml", "agent/plan/agilekickball-depth-live.md", "agent/task/agilekickball-depth-live.md", "agent/report/agilekickball-depth-live.md", "agent/handoff/agilekickball-depth-live.md"]
task_contract_sha256: "a6d94bb8122797c96338869b5a45cc464af70acd4f4bb6d7557db43d31c9fb9c"
tests: [{"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e285bbaef756008edc846cd4a06c7d45d16f544eb95777d67efe56c4fafd767f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "20b818090afe475e0dd0bff2777248cd4e691e7c392e4a51e5c3ab646586c0da", "runner": "run_engineering_tests.py"}, {"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --duration 2 --physics-dt 0.005 --output docs/agilekickball_v4/sim2sim_20261014/depth_live_smoke.json", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "df97a91dd31b903937264da48d123895a75798c08de7dce72c497382971b64da", "stdout_sha256": "7af590abd030484d0ecf4ddf0b4f086fff7a532705f1d7b7f6097d6615040a16", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

图形启动默认同步显示独立Tk深度窗口。最新帧/8帧历史、时间/最近距离/命中像素10Hz刷新；仅使用已有网络输入，不改变仿真控制。已通过8项原有CPU检查和真实桌面2秒双窗口短测（100控制步、20次深度刷新、零错误）。headless不创建窗口，--no-depth-window可显式关闭。未运行训练或真机。
