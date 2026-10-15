---
task_id: "carrybox-convergence-20261015"
language: "zh-CN"
axes: ["L", "E", "C"]
risk_tier: "T2"
status: "DONE"
changed_files: ["docs/carrybox/convergence_20261015", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-convergence-20261015.md", "agent/task/carrybox-convergence-20261015.md", "agent/report/carrybox-convergence-20261015.md", "agent/handoff/carrybox-convergence-20261015.md"]
task_contract_sha256: "141112bf131bd578371848414378fc7916d8623d72156c9e040681a8fc66cc32"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/convergence_20261015/analyze.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "038511bf99bd2cde8369498e99141446dd5c35d92745f56365178ef86eb665db", "stdout_sha256": "318013f7d7cab06e66563f781888a191714ea14eeeca234ae58881e0f86454a8", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/convergence_20261015/replay.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "98d783f8a60ae427269a90f78299d93ad6aa5ae745bd2e4fa25cb12b1276250b", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

完成本次不收敛诊断；没有修改生产源码、数据或checkpoint，没有停止/重启正式训练。

正式快照13691轮成功日志均值约0.0366%，不是独立成功率；之前约4秒/轮的吞吐正常。16环境3400步纯推理+200步状态探针均未更新优化器。模型13600的86个loco回合均3步倾倒，仅关闭push的77回合同样3步；保持reset角的156个loco回合平均38.70步。直接抱箱长轨迹占满有效AMP窗口，混合统计不能代表完整找箱拾取。

明确发现G1 head_link的link原点接近腰部，但奖励/终止直接把它当实际头部高度：USD头部几何位于局部z=.325–.531m，COM z=.449869m。抱箱279个有效采样中94.27%被head_origin>.8门槛拒绝。另已用实际PhysX数据和USD核验soft knee lower=.0610864，与专家抱箱两膝约-.087rad冲突：示范限位代价1.479，混合后-.02219/step，大于AMP最大+.01/step。

旧warm-start并非健康基线；继承动作std约1.58，扩大clip也改变超范围旧动作的实际目标。最新持箱策略有多关节长期饱和，原始动作最高38.31；loco未超过clip9仍倾倒，不能将clip说成唯一原因。确定性持箱AMP约.604，随机采样约.0102，正式style约.0023。无证据将失败简单归为AMP文件未加载或深度失效。

冻结两条命令均PASS，另200步探针PASS；只读组合专家完成审查。诊断期间共用GPU暂时减慢正式训练，诊断进程均已退出，正式训练继续且回到约4.15秒/轮。生产修复尚未做，建议先统一实际头部参考点及软限位一致性，再验收基础站立/接近和分阶段pickup课程；保留无特权actor/critic与数据身份，不再次盲目迁移失败checkpoint。

详见docs/carrybox/convergence_20261015/README.md。短测没有证明长期根因贡献比例或任何修复收敛；抱箱RSI不算完整拾取成功，未结束回合另记。正式日志被移入Trash，当前可用tail -n 100 -f /proc/2448113/fd/1查看。