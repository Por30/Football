---
task_id: "carrybox-wall5-play14200-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["docs/carrybox/wall5_play14200_20261020", "outputs/carrybox/wall5_play14200_20261020", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play14200-20261020.md", "agent/task/carrybox-wall5-play14200-20261020.md", "agent/report/carrybox-wall5-play14200-20261020.md", "agent/handoff/carrybox-wall5-play14200-20261020.md"]
task_contract_sha256: "51f0a6d082de2b2e9197e08442e15c2a9e35d7e56e842ba25ccf5e2f8945bfc1"
tests: [{"command": "bash docs/carrybox/wall5_play14200_20261020/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "31efd14a27beb01cbdebf5f054b723d2bafb8cb91a69848cc2c79d7baca4c84f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

本次选定最新正式model14200已严格加载并完成20秒MP4；路径/home/cao/perceptual_ball/outputs/carrybox/wall5_play14200_20261020/wall5_rev17_model14200_play_20s.mp4。已检查0.04、1、2、5、10、15、19.96和20秒关键帧，主体和箱子清晰可见。机器人在前1–2秒走近箱子，随后主要在箱旁站立和小幅调整，箱子仍在地面，没有完成抱起。第999步相对首步水平位移约1.05m，距箱约0.33m。全强度推扰配置下，此段未出现倾倒/低高度终止，唯一reset发生在1000步20秒超时；仅代表该单起点回放，不作为成功率评估。

完成1次自动reset，窗口末回合已持续0.00秒。记录到严格lift成功标记的完成回合数为0；窗口末回合标记为False。这是一段单环境视频，不是成功率评估。

500帧完整解码PASS，关键帧已视觉检查；源代码和checkpoint hash保持，未修改生产配置或操作后台训练。身份及回合数据见docs/carrybox/wall5_play14200_20261020。已有输出不覆盖，重新录制另存目录；无需恢复任务。
