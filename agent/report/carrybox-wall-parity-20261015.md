---
task_id: "carrybox-wall-parity-20261015"
language: "zh-CN"
axes: ["E", "L", "C"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "tests/test_carrybox_x2.py", "tests/test_carrybox_walled.py", "tests/test_carrybox_wall_parity.py", "docs/carrybox/wall_parity_20261015", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall-parity-20261015.md", "agent/task/carrybox-wall-parity-20261015.md", "agent/report/carrybox-wall-parity-20261015.md", "agent/handoff/carrybox-wall-parity-20261015.md", "tests/test_carrybox_queue.py"]
task_contract_sha256: "ab73b47c2a4fc673fb72dcbc1eaaa60770bedcbf9c48d1f533613483abfa5601"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "3bbe0b51c67194aba7504e346564433a363142ef311096d22c6062dd8cf1aee5", "stderr_sha256": "46ce5bee3e1f432fc639dab17720903a2b7b70af9e1d7051fe3a974ff4cd7db8", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall_parity_20261015/validate.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e88d18fd6908f2f6d59700f97849777380c19765dfeb26992f924ba3243a6ec8", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

已完成用户要求的公共修复与场景区分。wall3默认为一面墙，wall4为同一面墙加3圆柱；该划分是已告知、未收到额外选择的默认方案。配置逐项比较仅剩场景字段和任务/日志身份差异。

共享修复：实际头部COM高度用于奖励/终止；双膝下限惩罚采用真实物理下限，其他soft limits保留；位置动作目标按解析关节的hard limits裁剪。RSI统一60/30/10，搜索2%、分段yaw课程、推扰1000轮预热/4000轮渐增、初始std=.2与entropy=.001。按技能统计完成回合、真实执行步数、成功/倾倒和可形成完整AMP窗口的步数，独立于runner随机timeout年龄。数据、深度位置/遮挡/扰动、无特权输入和辅助监督边界保留。

41项CPU检查通过；两任务各4环境实际几何碰撞/深度遮挡、三技能初始化、3次PPO/AMP更新及恢复后1次更新、JIT/ONNX导出通过，AMP确有更新且参数有限。GPU通过之后的最终改动仅修正统计步数，CPU新增随机timeout年龄与部分reset回归；未为该纯统计变更重复GPU测试。旧mock字段遗漏和一次测试缩进失败均保留原回执，最终回执注明来源。源码hash和验证模型仅作为工程证据。

schema2/revision7拒绝旧revision6完整resume。正式wall3命令为4096环境从头训练，不采用旧失败模型。尚未启动新版正式训练或验证长期收敛，也没有新版4096耗时实测。PID2448113旧wall4仍使用revision6；先停止旧训练释放显存，再执行文档命令。本次未停止或重启任何正式训练。未改足球、共享资产和公共训练接口。

详细设计、证据和可复制命令见docs/carrybox/wall_parity_20261015/README.md。下一步是用户执行正式wall3训练，并按loco/pickup/hold分别监控；不能把直接抱箱RSI成功作为完整找箱拾取成功。
