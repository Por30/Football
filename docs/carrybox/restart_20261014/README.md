# Wall4 奖励修复后重新启动（2026-10-14）

用户明确要求重新启动训练，覆盖此前保持停止的运行指令。使用revision=4修正的当前失败奖励，schema=2，从头训练，不读取已退化的model_14600.pt；没有恢复旧等待器。控制动作范围、PD、奖励权重未调整，拾取参考目标范围不匹配仍是已知问题，不能以启动成功宣称收敛。

配置：128环境、seed42、40000迭代，RTX深度。AMP与RSI均读取`/home/cao/perceptual_ball/findbox`，17段文件哈希全部核对；CPU跌倒奖励回归2项通过。旧正式run与日志保留。无football或共享代码改动。

启动时间：2026-10-14T12:54:08.325892+09:00；PID：2322385。

正式目录：`logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_12-54-15_wall4_rewardfix_20261014_125408`。

日志：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/restart_20261014_125408/train.log`。

```bash
cd /home/cao/perceptual_ball
tail -n 80 -F logs/rsl_rl/g1_carrybox_depth/walled4/restart_20261014_125408/train.log
```

启动命令（已执行，不要重复启动）：

```bash
env CARRYBOX_VARIANT=4 bash scripts/rsl_rl/train_carrybox_walled.sh --max_iterations 40000 --run_name wall4_rewardfix_20261014_125408
```

运行身份见[launch.json](launch.json)，修复版本及数据哈希见[provenance.json](provenance.json)，冻结回归见[test_receipts.json](test_receipts.json)。PID/指标为时间快照，后续以进程和实时日志为准。

## 启动验收快照

2026-10-14 12:55 JST：用户重新授权后，修正跌倒奖励的wall4已从头启动，PID2322385；128环境、seed42、40000轮，AMP/RSI使用根findbox。检查到iteration24，平均回合32.92步、AMP有效比例77.47%，model_0.pt的schema2/revision4及有限值已核验。拾取动作目标范围问题未调整，未证明收敛。详细快照见[health.json](health.json)。正式训练保持后台运行，本次完成的是启动任务而非40000轮训练或独立评估。

2026-10-14 14:05：本页128环境进程按用户要求停止，最后日志1798，保留model_1600.pt。后续见[4096环境新run](../scale4096_20261014/README.md)。
