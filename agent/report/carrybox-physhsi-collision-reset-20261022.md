---
task_id: "carrybox-physhsi-collision-reset-20261022"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-physhsi-collision-reset-20261022.md", "agent/plan/carrybox-physhsi-collision-reset-20261022.md", "agent/report/carrybox-physhsi-collision-reset-20261022.md", "agent/task/carrybox-physhsi-collision-reset-20261022.md", "docs/carrybox/physhsi_collision_reset_20261022/README.md", "docs/carrybox/physhsi_collision_reset_20261022/artifact_validation.json", "docs/carrybox/physhsi_collision_reset_20261022/audit.json", "docs/carrybox/physhsi_collision_reset_20261022/audit.py", "docs/carrybox/physhsi_collision_reset_20261022/process_status.json", "docs/carrybox/physhsi_collision_reset_20261022/receipts.json", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "53630b5e42753d152381c7286aedd56901fd2b636a9ea4fc66a5e98cf633df43"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/physhsi_collision_reset_20261022/audit.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "790f51593d4a090818101729ea5111d6fbb6068fba42c1c81c35bac514136b4b", "stdout_sha256": "b54cb3bec2fa2c1f83a6d0c5808e1616b8eb13ee00ab00dc92becbd3b65ab5fd", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

已完成本地PhysHSI G1 carrybox/carrybox_resume与wall5 revision23的只读比较。完整来源、公式、形状和数据证据见 docs/carrybox/physhsi_collision_reset_20261022/README.md 与 audit.json。

碰撞：两边均开启自碰撞，但PhysHSI使用原始28个带碰撞link/30形状；wall5补全为35形状，尤其pelvis根凸包、膝/肩视觉外壳使接触范围增大。PhysHSI collision奖励没有注册；wall5髋膝净接触惩罚会计入自接触。两边都没有启用接触力直接reset，碰撞仍可通过姿态/高度越界间接触发。

Reset：PhysHSI 20%默认、80% RSI，归一化技能权重后全部reset的loco/pickup/carry比例为53.33/13.33/13.33%。参考根六维速度最终被±0.2随机值覆盖，关节速度保留；默认根速度则±0.5。当前wall5全RSI、固定75/5/20，pickup仍只抽地面03的0–31帧；保留参考速度，11段hash一致的loco源平均水平速度0.743m/s。PhysHSI动作延迟按物理步更新0–20ms，reset角填充队列；wall5无该动作队列。

终止：roll0.5/pitch1.1一致；PhysHSI mid360<0.6m、root<0.2m，与wall5 head_link COM<0.4387m、root<0.2311m测量点/阈值不同。PhysHSI另有hip_yaw低高及箱子速度终止；计算但未并入reset的gravity标记不生效，成功也不立即reset。

CPU审计PASS，来源hash复核未变；本次未启动PhysHSI仿真，不能声称已测其实际接触峰值或训练效果。正式PID1588407检查时仍运行，本次未改生产源码/资产/数据、未操作训练生命周期。已有未提交工作保持。
