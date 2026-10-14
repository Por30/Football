---
task_id: "carrybox-depth-v0"
language: "zh-CN"
axes: ["E", "P", "L", "D"]
risk_tier: "T2"
status: "DONE"
changed_files: ["README.md", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/smoke_carrybox.py", "scripts/rsl_rl/smoke_carrybox.sh", "tests/test_carrybox.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_state.py", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox/manifest.json", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox/pickUp/pickup1.pt", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox/pickUp/pickup2.pt", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox/pickUp/pickup3.pt", "docs/carrybox/README.md", "docs/carrybox/smoke.json", "docs/carrybox/test_receipts.json"]
task_contract_sha256: "82bc3ee5902987c33a1dcfe477ac34da90ffd743bc3462753a8587cebe67259d"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "42b17384345d730dc03d44602a42c594a91c64eaeda87caf937dda3780dbd95c", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "f01a7a1159719392a0a9b4db1ed67a69a3a26b30cdd1574d102b06bd2433d57c", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_carrybox.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "bfc09a947a1188d8a2742c446ec54a1268d07f1a789313b0ac0a48d521c77931", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# CarryBox 执行报告

已注册 `Template-Perceptual-Ball-CarryBox-v0`，新增独立真实深度环境、无特权 actor/critic、9维箱子位姿监督头和共同 PPO 优化器。源 pickUp 三片段复制到本地并记录 hash；片段仅参考归档，不用于当前训练或初始化。无搬运、放下、AMP 或踢球观测路径。

深度和标签均在同一渲染步更新，标签在 action 前随 observation 存入 rollout。支持方形箱体8种等价旋转，推理不需要任何箱子真值。物理成功要求双手过滤接触、箱体最低点离地0.12m、直立、低速连续0.5s。timeout 保存reset前历史，reset后重新渲染。

冻结测试全部PASS：5项CPU测试验证真值隔离、时序标签、梯度、对称性、坐标系、连续接触判定、PPO和checkpoint；4个RTX环境完成2次PPO更新、12个timeout、左右手物理接触探针、图像随箱子移出视野变化、checkpoint恢复和JIT/ONNX导出。接触探针使用人为相交，仅证明传感器/碰撞体接线有效，不代表正常夹持载荷。详情与回执见docs/carrybox。

未启动长期训练、未测量拾箱成功率。G1无手指，地面拾取及夹持稳定性需训练评估。只支持单设备固定学习率PPO。保留已有踢球与用户未提交修改，未提交git或修改源PhysHSI工程。额外静态编译与git diff --check通过。
