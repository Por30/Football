# AgileKickball v0（2026-09-20 学习链路修复）

任务：`Template-Perceptual-Ball-AgileKickball-v0`。保留 v0 的机器人、奖励、actor/critic 输入维度、8 帧合成深度和主要网络结构。新增观测组 `ball_status` 只用于诊断，不进入 actor/critic。历史实现与失败诊断保留在 `validation/`；当前验证以 `learning_validation/` 和 `learning_test_receipts.json` 为准。

## 启动训练

在已配置 IsaacLab 的 ball 环境、项目根目录执行。已经运行的 Python 进程不会热加载此次修改；结束旧训练后开新 run，从头训练：

```bash
python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-AgileKickball-v0 \
  --num_envs 4096 \
  --device cuda:0 \
  --headless \
  --max_iterations 50000 \
  --seed 42 \
  --run_name learning_fix
```

日志：`logs/rsl_rl/agilekickball_v0/<时间>_learning_fix/`。本次没有启动 50000 轮长训练或修改旧 checkpoint。

## 发球与恢复

完整 episode reset 已经重置机器人为默认站姿（RSI=0），此时立即初始化第一颗**运动中的球**，不再等待尚未学会站稳的策略通过恢复门控。清除上一球奖励脉冲，初始化上一帧球速度，避免把发球瞬移当成踢球。旧实现 reset 后再次把球放到 2.5 m 静止点的覆盖已删除。

一球结束后不重置机器人、不清空观测/动作历史，进入恢复；必须连续稳定至少 0.3 秒且等待至少 0.4 秒才可重发。根高度 0.7–0.9 m、重力投影 XY 范数 <0.15 且 z <−0.98、根三维线速度 <0.25 m/s、角速度 <0.5 rad/s、关节速度 RMS <1.5 rad/s，双脚 link 高度 −0.03–0.12 m。稳定中断清零计时。它是运动学代理，不是支撑接触力验证。

恢复等待达到 5 秒则正常终止并 reset；终止优先于同一步恢复。保留 v0 跌倒、倾倒、离开锚点、自碰和非有限值处理，episode 上限 60 秒。球结束仍沿用 v0 距离、后方位置和低速判据，并非一触球就结束。`kick_proxy_successes` 沿用 v0 的速度变化/方向/距离代理，不等于经真实足部接触传感器确认的成功。

## 来球课程

课程由**有效来球控制步数除以环境数**推进：球 active、球到机器人水平向量与球世界水平速度的点积 < −0.02 m²/s，且当前步机器人未终止。等待空转不推进，4096 环境不会比 16 环境按样本总数加速课程。

- 速度：曝光进度 0 → 120000 → 240000 步，上限 0.8 → 1.4 → 2.0 m/s；下限始终 0.4 m/s。
- 距离：曝光进度 0 → 60000 步，从 0.5–0.7 m 增长到 v0 的 1.3–2.0 m。近期来球使初学策略跌倒前能获得可交互样本；依然经过真实物理滚动。
- 课程在 episode reset 时更新采样范围，只影响随后发出的球，不改运动中的球。
- 新 checkpoint 保存环境数归一化后的曝光计数；`--resume` 恢复优化器时自动恢复进度。旧 checkpoint 没有该字段，曝光从 0 开始。删除旧 `start_step` 用法；当前不再按全局空转控制步推进。

## 监督和日志

监督目标依旧 6 维：root 坐标系下球位置，以及球**世界线速度旋转到 root 坐标系**。后者未减机器人速度，不能叫球相对机器人速度。预测头只从深度编码特征回归，结构没有增加本体信息。

`Loss/ball_regression` 现在是 PPO 更新后、辅助更新前对整个 rollout 每个样本统计一次的真实 MSE；不会因 KL 拒绝而变成零。分层的向量 RMSE 定义为 `sqrt(mean(sum_xyz(error²)))`，不是逐坐标 RMSE。P95 是逐样本三维误差范数的第 95 百分位。

TensorBoard 标签：

- `Loss/ball/{all,active,visible,active_visible,incoming,near_foot}/count` 与 `/fraction`：分层样本数和占全部 rollout 的比例。分层重叠。
- 同一前缀下 `position_cm_rmse`、`position_cm_p95`、`velocity_m_s_rmse`、`velocity_m_s_p95`：位置 cm，速度 m/s。count=0 时不写该层误差，不能把旧点当成当前有效值。
- `visible` 指最新深度帧有球像素，仅适用于当前无噪声、远裁剪 3 m 的合成深度；近脚层是球心距离任一 ankle link <0.35 m，不能当作接触。
- `Loss/aux/encoder_updates`、`head_only_batches`、`rejected_trials`：区分编码器更新、只更新预测头和试探拒绝。
- `Loss/aux/stage_monitor_kl`：固定最多 512 个 rollout 样本上的辅助阶段累计 actor KL；它是采样监测，不是全状态保证。`aux_action_kl` 是接受更新的 minibatch KL；`trial_max_kl` 含被拒绝的试探。
- `AgileKickball/initial_serves`、`recovered_serves`、`waiting_fraction`、`incoming_steps_per_env`、`near_steps_per_env`、`kick_proxy_successes`：分别观察首球、恢复后发球、等待、来球曝光、可交互覆盖和踢球代理。

Agile 辅助更新每轮遍历 rollout 一次（4 个 minibatch），PPO 默认仍为 5 epochs。辅助每个 minibatch 最多 7 次试探，学习率从 1e−3 按 0.25 倍递减，每次恢复参数及 Adam 状态；接受要求 minibatch 和累计监测 KL 均 ≤0.01。全部拒绝则回滚编码器并只训练预测头（encoder.grad=None），继续余下 minibatch。其他任务默认保留原辅助 epochs/拒绝处理，只共享真实误差修复。

## 实测与限制

当前 23 项 CPU 回归测试和真实仿真短训练均通过。16 环境、32 轮 PPO、1 个 PPO epoch/轮（验证预算；正式训练仍为 5），每轮 24 控制步。训练种子 42，固定留出种子 1731，独立新轨迹种子 9271；评估不更新网络/归一化。网络从头初始化；旧 model_5400 仅在同一留出集只读对照，不是公平训练预算比较。

固定留出 1536 个样本，其中活动且可见 972 个：

| 分层/指标 | 新网络训练前 | 新网络32轮后 | 旧model_5400 |
| --- | ---: | ---: | ---: |
| 活动且可见：位置 RMSE / cm | 77.67 | 19.72 | 92.54 |
| 活动且可见：速度 RMSE / m/s | 0.680 | 0.227 | 0.544 |
| 活动且可见：位置 P95 / cm | 89.54 | 30.28 | 103.25 |
| 活动且可见：速度 P95 / m/s | 0.830 | 0.362 | 0.707 |
| 近脚661样本：位置 RMSE / cm | 65.91 | 34.11 | 106.95 |
| 近脚661样本：速度 RMSE / m/s | 0.530 | 0.541 | 0.478 |

监督位置误差下降，近脚速度误差未改善。不能把整体改善概括成所有阶段都改善。新种子采样活动且可见 1416/1536，位置 RMSE 18.66 cm、速度 RMSE 0.256 m/s；该轨迹分布不同，不能与固定留出集直接混作前后比较。尚未做深度打乱或常量预测基线，因此误差下降也不单独证明网络充分利用了深度中的球运动信息。

32 轮训练每轮都有来球，平均占比 96.39%，最小 91.15%；近脚样本 1060/12288（8.63%）。编码器辅助更新 128 次，参数 L2 改变 2.871，最大辅助阶段监测 KL 0.00203，未出现永久拒绝或假零 loss。这个短跑从初始化网络开始，实际没有触发回溯；回溯、拒绝回滚与 head-only 路径由 CPU 回归覆盖。

累计初始发球 673 次、恢复后发球 0 次（含评估/reset），说明已解决无来球训练，但**尚未证明策略学会自然恢复后连续击球**。同 episode 第二球、无机器人 reset、稳定中断、超时和终止优先由状态边界测试验证。持续训练仍须同时观察 recovered_serves、episode 长度、近脚覆盖及回球质量，不能只看 serves 或 loss。恢复门槛没有因短跑未学会而降低。

本次没有测 4096 GPU 吞吐，没有完成 2 m/s、高速球或真实相机验证。当前精度是合成深度初级课程短训练的结果，不能用于真机性能承诺。

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_learning.py
bash scripts/rsl_rl/validate_agilekickball_learning.sh
```

原始结果：`learning_validation/result.json`；真实日志：`learning_validation/run.log`；短跑 checkpoint：`learning_validation/model_validation.pt`（仅验证用途，已验证包含辅助/AMP优化器与课程进度的保存加载）。前两次验证脚本/初始化失败及根因保存在 `learning_validation/diagnostics.md` 和 attempt receipts；最终通过回执为 `learning_test_receipts.json`。旧 `smoke_agilekickball.py` 属于已被替代的历史门控方案。
