# wall10：24步正式训练启动

2026-10-24 00:17 JST：wall10按用户选择24步正式fresh训练已启动，PID2402395；4096环境、20000轮、seed42、PPO 5×4。核验至iteration15，近10轮平均4.332s、最慢4.360s。首个checkpoint schema2/rollout24，策略与AMP参数有限、优化器已有更新。

启动与短时运行核验完成；正式训练进行中，未作独立成功率评估。生产默认仍为100步，本次通过CLI指定24步，从零训练，其他既有训练参数保持。

正式目录：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled10/2026-10-24_00-12-57_wall10_24step_fresh_20261024_001253`。PID与迭代为核验时间快照，后续操作前须再次只读核对。

启动命令（已执行，请勿重复执行）：

```bash
CARRYBOX_VARIANT=10 bash scripts/rsl_rl/train_carrybox_walled.sh agent.num_steps_per_env=24 --num_envs 4096 --max_iterations 20000 --seed 42 --run_name wall10_24step_fresh_20261024_001253
```

实时日志：

```bash
tail -n 100 -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled10/train_wall10_24step_fresh_20261024_001253.log
```

按Ctrl+C仅退出日志查看，后台训练继续。正式模型每500轮保存。

证据：[启动记录](launch.json)、[运行核验](health.json)、[检查回执](receipts.json)。核验读取实际进程、运行参数、连续迭代、首个checkpoint和TensorBoard事件；不创建额外仿真。
