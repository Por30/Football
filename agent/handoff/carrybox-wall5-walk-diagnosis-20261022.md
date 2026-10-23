---
task_id: "carrybox-wall5-walk-diagnosis-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-walk-diagnosis-20261022.md", "agent/plan/carrybox-wall5-walk-diagnosis-20261022.md", "agent/report/carrybox-wall5-walk-diagnosis-20261022.md", "agent/task/carrybox-wall5-walk-diagnosis-20261022.md", "docs/carrybox/wall5_walk_diagnosis_20261022/README.md", "docs/carrybox/wall5_walk_diagnosis_20261022/artifact_validation.json", "docs/carrybox/wall5_walk_diagnosis_20261022/check.sh", "docs/carrybox/wall5_walk_diagnosis_20261022/evidence.png", "docs/carrybox/wall5_walk_diagnosis_20261022/off.json", "docs/carrybox/wall5_walk_diagnosis_20261022/off.log", "docs/carrybox/wall5_walk_diagnosis_20261022/on.json", "docs/carrybox/wall5_walk_diagnosis_20261022/on.log", "docs/carrybox/wall5_walk_diagnosis_20261022/plot.py", "docs/carrybox/wall5_walk_diagnosis_20261022/process_status.json", "docs/carrybox/wall5_walk_diagnosis_20261022/receipts.json", "docs/carrybox/wall5_walk_diagnosis_20261022/replay.py", "docs/carrybox/wall5_walk_diagnosis_20261022/rev22_curve.json", "docs/carrybox/wall5_walk_diagnosis_20261022/rev23_curve.json", "docs/carrybox/wall5_walk_diagnosis_20261022/selection.json", "docs/carrybox/wall5_walk_diagnosis_20261022/summary.json", "docs/carrybox/wall5_walk_diagnosis_20261022/training_trends.json", "docs/carrybox/wall5_walk_diagnosis_20261022/verify.py", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "34b53881e24180b03356697e12ad1802794be6e95f6da4a1e6587f216168a00d"
tests: [{"command": "bash docs/carrybox/wall5_walk_diagnosis_20261022/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2e3bc223b99c31b806c2738862d136394c285dc8cc2cfcc051ff274cf82c5486", "stdout_sha256": "2bccd0a3591d0c1ec0c666e0fdd1d3fb1cdf141fcf8e492df767ef06aefdc789", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

revision23行走退化只读诊断：24个空手首回合，当前model6200关闭推扰/自碰撞仍约0.74秒倾倒；旧model6400在新自碰撞场景平均15.91秒、18/24跑满20秒。确认髋膝净接触惩罚计入自碰撞，新版近箱收益与抓取过渡不足，动作轨迹主动失稳；未将AMP或自碰撞认定为唯一训练根因。8组回放执行与身份检查通过，未修改生产源码或重启训练。

证据与局限：docs/carrybox/wall5_walk_diagnosis_20261022/README.md。模型6200及旧6400、82个生产源码hash未变；seed42/均值动作首回合诊断，无重新训练对照，不能量化三段AMP改变的独立作用。所有192个首回合完整结束。

后续应审计动态自接触/计分并改善稳定接近到伸手的奖励，再短训验收行走不退化；本轮未修改生产配置，正式PID1588407继续。既有诊断产物不可覆盖，没有待恢复执行。
