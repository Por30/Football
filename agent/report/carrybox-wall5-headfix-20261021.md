---
task_id: "carrybox-wall5-headfix-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "REPORT"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-headfix-20261021.md", "agent/plan/carrybox-wall5-headfix-20261021.md", "agent/report/carrybox-wall5-headfix-20261021.md", "agent/task/carrybox-wall5-headfix-20261021.md", "docs/carrybox/wall5_headfix_20261021/README.md", "docs/carrybox/wall5_headfix_20261021/artifact_validation.json", "docs/carrybox/wall5_headfix_20261021/attempt1_active_terms/reason.json", "docs/carrybox/wall5_headfix_20261021/attempt1_active_terms/receipts.json", "docs/carrybox/wall5_headfix_20261021/attempt1_active_terms/smoke.log", "docs/carrybox/wall5_headfix_20261021/attempt1_active_terms/smoke.py", "docs/carrybox/wall5_headfix_20261021/audit.json", "docs/carrybox/wall5_headfix_20261021/before.json", "docs/carrybox/wall5_headfix_20261021/before_source/source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py", "docs/carrybox/wall5_headfix_20261021/before_source/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "docs/carrybox/wall5_headfix_20261021/before_source/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_headfix_20261021/before_source/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "docs/carrybox/wall5_headfix_20261021/before_source/tests/test_carrybox_reward_geometry.py", "docs/carrybox/wall5_headfix_20261021/cpu.log", "docs/carrybox/wall5_headfix_20261021/cpu_pass", "docs/carrybox/wall5_headfix_20261021/finish.py", "docs/carrybox/wall5_headfix_20261021/launch.json", "docs/carrybox/wall5_headfix_20261021/launch.py", "docs/carrybox/wall5_headfix_20261021/launch.sh", "docs/carrybox/wall5_headfix_20261021/receipts.json", "docs/carrybox/wall5_headfix_20261021/restart.log", "docs/carrybox/wall5_headfix_20261021/smoke.json", "docs/carrybox/wall5_headfix_20261021/smoke.log", "docs/carrybox/wall5_headfix_20261021/smoke.py", "docs/carrybox/wall5_headfix_20261021/smoke.sh", "docs/carrybox/wall5_headfix_20261021/smoke_model.pt", "docs/carrybox/wall5_headfix_20261021/smoke_pass", "docs/carrybox/wall5_headfix_20261021/snapshot.json", "docs/carrybox/wall5_headfix_20261021/source_receipt.py", "docs/carrybox/wall5_headfix_20261021/start_and_verify.sh", "docs/carrybox/wall5_headfix_20261021/stop.py", "docs/carrybox/wall5_headfix_20261021/stopped_run.json", "docs/carrybox/wall5_headfix_20261021/validate_and_restart.sh", "docs/carrybox/wall5_headfix_20261021/validated_sources.json", "docs/carrybox/wall5_headfix_20261021/verify.log", "docs/carrybox/wall5_headfix_20261021/verify.py", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_reward_geometry.py"]
tests: [{"command": "bash docs/carrybox/wall5_headfix_20261021/validate_and_restart.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "5027862212976c1a843c9db93c5aefbc5d71f6f1344925429e80e321ed8b10f5", "stdout_sha256": "5acf227ac0ba51bc0f0d0e676e8cb0267e99d91e67ea9b20c464ef87015eb26f", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
task_contract_sha256: "b99b43c4e0efd8d6dda5248818f9105b23387596d34a696326ef06eb6adf9f74"
---

# wall5 头高标定修正与正式重启（revision20）

2026-10-21T13:35:32.466999+09:00 状态快照：实现完成，57项CPU检查、20环境仿真短测和4096环境正式启动验收通过。正式训练进行中，尚未验证拾箱收敛。

已确认本地旧版误用X2头高0.823 m；采用用户校正的head_yaw_link站立中位数1.112 m。G1沿用本地PhysX参考姿态FK的物理head COM 1.21962583 m。仿真复核资产和数据manifest hash与原标定一致。本次未找到X2原始资产，未独立重算X2 FK；1.112的来源保存在checkpoint契约中。

| 参数 | revision19 | revision20 |
|---|---:|---:|
| 头低终止/m | 0.592771 | 0.438714 |
| 即时成功/站起奖励头高门槛/m | 1.185542 | 0.877429 |
| 站起奖励头高目标/m | 1.259638 | 0.932268 |
| 头高指数系数/m⁻¹ | 5.398377 | 7.294040 |

头高缩放系数1.096785819，使用精确公式而非报告中保留3位的小数。拾箱参考最低头高0.662100 m，距终止线余量0.069329→0.223386 m。旧目标高于参考中位数，不能据此声称物理上永远不可达。

移除early_failure及其日志索引。旧−50为权重，RewardManager乘policy dt=0.02后是终止转移−1，再进入任务/AMP混合；不是每次直接−50。跌倒/超时/非有限检查仍保留。roll0.5、pitch1.1、骨盆阈值0.231137、3D近箱距离0.783688 m、箱高标定均保持。

终止注册拆为fell_pelvis/fell_head。当前IsaacLab的Episode_Termination只保留每环境最后触发原因；准确的多原因统计使用`Skill/{loco,pickup,hold}_fell_pelvis_fraction`、`Skill/{loco,pickup,hold}_fell_head_fraction`，分母为该技能已完成回合数，reset前读取物理状态，两者同时触发分别计入但fell合计只计一次。tipped也按reset前真实状态统计，因此多原因比例可相加超过1。

RSI仍75/5/20（3072/205/819）；pickup为0–31贴地帧，hold保持手边参考箱高。actor仍4帧本体+深度，critic独立108维特权MLP；AMP60维/13片段、辅助可见性监督、推扰、深度、碰撞、PD、PPO和足球均未调整。站位距离及膝碰撞未在本轮改变。

验证：57项CPU通过；真实G1四种受控姿态分别产生骨盆低/头低/同时低/均正常，部分reset记录两个原因各2次、fell合计3次。20环境覆盖15 loco/1 pickup/4 hold，PPO/AMP更新2轮、严格保存恢复再更新1轮；新模型恢复前后actor/critic输出完全一致，revision19严格恢复被拒绝。短测模型仅为验证产物。第一次短测断言漏列原有invalid非有限保护，修正测试期望后通过，失败回执保存在attempt1_active_terms中；未删除保护或放宽阈值。

旧PID1032672已停止，日志至430轮，保留模型`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_12-57-08_wall5_v19_rsi75_5_20_fresh_20261021_125703/model_400.pt`及历史日志；最后未保存迭代未恢复。新PID1042917，4096环境/seed42/40000轮，从头训练，无resume/checkpoint/warm-start。检查至15轮，近10轮平均3.821s、最慢3.840s。model_0确认schema2/revision20、优化器step20、AMP Normalizer count61440及全部新契约；参数/优化器有限。该验证不代表已学会抱箱。

训练目录：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_13-29-36_wall5_v20_headfix_fresh_20261021_132931`

```bash
tail -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v20_headfix_fresh_20261021_132931.log
```

[参数审计](audit.json)、[CPU日志](cpu.log)、[仿真短测](smoke.json)、[正式启动验收](snapshot.json)、[冻结测试回执](receipts.json)。

