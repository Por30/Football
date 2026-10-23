---
task_id: "carrybox-wall5-play-compare-20261023-1542"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
allowed_paths: ["docs/carrybox/wall5_play_compare_20261023_1542", "outputs/carrybox/wall5_play_compare_20261023_1542", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play-compare-20261023-1542.md", "agent/task/carrybox-wall5-play-compare-20261023-1542.md", "agent/report/carrybox-wall5-play-compare-20261023-1542.md", "agent/handoff/carrybox-wall5-play-compare-20261023-1542.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "那你就录制下最新的ckp看看抖动有没有改善"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["不修改生产、正式训练、模型、数据或旧产物", "不把持箱参考计为抓起，不以单seed四环境认定收敛"]
steps: ["锁定最新模型和旧model2200比较数据", "复用录像并固定旧课程/初态，仅更换权重", "录制20秒、完整解码并比较200Hz遥测和行为", "检查关键帧、记录结论和项目入口"]
tests: [{"command": "bash docs/carrybox/wall5_play_compare_20261023_1542/record_and_check.sh"}]
stop_conditions: ["身份/契约或初态不匹配则停配对比较", "显存不足6GiB不录制，非有限值则停止", "最多两次范围内修复，保留失败证据"]
safeguards: ["严格加载，权重和生产源hash不变，原训练进程保持", "仅诊断课程固定2200，推扰.30/yaw2.2°，完整披露不等于当前正式课程", "同模型配置同seed和reset随机状态；核对初态、PD、机器人材质、事件时钟与观测", "200Hz按scene.update后采样，50Hz动作；只比较共同首回合，不跨reset差分", "复用既有遥测/视频检查，既有输出不覆盖"]
expert_required: false
device_actions: []
real_device_authorized: false
---

复用既有四机器人20秒录像及200Hz遥测，锁定最新完整checkpoint，仅权重变化，固定2200轮课程和旧回放相同初态，比较关节波动/目标裁剪/接近及抓取行为。正式训练保持。
