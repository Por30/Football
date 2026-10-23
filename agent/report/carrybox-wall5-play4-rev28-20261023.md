---
task_id: "carrybox-wall5-play4-rev28-20261023"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-rev28-20261023.md", "agent/plan/carrybox-wall5-play4-rev28-20261023.md", "agent/report/carrybox-wall5-play4-rev28-20261023.md", "agent/task/carrybox-wall5-play4-rev28-20261023.md", "docs/carrybox/wall5_play4_rev28_20261023/README.md", "docs/carrybox/wall5_play4_rev28_20261023/analyze.log", "docs/carrybox/wall5_play4_rev28_20261023/analyze_behavior.py", "docs/carrybox/wall5_play4_rev28_20261023/artifact_validation.json", "docs/carrybox/wall5_play4_rev28_20261023/behavior.json", "docs/carrybox/wall5_play4_rev28_20261023/camera_trajectory.json", "docs/carrybox/wall5_play4_rev28_20261023/finish.py", "docs/carrybox/wall5_play4_rev28_20261023/formal_status.json", "docs/carrybox/wall5_play4_rev28_20261023/receipts.json", "docs/carrybox/wall5_play4_rev28_20261023/record.log", "docs/carrybox/wall5_play4_rev28_20261023/record.py", "docs/carrybox/wall5_play4_rev28_20261023/record_and_check.sh", "docs/carrybox/wall5_play4_rev28_20261023/recording.json", "docs/carrybox/wall5_play4_rev28_20261023/selection.json", "docs/carrybox/wall5_play4_rev28_20261023/trajectory.json", "docs/carrybox/wall5_play4_rev28_20261023/verify.log", "docs/carrybox/wall5_play4_rev28_20261023/verify.py", "docs/carrybox/wall5_play4_rev28_20261023/video_validation.json", "docs/carrybox/wall5_play4_rev28_20261023/visual_review.txt", "outputs/carrybox/wall5_play4_rev28_20261023/README.md", "outputs/carrybox/wall5_play4_rev28_20261023/contact_sheet.jpg", "outputs/carrybox/wall5_play4_rev28_20261023/frame_0001.png", "outputs/carrybox/wall5_play4_rev28_20261023/frame_0025.png", "outputs/carrybox/wall5_play4_rev28_20261023/frame_0050.png", "outputs/carrybox/wall5_play4_rev28_20261023/frame_0125.png", "outputs/carrybox/wall5_play4_rev28_20261023/frame_0250.png", "outputs/carrybox/wall5_play4_rev28_20261023/frame_0375.png", "outputs/carrybox/wall5_play4_rev28_20261023/frame_0499.png", "outputs/carrybox/wall5_play4_rev28_20261023/frame_0500.png", "outputs/carrybox/wall5_play4_rev28_20261023/initial_scene.png", "outputs/carrybox/wall5_play4_rev28_20261023/wall5_rev28_model1200_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "8fb1fc781ac009476202ee598891cca8c91979fc0168eaba4c476dc66ecce9d0"
tests: [{"command": "bash docs/carrybox/wall5_play4_rev28_20261023/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "657fcbb4e7b910925d05c0f36e63bd504af375597f0c154089f64271e8fea1f8", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

rev28 model_1200，4机器人同步20秒，1080p/25fps、高位镜头。固定来源为默认/loco/loco/hold，reset次数[1, 1, 1, 1]；保留全部失败回合。

已检查关键帧拼图、10秒和19.96秒原始画面，并核对逐步轨迹与回合终止记录。4个环境均跑满20秒，只在第1000步超时重置；未出现倾倒、头/骨盆过低或其他提前终止。

三个空手起点未出现手与箱子的接触，地面箱子未被抬起。默认起点的骨盆到箱子水平距离由0.899m变为1.085m；两个loco起点分别由1.407m降至1.023m、1.435m降至0.865m，随后画面中主要保持站姿，尚未形成完整的接近、下蹲、抓取流程。

hold起点在初始化时已抱着箱子，录像中保持双手接触（999个非reset采样中991个双手接触），箱底离地最低0.613m、末尾0.655m；这不能算从地面搬起。本段没有任务成功标记，也没有pickup来源环境。

这次为revision28第1200轮、关闭相机噪声且推扰课程尚未开始的单次回放。四格角标显示实际actor深度；背景、身体和箱子遮挡仍保留。本次未采集200Hz抖动指标，也未与旧模型采用相同初态和课程做对照，不能据此量化抖动是否改善或推断总体成功率。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev28_20261023/wall5_rev28_model1200_4robots_high20s.mp4。严格加载、完整解码及关键帧检查通过；正式训练和生产源码保持。没有待恢复工作，后续录像新建目录。
