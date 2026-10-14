# AgileKickball-v3：稳定性修复与 v2 权重初始化

任务：`Template-Perceptual-Ball-AgileKickball-v3`。当前 revision：`feedback_stable_20261008`。

2026-10-08 排查确认：前一版 `state_feedback_20261006` 已训练 50000 轮，但没有学会连续恢复。当前版本保留 v2 物理任务和球状态反馈结构，修复辅助学习的梯度路径与配置，并从已收敛 v2 初始化主策略。它是一次有明确初始化来源的新训练，不是恢复失败 v3 的训练状态，也不是 scratch 基线实验。

## 失败证据与原因边界

最后 1000 轮训练指标：

| 指标 | v2 | 失败 v3 |
|---|---:|---:|
| 平均 episode 时长 | 53.07 s | 1.176 s |
| 近期恢复发球份额 | 94.37% | 0% |
| 最终课程球速上限 | 6 m/s | 2 m/s，扩展未解锁 |
| 可见球位置向量 RMSE | 20.88 cm | 4.71 cm |

RSL-RL 的 `Train/mean_episode_length` 原始单位是控制步；本表乘以 0.02 s。这些是训练分布上的诊断，各自课程速度不同，不能比较位置误差来宣称感知方法更好。训练 termination 标量是各环境最后存储的终止类型，不是新发生事件的统计比例。

实际保存的 agent/env 配置对比显示，几何、奖励、恢复标准和终止阈值没有漂移。以同样的 0.4–2 m/s、1.3–2 m 距离回放，64 环境各运行 1500 控制步（30 s）：v2 确定性策略恢复发球 855 次，失败 v3 为 0，关闭 v3 残差仍为 0；采样动作时 v2 为 567，v3 为 0。v3 确定性回放新发生 1657 次终止，其中 1649 次走出边界。主策略已经学偏，单独关闭残差或归咎探索噪声不能解决问题。详见 [replay.json](stability_fix_20261008/replay.json)。

真实 512 个状态上的探针发现：位置 log 标准差三个维度的 raw 输出全部低于 -4，被旧硬截断固定；均值误差的精度权重达到约 2981。NLL 对共享编码器的梯度范数约为同尺度 `0.5×normalized MSE` 的 1369 倍。一次恢复旧 Adam 状态的辅助步，在该批上的未回退动作 KL 为 0.0296；将学习率从 1e-3 降到 1e-4 时为 0.000316。此前训练接受了 199767/200000 个辅助批，说明模块确实在更新。详见 [probe.json](stability_fix_20261008/probe.json)。

已确认的问题是方差硬截断饱和，以及高精度 NLL 可以直接更新主策略共享编码器；残差动作限幅约束不了这条路径。回放和探针支持修复这些机制，但不是单因素消融，尚不能把整个训练失败因果地归于某一个参数。

## 本次配置与实现修改

| 项目 | 失败 v3 | 修复 v3 |
|---|---|---|
| 主策略初始化 | 从零训练 | 加载已收敛 v2 的 encoder、主 actor、critic/归一化、动作 std 和 AMP 权重 |
| NLL 更新范围 | encoder + 预测头 | **仅预测头**，输入特征 detach；主 encoder 仍由 PPO 更新 |
| log 标准差 | 硬 clamp [-4,1] | 平滑 sigmoid 映射到 [-2,1] |
| 辅助学习率 | 1e-3 | 1e-4 |
| PPO 初始学习率 | 1e-3 | 1e-5，保留 adaptive KL 调度 |
| 完整动作辅助 KL 上限 | 0.01 | 0.001 |
| 修正动作上限 | 0.25 raw action | 0.1 raw action，即每关节最多 0.025 rad |
| 新预测头、残差 | 随机头、残差末层零初始化 | 相同；不加载失败 v3 权重 |
| PPO/辅助/AMP 优化器与迭代 | 从零 | 全部新建，迭代从 0 开始，不迁移 v2 优化器 |
| 课程起点 | E=0，0.5–0.7 m | 显式 E=60000，1.3–2 m、0.4–1.1 m/s，扩展仍锁定 |

物理规则保持 v2：横向 ±0.25 m，机器人离 anchor 0.6 m，球结束半径 3 m；控制 50 Hz，恢复要求连续稳定 0.3 s、最少等待 0.4 s、恢复超时 5 s。奖励、PPO 算法及其余参数、AMP、课程门槛与上限 6 m/s 不变。真实恢复测试发现迁移后直接使用从零训练的 PPO 初始学习率会破坏已有站立能力，因此新 v3 的初始学习率降到 1e-5，仍使用原 adaptive KL 调度。没有放宽标准制造恢复成功。

当前预测标签仍是完整机器人姿态坐标系中的位置，以及旋转到该系中的世界速度（没有减去机器人速度），尺度分别为 3 m、6 m/s。Gaussian NLL 可以为负。actor 只读本体历史/深度历史；训练真值不进入动作分支。

门控仍依据最近可见程度和预测标准差，动作修正从零输出开始。新方差下界是保守工程限制，不是经过校准的不确定性保证。当前可见性规则针对解析球深度图，不适用于任意实拍深度。导出包含预测头、平滑方差映射、门控、主 actor 和残差。

NLL 被明确配置为独立预测头训练，并不意味着超出 KL 后允许 head-only fallback。所有辅助尝试仍检查完整动作在批内和固定 monitor 上的 KL；失败恢复本次优化的全部参数及 Adam，整批跳过。新 schema2 元数据记录这些设置，普通 resume 必须一致。

## 正式训练

```bash
cd /home/cao/perceptual_ball
bash scripts/rsl_rl/train_agilekickball_v3.sh
```

默认 4096 环境、cuda:0、50000 迭代、seed 42、24 步 rollout、PPO 5 epoch / 4 minibatch；运行名 `feedback_stable_20261008_v2init`。脚本显式传入 `--warm_start_v2`，源文件为：

`logs/rsl_rl/agilekickball_v2/2026-09-25_22-18-55_v1_speed_only_20260925_scratch/model_49999.pt`

源路径、SHA256、迁移/新建项写入 run 的 `initialization.json` 和每个 checkpoint。开始前验证 v2 初始化动作及 critic 输出逐元素一致，AMP 权重一致，三个优化器为空。新课程起点来自配置，不读取 v2 已完成课程。

当前正式后台实例见 [launch.json](stability_fix_20261008/launch.json) 和 [verified_start.json](stability_fix_20261008/verified_start.json)。已有实例运行时不要重复启动。新版本中断续训可用同脚本追加 `--resume --checkpoint <新版本模型绝对路径>`，此时脚本不再传 warm-start。`V3_SCRATCH=1` 可显式禁用权重初始化，但课程仍由当前配置决定，不能直接当作原 scratch 配方。

TensorBoard 中辅助接受数看 `Loss/aux/predictor_updates`，`Loss/aux/encoder_updates` 应为 **0**，表示已阻断 NLL 对主编码器的更新。同时检查 `Loss/state_feedback/total_aux_updates`、`residual_abs_mean_raw`、`gate_mean`、阶段 KL、episode 长度、真实累计 `AgileKickball/recovered_serves` 和课程进度。

## 验证与历史兼容

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_state_feedback.py
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py
bash scripts/rsl_rl/smoke_agilekickball_v3.sh
```

本次验证增加独立预测头梯度隔离、平滑方差和动作界限、v2 权重精确迁移与新优化器、schema2 恢复及拒绝旧配置。真实仿真要求迁移前后及更新/续训后确实发生恢复发球；另用 4096 环境正式参数执行 100 轮短训，检查恢复、有限值和模块更新。结果以 [receipts.json](stability_fix_20261008/receipts.json)、[smoke.json](stability_fix_20261008/smoke.json)、[scale_smoke.json](stability_fix_20261008/scale_smoke.json) 为准。短训通过不等于长期收敛。100 轮后模型在与故障诊断相同的 64 环境 × 1500 步、0.4–2 m/s、1.3–2 m 回放中恢复发球 900 次，发生 12 次走出边界终止，无倒地终止，详见 [replay_repaired.json](stability_fix_20261008/replay_repaired.json)。该模型继承 v2 权重，因此这些数字不能单独证明新增反馈模块带来提升。

失败反馈版归档任务为 `Template-Perceptual-Ball-AgileKickball-v3-StateFeedback-20261006`；更早的未来后果版使用 `Template-Perceptual-Ball-AgileKickball-v3-Outcome`。原日志和模型不覆盖，旧配置默认行为与 checkpoint 兼容；新任务不能普通 resume 这些旧模型。修改前文件和本次证据保存在 `stability_fix_20261008/`。

这轮使用 v2 预训练，后续论文比较必须明确计算预训练预算、使用相同评测分布，并做多种子和消融。不能把恢复能力的初始化继承当作新增模块优于 v2 的证据。
