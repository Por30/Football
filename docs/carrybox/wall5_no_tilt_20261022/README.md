# wall5 revision25：取消角度终止并重新训练

2026-10-22。按用户本次要求，仅取消 roll/pitch 直接终止。**本地 PhysHSI 的 carrybox.py:303 同样含有角度终止**，所以这次是用户明确指定的例外，而不是声称与原始 PhysHSI 完全一致。原函数与hash保存在 [physhsi_termination.txt](physhsi_termination.txt)。

## 最终终止配置

| 条件 | revision25 |
|---|---|
| 原 `abs(roll)>0.5` / `abs(pitch)>1.1` | 未注册，不再触发 reset |
| 根部高度 | pelvis link origin 相对环境地面 `<0.2 m` |
| 头部高度 | mid360_link origin 相对环境地面 `<0.6 m` |
| 髋部高度 | 任一 hip_yaw link origin 相对环境地面 `<0.15 m` |
| 箱子水平速度 | 世界坐标 XY 速度模长 `>3 m/s` |
| 超时 | 20秒 / 1000 policy步，policy 50Hz |
| 非有限值 | 保留 FloatingPointError 检查；不允许继续传播 NaN/Inf |
| 箱子倾倒 / 任务成功 | 均无单独 reset |

父环境在回合结束时仍记录实际姿态是否超过原阈值。wall5将日志名改为 `Skill/{loco,pickup,hold}_tilt_at_episode_end_fraction`，明确这是**回合结束姿态统计**，不是角度导致reset的比例。`Episode_Termination/tipped` 不再存在。其他原因仍分别记录；本地 manager 的 Episode_Termination 标签会保留且覆盖其他同时触发项，不能直接当作近期回合比例。

仅修改 wall5 配置与 checkpoint/诊断接口两个生产文件。revision24 checkpoint 严格恢复到新环境会拒绝；本次使用新的正式run从零初始化，不加载旧模型或短测模型。保留 actor 372维本体+4×27×48米制深度、独立123维critic、60维AMP、辅助监督系数1.0、完整15段数据和PhysHSI混合RSI/动作延迟。足底穿地与奖励尺度问题未在本轮修改。

## 验证

32环境仿真，用抬高的机器人隔离高度条件，写入 roll=±0.6、pitch=±1.2 rad，确认原角度检测为true而终止管理器不触发；再分别验证低高度、箱子速度3.01/2.99 m/s和1000步超时。实际终止列表只有 time_out、invalid、fell_pelvis、fell_head、fell_hip、box_speed。

一轮完整PPO/AMP更新参数有限，actor/critic/CNN/辅助头有更新，新checkpoint可严格恢复，旧revision24被拒绝。新旧checkpoint环境契约仅改变revision、roll描述/阈值、终止角度配置、诊断语义五个顶层字段。wall3/wall4仍注册倾斜终止；生产源码hash确认除两个wall5文件外无本轮修改，足球和共享资产未改。

执行：`bash docs/carrybox/wall5_no_tilt_20261022/smoke.sh` 与 `bash docs/carrybox/wall5_no_tilt_20261022/start_and_verify.sh`。详见 [smoke.json](smoke.json)、[receipts.json](receipts.json)。短测只验证实现与训练运行，不证明学会走路或拾箱。取消角度早终止可能使回合变长，也可能让已经失稳的状态继续运动；不能把回合变长直接当成稳定性提升。

## 正式训练验收快照

2026-10-22T22:04:34.032669+09:00：旧revision24 PID **1760747** 已退出，日志最后第 **1270** 轮；保存到 `/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-22_20-33-25_wall5_v24_physhsi_fresh_20261022_203320/model_1200.pt`，所有旧文件保留。

新 PID **1792770**，4096环境、seed42、40000轮、**从零初始化**；首模型schema2/revision25、全新优化器step20与AMP计数61440、参数有限，环境契约与短测一致。核验到第 **16** 轮，近10轮平均 **3.914s/轮**、最慢 **3.930s/轮**。

Run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-22_22-00-37_wall5_v25_no_tilt_fresh_20261022_220032`

```bash
tail -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v25_no_tilt_fresh_20261022_220032.log
```

[正式启动快照](snapshot.json)、[来源身份](validated_sources.json)、[执行回执](receipts.json)。训练正在进行；目前未评估是否学会稳定行走或拾箱，也未修复之前诊断的接地缺陷。
