---
task_id: "carrybox-wall5-rev17-comparison-20261023"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "NO_CODE_CHANGE"
changed_files: ["agent/handoff/carrybox-wall5-rev17-comparison-20261023.md", "agent/plan/carrybox-wall5-rev17-comparison-20261023.md", "agent/report/carrybox-wall5-rev17-comparison-20261023.md", "agent/task/carrybox-wall5-rev17-comparison-20261023.md", "docs/carrybox/wall5_rev17_comparison_20261023/README.md", "docs/carrybox/wall5_rev17_comparison_20261023/artifact_validation.json", "docs/carrybox/wall5_rev17_comparison_20261023/attempt1_receipts.json", "docs/carrybox/wall5_rev17_comparison_20261023/check.py", "docs/carrybox/wall5_rev17_comparison_20261023/comparison.json", "docs/carrybox/wall5_rev17_comparison_20261023/receipts.json", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "f875e6baf418547f01dff90ef0c0dffb0c1dfeb793ed9b409878209c6fcb81b6"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_rev17_comparison_20261023/check.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "bcc0a5f7c5b1d9adeeefe9925ba7f31234cfbb0ba28ffb9c54e3aefea7e8c2a3", "stdout_sha256": "8d91277bd08ca0d006f36aa49cda3f603dc34c98e4e901082fa807540ff237c7", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

只读确认指定2026-10-20录像为rev17 model2800，当前为rev28 fresh；核对checkpoint、run参数及8份历史源码hash。奖励稳定项/近箱逻辑、RSI与动作延迟、碰撞、深度单位/噪声、critic/辅助监督、专家片段不同；PPO、AMP混合与特征、PD和力矩惩罚不变。未修改生产或重启，未作因果消融。

详见 docs/carrybox/wall5_rev17_comparison_20261023/README.md 和 comparison.json。当前配置采样使用model4800，不称为最新模型；旧视频只有一个loco回合，不能当作总体成功率。检查阶段正式PID2266428保持运行。没有待恢复进程；后续修改需按用户新任务执行。

2026-10-23 23:25 JST再次只读核对：wall5配置及实现仍为rev28；正式启动快照涉及文件中仅共享任务注册文件变化，新增独立wall10注册，wall5注册未变。原训练PID2266428已不存在，本机未发现train.py进程；日志最后为5739轮（23:15:49），最新保存model_5600.pt。日志末尾没有异常堆栈，不能确定退出原因。本次没有停止或重启训练。此前22:58仍运行的记录是历史快照。
