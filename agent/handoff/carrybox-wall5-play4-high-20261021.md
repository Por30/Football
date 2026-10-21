---
task_id: "carrybox-wall5-play4-high-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-high-20261021.md", "agent/plan/carrybox-wall5-play4-high-20261021.md", "agent/report/carrybox-wall5-play4-high-20261021.md", "agent/task/carrybox-wall5-play4-high-20261021.md", "docs/carrybox/wall5_play4_high_20261021/README.md", "docs/carrybox/wall5_play4_high_20261021/artifact_validation.json", "docs/carrybox/wall5_play4_high_20261021/camera_trajectory.json", "docs/carrybox/wall5_play4_high_20261021/finish.py", "docs/carrybox/wall5_play4_high_20261021/formal_status.json", "docs/carrybox/wall5_play4_high_20261021/receipts.json", "docs/carrybox/wall5_play4_high_20261021/record.log", "docs/carrybox/wall5_play4_high_20261021/record.py", "docs/carrybox/wall5_play4_high_20261021/record_and_check.sh", "docs/carrybox/wall5_play4_high_20261021/recording.json", "docs/carrybox/wall5_play4_high_20261021/selection.json", "docs/carrybox/wall5_play4_high_20261021/trajectory.json", "docs/carrybox/wall5_play4_high_20261021/verify.log", "docs/carrybox/wall5_play4_high_20261021/verify.py", "docs/carrybox/wall5_play4_high_20261021/video_validation.json", "docs/carrybox/wall5_play4_high_20261021/visual_review.txt", "outputs/carrybox/wall5_play4_high_20261021/README.md", "outputs/carrybox/wall5_play4_high_20261021/contact_sheet.jpg", "outputs/carrybox/wall5_play4_high_20261021/frame_0001.png", "outputs/carrybox/wall5_play4_high_20261021/frame_0025.png", "outputs/carrybox/wall5_play4_high_20261021/frame_0050.png", "outputs/carrybox/wall5_play4_high_20261021/frame_0125.png", "outputs/carrybox/wall5_play4_high_20261021/frame_0250.png", "outputs/carrybox/wall5_play4_high_20261021/frame_0375.png", "outputs/carrybox/wall5_play4_high_20261021/frame_0499.png", "outputs/carrybox/wall5_play4_high_20261021/frame_0500.png", "outputs/carrybox/wall5_play4_high_20261021/initial_scene.png", "outputs/carrybox/wall5_play4_high_20261021/wall5_rev19_model23000_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "37337b4338cdbe2f129929abb11e9b760dc1fa062b0e950ba132c93adfbfe22c"
tests: [{"command": "bash docs/carrybox/wall5_play4_high_20261021/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "3ea28c18d0264d33d94e9cdb25be163339415b8137c849320fdd8f11bad0c8f4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

录制model_23000.pt，4环境同步20秒、1920×1080/25fps四宫格，旁观相机基准高度5.8m（沿用上一段高位镜头）。保留默认3个loco/地面箱起点和1个明确标注的hold参考起点。每个机器人reset次数分别为[1, 1, 1, 1]，没有裁剪失败片段。

已检查0.04、1、2、5、10、15、19.96和20秒关键帧，四个高位视角中的机器人、箱子和实际策略深度角标清晰可见。前三个空手起点很快接近箱子，随后主要在箱旁站立、调整步态及手臂；部分画面可见俯身，但本段均未完成从地面抱起，三个环境的成功标记始终为false。4号从持箱参考姿态开始，并保持箱子中心约0.75–0.86m高，这不能算地面拾箱。四个环境均未发生倾倒或低高度终止，唯一reset均在第1000步、20秒超时，最后一帧保留了reset后的画面。该四起点均值动作回放不作为成功率评估。

四台较高旁观相机在同一物理时刻拍摄，完整视频解码和四格关键帧检查通过；持箱参考起点已标注，不能算地面拾箱。模型、生产任务和后台训练保持。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_high_20261021/wall5_rev19_model23000_4robots_high20s.mp4。详情：docs/carrybox/wall5_play4_high_20261021/README.md。现有产物不覆盖；如需再次录制，另存新目录。没有待恢复工作。
