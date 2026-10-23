---
task_id: "carrybox-wall5-play-compare-20261023-1704"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-play-compare-20261023-1704.md", "agent/plan/carrybox-wall5-play-compare-20261023-1704.md", "agent/report/carrybox-wall5-play-compare-20261023-1704.md", "agent/task/carrybox-wall5-play-compare-20261023-1704.md", "docs/carrybox/wall5_play_compare_20261023_1704/README.md", "docs/carrybox/wall5_play_compare_20261023_1704/analyze.log", "docs/carrybox/wall5_play_compare_20261023_1704/analyze_behavior.py", "docs/carrybox/wall5_play_compare_20261023_1704/artifact_validation.json", "docs/carrybox/wall5_play_compare_20261023_1704/baseline_initial.pt", "docs/carrybox/wall5_play_compare_20261023_1704/baseline_trace.json", "docs/carrybox/wall5_play_compare_20261023_1704/baseline_trace.npz", "docs/carrybox/wall5_play_compare_20261023_1704/before_reset_rng.pt", "docs/carrybox/wall5_play_compare_20261023_1704/behavior.json", "docs/carrybox/wall5_play_compare_20261023_1704/camera_trajectory.json", "docs/carrybox/wall5_play_compare_20261023_1704/compare_previous.py", "docs/carrybox/wall5_play_compare_20261023_1704/comparison.json", "docs/carrybox/wall5_play_compare_20261023_1704/comparison.log", "docs/carrybox/wall5_play_compare_20261023_1704/finish.py", "docs/carrybox/wall5_play_compare_20261023_1704/formal_status.json", "docs/carrybox/wall5_play_compare_20261023_1704/initial_match.json", "docs/carrybox/wall5_play_compare_20261023_1704/receipts.json", "docs/carrybox/wall5_play_compare_20261023_1704/record.log", "docs/carrybox/wall5_play_compare_20261023_1704/record.py", "docs/carrybox/wall5_play_compare_20261023_1704/record_and_check.sh", "docs/carrybox/wall5_play_compare_20261023_1704/recording.json", "docs/carrybox/wall5_play_compare_20261023_1704/selection.json", "docs/carrybox/wall5_play_compare_20261023_1704/trace.py", "docs/carrybox/wall5_play_compare_20261023_1704/trajectory.json", "docs/carrybox/wall5_play_compare_20261023_1704/verify.log", "docs/carrybox/wall5_play_compare_20261023_1704/verify.py", "docs/carrybox/wall5_play_compare_20261023_1704/video_validation.json", "docs/carrybox/wall5_play_compare_20261023_1704/visual_review.txt", "outputs/carrybox/wall5_play_compare_20261023_1704/README.md", "outputs/carrybox/wall5_play_compare_20261023_1704/comparison.png", "outputs/carrybox/wall5_play_compare_20261023_1704/contact_sheet.jpg", "outputs/carrybox/wall5_play_compare_20261023_1704/frame_0001.png", "outputs/carrybox/wall5_play_compare_20261023_1704/frame_0025.png", "outputs/carrybox/wall5_play_compare_20261023_1704/frame_0050.png", "outputs/carrybox/wall5_play_compare_20261023_1704/frame_0125.png", "outputs/carrybox/wall5_play_compare_20261023_1704/frame_0250.png", "outputs/carrybox/wall5_play_compare_20261023_1704/frame_0375.png", "outputs/carrybox/wall5_play_compare_20261023_1704/frame_0499.png", "outputs/carrybox/wall5_play_compare_20261023_1704/frame_0500.png", "outputs/carrybox/wall5_play_compare_20261023_1704/initial_scene.png", "outputs/carrybox/wall5_play_compare_20261023_1704/wall5_rev27_model4200_4robots_high20s.mp4", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "59bfd9090f1ea5cd8beb82f112282a0d2410a141a4ddf3369075a491c62009b1"
tests: [{"command": "bash docs/carrybox/wall5_play_compare_20261023_1704/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "c3082ecb88677b250f269aee06576f0ac7d63e992e499e426bd2700abbafc4d6", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

rev27 model_4200，4机器人同步20秒，1080p/25fps、高位镜头。固定来源为默认/loco/loco/hold，reset次数[1, 1, 1, 1]；保留完整回合；与model2800使用相同初态及2200轮课程。

本次空手行走抖动没有明显改善；持箱组波动幅度下降，但同时移动得更慢，不能据此认定步态平滑性已改善。录制开始时最新完整模型为model4200，与上次model2800比较。22项初态字段最大误差为0，含机器人/箱子/场景物体、PD、材质、动作延迟、观测和事件时钟；均固定2200轮课程（推扰0.30、箱子yaw2.2°），不是当前正式训练更强推扰的评估。

比较首回合2–20秒，排除启动阶段；200Hz物理遥测中腿部关节加速度RMS（rad/s²）如下：

| 起点 | model2800 | model4200 | 变化 | 平均机体水平速度（m/s） |
|---|---:|---:|---:|---:|
| 默认空手 | 93.0 | 92.1 | -0.9% | 0.126 → 0.086 |
| loco 1 | 40.0 | 40.4 | +1.0% | 0.075 → 0.056 |
| loco 2 | 52.6 | 50.6 | -3.8% | 0.112 → 0.096 |
| hold | 126.4 | 74.8 | -40.9% | 0.158 → 0.069 |

四个起点平均移动速度都下降，持箱组下降约56.3%。腿部速度≥8Hz功率占比依次为35.9%、29.6%、28.9%、55.5%；持箱组该占比反而从47.7%升高。RMS也包含接触冲击与运动幅度，不能单独用作抖动根因或改善百分数。

膝关节目标仍频繁被裁剪：各侧92.3%–100%，双膝平均为94.9%、100%、96.4%、100%。这是目标命令裁剪，不是实际限位接触次数。三个空手起点有内部接触力>1N的物理步比例分别为2.75%、0%、69.36%，因此本次也不支持把所有空手抖动统一归因于自碰撞；本轮没有改变碰撞配置或做新的因果消融。

已检查关键帧拼图及5、15、19.96秒原图。四台均完整20秒，仅超时reset，倾倒/高度/箱速失败计数为0。三台空手的水平箱距从0.90/1.41/1.43m缩短到0.68/0.70/0.49m，比model2800末段0.82/0.76/0.71m更近，但手箱接触仍全部为0，箱子始终贴地，没有地面抓起行为。hold组持续接触并保持箱子离地，本回合未触发配置中的成功标记；起始已持箱，不能算地面拾箱。视频末帧保留20秒超时切换，没有剪掉回合。

500帧、1080p/25fps视频完整解码通过。单seed四环境用于本段观察，不能认定训练收敛、正常行走或总体成功率。正式训练、源码和checkpoint均保持。

视频：/home/cao/perceptual_ball/outputs/carrybox/wall5_play_compare_20261023_1704/wall5_rev27_model4200_4robots_high20s.mp4。严格加载、完整解码及关键帧检查通过；正式训练和生产源码保持。没有待恢复工作，后续录像新建目录。
