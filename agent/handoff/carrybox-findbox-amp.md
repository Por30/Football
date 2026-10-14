---
task_id: "carrybox-findbox-amp"
language: "zh-CN"
axes: ["E", "L", "S"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/carrybox_amp.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py", "tests/test_carrybox_amp.py", "scripts/rsl_rl/smoke_carrybox.py", "findbox/amp_manifest.json", "docs/carrybox/README.md", "docs/carrybox/amp/README.md", "docs/carrybox/amp/test_receipts.json", "docs/carrybox/smoke.json", "README.md"]
task_contract_sha256: "4cc8704bbac4d20a319f11ac83710f8488b22e8e28ea28c6729b83ad411c2c66"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "a9c5897233359a596b48b5bb05a55d110a6ff179def63db5025a69ab5f84205d", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_carrybox.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "bfc09a947a1188d8a2742c446ec54a1268d07f1a789313b0ac0a48d521c77931", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

# FindBox AMP Handoff

当前状态DONE，CarryBox-v0默认启用AMP。数据为仓库findbox，manifest是60Hz/xyzw/29关节顺序及hash合同，加载器位于perceptual_ball/carrybox_amp.py。训练仍只做找箱、双手抬起保持；carryWith仅提供持箱姿态先验。

稳定验证：CPU9项，4真实RTX环境，2次PPO/pose/AMP更新与12个timeout，终止AMP缓存、fresh history、AMP参数改变、checkpoint/optimizer和策略导出全部通过。见docs/carrybox/amp/README.md及test_receipts.json。当前无长期训练进程。

用户授权后可在既有IsaacLab环境启动：`python scripts/rsl_rl/train.py --task Template-Perceptual-Ball-CarryBox-v0 --num_envs 128 --device cuda:0 --headless --enable_cameras --max_iterations 30000 --seed 42 --run_name depth_pose_amp_scratch`。脚本沿用默认AMP配置。训练恢复严格校验schema2、奖励契约与dataset metadata；play/export不读取动作库。不要把smoke_model.pt当作已学会拾箱的模型。

actor/critic继续只有proprio/perception；AMP64维全部为本体量，pose标签只进监督。需修改schema/组权重/奖励契约时新开训练；原无AMP schema1无法直接作为完整训练状态恢复。继续保留其他未提交修改。
