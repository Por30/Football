# wall11 正式训练启动（24步）

用户于2026-10-24明确要求停止当前训练并启动wall11。本次只切换正式训练，不改生产实现或配方。

## 旧训练停止

wall10 PID2402395经进程cmdline核验后发送SIGINT，已退出。最后日志iteration 11147；最新已保存模型为`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled10/2026-10-24_00-12-57_wall10_24step_fresh_20261024_001253/model_11000.pt`。停止前后SHA256一致，旧日志与所有已保存模型保留；中断时尚未到下一次保存点的迭代没有额外保存。

## 新训练

启动于2026-10-24T12:34:45.263515+09:00，PID2723259，fresh初始化，不resume或warm start。正式task为`Template-Perceptual-Ball-CarryBox-Walled11-v0`，4096环境、24步/轮、seed42、20000轮、5 epochs×4 minibatches；每500轮保存一次。深度噪声、3圆柱/随机墙、非对称AC、AMP与物理均使用[wall11已验证实现](../wall11_20261024/README.md)。

实际命令：

```bash
CARRYBOX_VARIANT=11 bash scripts/rsl_rl/train_carrybox_walled.sh agent.num_steps_per_env=24 --num_envs 4096 --max_iterations 20000 --seed 42 --run_name wall11_24step_fresh_20261024_123445
```

实时终端日志：

```bash
tail -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled11/train_wall11_24step_fresh_20261024_123445.log
```

## 启动验收已通过

2026-10-24T12:39:09.719645+09:00核验到iteration 14（从0开始的前15轮）。近10轮平均4.394秒，最慢4.430秒；排除了第0轮6.45秒的首次预热。正式训练运行中，尚未完成20000轮或做独立成功率评估。

实际run目录：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled11/2026-10-24_12-34-49_wall11_24step_fresh_20261024_123445`。

- cmdline与参数文件确认4096环境、24步、seed42、20000轮、5×4更新、fresh且aux0。
- 首checkpoint `model_0.pt`为schema2、walled11/revision1、rollout24，记录深度噪声/三柱/随机墙，actor本体558和4帧深度接口保持。
- policy与AMP权重有限，联合优化器有实际更新，TensorBoard事件文件已生成；没有异常堆栈/NaN/Inf/显存不足/PhysX错误。
- 旧wall10 PID2402395已退出，模型`model_11000.pt`停止前后hash一致。

证据：[launch.json](launch.json)、[previous_run.json](previous_run.json)、[health.json](health.json)、[receipts.json](receipts.json)、[source_identity.json](source_identity.json)。本次未修改生产实现、旧模型或动作数据。
