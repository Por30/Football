---
task_id: "carrybox-wall5-play4-rev27-20261023"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-rev27-20261023.md", "agent/plan/carrybox-wall5-play4-rev27-20261023.md", "agent/report/carrybox-wall5-play4-rev27-20261023.md", "agent/task/carrybox-wall5-play4-rev27-20261023.md", "docs/carrybox/wall5_play4_rev27_20261023/README.md", "docs/carrybox/wall5_play4_rev27_20261023/analyze.log", "docs/carrybox/wall5_play4_rev27_20261023/analyze_behavior.py", "docs/carrybox/wall5_play4_rev27_20261023/artifact_validation.json", "docs/carrybox/wall5_play4_rev27_20261023/behavior.json", "docs/carrybox/wall5_play4_rev27_20261023/camera_trajectory.json", "docs/carrybox/wall5_play4_rev27_20261023/finish.py", "docs/carrybox/wall5_play4_rev27_20261023/formal_status.json", "docs/carrybox/wall5_play4_rev27_20261023/per_robot_behavior.json", "docs/carrybox/wall5_play4_rev27_20261023/receipts.json", "docs/carrybox/wall5_play4_rev27_20261023/record.log", "docs/carrybox/wall5_play4_rev27_20261023/record.py", "docs/carrybox/wall5_play4_rev27_20261023/record_and_check.sh", "docs/carrybox/wall5_play4_rev27_20261023/recording.json", "docs/carrybox/wall5_play4_rev27_20261023/selection.json", "docs/carrybox/wall5_play4_rev27_20261023/trajectory.json", "docs/carrybox/wall5_play4_rev27_20261023/verify.log", "docs/carrybox/wall5_play4_rev27_20261023/verify.py", "docs/carrybox/wall5_play4_rev27_20261023/video_validation.json", "docs/carrybox/wall5_play4_rev27_20261023/visual_review.txt", "outputs/carrybox/wall5_play4_rev27_20261023/README.md", "outputs/carrybox/wall5_play4_rev27_20261023/contact_sheet.jpg", "outputs/carrybox/wall5_play4_rev27_20261023/frame_0001.png", "outputs/carrybox/wall5_play4_rev27_20261023/frame_0025.png", "outputs/carrybox/wall5_play4_rev27_20261023/frame_0050.png", "outputs/carrybox/wall5_play4_rev27_20261023/frame_0125.png", "outputs/carrybox/wall5_play4_rev27_20261023/frame_0250.png", "outputs/carrybox/wall5_play4_rev27_20261023/frame_0375.png", "outputs/carrybox/wall5_play4_rev27_20261023/frame_0499.png", "outputs/carrybox/wall5_play4_rev27_20261023/frame_0500.png", "outputs/carrybox/wall5_play4_rev27_20261023/initial_scene.png", "outputs/carrybox/wall5_play4_rev27_20261023/wall5_rev27_model1400_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "5c54a49abae57181470eacef4a1cc69a81e0a11529a7bb303be84f6e1543a5bf"
tests: [{"command": "bash docs/carrybox/wall5_play4_rev27_20261023/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "d50646c4ec26ef6ae02de3cd01e4e7ad9017c6534fa4860c94e6cf271155015f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

rev27 model_1400，4机器人同步20秒，1080p/25fps、高位镜头。固定来源为默认/loco/loco/hold，reset次数[1, 1, 1, 1]；保留全部失败回合。

已检查初始场景、0.04/1/2/5/10/15/19.96/20秒拼图及5/10/19.96秒原分辨率画面，机器人、箱子、起点标签和深度角标清楚。四个首回合均运行1000步/20秒，只在最后一帧因time_out重置；没有tipped、头/骨盆/髋过低、箱速或invalid终止。完整保留末帧超时reset。

默认站姿机器人基本原地调整，水平距箱0.90→0.95m，根部净位移0.10m；两个loco机器人有靠近行为，水平距箱分别1.41→0.90m、1.43→0.48m，净位移0.63m、1.66m。第二个loco最接近时约0.425m，后段仍站着。三个空手机器人合计2997个非reset控制步没有任何手箱接触，也没有地面拾箱成功；头高最低分别1.217/1.187/1.138m，没有观察到有效下蹲抓取过程。距离与位移从0.02至19.98秒计算，末帧reset位置不计入。

第四个从hold参考持箱开始，保持抱箱20秒并移动，999个非reset控制步中995步双手接触，成功标记为持箱保持；初始箱底已离地0.737m，不能算从地面搬起。当前录像显示本组空手起步稳定性改善、有部分接近行为，但尚未完成抓取。仅单seed四环境均值动作回放，推扰课程为0.10，不能据此认定训练整体或全强度扰动下已收敛，也不是与上一模型同初态的控制对照。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev27_20261023/wall5_rev27_model1400_4robots_high20s.mp4。严格加载、完整解码及关键帧检查通过；正式训练和生产源码保持。没有待恢复工作，后续录像新建目录。
