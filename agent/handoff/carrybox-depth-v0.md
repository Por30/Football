---
task_id: "carrybox-depth-v0"
language: "zh-CN"
axes: ["E", "P", "L", "D"]
risk_tier: "T2"
status: "DONE"
changed_files: ["README.md", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/smoke_carrybox.py", "scripts/rsl_rl/smoke_carrybox.sh", "tests/test_carrybox.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_state.py", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox/manifest.json", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox/pickUp/pickup1.pt", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox/pickUp/pickup2.pt", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox/pickUp/pickup3.pt", "docs/carrybox/README.md", "docs/carrybox/smoke.json", "docs/carrybox/test_receipts.json"]
task_contract_sha256: "82bc3ee5902987c33a1dcfe477ac34da90ffd743bc3462753a8587cebe67259d"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "42b17384345d730dc03d44602a42c594a91c64eaeda87caf937dda3780dbd95c", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "f01a7a1159719392a0a9b4db1ed67a69a3a26b30cdd1574d102b06bd2433d57c", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_carrybox.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "bfc09a947a1188d8a2742c446ec54a1268d07f1a789313b0ac0a48d521c77931", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

# CarryBox Handoff

稳定状态：独立CarryBox任务实现及冻结验证完成，状态DONE。环境/位姿标签位于carrybox_env_cfg.py与mdp/carrybox.py，学习与checkpoint位于rsl_rl_extensions/carrybox.py；所有入口、路径与命令见docs/carrybox/README.md。

后续如用户授权训练，在IsaacLab环境运行：`python scripts/rsl_rl/train.py --task Template-Perceptual-Ball-CarryBox-v0 --num_envs 128 --device cuda:0 --headless --enable_cameras --max_iterations 30000 --seed 42 --run_name depth_pose_scratch`。当前无在运行的训练。不要把docs/carrybox/smoke_model.pt当作已训练拾箱策略；它只经过2次短PPO更新。新模型不能加载踢球checkpoint。

框架不依赖PhysHSI绝对路径；数据manifest只记录来源。pickUp已归档但尚未接入AMP/行为克隆。actor/critic只接受proprio与perception，辅助标签只进入loss。真实传感器geometry/contact probe已验证，成功率和大规模训练资源仍待评估。已有无关工作区修改必须保留。
