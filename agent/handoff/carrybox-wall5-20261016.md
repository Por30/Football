---
task_id: "carrybox-wall5-20261016"
language: "zh-CN"
axes: ["L", "E"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_carrybox_walled.sh", "tests/test_carrybox_wall5.py", "docs/carrybox/wall5_20261016", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-20261016.md", "agent/task/carrybox-wall5-20261016.md", "agent/report/carrybox-wall5-20261016.md", "agent/handoff/carrybox-wall5-20261016.md"]
task_contract_sha256: "fc59e5b1983c1aa29752adacf6644533a064c2e704337e084c41381f412314db"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "22078755bb1eae043504d47b6016b46e2d1b1ed064269fcbd8adba066dedb7ef", "stderr_sha256": "21b2a448b6a1de9db4f559175aca53f2345c4ffc1ad321560a637b1f4517aac7", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_20261016/validate.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "d403bb35da27dccc7468a99d847f98385f25af2628a6c0239dc48fa418fd60a8", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

依据用户差异文档第6节阶段A，已新增独立wall5，继承wall4 revision8物理任务，只实施P0 AMP组。每步奖励0.75*r_task+0.125*style，无dt AMP；在线/专家/terminal为10×35纯本体，去jointvel、归一化与clamp；D独立Adam5e-5、trunk/output decay .001/.1，从reset首步给奖励并更新。重复首帧由原CircularBuffer保证，terminal保存旧回合最后帧；按变体修正valid样本统计并新增四项奖励日志。原始15段数据与RSI速度不动，PPO/相机/任务奖励/RSI均保留；P1/P2明确未做。

外层schema2保持，wall5环境revision9、AMP配置schema2；双向完整恢复拒绝wall4/wall5混用，显式policy-only迁移仍可用但未执行。共用改动只有注册/runner分支、yaw合法枚举及有效步统计的默认8兼容分支。原wall3/wall4回归通过，足球Gym与runner分支保持。

50项CPU PASS；4环境生产24步×4epochs×4minibatches，3轮更新＋新runner恢复1轮，6次错开reset、JIT输出一致和ONNX checker通过。初次唯一CPU失败为测试脚本缺少inference_mode，修复测试后用run_engineering_tests原样复跑CPU；保留首轮失败回执及成功GPU回执，生产代码未再变，不重复GPU测试。组合专家只读最终复核无阻塞。全部短测产物在docs/carrybox/wall5_20261016，未写正式wall5日志目录。

2026-10-16 12:35 JST原wall4 PID2660033仍在4096环境训练；本轮未启动、停止或重启任何正式训练。wall5仅实现及短测通过，未验证长训收敛或4096环境≤6s性能。下一步用户若要求正式训练，应先核对资源并独立计时；具体命令及完整对照见docs/carrybox/wall5_20261016/README.md。用户输入x2g1differ.md保留原样，未纳入改动。
