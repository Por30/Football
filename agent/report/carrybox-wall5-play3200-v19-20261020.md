---
task_id: "carrybox-wall5-play3200-v19-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play3200-v19-20261020.md", "agent/plan/carrybox-wall5-play3200-v19-20261020.md", "agent/report/carrybox-wall5-play3200-v19-20261020.md", "agent/task/carrybox-wall5-play3200-v19-20261020.md", "docs/carrybox/wall5_play3200_v19_20261020/README.md", "docs/carrybox/wall5_play3200_v19_20261020/artifact_validation.json", "docs/carrybox/wall5_play3200_v19_20261020/finish.py", "docs/carrybox/wall5_play3200_v19_20261020/formal_status.json", "docs/carrybox/wall5_play3200_v19_20261020/receipts.json", "docs/carrybox/wall5_play3200_v19_20261020/record.log", "docs/carrybox/wall5_play3200_v19_20261020/record.py", "docs/carrybox/wall5_play3200_v19_20261020/record_and_check.sh", "docs/carrybox/wall5_play3200_v19_20261020/recording.json", "docs/carrybox/wall5_play3200_v19_20261020/selection.json", "docs/carrybox/wall5_play3200_v19_20261020/trajectory.json", "docs/carrybox/wall5_play3200_v19_20261020/verify.log", "docs/carrybox/wall5_play3200_v19_20261020/verify.py", "docs/carrybox/wall5_play3200_v19_20261020/video_validation.json", "docs/carrybox/wall5_play3200_v19_20261020/visual_review.txt", "outputs/carrybox/wall5_play3200_v19_20261020/README.md", "outputs/carrybox/wall5_play3200_v19_20261020/contact_sheet.jpg", "outputs/carrybox/wall5_play3200_v19_20261020/frame_0001.png", "outputs/carrybox/wall5_play3200_v19_20261020/frame_0025.png", "outputs/carrybox/wall5_play3200_v19_20261020/frame_0050.png", "outputs/carrybox/wall5_play3200_v19_20261020/frame_0125.png", "outputs/carrybox/wall5_play3200_v19_20261020/frame_0250.png", "outputs/carrybox/wall5_play3200_v19_20261020/frame_0375.png", "outputs/carrybox/wall5_play3200_v19_20261020/frame_0499.png", "outputs/carrybox/wall5_play3200_v19_20261020/frame_0500.png", "outputs/carrybox/wall5_play3200_v19_20261020/initial_scene.png", "outputs/carrybox/wall5_play3200_v19_20261020/wall5_rev19_model3200_play20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "b93a5e9b237bca3c189be862929a3c1eb1c33cb83875be16bf2a5f0e7e9d9bf2"
tests: [{"command": "bash docs/carrybox/wall5_play3200_v19_20261020/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "ab04ce06a49e52cd93135d5dbfda0a448e5dd032e91ed5d644561634ec46379d", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

本次选定最新正式model3200已严格加载并完成20秒MP4；路径/home/cao/perceptual_ball/outputs/carrybox/wall5_play3200_v19_20261020/wall5_rev19_model3200_play20s.mp4。已检查0.04、1、2、5、10、15、19.96和20秒关键帧，机器人、箱子和实际策略深度角标清晰可见。机器人前1–2秒走近箱子，箱子被推移，随后主要在箱旁站立和小幅调整，没有看到明显下蹲并完成抬箱的动作。第999步相对首步水平位移约1.207m，水平距箱约0.249m；1秒后箱心基本保持在0.125m贴地高度，严格lift成功标记始终为false。整段没有倾倒或低高度终止，唯一reset在第1000步达到20秒超时。该单起点均值动作回放不能代替稳定行走或拾箱成功率评估。

完成1次自动reset，窗口末回合已持续0.00秒。记录到严格lift成功标记的完成回合数为0；窗口末回合标记为False。这是一段单环境视频，不是成功率评估。

500帧完整解码PASS，关键帧已视觉检查；源代码和checkpoint hash保持，未修改生产配置或操作后台训练。身份及回合数据见docs/carrybox/wall5_play3200_v19_20261020。已有输出不覆盖，重新录制另存目录；无需恢复任务。
