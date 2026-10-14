---
task_id: "AGILE-V3-OUTCOME-20261003"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/contact_outcome.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_contact_outcome.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "README.md", "agent/plan/agilekickball-v3-outcome.md", "agent/task/agilekickball-v3-outcome.md", "agent/report/agilekickball-v3-outcome.md", "agent/handoff/agilekickball-v3-outcome.md", "docs/agilekickball_v3/outcome_20261003/receipts.json", "docs/agilekickball_v3/outcome_20261003/smoke.json", "docs/agilekickball_v3/outcome_20261003/scale_smoke.json", "docs/agilekickball_v3/outcome_20261003/artifacts.json"]
task_contract_sha256: "de4540187e4b1e004818468d730f6eb80aff450f0a054300b25bdd5773c28637"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_contact_outcome.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "ebc452bf6ef4682ef1ef5e33c5df62def4be280ba7e322577cf114ac2c5b4363", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "b60527577bf5fb3e9096ac886240aa640e47779b31142e667b9e25fddf137679", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c2cdedcfd922b65a901ff9fbcdfea89ab151033175e669e47945355a8beed98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "08ecbab12305b688f3483bad12ddf4a60c20bad35b6e4600d8ed2b39467019c6", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1d62a83bc8ed2afddb0ddf08e9ab2de07b15492cd74d08f81223147e2124831e", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

实现与验证已完成，没有等待中的训练进程。v3 revision 为 contact_outcome_20261003，默认 scratch；旧 v2/空间版 v3 checkpoint 不能直接 resume。

主要入口：scripts/rsl_rl/train_agilekickball_v3.sh；算法：rsl_rl_extensions/contact_outcome.py；训练真值：mdp/agilekickball_v3.py::outcome_training_state；配置：agilekickball_v3_env_cfg.py。原 actor/critic 路由、50 Hz 控制、奖励/PPO/AMP 不变。

可直接执行：bash scripts/rsl_rl/train_agilekickball_v3.sh。日志 roots 为 logs/rsl_rl/agilekickball_v3（正式）和 agilekickball_v3_smoke（本次测试）。正式脚本允许追加 CLI/Hydra 覆盖。新辅助 checkpoint config 必须匹配，包括关闭辅助的系数；推理加载不要求辅助 optimizer。

三个冻结测试全部 PASS；额外 4096 环境一次正式参数迭代通过，证据位于 docs/agilekickball_v3/outcome_20261003/。单元测试覆盖因果时间窗口对齐、信息隔离、KL 回退和 optimizer 动量恢复；后续如修改 optimizer restore，保留深拷贝以避免 Adam tensor 别名污染快照。

尚未开展性能评测和长训练。0.16 s 姿态预测不是恢复能力证明，proxy 非真实接触；缺少终止未来标签时样本被排除。当前纯辅助表征版本不含候选规划或教师蒸馏。下一步若用户要求训练，直接使用上面的正式脚本，无需重新做本次已通过的检查。
