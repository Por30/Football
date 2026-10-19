---
task_id: "carrybox-wall5-play11000-20261019"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["docs/carrybox/wall5_play11000_20261019", "outputs/carrybox/wall5_play11000_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play11000-20261019.md", "agent/task/carrybox-wall5-play11000-20261019.md", "agent/report/carrybox-wall5-play11000-20261019.md", "agent/handoff/carrybox-wall5-play11000-20261019.md"]
task_contract_sha256: "f19f240c1634e0ec80f14aae43a9cf9497505cfd6c09769e416b26b10ed780f0"
tests: [{"command": "bash docs/carrybox/wall5_play11000_20261019/record_and_check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "53191eb1671dc6f341cb7236b4dec75081c5433cf007eb1d9d3ba79efaecbdf1", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

指定revision14 model11000录像已完成，MP4在outputs/carrybox/wall5_play11000_20261019/wall5_rev14_model11000_play_20s.mp4。严格对照归档环境与权重，无生产修改。实际录制：完成2个回合，loco 10步（tipped，pitch=1.225rad）；loco 10步（tipped，pitch=1.151rad）。窗口结束仍处于hold起点回合，已经持续980步（19.60秒），未完成回合。这段视频未展示从地面找箱并完整抱起的成功流程。

500帧/25fps/20秒完整解码通过，关键帧已视觉检查。实际模型和源码hash在recording.json；只做推理，不更新优化器/AMP或导出覆盖训练工件。现有视频不会被脚本静默覆盖；再次录制应另存新输出。

后台PID4038923仍运行，源码revision15保持，独立录像使用归档rev14。无需恢复任务；短视频不作为成功率证据。
