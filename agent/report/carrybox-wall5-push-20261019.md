---
task_id: "carrybox-wall5-push-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "tests/test_carrybox_push.py", "docs/carrybox/wall5_push_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-push-20261019.md", "agent/task/carrybox-wall5-push-20261019.md", "agent/report/carrybox-wall5-push-20261019.md", "agent/handoff/carrybox-wall5-push-20261019.md"]
task_contract_sha256: "b9bd89c2a8ad26291434f7d7cfef7132f190a89b562d5e0c91f7a109a261485b"
tests: [{"command": "bash docs/carrybox/wall5_push_20261019/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8b926d7c8d674370c5862be3b9a44f6debb5b6c9b60c0893921b77fe0bfdf1c7", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_push_20261019/replay.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e2d0bab91f9ba2bdb231879742d57a0c18698d09af4eaeabde039f95ee551719", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_push_20261019/smoke.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "a29b9c7de10fb14c83c32cdcf3058820aa960b38499fb2741f7884c7ffde3050", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

本次完成wall5推扰/摩擦局部修复和用户指定的rev13三个回放条件。生产改动仅两份wall5文件：current + scale * sample、地面/default 1.0/multiply，契约revision15。保持revision14的非对称AC、全部AMP/PPO/RSI/奖励/深度/PD/几何及football/wall3/wall4行为。

rev13实际结束10637轮。model10600每组16环境×1200步旧材质回放：loco约12.84/12.68/12.70步，381个完成回合全部首次push前pitch>1.1；hold约886.47/969.53/1000步，分别9/13/15个timeout（各15个完成回合）。报告删失年龄和19200步守恒，未将短回放当训练因果或成功率。推扰影响持箱稳定，但不能解释当前loco早死；hold占90.8–92.5%样本步，提示按回合RSI比例不能代表交互步占比。

21项CPU、三组回放和4环境2＋1轮PPO/AMP更新恢复导出通过。原摩擦0.5已实测，新35形状1.0及双脚/手、物理速度set/increment/none和课程/partial IDs经PhysX读回确认。回放写后速度是Isaac缓存，实际读回在独立smoke；不夸大证据。

2026-10-19 12:08:52 JST原PID4038923仍为revision14、10779轮。未停止/重启或热改；诊断结束后轮时约4秒。revision15尚无正式训练和拾箱评估。完整结果、原始数据、hash、回执及限制见docs/carrybox/wall5_push_20261019/README.md。
