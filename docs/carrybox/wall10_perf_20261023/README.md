# Wall10 深度与学习性能优化

2026-10-24（任务于10月23日开始）。实现完成，定向检查和真实4096环境短测通过；未启动或恢复正式长训，未评估拾箱成功率。

4096×100完整短测从52.81s降到18.49s/轮，学习从40.89s降到7.63s；另测4096×24为4.41s/轮。默认仍保持PhysHSI的100步rollout、5 epochs×4 minibatches；本地历史约4秒成绩使用24步，不能直接与100步一轮比较。

## 同机器计时

RTX4090，4096环境，24个PyTorch CPU线程，相同正式model_0、seed42、奖励/物理/网络。排除场景创建、首轮预热；baseline第3轮另有profile，不参与均值。边界CUDA同步计时，循环中未插入分项同步。两组训练会因浮点差异产生不同轨迹，不是逐轨迹复现。

| 配置 | 采样 s | 学习 s | 合计 s |
|---|---:|---:|---:|
| 修改前，100步 | 11.916 | 40.891 | 52.807 |
| 修改后，100步 | 10.859 | 7.634 | 18.492 |
| 修改后，24步，仅作另一工作量测量 | 2.602 | 1.807 | 4.409 |

100步同规模耗时降低65.0%，吞吐约2.86倍。旧用户run的TensorBoard最后几轮约48秒（采样约11、学习约37），本次固定配置对照见上表。进程2394108在检查时已退出，本次没有停止它或修改其模型。

场景创建单独耗时：baseline 204.8s、candidate 202.0s。100步候选PyTorch峰值分配17.75GB，不含PhysX/驱动等额外显存。

## 改动

1. 原更新每轮7920个256样本微批。保留每256行的动作采样RNG消耗、smooth随机数、专家片段/时刻和共享时间倍率；将纯计算合并到最多8192行。每完整PPO minibatch仍只有一次联合Adam，共20次。AMP参数采样顺序不变，插值批量执行。
2. current和mixed深度一起编码，再分别计算各自actor输出；critic仍是独立MLP。没有复用旧latent或省略smooth图像。更新时仅索引实际参与损失的观测，避免复制标签/AMP观测副本；rollout保存内容不变。
3. KL和日志在GPU累计，每完整minibatch读取KL、每轮集中读取日志；loss/梯度非有限检查仍在优化器更新前执行。
4. 可变尺寸箱子的逐像素相交由大规模Torch广播改为单个Warp slab kernel；原完整机器人/地面/墙/支撑板BVH、50Hz、4×27×48米制FP32深度和近远裁剪保持。partial rows、平行光线、盒内出口和最近遮挡保留。
5. 外力只在每8策略步的首个物理子步写入，随后子步显式清零；省去其余零外力写入。原力脉冲、PD、力矩限幅和RSI未改。

checkpoint仍schema2；原amp_config中的cnn_microbatch=256继续约束逻辑随机分块，执行批8192只改变计算布局。原wall10正式checkpoint和新保存checkpoint均已严格恢复，联合Adam与当前学习率恢复正常。其他任务、共享CNN/相机、资产和动作数据未改。

## 验证及数值边界

- 34项CPU检查通过：原wall10/CarryBox/AMP/足球回归，加逻辑采样与RNG、loss/梯度/一次Adam/KL、非有限值拦截、Warp边界与partial rows、连续72个物理步外力序列。等价外力效果下，setter调用从72次降到4次。
- 固定4096×24数据上，完整5×4学习更新时间从8.031s降到1.910s；GPU RNG最终状态相同，联合Adam20次更新且参数有限。
- CPU严格单次更新对照使用512执行批及小网络。GPU大批归约/TF32改变浮点计算顺序，多次更新可放大差异，并可能改变临界KL调度分支；不宣称参数或轨迹逐位一致。本次GPU20次更新后policy/D最大参数差分别为0.00668744/0.00282595。
- 16环境原100步、5×4更新的2+1轮、partial reset、终止观测、力矩限幅、旧任务隔离、JIT/ONNX导出通过；实际随机尺寸箱体三角网格对照最大深度差3.57627869e-07m，仅代表本组验收场景。
- 4096环境100步4轮更新、旧正式checkpoint加载及新验证checkpoint严格恢复通过；随后24步4轮计时通过。所有验证模型仅保存在本目录。

首次CPU检查遗漏Warp初始化，已在测试夹具补齐，保留cpu_attempt1.log。首次4096串测完成100步及恢复后，在切换24步时因验证脚本复用推理张量的reset上下文中断；补齐inference_mode及异常输出后16环境复现通过，再原样重跑三条冻结验收。失败回执与100步记录保留在attempt1/，未删断言或更改生产语义。

## 使用

默认原100步配方：

```bash
CARRYBOX_VARIANT=10 bash scripts/rsl_rl/train_carrybox_walled.sh
```

若明确采用与本地约4秒基线相同的24步rollout，可新建训练：

```bash
CARRYBOX_VARIANT=10 bash scripts/rsl_rl/train_carrybox_walled.sh agent.num_steps_per_env=24
```

24步改变rollout长度、minibatch样本量与每轮采样数，不能把相同迭代数当作原100步的等量训练；旧100步checkpoint应按100步严格恢复。当前未自动切换默认或启动正式训练。

原始结果：receipts.json、comparison.json、baseline100.json、candidate100.json、candidate24.json、learning.json、smoke.json、validated_sources.json。冻结验收命令见agent/task/carrybox-wall10-perf-20261023.md。
