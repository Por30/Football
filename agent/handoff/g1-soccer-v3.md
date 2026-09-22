---
task_id: "ENG-G1-SOCCER-V3-20260919"
status: "DONE"
language: "zh-CN"
axes: ["E", "P", "C", "L", "D", "S"]
risk_tier: "T2"
changed_files: ["source/perceptual_ball/perceptual_ball/amp_features.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/amp.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/algorithm.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/modules.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/perceptual_ball_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/soccer_env.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/soccer_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agents/rsl_rl_ppo_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/amp.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/events.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/soccer_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/depth_v3.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/smoke_soccer_v3.py", "scripts/rsl_rl/smoke_soccer_v3.sh", "scripts/rsl_rl/train_soccer_v3.sh", "tests/test_soccer_v3.py", "docs/research/iros2027/SOCCER_V3.md", "docs/research/iros2027/v3_test_receipts.json", "docs/research/iros2027/v3_artifact_validation.json", "docs/research/iros2027/validation/smoke_model.pt", "docs/research/iros2027/validation/smoke_v3.log", "docs/research/iros2027/validation/smoke_v3.json", "docs/research/iros2027/validation/exported/manifest.json", "docs/research/iros2027/validation/exported/policy.onnx", "docs/research/iros2027/validation/exported/policy.pt", "agent/plan/g1-soccer-v3.md", "agent/task/g1-soccer-v3.md", "agent/report/g1-soccer-v3.md", "agent/handoff/g1-soccer-v3.md"]
task_contract_sha256: "acd5267f781def68fd1dd8407476dcb345a8dd2578d691ea6dca11fdebff27b9"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_soccer_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "f98b3af5225002c9dd389df5ac57b81c02d4b856396f68badf45b7ba77926690", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "a5dadddf7c0febaea6683fb845c678d4e172fcf93b2c6f1f0dfce5345b6aba9d", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_soccer_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e5018c6b950808f9f13d89dc5e7827c003bc2eff50c0878a7f724fda5f087353", "stdout_sha256": "2415a7848c8cc96e66d273c28ea355bad3225cc03cae74a1682feb2cc85fd5d9", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

# G1 Soccer v3 交接

工程任务完成。使用 agent/task/g1-soccer-v3.md 的冻结范围与绑定回执；实现细节、参数和运行说明见 docs/research/iros2027/SOCCER_V3.md。当前平台是 G1，任务 ID 为 Template-Perceptual-Ball-Soccer-v3。

启动新的基线训练：

```bash
cd /home/cao/perceptual_ball
bash scripts/rsl_rl/train_soccer_v3.sh --max_iterations 10000 --run_name v3_baseline
```

默认 CUDA:0、256 环境、seed 42、headless。脚本使用本机 ball Python 与 Isaac Sim 路径；日志在 logs/rsl_rl/g1_soccer_v3。尚未运行长期训练，也未验证大规模 GPU 吞吐/显存；validation/smoke_model.pt 只是流程产物。不要把旧 v2 checkpoint 当作完整 v3 恢复。下一步记录训练失败分布与学习曲线，再确定更高速度或研究实验；不将本轮 smoke 转述为性能结果。

若后续修改任务，按冻结命令重跑 CPU 测试和真实 smoke。尤其保留 terminal 历史只推进一次、动作时刻 skill、发球只结算一次、跌倒优先失败、辅助 KL 回退、完整 CNN 导出。PhysX 4.5 的 Robot/.* 分组过滤实测为空，必须使用具名碰撞部件；更换 G1 USD 时同步更新过滤集合。终止环境必须先关闭再关闭 App，以免异常退出挂起。

工作区原先已有大量未跟踪代码、数据和用户修改；本轮未提交或清理这些内容。历史 audit_soccer_cpu.py 用于复现旧缺陷，不作为修复后的回归命令。所有工件已交叉校验，本轮无未完成恢复动作。
