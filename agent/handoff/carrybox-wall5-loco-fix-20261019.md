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
artifact: "HANDOFF"
---

用户要求修复空手立即reset后从零启动4096环境wall5正式训练。本任务未达目标，状态PARTIAL；不要汇报“训练已启动”或“修复成功”。只读状态见runtime_status.json，生成时无train/play进程；原rev14进程此前已退出，旧模型保留。

当前生产5个源码已恢复到before_hashes.json逐字节一致的本次修改前revision15，包括此前非对称AC、增量push和1.0/multiply摩擦；没有git reset或清理用户工作。此次候选revision16完整隔离在candidate/及candidate.patch，新测试原字节在candidate/tests/test_carrybox_loco_fix.py.candidate。不要未经评估直接覆盖回生产。

39项CPU检查曾通过初始候选；原冻结250步物理检查三次结果为0/16、0/16、1/16存活，两次物理修正均用完。最新smoke FAIL，physical.json的RUNNING是写于断言前的原始快照；最终失败以receipts_smoke.json、physical.log和evidence_summary.json为准。limits精确float guard失败单独保存，没有放宽存活断言。PPO更新/恢复/导出和4096pilot根本未执行。

启动命令的FAIL是前置门禁阻止，没有创建正式run。候选流程脚本与历史receipts留作审计；生产已经恢复，原check.sh依赖归档测试，不能直接重跑并以缺少候选为新的修复机会。先执行frontmatter中的只读恢复命令；后续必须从本次失败边界继续做明确的闭环控制诊断，不能把同一工作改名重置预算或继续试参数。固定角度开环失败不是无法训练的证明，更不能为了启动而放宽终止条件。
