---
task_id: "ENG-AGILE-V1-20260921"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "REPORT"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v1.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v1_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/smoke_agilekickball_v1.py", "scripts/rsl_rl/smoke_agilekickball_v1.sh", "tests/test_agilekickball_v1.py", "docs/agilekickball_v1/README.md", "docs/agilekickball_v1/test_receipts_attempt1.json", "docs/agilekickball_v1/test_receipts.json", "docs/agilekickball_v1/validation/smoke_model.pt", "docs/agilekickball_v1/validation/smoke.log", "docs/agilekickball_v1/validation/diagnostics.md", "docs/agilekickball_v1/validation/smoke.json", "agent/plan/agilekickball-v1.md", "agent/task/agilekickball-v1.md", "agent/report/agilekickball-v1.md", "agent/handoff/agilekickball-v1.md"]
task_contract_sha256: "d316655981c3af6e982493f3c5b9eb795f85b3b118c6361a830ea542c2aec2c2"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "b4b60dbc7e19b021e8aa3c779067db6a2cf08505ea94fdb559dd07717aa08855", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "a8e26f4d9de3d13eed0b80eab9cd14a2e06c705aa77040f28baa36bf90a529ae", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v1.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "16c1118b590fe835280148e6f58681b05f8ce54124562e7c2dd440ed1b0c9ebb", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
---

新增独立Template-Perceptual-Ball-AgileKickball-v1。速度下限0.4，上限分10级至5.0m/s；50%挑战新区间，50%慢球复习，第0级全部挑战。至少4096已结算球和1024挑战球组成一个完整批次窗口，整体/挑战都80%，连续2窗口且驻留1000步晋级。失败窗口清连续计数，飞行中球不变，旧阶段在途结果不推动新阶段。

课程代理成功比v0奖励严格：足部近邻速度突变、主动相对足速沿向外方向>0.5m/s、球向外>0.4m/s、沿冻结方向回传推进0.5m、完成连续0.3s稳定恢复；终止优先计失败。每球幂等结算，尚未完成不入分母。固定发球距离1.3–2m，原v0网络/输入/奖励/恢复gate保持，v0任务仍保留。

checkpoint保存stage/窗口/驻留及配置校验，播放恢复且冻结课程；物理开放球不恢复，截断单独记录。v0权重加载v1从stage0开始。训练支持显式绝对checkpoint路径，日志放新agilekickball_v1目录。

32项CPU回归及真实16环境smoke通过。最高实际抽样4.88465m/s；构造高速阶段不冒充晋级。既有v0模型在stage0自然结算30球，29个严格课程代理成功、0次episode终止，因不够样本和驻留而未晋级。一次PPO/辅助/AMP更新、checkpoint roundtrip及play冻结通过。首次smoke更新前在inference_mode加载Adam造成验证脚本错误，一次修复上下文后通过，未改算法或放宽断言。

未运行4096长训练，未证明5m/s稳定回球，未解决此前近脚视觉盲区，未增加真实接触传感器。文档给出4096环境、额外50000轮的v0 checkpoint初始化命令及从头训练选项。
