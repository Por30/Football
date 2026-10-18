# Wall5从零正式启动（2026-10-18）

按用户“不用恢复，重新启动”的明确要求，已停止恢复运行PID3810947，保留旧run/checkpoint/log；从零启动当前优化版wall5。

- PID：3812053；4096环境、seed42、40000轮。
- 初始化：fresh，命令无resume/checkpoint/warm-start；实际agent.yaml为resume:false，日志无checkpoint加载记录。
- 首model_0.pt：PPO与AMP优化器step均20（首次5epochs×4minibatches更新），Normalizer running_count=61440（专家初始化20480＋首更新40960）；确认不是继承旧优化器/Normalizer。
- 契约：schema2 / environment revision13 / AMP config3，13段ground_pickup数据、60D AMP，RSI80%loco/0%pickup/20%hold。深度、自遮挡、全身碰撞和性能优化保持，生产源码/配置/数据未改。
- 正式进度快照：2026-10-18T13:16:21+09:00，迭代11→14；最近10轮平均3.801s、最慢3.830s。参数、PPO/AMP优化器有限值检查通过。训练进行中，未完成长训或证明收敛。
- Run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_13-10-42_wall5_v13_perf_fresh_20261018_131037`

查看日志：

```bash
tail -f '/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v13_perf_fresh_20261018_131037.log'
```

launch.json保存实际命令/PID，stopped_run.json保存被替换运行，snapshot.json与receipts.json保存实际检查结果。时间/PID/迭代为快照，下次操作前需实时核对。此前性能与等价性验证沿用../wall5_perf_20261018/，本次只切换fresh启动，不重复额外GPU验证。
