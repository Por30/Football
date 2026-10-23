---
task_id: "carrybox-wall5-play-compare-20261023-1542"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play-compare-20261023-1542.md", "agent/plan/carrybox-wall5-play-compare-20261023-1542.md", "agent/report/carrybox-wall5-play-compare-20261023-1542.md", "agent/task/carrybox-wall5-play-compare-20261023-1542.md", "docs/carrybox/wall5_play_compare_20261023_1542/README.md", "docs/carrybox/wall5_play_compare_20261023_1542/analyze.log", "docs/carrybox/wall5_play_compare_20261023_1542/analyze_behavior.py", "docs/carrybox/wall5_play_compare_20261023_1542/artifact_validation.json", "docs/carrybox/wall5_play_compare_20261023_1542/baseline_initial.pt", "docs/carrybox/wall5_play_compare_20261023_1542/baseline_trace.json", "docs/carrybox/wall5_play_compare_20261023_1542/baseline_trace.npz", "docs/carrybox/wall5_play_compare_20261023_1542/before_reset_rng.pt", "docs/carrybox/wall5_play_compare_20261023_1542/behavior.json", "docs/carrybox/wall5_play_compare_20261023_1542/camera_trajectory.json", "docs/carrybox/wall5_play_compare_20261023_1542/compare_previous.py", "docs/carrybox/wall5_play_compare_20261023_1542/comparison.json", "docs/carrybox/wall5_play_compare_20261023_1542/comparison.log", "docs/carrybox/wall5_play_compare_20261023_1542/finish.py", "docs/carrybox/wall5_play_compare_20261023_1542/formal_status.json", "docs/carrybox/wall5_play_compare_20261023_1542/initial_match.json", "docs/carrybox/wall5_play_compare_20261023_1542/receipts.json", "docs/carrybox/wall5_play_compare_20261023_1542/record.log", "docs/carrybox/wall5_play_compare_20261023_1542/record.py", "docs/carrybox/wall5_play_compare_20261023_1542/record_and_check.sh", "docs/carrybox/wall5_play_compare_20261023_1542/recording.json", "docs/carrybox/wall5_play_compare_20261023_1542/selection.json", "docs/carrybox/wall5_play_compare_20261023_1542/trace.py", "docs/carrybox/wall5_play_compare_20261023_1542/trajectory.json", "docs/carrybox/wall5_play_compare_20261023_1542/verify.log", "docs/carrybox/wall5_play_compare_20261023_1542/verify.py", "docs/carrybox/wall5_play_compare_20261023_1542/video_validation.json", "docs/carrybox/wall5_play_compare_20261023_1542/visual_review.txt", "outputs/carrybox/wall5_play_compare_20261023_1542/README.md", "outputs/carrybox/wall5_play_compare_20261023_1542/comparison.png", "outputs/carrybox/wall5_play_compare_20261023_1542/contact_sheet.jpg", "outputs/carrybox/wall5_play_compare_20261023_1542/frame_0001.png", "outputs/carrybox/wall5_play_compare_20261023_1542/frame_0025.png", "outputs/carrybox/wall5_play_compare_20261023_1542/frame_0050.png", "outputs/carrybox/wall5_play_compare_20261023_1542/frame_0125.png", "outputs/carrybox/wall5_play_compare_20261023_1542/frame_0250.png", "outputs/carrybox/wall5_play_compare_20261023_1542/frame_0375.png", "outputs/carrybox/wall5_play_compare_20261023_1542/frame_0499.png", "outputs/carrybox/wall5_play_compare_20261023_1542/frame_0500.png", "outputs/carrybox/wall5_play_compare_20261023_1542/initial_scene.png", "outputs/carrybox/wall5_play_compare_20261023_1542/wall5_rev27_model2800_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "8fc10ce570ff9090ebd26e377605b884875b6dad61d52cd02d5cf1dd272c9bc2"
tests: [{"command": "bash docs/carrybox/wall5_play_compare_20261023_1542/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "c1e5abddc14ce4ac9d60c55c06565e5613499a1241c2eb1334861a244b07ffbb", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

rev27 model_2800，4机器人同步20秒，1080p/25fps、高位镜头。固定来源为默认/loco/loco/hold，reset次数[1, 1, 1, 1]；保留完整回合；与model2200使用相同初态及2200轮课程。

本次为局部改善，尚不能认定抖动问题已经解决。录制开始时最新完整模型为model2800；与model2200匹配初态、观测、延迟、PD、材质、事件时钟，并固定旧课程（推扰0.30、yaw2.2°），仅替换策略权重。已检查关键帧拼图、15秒/19.96秒原图和200Hz遥测；视频500帧完整解码通过。

比较窗口为首回合2–20秒，排除启动阶段，两个模型都没有提前reset。腿部关节加速度RMS（rad/s²）变化如下：

| 起点 | model2200 | model2800 | 变化 | 平均机体水平速度（m/s） |
|---|---:|---:|---:|---:|
| 默认空手 | 126.6 | 93.0 | -26.6% | 0.111 → 0.126 |
| loco 1 | 62.1 | 40.0 | -35.6% | 0.110 → 0.075 |
| loco 2 | 76.3 | 52.6 | -31.1% | 0.140 → 0.112 |
| hold | 106.2 | 126.4 | +19.0% | 0.144 → 0.158 |

三台空手机器人的关节波动幅度下降；其中两台loco同时移动得更慢，且≥8Hz的关节速度功率占比从17.4%/23.6%升至37.9%/30.7%，所以不能仅凭RMS下降认定步态平滑性全面改善。持箱组波动和动作变化反而增大。模型/自碰撞配置未改，本次没有新的自碰撞因果消融。

膝目标裁剪仍很严重：新模型各侧膝在95.1%–100%的策略时间被裁剪，双膝平均比例为96.3%、100%、98.2%、100%，比旧模型更高。这是目标命令裁剪，不能当作实际关节限位碰撞次数。

四台机器人均维持完整20秒，只因超时重置，所有倾倒/高度/箱速失败计数为0。两台loco的水平箱距从1.41/1.43m缩短到0.76/0.71m，但三个空手起点全程没有手箱接触，箱子仍贴地；关键帧中没有完成下蹲抓取。hold组保持箱子离地，开始时箱子就已在手中，不算从地面搬起。单seed四环境只能说明本段表现，不能推出整体成功率或已学会正常行走。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play_compare_20261023_1542/wall5_rev27_model2800_4robots_high20s.mp4。严格加载、完整解码及关键帧检查通过；正式训练和生产源码保持。没有待恢复工作，后续录像新建目录。
