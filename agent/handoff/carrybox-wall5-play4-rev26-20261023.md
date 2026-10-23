---
task_id: "carrybox-wall5-play4-rev26-20261023"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-rev26-20261023.md", "agent/plan/carrybox-wall5-play4-rev26-20261023.md", "agent/report/carrybox-wall5-play4-rev26-20261023.md", "agent/task/carrybox-wall5-play4-rev26-20261023.md", "docs/carrybox/wall5_play4_rev26_20261023/README.md", "docs/carrybox/wall5_play4_rev26_20261023/analyze_behavior.py", "docs/carrybox/wall5_play4_rev26_20261023/artifact_validation.json", "docs/carrybox/wall5_play4_rev26_20261023/behavior.json", "docs/carrybox/wall5_play4_rev26_20261023/camera_trajectory.json", "docs/carrybox/wall5_play4_rev26_20261023/finish.py", "docs/carrybox/wall5_play4_rev26_20261023/formal_status.json", "docs/carrybox/wall5_play4_rev26_20261023/last_episode_initial_states.json", "docs/carrybox/wall5_play4_rev26_20261023/receipts.json", "docs/carrybox/wall5_play4_rev26_20261023/record.log", "docs/carrybox/wall5_play4_rev26_20261023/record.py", "docs/carrybox/wall5_play4_rev26_20261023/record_and_check.sh", "docs/carrybox/wall5_play4_rev26_20261023/recording.json", "docs/carrybox/wall5_play4_rev26_20261023/selection.json", "docs/carrybox/wall5_play4_rev26_20261023/trajectory.json", "docs/carrybox/wall5_play4_rev26_20261023/verify.log", "docs/carrybox/wall5_play4_rev26_20261023/verify.py", "docs/carrybox/wall5_play4_rev26_20261023/video_validation.json", "docs/carrybox/wall5_play4_rev26_20261023/visual_review.txt", "outputs/carrybox/wall5_play4_rev26_20261023/README.md", "outputs/carrybox/wall5_play4_rev26_20261023/contact_sheet.jpg", "outputs/carrybox/wall5_play4_rev26_20261023/frame_0001.png", "outputs/carrybox/wall5_play4_rev26_20261023/frame_0025.png", "outputs/carrybox/wall5_play4_rev26_20261023/frame_0050.png", "outputs/carrybox/wall5_play4_rev26_20261023/frame_0125.png", "outputs/carrybox/wall5_play4_rev26_20261023/frame_0250.png", "outputs/carrybox/wall5_play4_rev26_20261023/frame_0375.png", "outputs/carrybox/wall5_play4_rev26_20261023/frame_0499.png", "outputs/carrybox/wall5_play4_rev26_20261023/frame_0500.png", "outputs/carrybox/wall5_play4_rev26_20261023/initial_scene.png", "outputs/carrybox/wall5_play4_rev26_20261023/wall5_rev26_model13200_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "49a3bb95918384979106c60830df67c262d0a51f5e77535324c9334bae908f56"
tests: [{"command": "bash docs/carrybox/wall5_play4_rev26_20261023/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "f25c621e98f451ada0abd7f33014240a242bac0e9242ffa46e7c0892a90c5ebd", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

最新完整model_13200.pt，revision26，4环境同步20秒、1920×1080/25fps、高位镜头基准5.8m。默认随机reset保持，每格reset次数[2, 1, 6, 7]；起点标签随回合变化，失败过程完整保留。

已检查0.04、1、2、5、10、15、19.96、20秒关键帧拼图，以及2、10、20秒原分辨率四宫格；机器人、箱子、当前reset起点标签和实际深度角标可辨。开场为1个默认站姿、3个loco RSI，空手起点在前段反复倾斜reset。20秒内共16次结束（每格2/1/6/7次），全部实际触发tipped；其中3个默认站姿回合平均0.127秒、12个loco回合平均0.192秒，最长loco仅0.58秒，另1个pickup参考回合0.22秒。排除reset后的样本，空手119个控制步样本没有任何手箱接触，没有观察到走到地面箱旁并抓起的流程。

后半段四格都能保持抱箱并调整步态，但来自随后随机抽中的3个pickup中途参考起点和1个hold起点。它们在0.34/0.16/1.30/1.10秒reset时，箱底已分别离地约0.714/0.737/0.758/0.722m；不是本回合从地面搬起。四个最后回合在视频结束时已持续19.66/19.84/18.70/18.90秒，仍未结束，且都触发过保持成功标记；这些标记不能算地面拾箱成功。完整保留前段失败和后段参考持箱，没有挑选或剪掉失败回合。本段说明空手行走/接近仍未成功，参考持箱保持明显优于空手起步；这是单seed四环境录像观察，不是总体成功率评估。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev26_20261023/wall5_rev26_model13200_4robots_high20s.mp4。严格加载、完整解码、关键帧检查通过；不改生产或正式训练。当前起点随机，不能套用旧版固定3loco+1hold描述。没有待恢复工作；既有产物不覆盖。
