---
task_id: "carrybox-play-v6-20261015"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "HANDOFF"
status: "DONE"
changed_files: ["scripts/rsl_rl/play.py", "docs/carrybox/play_v6_20261015", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-play-v6-20261015.md", "agent/task/carrybox-play-v6-20261015.md", "agent/report/carrybox-play-v6-20261015.md", "agent/handoff/carrybox-play-v6-20261015.md"]
task_contract_sha256: "fb79a2ba969b8155168db92026a0af4bbb8009a189c1ef06cbb7ee46fdafe472"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/play_v6_20261015/check.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "ff0ca3b52ca845a788bfc583c38f6f6273a86aa20ed313c07b42031a7a985693", "stdout_sha256": "c33e5fcfaaae02b3e637d82d7ad050784a28b1b1e29d7e133d73d604484e25af", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
---

新增显式--carrybox_weights_only播放选项，复用现有warm_start校验schema/shape/finite，仅导入策略权重。默认播放的严格契约检查保持，足球分支默认行为不变；误用选项到其他runner时报错。导出写入独立exported_current_env，避免覆盖旧环境导出。

实际model_14000.pt为revision6，当前环境为revision7。CPU已验证真实模型与当前模型结构匹配、权重完整导入及默认/显式/错误runner分支。未启动GPU播放或正式训练，未停止现有训练。此命令是在修复后的当前环境播放旧策略，不是revision6环境原样复现，也不能作为原训练环境评估。

命令见docs/carrybox/play_v6_20261015/README.md。
