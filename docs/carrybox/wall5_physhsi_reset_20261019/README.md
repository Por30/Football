# PhysHSI carrybox 与 wall5 revision17 的 reset 对照

2026-10-19，只读审计。用户要求参考本地 PhysHSI 的 reset 逻辑；本次没有修改生产源码、数据、配置，也没有停止或重启训练。CPU 核验通过；未运行物理对照，不能把以下差异认定为失稳原因。

最值得验证的是根部初速度与默认站姿覆盖。PhysHSI 并不是所有回合都恢复完整专家运动状态：20% 从默认站姿开始，80% 使用 RSI，而 RSI 的参考根部速度最终被 ±0.2 的随机值覆盖。wall5 当前全部使用参考姿态并保留参考速度。两者 roll/pitch 终止阈值相同。

## 来源与实际调用

PhysHSI 的 `carrybox` / `carrybox_resume` 都注册到同一个 G1 环境：[注册入口](/home/cao/PhysHSI/legged_gym/legged_gym/envs/__init__.py:65)。本报告描述本地源码默认配置，没有把它当成某个已成功训练 run 的参数快照。

PhysHSI [reset_idx](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:310) 的顺序是：

1. 清理上次 reset 的参考片段索引，选择默认/参考初始化并设置机器人。
2. 根据同一片段及采样时刻设置箱子和支撑台，再设置搬运目标/目标台。
3. 批量提交机器人、箱子、两个平台的 root 状态与关节状态。
4. 清理动作变化、关节速度历史、力矩、脚腾空时间等缓存，用 `q_reset - q_default` 填满动作延迟缓存，再采样随机化参数、清零回合计数。

当前 wall5 则由 IsaacLab reset events 先重置机器人，随后执行 [wall5 reset_scene](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py:32)：分配固定技能 → 参考机器人状态 → 更新运动学并修正足底穿地 → 同步箱子 → 墙与圆柱 → 深度缓存。观察/动作 manager 随后 reset。两者都先确定最终机器人状态，再放箱子；没有发现箱子使用上一回合机器人位置的调用顺序错误。

## 差异及适用边界

| 项目 | PhysHSI 默认 carrybox | wall5 revision17 |
|---|---|---|
| 初始化类型 | hybrid：20% 默认、80% RSI | 100% RSI，没有默认站姿分支 |
| 技能分布 | 每次 reset 重新抽样；总概率约默认20%、loco53.33%、pickup13.33%、carry13.33%、putDown0% | 按环境固定配额：4096 中3277 loco、819 hold、0 pickup，约80/20 |
| RSI 根部速度 | 先读专家速度，随后六维全部覆盖为 U[-0.2,0.2]；线速度单位m/s，角速度rad/s | 保留参考根部平移差分与角速度，除去 yaw 后旋转到对应世界方向；使用 root-link 写入接口 |
| 默认起点 | root高度0.8m、默认关节角加±0.1rad扰动并裁剪，关节速度0；root六维速度仍为±0.5，因此不是完全静止起点 | 没有该分支 |
| RSI 关节状态 | 插值参考关节角，加±0.1rad扰动并裁剪；保留参考关节速度 | 采样原生帧，保留该帧关节角/速度，无同样的每次reset角度扰动 |
| 高度 | `base_height + 0.05`，不按当前脚碰撞几何二次修正 | 同样参考高度加0.05m，另按G1实际足部碰撞凸包向上修正至至少5mm间隙 |
| 初始朝向 | 保留参考yaw和轨迹XY | 归零yaw及相对环境XY，速度和箱子相对向量做一致旋转 |
| 箱子 | loco/default在每个XY轴的远近区间随机；高度可达0.65m，用平台支撑；pickup/hold按参考；箱子速度清零 | loco距0.7–2m、贴地、姿态课程；2% loco视野外搜索；hold保持参考手边高度；没有平台；箱子速度清零 |
| 动作缓存 | 延迟缓存预填reset姿态，默认开启0–4个物理步延迟，最多20ms | 无该动作延迟管线；manager动作/上一动作清零，下次step先处理新动作再推进物理 |
| 观察历史 | 环境reset未见清除actor/AMP历史的处理，不宜整段照搬 | manager清理历史，第一条reset后观测填满相应历史；Warp运动学显式刷新 |

比例依据：[PhysHSI 配置](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox_config.py:168) 的技能权重 `[0.8,0.2,0.2,0]` 总和为1.2，`torch.multinomial` 自动按总和归一化，再乘80% RSI概率。不能直接写成“80/20/20%”。本项目固定80/20环境配额是revision17防止长hold回合挤占采样步数的设计，不应随此参考审计撤回。

根部速度覆盖的直接证据在 [PhysHSI carrybox.py:814](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:814)。它保留了专家关节速度，因此也不是完全静止的RSI；只把根部速度改小并不保证更稳定。

动作缓存依据：[reset预填](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:344)、[每个物理步读取延迟目标](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:747)。wall5中底层JointAction.reset只清raw action，processed target暂存；但 [IsaacLab step](/home/cao/IsaacLab/source/isaaclab/isaaclab/envs/manager_based_rl_env.py:174) 在任何下一物理步前重新process/apply action。本次没有发现“旧动作缓存必然继续推动新回合”的代码路径；没有物理运行证明首次新动作的冲击大小。

## 当前 RSI 的速度尺度

CPU 读取当前13段manifest，核验全部文件hash；其中11段loco与PhysHSI原始carrybox数据逐文件hash一致。按wall5实际的“均匀抽片段，再在0..N-2均匀抽帧”计算3345个候选帧，统计的是写入前的参考根部水平速度，非仿真测量：

| 指标 | wall5 loco参考速度 |
|---|---:|
| 均值 | 0.743m/s |
| 中位数 | 0.788m/s |
| 95%分位数 | 1.071m/s |
| 最大值 | 1.290m/s |
| 超过PhysHSI RSI水平速度理论最大值的采样概率 | 91.54% |

PhysHSI RSI水平速度理论最大值为 `sqrt(2)*0.2 = 0.283m/s`，RMS为0.163m/s。wall5 yaw变换不改变水平速度模长。因此当前空手起点通常已经具有行走速度，而PhysHSI更接近低速起点。这是明确的初始化分布差异；它是否解释失稳，仍需同模型、同参考姿态/箱位、只改变根部初速度的物理对照。

## 终止条件

[PhysHSI check_termination](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:284) 实际启用：abs(roll)>0.5、abs(pitch)>1.1、root z<0.2m、mid360 link z<0.6m、rigid-body索引2水平速度>3m/s、任一hip_yaw link z<0.15m及超时。接触终止函数虽然存在，但默认`terminate_after_contacts_on=[]`。没有reset后的跌倒检测宽限期；成功标记不触发reset。

`gravity_termination_buf` 中的0.8被计算，但没有并入reset_buf，不能当作生效的倾倒阈值。`carrybox_resume` 才启用箱子倾覆终止；默认carrybox关闭。两配置还在AMP系数、总迭代数和resume默认值上不同，但机器人reset路径相同。

wall5当前同样roll0.5/pitch1.1、root低于0.2m；头部使用实际头部COM低于0.4m。没有PhysHSI的hip高度和索引2速度终止，没有成功立即reset，也没有起步宽限期。因此不支持“PhysHSI是靠更宽松roll/pitch条件才不reset”的解释。

## 工程判断

用户进一步询问这两处差异的影响。根部初速度改变的是初始动量及策略接续步态的要求：0.74m/s是已在运动的起点，新策略必须立即协调支撑、落脚和身体平衡；低速起点通常降低这一要求，但参考步态的关节速度仍保留，单独压低根部速度也可能破坏脚相对地面速度的一致性。因此当前专家速度不自动构成bug，低速也不是必然更好。

延迟缓存预填的作用是，在首次新动作尚未到达时令 `q_target=q_reset`，使PD的位置误差项起初为零；速度阻尼项、外力和身体运动仍存在，机器人并未被冻结。PhysHSI每5ms移入一次动作，缓存5格，实际延迟为0/5/10/15/20ms；随后新目标仍可能发生跳变，它没有做目标插值。当前wall5直接执行 `q_default+0.25*action`（经限位裁剪），如果这与RSI关节角差距大，会立即产生较大的位置误差和控制力矩。预填可能影响最初接触瞬态，但不能单独解释持续数百毫秒后的倾倒，更不能把增加整条随机延迟管线视为必然改善：它同时延后了策略的平衡修正。

优先验证低根部初速度这一项，保持关节姿态、数据、奖励、20% hold、PD与终止不变；然后再独立评估是否在80%空手环境内加入默认站姿分支。若采用20%总环境默认站姿，则可保留60% loco RSI＋20% hold，不直接照搬会改变hold/pickup比例的PhysHSI配方。这只是下一步候选，未应用。

保留G1足底接地修正、正确的root-link速度语义和干净历史。PhysHSI包含平台、搬运到目标和放下流程，不能整段移植其箱子/目标reset。两边PD数值相同也不意味着IsaacGym显式力矩与本项目IsaacLab驱动、资产碰撞和接触动力学相同。本次不重做资产或物理对照。

## 验证与训练快照

[evidence.json](evidence.json) 保存18份调用链源码hash、13段数据身份、概率计算及速度统计。[receipts.json](receipts.json) 为一次CPU检查PASS回执。可复核：

```bash
cd /home/cao/perceptual_ball
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_physhsi_reset_20261019/check.py
```

2026-10-19 22:12:47 JST：原revision17 PID254358仍运行，最新134轮，最近10轮3.80–3.87秒。未操作进程；这仅是运行快照，不是稳定行走或拾箱成功证据。
