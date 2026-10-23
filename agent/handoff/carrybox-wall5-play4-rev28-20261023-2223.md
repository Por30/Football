---
task_id: "carrybox-wall5-play4-rev28-20261023-2223"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-rev28-20261023-2223.md", "agent/plan/carrybox-wall5-play4-rev28-20261023-2223.md", "agent/report/carrybox-wall5-play4-rev28-20261023-2223.md", "agent/task/carrybox-wall5-play4-rev28-20261023-2223.md", "docs/carrybox/wall5_play4_rev28_20261023_2223/README.md", "docs/carrybox/wall5_play4_rev28_20261023_2223/analyze.log", "docs/carrybox/wall5_play4_rev28_20261023_2223/analyze_behavior.py", "docs/carrybox/wall5_play4_rev28_20261023_2223/artifact_validation.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/behavior.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/camera_trajectory.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/finish.py", "docs/carrybox/wall5_play4_rev28_20261023_2223/formal_status.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/receipts.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/record.log", "docs/carrybox/wall5_play4_rev28_20261023_2223/record.py", "docs/carrybox/wall5_play4_rev28_20261023_2223/record_and_check.sh", "docs/carrybox/wall5_play4_rev28_20261023_2223/recording.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/selection.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/trajectory.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/verify.log", "docs/carrybox/wall5_play4_rev28_20261023_2223/verify.py", "docs/carrybox/wall5_play4_rev28_20261023_2223/video_validation.json", "docs/carrybox/wall5_play4_rev28_20261023_2223/visual_review.txt", "outputs/carrybox/wall5_play4_rev28_20261023_2223/README.md", "outputs/carrybox/wall5_play4_rev28_20261023_2223/contact_sheet.jpg", "outputs/carrybox/wall5_play4_rev28_20261023_2223/frame_0001.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/frame_0025.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/frame_0050.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/frame_0125.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/frame_0250.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/frame_0375.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/frame_0499.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/frame_0500.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/initial_scene.png", "outputs/carrybox/wall5_play4_rev28_20261023_2223/wall5_rev28_model4800_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "dc839075386b2d0ebada8f06993c0c2c410e26a557716d640994ce0be581deab"
tests: [{"command": "bash docs/carrybox/wall5_play4_rev28_20261023_2223/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "f30f169b86148a766dd8981cd3b73766445fca3e53c966870951e327b55e6e45", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

rev28 model_4800，4机器人同步20秒，1080p/25fps、高位镜头。固定来源为默认/loco/loco/hold，reset次数[1, 1, 1, 1]；保留全部失败回合。

已检查0.04、1、2、5、10、15、19.96、20秒关键帧拼图，以及2、15、19.96秒原始四宫格，并核对逐步轨迹。4台机器人均跑满20秒，唯一reset是第1000步超时；没有倾倒、头/骨盆过低或其他提前终止。

两个loco起点向箱子靠近，骨盆到箱子的水平距离分别由1.407m降至0.826m、1.435m降至0.736m，过程最近为0.668m、0.643m。画面能看到右上机器人朝箱子伸出一只手，但三个空手起点的2997个非reset控制步样本均没有手箱接触；地面箱底最大离地仅5.45mm，没有抓取抬箱。默认站立起点距离由0.899m变为0.871m，主要保持站立。不能将靠近或伸手当作完整拾箱成功。

hold起点初始化时已抱着箱子，999个非reset采样中994个双手接触，箱底离地最低0.622m、末尾0.675m；这段保持不能算从地面搬起。本段没有任务成功标记，也没有pickup来源环境。

录像固定选取时最新完整revision28 model_4800.pt，采用该轮yaw课程4.8°、推扰强度0，保留自碰撞、障碍遮挡和动作延迟。人工相机噪声关闭，深度角标来自实际actor输入。单seed四环境只反映本段表现；未进行同初态同课程的旧模型对照，也没有200Hz抖动指标，不能量化抖动改善或推断总体成功率。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev28_20261023_2223/wall5_rev28_model4800_4robots_high20s.mp4。严格加载、完整解码及关键帧检查通过；正式训练和生产源码保持。没有待恢复工作，后续录像新建目录。
