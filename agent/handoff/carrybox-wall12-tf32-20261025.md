---
task_id: "carrybox-wall12-tf32-20261025"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall12-tf32-20261025.md", "agent/plan/carrybox-wall12-tf32-20261025.md", "agent/report/carrybox-wall12-tf32-20261025.md", "agent/task/carrybox-wall12-tf32-20261025.md", "docs/carrybox/wall12_start24_20261025/tf32_fix/README.md", "docs/carrybox/wall12_start24_20261025/tf32_fix/artifact_validation.json", "docs/carrybox/wall12_start24_20261025/tf32_fix/check_cpu.sh", "docs/carrybox/wall12_start24_20261025/tf32_fix/check_cuda.sh", "docs/carrybox/wall12_start24_20261025/tf32_fix/cpu.log", "docs/carrybox/wall12_start24_20261025/tf32_fix/cuda.log", "docs/carrybox/wall12_start24_20261025/tf32_fix/receipts.json", "docs/carrybox/wall12_start24_20261025/tf32_fix/source_identity.json", "source/perceptual_ball/perceptual_ball/carrybox_wall12.py", "tests/test_carrybox_wall12_tf32.py"]
task_contract_sha256: "5fabb19bb3cfe96a361b059557486b30cc60e2d79097e0fbba4156ba26177dd1"
tests: [{"command": "bash docs/carrybox/wall12_start24_20261025/tf32_fix/check_cpu.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "25e8a82dbba1eaf38bbd531089f58a5c8ef588471e44330fb9a411b4b4c30e38", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall12_start24_20261025/tf32_fix/check_cuda.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "b0211f26bfb772da81fb197b6008807a4a4858d7ac6f48367cece6150e449204", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

已修复wall12正式首轮非有限损失的局部原因：8192行TF32矩阵乘法使尺寸对称判定误排全部候选。尺寸轴置换改用精确索引，其他训练语义、共享代码和全局TF32开关不变。44项CPU及新增CUDA92/8192行、TF32开关与有限前后向检查通过；旧表达式在同卡8192行TF32复现8192个空候选，修复后0个。

本子任务数值修复完成，实际4096正式启动验收由carrybox-wall12-start24-20261025继续；不得据此声称训练收敛。失败run保留，精确证据和修改说明见docs/carrybox/wall12_start24_20261025/tf32_fix/README.md。
