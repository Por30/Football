---
task_id: "carrybox-wall5-play4-rev22-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-rev22-20261021.md", "agent/plan/carrybox-wall5-play4-rev22-20261021.md", "agent/report/carrybox-wall5-play4-rev22-20261021.md", "agent/task/carrybox-wall5-play4-rev22-20261021.md", "docs/carrybox/wall5_play4_rev22_20261021/README.md", "docs/carrybox/wall5_play4_rev22_20261021/artifact_validation.json", "docs/carrybox/wall5_play4_rev22_20261021/behavior.json", "docs/carrybox/wall5_play4_rev22_20261021/camera_trajectory.json", "docs/carrybox/wall5_play4_rev22_20261021/finish.py", "docs/carrybox/wall5_play4_rev22_20261021/formal_status.json", "docs/carrybox/wall5_play4_rev22_20261021/receipts.json", "docs/carrybox/wall5_play4_rev22_20261021/record.log", "docs/carrybox/wall5_play4_rev22_20261021/record.py", "docs/carrybox/wall5_play4_rev22_20261021/record_and_check.sh", "docs/carrybox/wall5_play4_rev22_20261021/recording.json", "docs/carrybox/wall5_play4_rev22_20261021/selection.json", "docs/carrybox/wall5_play4_rev22_20261021/trajectory.json", "docs/carrybox/wall5_play4_rev22_20261021/verify.log", "docs/carrybox/wall5_play4_rev22_20261021/verify.py", "docs/carrybox/wall5_play4_rev22_20261021/video_validation.json", "docs/carrybox/wall5_play4_rev22_20261021/visual_review.txt", "outputs/carrybox/wall5_play4_rev22_20261021/README.md", "outputs/carrybox/wall5_play4_rev22_20261021/contact_sheet.jpg", "outputs/carrybox/wall5_play4_rev22_20261021/frame_0001.png", "outputs/carrybox/wall5_play4_rev22_20261021/frame_0025.png", "outputs/carrybox/wall5_play4_rev22_20261021/frame_0050.png", "outputs/carrybox/wall5_play4_rev22_20261021/frame_0125.png", "outputs/carrybox/wall5_play4_rev22_20261021/frame_0250.png", "outputs/carrybox/wall5_play4_rev22_20261021/frame_0375.png", "outputs/carrybox/wall5_play4_rev22_20261021/frame_0499.png", "outputs/carrybox/wall5_play4_rev22_20261021/frame_0500.png", "outputs/carrybox/wall5_play4_rev22_20261021/initial_scene.png", "outputs/carrybox/wall5_play4_rev22_20261021/wall5_rev22_model6400_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "f6bc3eaeea817451687e62facfd312eb864b71b0948f2f6173da9eba8b54f096"
tests: [{"command": "bash docs/carrybox/wall5_play4_rev22_20261021/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "b46d4460f97efbf3eb5daa877a1bbc5d3baa8e95ac54c5b618eb3e7c3f3a8ebe", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

录制model_6400.pt，4环境同步20秒、1920×1080/25fps四宫格，旁观相机基准高度5.8m（沿用上一段高位镜头）。保留默认3个loco/地面箱起点和1个明确标注的hold参考起点。每个机器人reset次数分别为[1, 1, 1, 1]，没有裁剪失败片段。

已检查0.04、1、2、5、10、15、19.96和20秒关键帧，以及1、5、10秒原分辨率画面；四个机器人、箱子、深度角标及起点/reset标注可见。前三个空手起点能走近箱子，随后主要在箱边站立、调整步态和手臂，没有完成下蹲接触并从地面抬起。去掉最后一帧reset后的状态，三个loco环境手箱有效接触均为0/999步，双手中心距箱心最小分别约0.585、0.472、0.555m；箱底最大离地仅约2.5mm，箱心高的短暂变化不代表抬起。4号由持箱参考初始化，箱心保持在约0.825–1.148m，993/999步双手有接触；该画面不能算地面拾箱成功，严格连续抬起统计也未达成。四个机器人均无倾倒或低高度提前终止，唯一reset均为第1000步、20秒超时，最后一帧完整保留了重置画面。本段4起点均值动作回放不作为总体成功率评估。

四台较高旁观相机在同一物理时刻拍摄，完整视频解码和四格关键帧检查通过；持箱参考起点已标注，不能算地面拾箱。模型、生产任务和后台训练保持。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev22_20261021/wall5_rev22_model6400_4robots_high20s.mp4。详情：docs/carrybox/wall5_play4_rev22_20261021/README.md。现有产物不覆盖；如需再次录制，另存新目录。没有待恢复工作。
