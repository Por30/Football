# FindBox wall10：PhysHSI 搬箱任务迁移

2026-10-24更新：[深度与学习性能优化及4096验收](../wall10_perf_20261023/README.md)。4096×100完整短测从52.81s降到18.49s/轮，学习从40.89s降到7.63s；另测4096×24为4.41s/轮。默认100步保持；下文256微批为首次实现记录，当前保留256逻辑随机块并合并为8192执行批。

2026-10-23。新任务 `Template-Perceptual-Ball-CarryBox-Walled10-v0`，源码与 wall5 独立。用户所指的本机 `phsi` 目录为空，实际迁移依据为 `/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py`、`carrybox_config.py` 及其实际调用的 HIMPPO、AMP、motionlib。源文件身份见 `source_identity.json`。

## 任务流程

普通起点是空手站立/行走，箱子在机器人前方 ±45°、0.7–2 m 的地面上。策略通过深度寻找、接近箱子，双手搬起，在箱子原位置附近直立保持。不生成搬运目的地，不要求搬运、放下、松手或放下后恢复空手站姿。

保持成功要求以下条件**连续满足 2 秒（100 个控制步）**：

- 双手与箱子的过滤接触力均 >1 N；箱底离地 >0.10 m，箱中心高度 ≥0.70 m。
- 箱子竖直方向与世界竖直方向点积 >0.8，机器人对应点积 >0.95，mid360 连杆原点高度 >1.05 m。
- 机器人水平速度 <0.15 m/s、偏航角速度 <0.3 rad/s，箱子速度 <0.15 m/s。
- 箱子水平位置相对本回合初始箱位偏移 <0.35 m。

成功标记不会立即终止回合，策略继续抱箱至失败或 20 秒超时。条件中断时连续计时清零；曾完成的成功标记保留到回合结束。日志分别记录 default、loco RSI、pickup RSI、hold RSI；另有初始箱底离地 <3 cm 的地面起点计数与成功比例，避免将已经抱箱的参考起点当成完整拾箱成功。

## 观测与网络

| 分支 | 输入 | 网络/用途 |
|---|---|---|
| actor 本体 | 93 维 × 6 帧 = 558；角速度3、重力3、关节角29、关节速度29、上一动作29 | 原始6帧本体历史；不输入末端世界真值、箱位、目标点或阶段 |
| actor 深度 | 4 × 27 × 48；0.1–3 m 光轴深度，米制 | 复用 FindBox CNN 和 G1 名义相机安装；保留机器人自遮挡、地面、墙、支撑板与箱子遮挡 |
| critic | 当前本体93 + 双掌/双踝/mid360相对骨盆位置15 + 骨盆局部线速度3 + 箱相对位置3/旋转6/尺寸3 = 123 | 独立 MLP，无深度输入；线速度乘2，旋转采用原始 x/z 两轴表示 |
| AMP | 60 × 10 帧 | 训练专用判别器与风格回报，不进入 actor/critic |

actor/critic MLP 均为 `[512,256,256]`、ELU，初始动作标准差1。actor 本体按原配方添加均匀噪声，输入缩放后幅度为角速度0.075、重力0.05、关节角0.02、关节速度0.1；动作无噪声。critic 无噪声。本阶段深度无额外人工噪声或随机延迟。

与原 PhysHSI 的必要区别：以深度替代 actor 的箱/目标真值；actor 去掉仿真末端位置，保留部署可直接获得的本体93维；critic 去掉目标点3维。相同的“123维”不意味着兼容 wall5 的排列与缩放。任务阶段、成功标记均不输入策略。位姿标签组仍可作诊断，**辅助损失系数为0**，遵循原 PhysHSI 无位姿辅助损失的配方；保留的兼容 pose head 冻结且不导出。

## 保留的训练细节

| 项目 | wall10 |
|---|---|
| 默认规模 | 4096环境，100步/轮，20000轮，500轮保存一次 |
| PPO | 5 epochs × 4 minibatches；lr=1e-3；adaptive KL=.01；gamma=.99；lambda=.95；clip=.2；value coef=1；entropy=.01；AC梯度上限1 |
| 优化器 | 一个 Adam 联合更新 actor、critic、CNN、AMP；D trunk/head weight decay=.001/.1，三个组共同调整学习率 |
| 时间平滑 | 原系数 policy=1/9、value=1/90；相邻状态混合系数为 `(1-done)×U[-1,1]`；只用 rollout 前99步构成相邻对，done处不跨回合平滑 |
| AMP | 600→512→256→1，ReLU；保留原初始化、LSGAN和0.5倍专家输入梯度平方惩罚；无Normalizer，无输入标准化/裁剪 |
| 回报混合 | `0.75 × task_reward + 0.125 × style_reward`；task先按0.02秒积分，style不再乘dt |
| AMP特征顺序 | height1、joints29、ends15、box3、lin3、ang3、rot6；箱子水平相对位置截断到0.7 m，远处z设0 |
| 专家采样 | 原生60Hz特征插值至50Hz，速度倍率0.95–1.05；保留片段的源权重loco每段1、pickup每段4、hold每段5 |

数据仍使用规范 `assets/motions/findbox/` 的15段文件（11行走、3完整pickup、1原地hold），所有文件、manifest及旧快照未修改。源任务的移动抱箱/放下片段不适合缩短后的流程，因此采用项目已经整理的 hold 片段，保留片段归一化后的总权重为11/28、12/28、5/28；这不是原完整搬运数据分布。

为限制深度网络激活内存，每个 PPO minibatch 内按最多256样本累积梯度，再做一次 Adam 更新；KL按完整 minibatch 加权，保持5×4更新次数和损失均值。CPU随机数与采样次序不会逐位复现原 Isaac Gym。checkpoint明确保存100步rollout、联合优化、平滑、数据身份和完整任务契约。继续使用schema2，但wall10与wall5/原PhysHSI模型不能直接严格恢复互换。

## 物理与初始化

- 29自由度 G1；200Hz显式 PD、50Hz策略、动作缩放0.25、原始动作裁剪±100。位置目标不额外裁剪，按原代码在施加力矩前使用实际URDF力矩限幅。已专门防止 Isaac Lab 显式执行器默认1e9上限替代真实电机限幅。
- Kp/Kd：髋150/2、膝300/4、踝40/1、腰300/4、肩200/3、肘100/1、腕20/0.5。每回合Kp、Kd、motor strength独立乘0.9–1.1；力矩偏置±5%电机上限。五格物理步延迟队列对应0–20ms，reset预填最终实际关节姿态。
- 20%默认起点、80%随机RSI；RSI内部loco/pickup/hold概率2/3、1/6、1/6，保留每次随机选择。参考关节速度使用记录值，关节角扰动±0.1rad并裁剪到90%软限位；默认根速度各轴±0.5，RSI各轴±0.2。沿用本项目实际足凸包5mm向上接地修正，并同步配对箱位。
- 三段完整pickup参考可在接触前使用原尺寸0.4×0.4×0.02 m支撑板；其他起点将支撑板移至地下。默认/loco箱子在地面，hold RSI保留已抱起的箱位。
- 原G1碰撞和自碰撞，肩部使用原胶囊；不带入wall5额外全身碰撞或接触扣分。机器人各连杆质量乘0.8–1.2并重算惯量、torso COM各轴±0.1m；每环境统一机器人摩擦0.1–1.5、恢复系数0–1；地面摩擦0.9。源配置声明的payload随后被源link-mass循环覆盖，本次遵循实际生效行为，不声称有额外payload随机化。
- 箱子基础尺寸0.30×0.30×0.25m；xy比例0.7–1.3、z比例0.6–1.4，步长0.1；密度10–100kg/m³，按体积计算质量。每环境实际形状、深度交点、critic尺寸、离地判据保持一致。
- 保留原每8个策略步触发一次的局部torso各轴±50N短力脉冲，施加于下一物理步；不使用wall5速度推扰课程。

正则奖励保留原权重：加速度−1e−7、动作变化−.03、力矩−1e−4、关节速度−2e−4、软位置越限−5、速度越限−.001、力矩越限−.03。**力矩惩罚是 `sum((applied_torque/nominal_Kp)^2)`**；速度软限位0.8、限幅前力矩软限位0.95。

接近奖励保留0.85m/s目标、0.5朝向项、0.7m近距饱和；抬箱保留0.7手位置项＋2.0箱高项，箱中心目标0.72m，去掉原目标放置位置触发的奖励捷径。原放下后空手站起奖励替换为有双手接触、已离地的持箱直立/低速/位置保持，权重仍为0.2；没有混入wall5的alive、抓取塑形、腰部或手臂额外惩罚。

失败终止保留：骨盆<0.2m、mid360<0.6m、任一hip_yaw<0.15m、abs roll>0.5rad或pitch>1.1rad、箱水平速度>3m/s；另保留非有限值保护。与现有FindBox一致，terminal critic/AMP在reset前保存，reset历史隔离，防止跨回合污染。

## 使用与验证

正式训练命令（本次未执行）：

```bash
CARRYBOX_VARIANT=10 bash scripts/rsl_rl/train_carrybox_walled.sh \
  --num_envs 4096 --max_iterations 20000 --seed 42 \
  --run_name wall10_physhsi_lift_hold_fresh
```

输出进入 `logs/rsl_rl/g1_carrybox_depth/walled10/`。恢复同任务训练加 `--resume --checkpoint /path/to/wall10/model.pt`。播放：

```bash
CARRYBOX_VARIANT=10 bash scripts/rsl_rl/play_carrybox_walled.sh /path/to/wall10/model.pt 4
```

Warp深度无需RTX的 `--enable_cameras`。默认原训练规模保留，但本轮仅验收16环境，未验收4096环境的显存峰值、速度或长训收敛。本次未对wall5正式进程执行停止或重启操作。`smoke_model.pt`及`exported/`只作工程验证，不能充当正式训练或任务成功证据。

**最终验证：29项CPU检查通过；16环境原100步、5×4更新的2轮训练＋严格恢复后1轮通过；actor/critic/CNN/AMP实际更新、真实力矩限幅、partial reset、terminal观测、JIT/ONNX导出与actor特权隔离通过。** 16个随机尺寸箱子的实际三角网格与组合深度逐像素比较，最大误差0.000146657m（约0.147mm）。最终短测reset来源计数为default48、loco98、pickup17、hold25；只是覆盖证明，不是任务成功率评估。

定向测试及实际结果见 `receipts.json`、`cpu.log`、`sim.log`、`smoke.json`。首轮验证中的推理比较漏用inference_mode已修正，保留于`attempt1/`；最后补齐源地面摩擦、支撑板尺寸、重算惯量和reset首步加速度语义后重新运行冻结测试。实现完成、短测通过、正式训练完成和独立评估是四个不同状态。

代码入口：`tasks/manager_based/perceptual_ball/carrybox_wall10_env_cfg.py`、`mdp/carrybox_wall10.py`、`carrybox_wall10.py`、`rsl_rl_extensions/carrybox_wall10.py`。共享train/play只新增独立分派；既有任务ID、资产、数据和模型路径保留。
