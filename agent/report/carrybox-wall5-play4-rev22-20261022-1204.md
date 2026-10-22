---
task_id: "carrybox-wall5-play4-rev22-20261022-1204"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-rev22-20261022-1204.md", "agent/plan/carrybox-wall5-play4-rev22-20261022-1204.md", "agent/report/carrybox-wall5-play4-rev22-20261022-1204.md", "agent/task/carrybox-wall5-play4-rev22-20261022-1204.md", "docs/carrybox/wall5_play4_rev22_20261022_1204/README.md", "docs/carrybox/wall5_play4_rev22_20261022_1204/analyze.py", "docs/carrybox/wall5_play4_rev22_20261022_1204/artifact_validation.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/behavior.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/camera_trajectory.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/finish.py", "docs/carrybox/wall5_play4_rev22_20261022_1204/formal_status.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/receipts.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/record.log", "docs/carrybox/wall5_play4_rev22_20261022_1204/record.py", "docs/carrybox/wall5_play4_rev22_20261022_1204/record_and_check.sh", "docs/carrybox/wall5_play4_rev22_20261022_1204/recording.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/selection.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/trajectory.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/verify.log", "docs/carrybox/wall5_play4_rev22_20261022_1204/verify.py", "docs/carrybox/wall5_play4_rev22_20261022_1204/video_validation.json", "docs/carrybox/wall5_play4_rev22_20261022_1204/visual_review.txt", "outputs/carrybox/wall5_play4_rev22_20261022_1204/README.md", "outputs/carrybox/wall5_play4_rev22_20261022_1204/contact_sheet.jpg", "outputs/carrybox/wall5_play4_rev22_20261022_1204/frame_0001.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/frame_0025.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/frame_0050.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/frame_0125.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/frame_0250.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/frame_0375.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/frame_0499.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/frame_0500.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/initial_scene.png", "outputs/carrybox/wall5_play4_rev22_20261022_1204/wall5_rev22_model22800_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "42225ceb9bba34fab892201e1dec5e3367e8739335efdd6d0d1ac81c457b1bf4"
tests: [{"command": "bash docs/carrybox/wall5_play4_rev22_20261022_1204/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "44ca861f6b9e2d16d7e620975ffc3b0eafa29e5b1068e635b19a0ec97fb4b932", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

录制model_22800.pt，4环境同步20秒、1920×1080/25fps四宫格，旁观相机基准高度5.8m（沿用上一段高位镜头）。保留默认3个loco/地面箱起点和1个明确标注的hold参考起点。每个机器人reset次数分别为[1, 1, 1, 1]，没有裁剪失败片段。

已检查0.04、1、2、5、10、15、19.96、20秒关键帧拼图和15秒原分辨率四宫格。前三个空手起点都会接近地面箱子，随后主要站立、小步调整或碰动箱子，没有明显的深蹲抓取和从地面抱起。排除自动reset后的状态，各999个控制步中三个机器人的手箱接触均为0，双手中心到箱子中心的最小距离分别为0.523/0.455/0.529m，箱底最大离地量分别为0.0025/0.0025/0.0074m；三个环境严格成功标记均为false。头高最低仍有1.174/1.151/1.132m，未出现接近拾箱参考的深蹲。

第四个机器人从持箱参考姿态初始化，能够维持持箱；双手同时接触箱子995/999步，箱心高度0.749–1.005m，严格成功标记true。它开场即有箱子，不能计为学会了地面拾箱。

四个回合均完成1000个控制步（20秒）后timeout，tipped、fell_pelvis和fell_head均为false；视频最后一帧保留这次正常超时reset。相较此前model10400的录像，本次仍未观察到从接近箱子到下蹲抓取的突破。此结论仅描述本段seed42、均值动作的四环境回放，不是整体成功率评估。

四台较高旁观相机在同一物理时刻拍摄，完整视频解码和四格关键帧检查通过；持箱参考起点已标注，不能算地面拾箱。模型、生产任务和后台训练保持。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev22_20261022_1204/wall5_rev22_model22800_4robots_high20s.mp4。详情：docs/carrybox/wall5_play4_rev22_20261022_1204/README.md。现有产物不覆盖；如需再次录制，另存新目录。没有待恢复工作。
