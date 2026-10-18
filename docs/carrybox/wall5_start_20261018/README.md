# Wall5正式训练启动核验

时间：2026-10-18T12:33:38+09:00。用户启动的PID 3804340正在运行4096环境、fresh、40000轮wall5 revision13；连续12秒观察迭代8→10，不是仅存活或停留在构建场景。

已生成model_0.pt，验证CarryBox schema2、environment revision13、AMP schema3/10×60、13段ground_pickup、RSI80/0/20、held reference、pose coef0.1及adaptive PPO均正确。策略/AMP参数、PPO/AMP优化器状态有限且优化器非空，Normalizer统计已初始化；AMP有效率100%。

第1–10轮平均7.001秒，最大7.21秒，当前尚未达到之前6秒/轮目标。第10轮episode length约30.64步、辅助位置loss0.1543，仍是训练初期，不能判断收敛。启动阶段场景构建123.36秒、仿真初始化150.73秒，不应当作每轮训练耗时。

日志：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_v13_20261018_122733.log`。
模型：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_12-27-37_wall5_v13_hold_rsi/model_0.pt`。

本次只读核验，没有修改配置、启动/停止/重启进程或额外GPU仿真。详细快照[snapshot.json](snapshot.json)，真实检查回执[receipts.json](receipts.json)。
