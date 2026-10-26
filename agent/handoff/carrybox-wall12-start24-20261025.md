---
task_id: "carrybox-wall12-start24-20261025"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall12-start24-20261025.md", "agent/plan/carrybox-wall12-start24-20261025.md", "agent/report/carrybox-wall12-start24-20261025.md", "agent/task/carrybox-wall12-start24-20261025.md", "docs/carrybox/wall12_start24_20261025/README.md", "docs/carrybox/wall12_start24_20261025/artifact_validation.json", "docs/carrybox/wall12_start24_20261025/attempt1/failed_launch_receipts.json", "docs/carrybox/wall12_start24_20261025/attempt1/failure.json", "docs/carrybox/wall12_start24_20261025/attempt1/handoff.md", "docs/carrybox/wall12_start24_20261025/attempt1/launch.json", "docs/carrybox/wall12_start24_20261025/attempt1/plan.md", "docs/carrybox/wall12_start24_20261025/attempt1/report.md", "docs/carrybox/wall12_start24_20261025/attempt1/source_identity.json", "docs/carrybox/wall12_start24_20261025/attempt1/task.md", "docs/carrybox/wall12_start24_20261025/check.py", "docs/carrybox/wall12_start24_20261025/check.sh", "docs/carrybox/wall12_start24_20261025/failed_launch_receipts.json", "docs/carrybox/wall12_start24_20261025/final_state.json", "docs/carrybox/wall12_start24_20261025/health.json", "docs/carrybox/wall12_start24_20261025/launch.json", "docs/carrybox/wall12_start24_20261025/preflight.json", "docs/carrybox/wall12_start24_20261025/previous_football.json", "docs/carrybox/wall12_start24_20261025/receipts.json", "docs/carrybox/wall12_start24_20261025/resource_pending_receipts.json", "docs/carrybox/wall12_start24_20261025/source_identity.json", "projects/README.md", "projects/findbox/README.md", "projects/football/README.md"]
task_contract_sha256: "8ee61caf8c094334018ada39e77f6f7b3f7b2817227b5b2560c63b226ba707aa"
tests: [{"command": "bash docs/carrybox/wall12_start24_20261025/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1e53f243e8b81ae36dedcd12a921f3c3769382640b70fa77dcca94454e31e5cb", "stdout_sha256": "f8958499ee0458c7c3ee280d6b70bbc3a8bf2823fd8e2c850d636c25ec094b8d", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

已按用户明确指令停止足球v11 PID3261150，确认进程退出和显存释放；最后日志iteration278，已保存model0及所有历史日志保留。wall12正式fresh PID3269279正在运行，4096环境×24步、20000轮、seed42、5×4和aux1.0。

2026-10-25 12:37 JST核验至iteration16，近10轮平均4.471秒、最慢4.500秒。首模型schema2/walled12 revision1正确，policy/AMP有限，联合Adam更新20次且回归头四组参数动量非零；TensorBoard位姿位置/旋转/加权损失有限，每轮辅助样本计数471040。原冻结启动检查真实执行PASS。

首个run首轮因TF32尺寸置换舍入导致空对称候选及inf而退出，未生成checkpoint。独立局部修复任务carrybox-wall12-tf32-20261025将该精确分类改用索引；44项CPU和8192样本CUDA TF32前后向通过，保持全局TF32和训练配方。本启动任务未修改生产代码，唯一生产修复归属该独立故障任务。原失败日志、启动身份和等待资源回执均保留。

任务启动与核验已完成，正式训练仍在后台进行，不能视为20000轮结束或独立成功率/位姿精度评估。精确run、日志命令和证据见docs/carrybox/wall12_start24_20261025/README.md。后续先复核实时进程和日志，不重复启动或恢复足球。
