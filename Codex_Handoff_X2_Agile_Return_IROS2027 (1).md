# Codex 交接记忆：X2 机载深度驱动的敏捷回踢，目标 IROS 2027

更新：2026-09-18。用途：让另一份 Codex 直接续接研究讨论。

> 接手说明：优先遵守下文“已确认目标”和“v3 基线”。配置来自用户提供的训练工作流，不等于已经检查源码或复现实验。候选方法均为研究设想，不能描述成已实现或已有实验收益。请继续收敛方法与诊断实验，不必重新询问已经明确的任务和投稿年份。

## 1. 已确认的目标与当前问题

- **投稿目标是 IROS 2027。** 用户已经纠正年份；尚未核验会议截稿日期。
- 当前任务是 **X2 人形机器人用机载头部深度相机观察传来的滚动足球，敏捷地一触回踢，逐步加入指定回传区域，并恢复到能处理下一球的状态**。
- 研究重心是**高速来球下的反应、动作准备、接触时机和踢后平衡**。必须区分来球速度与出球速度；把球踢得更快不能替代“应对更快来球”。
- 部署时 actor 使用深度历史和本体感知，用户希望保持 end-to-end 感控路线。不能把球的位置、速度真值或光捕测量送入 actor。仿真真值用于 critic、奖励和辅助监督是允许的；用人体动捕制作 AMP 示范与在线依赖光捕是不同问题。
- 用户报告：基础仿真方案目前能训练 **0.4–0.8 m/s** 来球，踢球后姿态不稳；提高来球速度会失去平衡。这是当前表现范围，**不是已经测出的硬件或方法上限**。
- 用户需要兼顾性能提升与论文创新，希望围绕“如何从有延迟、可能被遮挡的深度观测中找到来得及执行的回踢动作，并容忍来球预测误差”继续展开。
- 更早讨论过篮球接球/回传及 TaskNPoint，当前主线已经转为足球敏捷回踢，不要再把篮球接抛作为默认目标。主动观察可以辅助，优先级低于敏捷交互。

## 2. 已有材料与证据边界

用户给出了完整 `x2_kickball_depth_v3` 工作流，参考训练产物位置为：

```text
logs/TASK_KickBallDepthV3_x2_flat/2026-09-11_11-54-30/
  params/env.yaml
  params/agent.yaml
  model_49200.pt
  events.out.tfevents.*
```

这些是用户描述的项目内路径；交接不代表这些文件已下载或已验证。实际冻结配置以 YAML 为准。用户还曾上传左右脚踢球 BVH：`tiqiu_you_000_Skeleton_2.bvh`、`tiqiu_zuo_000_Skeleton_2.bvh`。不要把这两份原始文件与训练使用的 37 条处理后 PKL 混同。

**未完成或未确认：**当前源码审计、checkpoint 评测、训练复现、具体深度相机及计算平台、实机接口与实验条件、感知总延迟、执行器饱和情况、各类失败比例。不要虚构实机结果或已达到的高速指标。

## 3. v3 基线：复现时必须保留的事实

### 3.1 入口、物理与初始化

```python
task_registry.register(
    "x2_kickball_depth_v3",
    TASK_KickBallDepthV2_X2_29DOF_Env,
    TASK_KickBallDepthV3_X2FlatEnvCfg(),
    TASK_KickBallDepthV3_X2FlatAgentCfg(),
)
```

v3 没有独立环境类，使用 v2 环境继承基础 KickBall 环境。

| 项目 | 用户给出的配置 |
|---|---|
| 机器人 | 29-DoF X2；`assets/agibot/x2/urdf/x2_t2.urdf`；actuator 使用 `X2_CYLINDER_CFG` |
| 动作 | `q_target = default_joint_pos + 0.25 * clip(action, -100, 100)` |
| 步长 | 物理 0.005 s，每动作 4 个物理步；控制 50 Hz |
| 环境 | 4096 个并行环境，平面，间距 12 m；episode 12 s / 600 步 |
| 球 | 半径 0.11 m，质量 0.43 kg；线/角阻尼 0.02；静/动摩擦 0.6/0.5；恢复系数 0.5 |
| 延迟 | action delay 默认关闭 |
| 初始化 | 80% AMP 随机时刻初始化，20% 默认站姿；AMP RSI 内部 kick/carryWith 比例 0.85/0.15；随机全局 yaw |

reset 记录机器人 root 的 xy/yaw 为站立 anchor，立即发球。该 anchor 是任务参考，不能据此认定机器人基座被物理固定。

- 初始球距 anchor 1.3–2.0 m，方位角 ±0.35 rad，瞄准点横向偏移 ±0.25 m，初速 0.4–0.8 m/s。
- 滚动初始角速度为 `[-v_y / 0.11, v_x / 0.11, 0]`。
- 球距 anchor >3 m、向身后越过 -0.3 m，或 xy 速度 <0.15 m/s 时，本次发球结束；再等 20 个控制步后重发。**不是固定在踢中后 0.4 s 发下一球。**
- 机器人 reset：`|roll|>0.5`、`|pitch|>0.7`、root z<0.4 m、root xy 离 anchor>0.6 m，或超时。

### 3.2 观测、视觉网络与辅助监督

```text
proprio(108) = root_ang_vel_body(3) + projected_gravity_body(3)
            + joint_pos-default(29) + joint_vel-default(29)
            + five_EE_positions_relative_root(15) + previous_action(29)

actor(11232) = 8 × proprio(108) + 8 × depth(27×48)
critic(117) = proprio(108) + root_lin_vel_body(3)
            + ball_pos_local(3) + ball_vel_local(3)
```

深度相机安装在 `head_pitch_link`，48×27，垂直 FOV 58°，每 0.02 s 更新，裁剪到 [0.1, 3.0] m，不归一化、无深度噪声。ray-caster 必须包含地面、动态球和机器人自遮挡。8 帧首尾相距约 0.14 s。

`ActorCriticDepthAux`：8 帧作为 CNN 的 8 个输入通道，三层 stride-2 卷积 `8→16→32→64`，max pool，256 维 head，得到 128 维 latent；与 864 维 proprio 历史拼接，再经 `512→256→256→29`。critic 为 `117→512→256→256→1`。

辅助损失为 `MSE(aux_head(depth_latent), critic_obs[:, -6:])`，系数 1.0。当前辅助头输入只有 depth latent；actor 后续仍会融合 proprio。最后 6 维标签为球的局部位置和速度，不能把这些标签直接接到 actor 输入。

### 3.3 AMP 与奖励

一个 discriminator，没有左右脚分支。单帧 AMP 60 维：

```text
height(1) + joint_pos(29) + five_EE_pos(15)
+ base_lin_vel(3) + base_ang_vel(3) + root_rot_6d(6) + object_pos(3)
10 帧拼接 → 600 维
```

用户明确说明原始 mocap 没有球轨迹，因此 **expert 和 policy 两侧的 object 三维都通过 `thresh_robot2object=0.0` 清零**。当前 AMP 是人体动作先验，球交互由任务奖励和仿真物理学习。没有球轨迹不妨碍继续推进；不能只在 policy 一侧启用球特征。若将来加入物体 AMP，需同步可靠的示范球轨迹、坐标系和接触时序，而非填入任意轨迹。

```text
assets/agibot/datasets/config/kickball_rebuild.yaml
assets/agibot/datasets/dataset/dataset_kickball_rebuild/kick/*.pkl  # 37 条
assets/agibot/datasets/dataset/dataset_findboxstill/carryWith/stand100.pkl
```

原始 task reward 所有项均乘 `dt=0.02`：

| 项 | 权重 | 主要含义 |
|---|---:|---|
| stand_task | 1.0 | anchor、xy 速度、直立、基础高度四项指数奖励的平均 |
| face_ball_task | 0.5 | `exp(-abs(yaw_error)) * ball_active` |
| kick_approach_task | 1.2 | `exp(-4*min_foot_ball_dist)`；未踢中且球距<1.6 m |
| kick_return_task | 4.0 | `clamp(ball_return_speed,0,3)/3`；球距<2 m |
| kick_bonus | 60.0 | 一次成功事件；乘 dt 后 +1.2 |
| miss_penalty | -15.0 | 未踢中且球越过身后；一次 -0.3 |

另有关节加速度、动作变化、力矩、关节速度和限位正则，具体权重需要读实际配置。

```text
reward_to_PPO = 0.75 * raw_task_reward + 0.25 * (0.5 * amp_reward)
              = 0.75 * raw_task_reward + 0.125 * amp_reward
```

因此成功事件对 PPO 的直接贡献为 +0.9，漏球为 -0.225。不能把系数 0.25 解释成 AMP 实际贡献恰占总奖励 25%。

v2 的踢中检测使用 `||v_ball_xy(t)-v_ball_xy(t-1)|| > 0.15 m/s`，这是速度变化阈值，不是直接测得的接触冲量。只有检测到该事件或已锁存 `ball_kicked`，向外的回球速度才有效。首次满足球 active、尚未 kicked、机器人球距<2 m、向外回球速度>0.4 m/s，就设置成功并锁存到下一球。

**现有成功条件没有严格要求脚球接触、指定回传方向以及踢后恢复平衡。** 提升论文任务质量时应补充评测定义，并核查非脚碰撞、被动反弹或重发速度突变的误判。

### 3.4 训练与代码定位

AMPPPO + Adam；seed 42；rollout 24 步；最大 50000 iterations；PPO 5 epochs×4 mini-batches；学习率 1e-3，adaptive KL，target KL=0.01；gamma=0.99，lambda=0.95，clip=0.2，value/entropy 系数 1.0/0.01。

奖励必须在 reset 前按当前物理状态计算；保存 terminal critic observation。若改变为循环网络，要核查历史和 hidden state 的 reset、序列采样与终止处理。

| 文件 | 作用 |
|---|---|
| `kickball_depth/x2_env.py` | 基础环境、观测、奖励、球状态机和 reset |
| `kickball_depth/x2_config.py` | AMP、网络和 PPO |
| `kickball_depth_v2/x2_env.py` | 速度突变踢球识别 |
| `kickball_depth_v3/x2_config.py` | v3 发球与奖励权重 |
| `scene.py` | 深度 ray-caster |
| `motionlib_carrybox.py` | AMP 数据和 expert observation |
| `agibot_fix.py` | X2 模型与执行器配置 |

```bash
python legged_lab/scripts/train.py --task x2_kickball_depth_v3 --headless --logger tensorboard
# smoke test 追加：--num_envs 4 --max_iterations 1
```

**冻结 v3 复现时**不要混入 v4 speed-level/EMA 课程、其他奖励权重，或 v5+ 多 critic、左右脚路由、深度噪声、curated AMP。新研究可以另建变体；这项约束不等于禁止在新方法中探索这些设计。

## 4. 后续研究应围绕的机制与待验证假设

尚未选定最终架构。优先把问题写成：**来球剩余时间、机器人准备时间和预测不确定性如何共同决定回踢动作，并影响完整回合成功率？**

可继续收敛的候选方向：

1. **预测接触与身体准备的时序表征。** 深度与 proprio、时间戳及观测有效性尽早融合；学习未来球位置/到达时间，同时判断当前支撑状态下哪只脚、哪个时刻来得及完成回踢。关键是动作可执行性，而非只加一个球状态预测头。
2. **面向延迟和遮挡的记忆。** 新视觉帧到达时修正状态，控制步间利用本体感知、动作历史和观测年龄维持预测。TCN/GRU/Transformer 都只是实现选项，单独换网络不构成充分创新。
3. **容忍接触时机误差的回踢与恢复。** 让动作在一段来球到达时间误差范围内仍能完成定向回传，并恢复平衡。需要与普通随机化公平比较；“不确定性”不能只停留在输出一个方差。

辅助方向包括短引脚、利用来球动量调整出脚方式、准备下一球以及必要时适度调整 AMP 对动作速度的约束。不要一开始同时堆叠全部模块；选一个机制做主贡献。

当前配置可能限制上限的因素，**均需实验确认**：低分辨率及下采样丢失远处小球信息；短历史或相机自运动影响速度估计；随机 AMP 初始化后立即发高速球导致来不及准备；接近当前球位置的奖励不利于提前调整支撑；固定时间尺度的 AMP 抑制敏捷动作；接触奖励缺少恢复要求；执行器或碰撞解析成为瓶颈。

## 5. 建议接手后的工作顺序与评测

1. **有源码后先核对冻结配置，保存 v3 基线。** 不要依据本记忆假装已经完成代码审计。
2. **先定位上限。** 用同一组来球，逐步评测 0.8、1.0、1.2、1.6、2.0 m/s 等速度；这些是待测点，不是已经达到的指标。区分感知/时机导致踢空、准备时失衡、接触后失衡。记录首次有效观测、准备动作、接触、恢复时刻及执行器饱和。
3. **区分速度和反应时间。** 在相同来球速度下改变首次可见距离、延迟和遮挡，测可用准备时间；再检查站稳初始化与随机 RSI 的差异。必要时减小物理步长但保持控制周期，检验高速接触仿真是否可信。
4. **建立公平的强化基线后再验证新方法。** 先完善成功定义和恢复奖励，再用早期感知融合/未来预测等小改动检验机制；最后增加接触时序选择或误差容忍训练。新方法与基线使用一致的相机、执行器、数据、奖励和训练预算；额外分支仿真也计入预算。
5. **以完整交互为核心结果。** 同时报告来球速度、可用反应时间、回传目标误差、出球速度范围、跌倒率、恢复时间、连续回合表现和机载延迟。所有来球计入统计；若另报告可达子集，要预先定义并同时报告整体结果。

优先画“来球速度 × 可用准备时间”的成功率，以及“到达时间误差 → 完整回合成功率”曲线。这样才能说明敏捷性来自什么机制。后续速度目标和实机结果必须由测量支持。

注意：原工作流写“球速始终在 [0.4,0.8] m/s”不应照搬为运行时不变量；这是**初始发球速度范围**，球会因摩擦和踢击改变速度。评测应另外记录实际到达速度。

## 6. 相关工作与交接时不能丢失的提醒

- 用户特别强调：研究对象是**传来的运动球**，目标年份是 **2027**。
- 用户把“robonal”描述为静止球工作。后续引用前应核对其准确名称、训练阶段和真实实验是否也包含移动来球；不要仅据这一说法写“已有工作只踢静止球”或宣称首次动态回踢。
- 机载视觉、深度输入、时序网络、未来状态辅助监督、接触时机不确定性本身都需要逐项核对已有研究。当前没有完成可支撑“首次”声明的文献审计。
- 更早评估的 [TaskNPoint 仓库](https://github.com/wernerb43/tasknpoint) 只是历史参考；当前 X2 v3 是用户给出的 AMP/PPO 深度踢球框架，不应混用二者的接口、依赖和训练事实。
- 接手者应把讨论推进到**一个明确研究假设、一版最小架构改动和能推翻该假设的实验**，而不是重复列举通用网络模块。

---

可直接给下一份 Codex 的任务：

> 请先读取本交接记忆。沿用 IROS 2027、X2、机载深度与本体感知、应对高速传入足球并稳定一触回踢的目标。基于 v3 已知结构，先提出最小诊断实验，区分感知时序、身体准备与接触后恢复的瓶颈；再收敛一个可实现、可消融的核心方法。区分用户提供的配置、已验证结果和研究假设，不要把换网络或“处理运动球”直接当作已成立的创新。
