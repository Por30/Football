---
task_id: "carrybox-wall5-play4-rev23-20261022-1903"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play4-rev23-20261022-1903.md", "agent/plan/carrybox-wall5-play4-rev23-20261022-1903.md", "agent/report/carrybox-wall5-play4-rev23-20261022-1903.md", "agent/task/carrybox-wall5-play4-rev23-20261022-1903.md", "docs/carrybox/wall5_play4_rev23_20261022_1903/README.md", "docs/carrybox/wall5_play4_rev23_20261022_1903/analyze.py", "docs/carrybox/wall5_play4_rev23_20261022_1903/artifact_validation.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/behavior.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/camera_trajectory.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/episode_summary.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/finish.py", "docs/carrybox/wall5_play4_rev23_20261022_1903/formal_status.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/receipts.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/record.log", "docs/carrybox/wall5_play4_rev23_20261022_1903/record.py", "docs/carrybox/wall5_play4_rev23_20261022_1903/record_and_check.sh", "docs/carrybox/wall5_play4_rev23_20261022_1903/recording.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/selection.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/training_metrics.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/trajectory.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/verify.log", "docs/carrybox/wall5_play4_rev23_20261022_1903/verify.py", "docs/carrybox/wall5_play4_rev23_20261022_1903/video_validation.json", "docs/carrybox/wall5_play4_rev23_20261022_1903/visual_review.txt", "outputs/carrybox/wall5_play4_rev23_20261022_1903/README.md", "outputs/carrybox/wall5_play4_rev23_20261022_1903/contact_sheet.jpg", "outputs/carrybox/wall5_play4_rev23_20261022_1903/frame_0001.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/frame_0025.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/frame_0050.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/frame_0125.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/frame_0250.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/frame_0375.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/frame_0499.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/frame_0500.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/initial_scene.png", "outputs/carrybox/wall5_play4_rev23_20261022_1903/wall5_rev23_model6200_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "2f9a1c5419bd00bfad5131b53ed382100087cc22e1c9d8a1055e53dd22e2f1c5"
tests: [{"command": "bash docs/carrybox/wall5_play4_rev23_20261022_1903/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "3fb09451757dcaaf5054d4322aed7d61a402a9f56a4cebe3e596cd42345846bd", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

录制model_6200.pt，4环境同步20秒、1920×1080/25fps四宫格，旁观相机基准高度5.8m（沿用上一段高位镜头）。保留默认3个loco/地面箱起点和1个明确标注的hold参考起点。每个机器人reset次数分别为[23, 30, 33, 1]，没有裁剪失败片段。

本次model_6200回放中，空手起点尚未学会稳定行走，也未观察到从地面抓取并抬箱。人工检查关键帧可见前三个机器人反复侧倾、前扑和reset；它们在20秒内分别结束23/30/33个回合，已结束回合平均持续0.841/0.651/0.585秒，全部触发tipped，其中第二、第三格另有2/3次同时触发头高跌倒。终止标签可重叠，不能相加当作回合数。排除自动reset后的状态，前三格双手同时接触箱子的采样步数均为0，箱底最大离地仅2.55/5.97/5.10毫米，未形成有效抬箱；单手接触仅分别出现2/0/1个采样步。第四格从持箱参考姿态开始，大部分时间维持双手接触，后段靠近墙，在19.96秒同时触发骨盆和头高跌倒并reset；其success标签不能当作从地面拾箱成功。前三格的瞬时前倾或下探也不足以判定为有效抓取尝试。本次为seed42、均值动作的4环境20秒观察，不是成功率评估，也不能据此把失稳单独归因于自碰撞、奖励或推扰。后台正式训练继续运行，本次未调参或重启。

四台较高旁观相机在同一物理时刻拍摄，完整视频解码和四格关键帧检查通过；持箱参考起点已标注，不能算地面拾箱。模型、生产任务和后台训练保持。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev23_20261022_1903/wall5_rev23_model6200_4robots_high20s.mp4。详情：docs/carrybox/wall5_play4_rev23_20261022_1903/README.md。现有产物不覆盖；如需再次录制，另存新目录。没有待恢复工作。
