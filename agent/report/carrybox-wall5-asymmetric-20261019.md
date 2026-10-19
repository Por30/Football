---
task_id: "carrybox-wall5-asymmetric-20261019"
language: "zh-CN"
axes: ["L", "A"]
risk_tier: "T2"
status: "DONE"
changed_files: ["AGENTS.md", "agent/handoff/carrybox-wall5-asymmetric-20261019.md", "agent/plan/carrybox-wall5-asymmetric-20261019.md", "agent/report/carrybox-wall5-asymmetric-20261019.md", "agent/task/carrybox-wall5-asymmetric-20261019.md", "docs/carrybox/wall5_asymmetric_20261019/README.md", "docs/carrybox/wall5_asymmetric_20261019/artifact_validation.json", "docs/carrybox/wall5_asymmetric_20261019/before/carrybox_wall5.py", "docs/carrybox/wall5_asymmetric_20261019/before/carrybox_wall5_env_cfg.py", "docs/carrybox/wall5_asymmetric_20261019/before/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "docs/carrybox/wall5_asymmetric_20261019/before/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "docs/carrybox/wall5_asymmetric_20261019/before/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_asymmetric_20261019/check.sh", "docs/carrybox/wall5_asymmetric_20261019/cpu.log", "docs/carrybox/wall5_asymmetric_20261019/cpu.task.md", "docs/carrybox/wall5_asymmetric_20261019/cpu_attempt1.log", "docs/carrybox/wall5_asymmetric_20261019/expert_review.md", "docs/carrybox/wall5_asymmetric_20261019/exported/manifest.json", "docs/carrybox/wall5_asymmetric_20261019/exported/policy.onnx", "docs/carrybox/wall5_asymmetric_20261019/exported/policy.pt", "docs/carrybox/wall5_asymmetric_20261019/finish.py", "docs/carrybox/wall5_asymmetric_20261019/gpu_release.json", "docs/carrybox/wall5_asymmetric_20261019/launch.json", "docs/carrybox/wall5_asymmetric_20261019/launch.sh", "docs/carrybox/wall5_asymmetric_20261019/launch.task.md", "docs/carrybox/wall5_asymmetric_20261019/launch_after_release.py", "docs/carrybox/wall5_asymmetric_20261019/launch_failed_import.json", "docs/carrybox/wall5_asymmetric_20261019/launch_import_fix.json", "docs/carrybox/wall5_asymmetric_20261019/production_changes.json", "docs/carrybox/wall5_asymmetric_20261019/receipts.json", "docs/carrybox/wall5_asymmetric_20261019/receipts_cpu.json", "docs/carrybox/wall5_asymmetric_20261019/receipts_cpu_attempt1.json", "docs/carrybox/wall5_asymmetric_20261019/receipts_launch.json", "docs/carrybox/wall5_asymmetric_20261019/receipts_launch_attempt1.json", "docs/carrybox/wall5_asymmetric_20261019/receipts_smoke.json", "docs/carrybox/wall5_asymmetric_20261019/restart.py", "docs/carrybox/wall5_asymmetric_20261019/smoke.json", "docs/carrybox/wall5_asymmetric_20261019/smoke.log", "docs/carrybox/wall5_asymmetric_20261019/smoke.py", "docs/carrybox/wall5_asymmetric_20261019/smoke.sh", "docs/carrybox/wall5_asymmetric_20261019/smoke.task.md", "docs/carrybox/wall5_asymmetric_20261019/smoke_model.pt", "docs/carrybox/wall5_asymmetric_20261019/snapshot.json", "docs/carrybox/wall5_asymmetric_20261019/stopped_run.json", "docs/carrybox/wall5_asymmetric_20261019/task_before_expert_metadata.md", "docs/carrybox/wall5_asymmetric_20261019/verify_launch.py", "logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/events.out.tfevents.1792338112.cao.4038923.0", "logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/git/perceptual_ball.diff", "logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/model_0.pt", "logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/params/agent.yaml", "logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/params/env.yaml", "logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v13_perf_fresh_20261018_131037.log", "logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v14_asymmetric_fresh_20261019_003630.log", "logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v14_asymmetric_fresh_20261019_003706.log", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "tests/test_carrybox_asymmetric.py"]
task_contract_sha256: "5f2fbdcf8cc7ed84f4de3895192f25947d39d0ee7565c4065cf189109db1f94f"
tests: [{"command": "bash docs/carrybox/wall5_asymmetric_20261019/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "aa85f3ad133be7a97c049363a5f67a4fd5f14abd6482a7b14f47356358e14aae", "stdout_sha256": "a4ca10a009c8b1a9075a74ed6cb2ccae867a4ede5d32e48b1c588693b2ef0a9e", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_asymmetric_20261019/smoke.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "a41c6d0229d56e20a79afa0c29e2c479960a6a544c69c38f9be2bf479e80e7a7", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_asymmetric_20261019/verify_launch.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e567430e6e46418caf129335461b8e76e62a2c463057ca486d7a76699c43f1de", "stdout_sha256": "b6501bce0a1fc064d9cff57893545784b82f09f968ed8c070ea713da42fafe09", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# Wall5非对称Actor–Critic与正式重启（2026-10-19）

用户明确要求仅critic使用特权信息。wall5已升级revision14，actor及部署接口保持深度与本体；critic独立MLP，无深度输入，也不向深度CNN反传value loss。

| 分支 | 实际输入 | 网络 |
|---|---|---|
| Actor | 4帧本体93×4=372；4帧27×48深度 | 原CNN输出128，与本体拼成500；MLP512/256/256→29动作 |
| Critic | 当前本体93＋机体线速度3＋箱子相对位置3＋相对旋转6＋完整尺寸3=108 | 独立MLP108→512→256→256→1 |
| 辅助位姿头 | actor深度latent128 | 原9维位姿预测，保留可见性配对mask及coef0.1 |

本体93为角速度3（×0.25）、投影重力3、关节位置偏差29、关节速度偏差29（×0.05）、上一动作29。critic用当前帧；actor保持4帧历史，不含线速度。critic新增速度为pelvis link原点的机体系速度m/s；箱子位置为同坐标系米制相对位置，旋转为pelvis逆姿态乘箱子姿态的旋转矩阵前两列，尺寸为箱子局部完整边长（当前0.30×0.30×0.25m）。critic真值不施加相机遮挡、延迟或AMP的0.7m截断；这些真值不会进入actor、pose head输入或部署导出。

只修改三个wall5生产文件。新增critic_state观测、独立critic类、PPO快路和reset前critic快照；timeout bootstrap取本回合终止状态，避免使用重置后的箱子/机器人状态。新模型环境契约为schema2/revision14，旧revision13完整resume及完整权重warm-start因critic形状/契约变化不兼容；本次按用户要求fresh。

AMP仍为ground_pickup的13段、60维×10窗口、running normalization；AMP采样40/40/20，RSI80/0/20，奖励/PPO超参/深度/全身碰撞均保持。wall3/wall4、CarryBox-v0和football生产接口未改。

验证：31项CPU通过（含6项非对称专用检查）；4环境真实PPO/AMP完整配方2＋恢复1轮通过，含强制timeout、部分reset、终止快照、有限更新、严格恢复、TorchScript/ONNX导出与wall4配置隔离。正式4096检查于2026-10-19T00:42:58.492209+09:00通过：迭代0→15，最近10轮平均3.813秒，最慢3.830秒。

旧PID3812053已停止，旧模型保留至`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_13-10-42_wall5_v13_perf_fresh_20261018_131037/model_10600.pt`。新PID4038923，4096环境、seed42、40000轮、从零初始化；首model_0中PPO/AMP优化器均step20，AMP Normalizer count61440，确认没有继承旧训练状态。训练已启动，尚无收敛结论。

新run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706`

```bash
tail -f '/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v14_asymmetric_fresh_20261019_003706.log'
```

启动过程中旧进程退出后的GPU显存释放有短暂延迟，复查空闲后才启动。首个新进程因未加载Isaac Sim环境在导入阶段退出、没有训练迭代；补齐显式setup_conda_env.sh及导入预检后启动当前run。失败回执、日志和诊断均保留，没有盲目循环重启。CPU首次检查仅测试脚本误用元数据键num_clips，修正为实际clip_count后通过，原失败记录保留。

证据：production_changes.json记录三个生产文件hash；expert_review.md为独立只读审查；receipts.json为三条冻结命令最终回执，smoke.json为真实仿真，snapshot.json为正式运行快照，launch.json/stopped_run.json记录进程身份。验证模型仅在本docs目录，正式run没有加载它。

