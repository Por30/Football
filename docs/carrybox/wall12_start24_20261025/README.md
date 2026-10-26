# wall12 正式训练启动

2026-10-25 12:26 JST。用户明确要求“停止足球 启动wall12”。已核对并SIGINT停止足球v11 PID3261150，确认退出、释放至约23GB可用显存。足球最后完整日志iteration278，最新已保存model_0及所有日志保留，尚未到500轮保存点，未完成预定训练。

wall12正式fresh进程PID3269279已于12:32:49重新启动；12:37 JST检查到iteration16，近10轮平均4.471秒、最慢4.500秒。从零训练4096环境×24步、20000轮、seed42、5×4更新，回归块保持现有相机系9维输出与aux系数1.0。正式训练正在运行，尚未完成长训或独立评估。

首次启动PID3268135在首轮更新因TF32大批量尺寸对称判定产生inf退出，未生成模型。已完成[局部数值修复](tf32_fix/README.md)：尺寸轴置换改为精确索引，保留损失定义、尺寸容差和全局TF32；44项CPU及8192样本CUDA TF32前后向测试通过。首轮失败run和原始身份保存在`attempt1/`及原logs路径。本次修复之外的生产源码保持原短测身份。

```bash
cd /home/cao/perceptual_ball
CARRYBOX_VARIANT=12 bash scripts/rsl_rl/train_carrybox_walled.sh \
  agent.num_steps_per_env=24 --num_envs 4096 --max_iterations 20000 \
  --seed 42 --run_name wall12_24step_pose_aux_fresh_20261025_123249
```

查看日志：

```bash
tail -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled12/train_wall12_24step_pose_aux_fresh_20261025_123249.log
```

正式run：`logs/rsl_rl/g1_carrybox_depth/walled12/2026-10-25_12-32-53_wall12_24step_pose_aux_fresh_20261025_123249/`。首模型`model_0.pt`已生成，后续每500轮保存。

只读启动检查`bash docs/carrybox/wall12_start24_20261025/check.sh`通过：首模型schema2/walled12 revision1、4096×24/5×4/seed42及aux1.0契约正确；policy/AMP全部有限，联合Adam完成20步，回归头四组参数均有非零有限Adam动量。TensorBoard辅助位置/旋转/加权损失约0.22290/0.16737/0.39028，每轮辅助样本计数471040（4096×23×5）。这些是启动时的训练损失，不是位姿精度或收敛结论。

此前等待资源授权时检查以exit2停止，原`resource_pending_receipts.json`保留；第一次实际启动失败回执在`failed_launch_receipts.json`与`attempt1/`。成功启动回执为[receipts.json](receipts.json)，完整核验为[health.json](health.json)，源码身份为[source_identity.json](source_identity.json)。
