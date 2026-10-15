---
task_id: "carrybox-handoff-restart-20261014"
language: "zh-CN"
axes: ["L", "P", "C"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "tests/test_carrybox_x2.py", "scripts/rsl_rl/validate_carrybox_handoff.py", "scripts/rsl_rl/validate_carrybox_handoff.sh", "handoff.txt", "README.md", "projects/README.md", "projects/findbox/README.md", "docs/carrybox/handoff_20261014", "agent/plan/carrybox-handoff-restart-20261014.md", "agent/task/carrybox-handoff-restart-20261014.md", "agent/report/carrybox-handoff-restart-20261014.md", "agent/handoff/carrybox-handoff-restart-20261014.md"]
task_contract_sha256: "a96246bd2f1b221f9ed1c6bba68d9ccc21e9e5f675d4a16693003aed055c03a6"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "e69bb9975490fc95eedf624150c7516747bcbeebed779a73cae4dcc60fd4fc97", "stderr_sha256": "39679b8f54f740f34dca0d07907393dbfa3174acb9be209c6eecd6bf79057655", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/validate_carrybox_handoff.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "3cf886ea9a18cedac09c9cd5c354afc61cc73bc7dda50e53bfcf8e7e52734a1c", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

实现完成且验证通过，正式训练已重启，首轮日志和正式checkpoint核验通过。

wall3/wall4按handoff更新完整18/19项奖励、RSI80/0/20、abs roll终止、深度噪声/孔洞/边缘/延迟/15帧冻结、箱体质量摩擦/default角/torso COM/推扰随机化。G1的深度本体actor/critic、纯本体AMP和相机名义安装保持；手接触过滤Box，严格成功率与即时standup门控分开，全部高度相对origin。新版规范15段数据，AMP采样40/40/20不变。

动作范围专项检查发现旧clip5不能覆盖pickup深蹲。wall专属clip9覆盖最大动作8.842及默认位置偏移，scale0.25和物理关节限制不改，原CarryBox-v0与football配置不改。固定配方env contract revision6；旧完整checkpoint明确拒绝，现有warm-start迁移策略/辅助头、重建PPO/AMP/课程。

35项CPU检查PASS。4环境实际PhysX参数/offset/更新/新runner恢复/导出通过；4096环境24步、4×4 PPO/完整AMP的6+4次更新通过，热身后均值4.295秒、最慢4.318秒，50Hz全场景Warp遮挡保持。没有降低规模/频率或放宽测试。只读组合专家审查无新增阻塞。

旧PID2348537已核验身份并于21:01 JST停止，原model_4200.pt与日志保留。新版4096正式PID2448113于21:08 JST启动，run_name wall4_handoff_v6_amp15_20261014_210808；21:13 JST核验到iteration30，热身后平均4.230秒、最慢4.300秒。首个model_0.pt为schema2/revision6，15段AMP身份、4096环境、clip9、19项奖励及有限参数均核验通过。训练尚未完成，未证明搬箱子收敛或真实部署成功。详细结果与启动信息见docs/carrybox/handoff_20261014/README.md及launch.json。

正式证据：docs/carrybox/handoff_20261014/formal_health.json。早期回合较短且主要因姿态越限终止，尚无收敛结论；本次授权的修改、验证与重启已完成。
