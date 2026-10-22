---
task_id: "carrybox-wall5-play4-rev22-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-rev22-20261022.md", "agent/plan/carrybox-wall5-play4-rev22-20261022.md", "agent/report/carrybox-wall5-play4-rev22-20261022.md", "agent/task/carrybox-wall5-play4-rev22-20261022.md", "docs/carrybox/wall5_play4_rev22_20261022/README.md", "docs/carrybox/wall5_play4_rev22_20261022/analyze.py", "docs/carrybox/wall5_play4_rev22_20261022/artifact_validation.json", "docs/carrybox/wall5_play4_rev22_20261022/behavior.json", "docs/carrybox/wall5_play4_rev22_20261022/camera_trajectory.json", "docs/carrybox/wall5_play4_rev22_20261022/finish.py", "docs/carrybox/wall5_play4_rev22_20261022/formal_status.json", "docs/carrybox/wall5_play4_rev22_20261022/receipts.json", "docs/carrybox/wall5_play4_rev22_20261022/record.log", "docs/carrybox/wall5_play4_rev22_20261022/record.py", "docs/carrybox/wall5_play4_rev22_20261022/record_and_check.sh", "docs/carrybox/wall5_play4_rev22_20261022/recording.json", "docs/carrybox/wall5_play4_rev22_20261022/selection.json", "docs/carrybox/wall5_play4_rev22_20261022/trajectory.json", "docs/carrybox/wall5_play4_rev22_20261022/verify.log", "docs/carrybox/wall5_play4_rev22_20261022/verify.py", "docs/carrybox/wall5_play4_rev22_20261022/video_validation.json", "docs/carrybox/wall5_play4_rev22_20261022/visual_review.txt", "outputs/carrybox/wall5_play4_rev22_20261022/README.md", "outputs/carrybox/wall5_play4_rev22_20261022/contact_sheet.jpg", "outputs/carrybox/wall5_play4_rev22_20261022/frame_0001.png", "outputs/carrybox/wall5_play4_rev22_20261022/frame_0025.png", "outputs/carrybox/wall5_play4_rev22_20261022/frame_0050.png", "outputs/carrybox/wall5_play4_rev22_20261022/frame_0125.png", "outputs/carrybox/wall5_play4_rev22_20261022/frame_0250.png", "outputs/carrybox/wall5_play4_rev22_20261022/frame_0375.png", "outputs/carrybox/wall5_play4_rev22_20261022/frame_0499.png", "outputs/carrybox/wall5_play4_rev22_20261022/frame_0500.png", "outputs/carrybox/wall5_play4_rev22_20261022/initial_scene.png", "outputs/carrybox/wall5_play4_rev22_20261022/wall5_rev22_model10400_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "24809528a34f18e8a341a7732dcf59c886aa9d1c5d17a663b19d76bb2ff29aac"
tests: [{"command": "bash docs/carrybox/wall5_play4_rev22_20261022/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "0c08eecc22bb5205abe99ba97bc6c1e021b0a79d1388db2b2c999196ffa48417", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

录制model_10400.pt，4环境同步20秒、1920×1080/25fps四宫格，旁观相机基准高度5.8m（沿用上一段高位镜头）。保留默认3个loco/地面箱起点和1个明确标注的hold参考起点。每个机器人reset次数分别为[1, 1, 1, 1]，没有裁剪失败片段。

已检查0.04、1、2、5、10、15、19.96和20秒关键帧，以及1、5、10秒原分辨率画面；四格机器人、箱子、米制深度角标、起点与reset标注均可见。前三个空手起点能走到箱边，随后主要站立、调整脚步和手臂，仍未完成从地面拾箱。去掉最后一帧reset后的状态，三个loco环境手箱有效接触均为0/999步，双手中心距箱心最小分别约0.560、0.490、0.499m；箱底最大离地分别约0.25、3.45、0.99cm，短暂跳动未形成手部抬起，三个完整回合成功均为false。4号为持箱参考起点，箱心保持在约0.831–1.174m，995/999步双手接触，并达到过连续稳定保持的成功判据；这属于持箱保持，不能算从地面抱起。四个机器人均未发生倾倒或低高度提前终止，唯一reset均为第1000步、20秒超时，最后一帧保留重置画面。本段为4起点均值动作回放，不作为总体成功率评估。

四台较高旁观相机在同一物理时刻拍摄，完整视频解码和四格关键帧检查通过；持箱参考起点已标注，不能算地面拾箱。模型、生产任务和后台训练保持。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev22_20261022/wall5_rev22_model10400_4robots_high20s.mp4。详情：docs/carrybox/wall5_play4_rev22_20261022/README.md。现有产物不覆盖；如需再次录制，另存新目录。没有待恢复工作。
