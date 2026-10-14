---
task_id: "carrybox-wall4-convergence"
language: "zh-CN"
axes: ["E", "L", "A"]
risk_tier: "T2"
status: "DONE"
changed_files: ["README.md", "agent/handoff/carrybox-wall4-convergence.md", "agent/plan/carrybox-wall4-convergence.md", "agent/report/carrybox-wall4-convergence.md", "agent/task/carrybox-wall4-convergence.md", "docs/carrybox/convergence_20261014/README.md", "docs/carrybox/convergence_20261014/reference_action_coverage.json", "docs/carrybox/convergence_20261014/rollout_audit.json", "docs/carrybox/convergence_20261014/rollout_audit.log", "docs/carrybox/convergence_20261014/test_receipts.json", "docs/carrybox/convergence_20261014/training_analysis.json", "docs/carrybox/convergence_20261014/training_curve.csv", "docs/carrybox/convergence_20261014/training_curve.png", "docs/carrybox/walled/README.md", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/status.before_user_stop_20261014.json", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/status.json", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/train.log", "projects/README.md", "projects/findbox/README.md", "scripts/analyze_carrybox_training.py", "scripts/rsl_rl/audit_carrybox_convergence.py", "scripts/rsl_rl/audit_carrybox_convergence.sh", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_convergence.py"]
task_contract_sha256: "1bc3eb68ea4de80d01c7a3de3e63c6dec1065a056d0ee58be2c6448aaf46131b"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "c2021b0b5abcd53782def2f4fbc702610e167442439d2ef31fafe17522c299d8", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python scripts/analyze_carrybox_training.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "01410559921711c5ff346e02bc81c455ad2349ea1130c06901aee4e1c154e22f", "stdout_sha256": "8557ebecbbc2711ba40a033fcc0ea6d41522fb5594092d642ae241101a8993f3", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/audit_carrybox_convergence.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "c5711938761a34c41fca73ba1f24613cfed402cc03b960f83fcafd2797b94e6e", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

已完成停止、根因诊断、确定bug的最小修复及当前任务设计说明。不是训练收敛完成。正式wall4 PID2307414和等待器2300674在核验身份后停止；最后完整iteration14695，整个run及model_14600.pt保留，状态STOPPED_BY_USER。没有新PPO/AMP训练更新，没有自动恢复。

确定根因：本机IsaacLab termination manager保留最近回合term标记，原is_terminated_term错误地在正常alive步读取历史fell/tipped，从一次跌倒后持续每步处罚-.2。代码审计、曲线和真实同轨迹新旧奖励对照一致。wall3/wall4使用局部failure_event，将历史named flags与当前terminated及非timeout相与，一次失败只处罚一次；环境契约revision=4、schema仍2。未改系统IsaacLab、足球或基线CarryBox-v0。旧基线同类reward接口风险不在本次修改范围，不能宣称基线学习目标已修复。

正式曲线前50轮平均31.12步，最后1000轮2.11步；奖励-6.21→-.438反映缩短受罚回合而非学会拾箱。10帧AMP需reset后9步，最后1000轮64.4%迭代无有效AMP样本，成功统计全部为0。辅助损失下降不能证明任务进步。

五组16环境各240步纯推理回放：default target41.70步、hold reset43.01步、model0为41.37步、model200为3.77步、model14600为2.10步且AMP窗口0。默认目标同轨迹旧公式对2967个正常步漏罚，新公式为0；86次真实失败对应-17.2，旧公式-610.6。全部21项CPU、离线曲线统计、真实回放及日志检查通过。仅验证奖励修复和退化现象，未验证新训练收敛。

另确认动作范围不匹配：qtarget=qdefault+.25*clip(action,±5)，pickup1/2/3分别20.83%、29.78%、49.61%帧至少1关节目标不可表达；max required action7.66/8.84/8.62。关节名字映射正确；本轮未同时改变控制范围/PD或奖励权重。后续需对齐参考与目标范围、核验基础站稳行走和拾取，再分阶段训练。没有X2父任务源码和启动配置，已异步询问用户路径；当前仅按说明移植附加项，本地基础奖励/无特权critic/从头训练与X2成功流程不能认作完全等价。

完整任务设计、指标定义、限制及后续顺序在docs/carrybox/convergence_20261014/README.md；曲线PNG/CSV、action coverage、rollout JSON及冻结回执均已保存。项目入口、总看板和根README已更新为停止待诊断后续验证，不保留当前正在排队/训练的错误状态。

最新用户停止指令覆盖此前自动串行启动意图。不要启动旧队列或resume model_14600。先查看status.json和本次审计，等待用户对后续修复/训练的指令。reward契约已变化，旧checkpoint直接resume应拒绝；纯回放脚本显式仅加载policy权重，不能复制为训练恢复捷径。若用户提供X2路径，优先核对父奖励、训练初始化/AMP窗口、动作范围与PD，不据任务名字推测已预训练。
