---
task_id: "carrybox-findbox-amp"
language: "zh-CN"
axes: ["E", "L", "S"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/carrybox_amp.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py", "tests/test_carrybox_amp.py", "scripts/rsl_rl/smoke_carrybox.py", "findbox/amp_manifest.json", "docs/carrybox/README.md", "docs/carrybox/amp/README.md", "docs/carrybox/amp/test_receipts.json", "docs/carrybox/smoke.json", "README.md"]
task_contract_sha256: "4cc8704bbac4d20a319f11ac83710f8488b22e8e28ea28c6729b83ad411c2c66"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "a9c5897233359a596b48b5bb05a55d110a6ff179def63db5025a69ab5f84205d", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_carrybox.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "bfc09a947a1188d8a2742c446ec54a1268d07f1a789313b0ac0a48d521c77931", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# FindBox AMP 执行报告

已将用户指定findbox直接接入CarryBox默认训练：17段/4628帧，行走/拾起/持箱按40/40/20%平衡采样。原始文件未修改，新增manifest冻结60Hz、xyzw、原关节顺序及hash。源文件与PhysHSI同名数据字节一致，schema有源配置依据。

新增64维本体AMP帧/10帧窗口、60→50Hz片段内重采样，按joint_names对齐当前G1。专家角速度处理q/-q，速度逐片段差分。不读取box/末端/根位置/根线速度，不增加actor/critic输入，不改变找箱与拾起流程。

复用AMP判别器，独立优化器训练，完整窗口按0.75*任务奖励+0.25*2*dt*风格奖励混合；未满窗口保持原任务奖励。terminal窗口在reset前截取，评分/训练使用同一缓存，reset清除对应历史。schema2保存AMP、统计量、优化器和数据身份，训练时lazy校验数据，推理不依赖数据。

冻结CPU9项与4环境RTX集成测试全部PASS。两次更新使用32/52个完整运动窗口、触发12个timeout，断言AMP参数实际更新；checkpoint含优化器恢复，JIT/ONNX输出一致。另完成compileall与git diff --check。测试开发中修复了mock定位和inference_mode测试上下文，未放宽断言；冻结回执见docs/carrybox/amp/test_receipts.json。

未运行长期训练，不能声称拾箱成功率或动作自然度已提升。新的AMP模型不能直接恢复之前无AMP的schema1状态。用户原有其他修改、源PhysHSI项目和findbox原始片段保持不变。
