---
task_id: "carrybox-wall5-loco-fix-20261019"
language: "zh-CN"
axes: ["E", "C", "L"]
risk_tier: "T2"
status: "PARTIAL"
changed_files: ["docs/carrybox/wall5_loco_fix_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-loco-fix-20261019.md", "agent/task/carrybox-wall5-loco-fix-20261019.md", "agent/report/carrybox-wall5-loco-fix-20261019.md", "agent/handoff/carrybox-wall5-loco-fix-20261019.md"]
task_contract_sha256: "8a9e58a3482cff10ef23b61b00408fb4323bcfa64c65499bd2b49040eac440db"
tests: [{"command": "bash docs/carrybox/wall5_loco_fix_20261019/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "4043df2e84b2600d8d790f622f956fcdb90789c72d3323682670864b79e92747", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_loco_fix_20261019/smoke.sh", "result": "FAIL", "exit_code": 1, "executed": true, "receipt_sha256": "785d2d214f46d28b31a266ee44f1fe484b9aa861347a7f2271dc2334274806a1", "stdout_sha256": "5b5219954d38b8245d6083467c9471169a66e4dd94a1a76bacdbdf21758a9ee6", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_loco_fix_20261019/launch.sh", "result": "FAIL", "exit_code": 1, "executed": true, "receipt_sha256": "0ca634f5fd32d7cd199c8b17e3877783459533c51195c121c9eb29a63805e00a", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "a7813590d42413401bb4d3cfb2b0525cd640b579827c1b0e84f3850f712f2f6d", "runner": "run_engineering_tests.py"}]
resume_command: "cat /home/cao/perceptual_ball/docs/carrybox/wall5_loco_fix_20261019/README.md"
artifact: "REPORT"
---

本次修复与正式重启未完成。固定技能环境配额、静止起点课程、策略均值物理范围惩罚/std上限候选通过39项CPU检查，但没有通过冻结物理验收。20环境中16个loco零动作、零初速保持250步：初始0/16存活；只改踝PD后0/16；再配对中立腿姿后1/16。最终15个失败环境首结束106–195步（2.12–3.90秒），踝力矩峰值32.55Nm、未达到35Nm上限。不能据此证明PPO无法学会平衡或资产必然错误。

两次物理修正预算用完，停止试参；限位精确比较导致的前置失败与后续实际物理失败分别保留。smoke中的PPO更新/恢复/导出及4096性能pilot均未执行。launch冻结命令实际执行但被前置FAIL门禁拦截，没有创建训练进程、run或checkpoint。此FAIL不是正式训练启动后崩溃。未测得候选正式轮时或收敛效果。

候选5个源码、新增测试、diff及全部失败证据保存在docs/carrybox/wall5_loco_fix_20261019。5个生产文件已按before_hashes.json逐字节恢复本次修改前revision15，保留用户此前未提交更改；未采用的新增测试原字节移入候选归档，不改变断言。CPU回执对应撤回前的候选逻辑，不能声称恢复后源码或最终PD参数重新通过39项检查。actor深度/本体与独立108维critic、现有80/0/20 RSI、AMP数据、旧模型均保留。项目入口及总看板记录未完成、未启动。

恢复命令仅用于读证据；本任务两次修正次数不能通过重命名任务或重跑脚本重置。下一步需要有明确范围的G1闭环站立/移动控制适配诊断，先审阅当前静态保持验收的适用范围、真实关节响应/支撑与候选方案，再决定后续实现。当前源码revision15也尚未正式训练，不是已修复版本。
