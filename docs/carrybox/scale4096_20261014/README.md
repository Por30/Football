# Wall4 4096环境重新启动

2026-10-14 14:18 JST：按用户要求停止128环境训练（最后日志1798轮，model_1600.pt保留），4096环境wall4于14:06从头启动，PID2330803。实际环境配置4096已核对，检查到18/40000轮；平均回合37.23步，AMP有效比例76.86%，model_0.pt有限值及schema2/revision4、根findbox数据身份验收通过。尚未完成训练或证明收敛；动作目标范围问题仍未调整。

只将并行环境数由128改为4096；奖励修复版、seed42、40000轮、相机分辨率/遮挡和AMP数据保持原配置。未使用旧checkpoint初始化，旧队列未恢复。14:18附近GPU总占用约22836/24564 MiB，每轮约25秒。

正式run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_14-06-14_wall4_4096_20261014_140607`。

日志命令：

```bash
tail -n 80 -F /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/restart4096_20261014_140607/train.log
```

[启动身份](launch.json)、[实际运行验收](health.json)、[冻结命令回执](test_receipts.json)。快照不是长期监控或任务成功率评估。

2026-10-14：原PID2330803在23轮按性能优化任务停止。最新状态见[性能优化与新正式run](../performance_20261014/README.md)，旧模型和日志保留。
