---
task_id: "carrybox-wall12-pose-eval-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall12-pose-eval-20261026.md", "agent/plan/carrybox-wall12-pose-eval-20261026.md", "agent/report/carrybox-wall12-pose-eval-20261026.md", "agent/task/carrybox-wall12-pose-eval-20261026.md", "docs/carrybox/wall12_pose_eval_20261026/README.md", "docs/carrybox/wall12_pose_eval_20261026/analysis.log", "docs/carrybox/wall12_pose_eval_20261026/analyze.py", "docs/carrybox/wall12_pose_eval_20261026/artifact_validation.json", "docs/carrybox/wall12_pose_eval_20261026/attempt1/evaluate.py", "docs/carrybox/wall12_pose_eval_20261026/attempt1/evaluation.log", "docs/carrybox/wall12_pose_eval_20261026/attempt1/receipts.json", "docs/carrybox/wall12_pose_eval_20261026/attempt2/evaluate.py", "docs/carrybox/wall12_pose_eval_20261026/attempt2/evaluation.log", "docs/carrybox/wall12_pose_eval_20261026/attempt2/failure.txt", "docs/carrybox/wall12_pose_eval_20261026/attempt2/receipts.json", "docs/carrybox/wall12_pose_eval_20261026/check_cpu.sh", "docs/carrybox/wall12_pose_eval_20261026/evaluate.py", "docs/carrybox/wall12_pose_eval_20261026/evaluate.sh", "docs/carrybox/wall12_pose_eval_20261026/evaluation.json", "docs/carrybox/wall12_pose_eval_20261026/evaluation.log", "docs/carrybox/wall12_pose_eval_20261026/failure.txt", "docs/carrybox/wall12_pose_eval_20261026/final_state.json", "docs/carrybox/wall12_pose_eval_20261026/metrics.py", "docs/carrybox/wall12_pose_eval_20261026/receipts.json", "docs/carrybox/wall12_pose_eval_20261026/samples.npz", "docs/carrybox/wall12_pose_eval_20261026/training_analysis.json", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "886c54aed73e7aa570865188310066f09836dcf8c8c8d3357fe50ba25e851c45"
tests: [{"command": "bash docs/carrybox/wall12_pose_eval_20261026/check_cpu.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1df7e053f19e392ee328ec7cc03fb7bedd5dc4cd91a2ed0ef83a96c67a065167", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall12_pose_eval_20261026/evaluate.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c4561c70edfdda39f3053dee8eeeeaf0013020bf5eee5fd78e6dfb95b535f49", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

用户指定wall12 model19999已核验，训练日志0–19999共20000轮完整、最终权重有限。检查时无后台训练，未发送停止信号、未重启或修改生产/模型；GUI play命令已写入README。

64环境×1000步、seed12345、原噪声墙柱与随机reset的均值动作回放完成，64000配对帧保存在samples.npz。箱心位置平均误差5.63cm、中位3.60cm、P90 6.92cm、三维RMSE16.08cm；几何可见时平均4.60cm，持箱时3.84cm。对称折叠后平均旋转角误差58.10°，姿态回归仍不准确；少量不可见帧有大位置误差。预测9维位姿，未预测尺寸。

训练最后1000轮位置MSE0.010845、旋转6D MSE0.205815，分别记录而非把混合损失换算为角度。CPU单位/对称测试及真实回放两条冻结检查最终PASS；先前诊断脚本TF32参考矩阵舍入导致标签对照失败的日志保留，改用float64参考且保持原断言后通过。正式生产及checkpoint未改。

此为单seed相关帧工程诊断，不代表总体任务成功率或实机精度。所有指标、定义、限制和原始证据见docs/carrybox/wall12_pose_eval_20261026/README.md；当前没有遗留训练或评估进程。
