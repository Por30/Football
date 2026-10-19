---
task_id: "carrybox-wall5-latest-play-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["docs/carrybox/wall5_latest_play_20261020", "outputs/carrybox/wall5_latest_play_20261020", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-latest-play-20261020.md", "agent/task/carrybox-wall5-latest-play-20261020.md", "agent/report/carrybox-wall5-latest-play-20261020.md", "agent/handoff/carrybox-wall5-latest-play-20261020.md"]
task_contract_sha256: "fa53b7888b015d2592a2808c59ee130fbdc29edf401c9f6f7680a3fb6c37a929"
tests: [{"command": "bash docs/carrybox/wall5_latest_play_20261020/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "32e6106c666a5b9ae2b761007ede9d3efcba38ee39bd695e18b97964aec1f725", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

本次选定最新正式model2800已严格加载并完成20秒MP4；路径/home/cao/perceptual_ball/outputs/carrybox/wall5_latest_play_20261020/wall5_rev17_model2800_play_20s.mp4。已检查0.04、1、2、5、10、15、19.96和20秒画面，机器人与箱子清晰可见。此段空手起点回放能向箱子移动，前两秒接近后主要在箱旁站立；第999步相对首步水平位移约1.33m，距箱约0.41m。箱子仍在地面，没有完成抱起。整段没有倾倒/低高度终止，唯一reset发生在第1000步，是20秒超时；这不能代替多起点稳定行走评估。

完成1次自动reset，窗口末回合已持续0.00秒。记录到严格lift成功标记的完成回合数为0；窗口末回合标记为False。这是一段单环境视频，不是成功率评估。

500帧完整解码PASS，关键帧已视觉检查；源代码和checkpoint hash保持，未修改生产配置或操作后台训练。身份及回合数据见docs/carrybox/wall5_latest_play_20261020。已有输出不覆盖，重新录制另存目录；无需恢复任务。
