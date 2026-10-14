# 深度找箱并拾起

任务：`Template-Perceptual-Ball-CarryBox-v0`。参考 PhysHSI 的 `carrybox.py` 接近/拾起奖励、G1 29 DOF 资产和 `dataset_carrybox/pickUp`，迁移到本项目 Isaac Lab 管线。流程只有接近、双手接触、抬起保持；没有搬运目标点或放下阶段。

## 观测与监督边界

| 数据 | actor | critic | 辅助监督/评分 |
|---|---|---|---|
| 本体：角速度、重力方向、关节位置/速度、上次动作 | 是 | 是 | — |
| 真实 TiledCamera 深度，4 × 32 × 48 | 是 | 是 | 共享编码器 |
| 箱子位姿真值 | 否 | 否 | 仅监督标签 |
| 接触、箱子世界位置/速度、成功计时 | 否 | 否 | 仅奖励/终止 |
| AMP 本体运动窗口（10 × 64） | 否 | 否 | 仅判别器与风格奖励 |
| 根线速度、技能标签 | 否 | 否 | 未使用 |

`proprio` 为 4 帧、372 维，`perception` 为四帧图像；actor 与 critic 均为同一个深度 CNN 特征与本体信息的组合。相机包含地面、机器人自身遮挡和箱子的场景深度，不使用真值生成深度、分割或 ROI。50 Hz 控制与渲染对齐，深度为光轴方向距离，0.1–3 m 裁剪后除以 3；无效像素设为远平面。相机位于 torso 的 D435 安装位置，向下约 47.6°，水平视场约 79.6°、垂直视场约 58.1°。

`box_pose_target` 是训练专用的 9 维标签：相机 ROS 光学坐标系（右 x、下 y、前 z）的箱子中心位置（米）和箱体旋转矩阵前两列。标签与同一 observation 中最新深度帧对应，rollout 按 action 前的 observation 保存，不拿下一步标签配前一帧。

辅助头从深度 latent 回归 9 维位姿。总损失为 PPO 损失加 `0.5 × (位置 MSE + 对称旋转 6D MSE)`；编码器和位姿头参与同一个优化器更新。0.30 × 0.30 × 0.25 m 无纹理箱子存在 8 个等价朝向，旋转损失取最小等价误差，因此预测的是物理可辨识的朝向等价类。推理可完全删除监督标签，actor/critic 输出不变。

## 场景与成功判定

箱子质量 1.125 kg（对应源默认密度 50 kg/m³），随机生成在机器人前方 0.65–1.25 m、横向 ±0.25 m，随机 yaw。起点为地面，机器人初始站姿固定。动作是 29 关节位置偏移，scale=0.25，动作 clip=5。

奖励包含接近/朝向、双手接近箱体表面、接触门控抬升和成功奖励，并惩罚动作变化、关节加速度/力矩、超限和跌倒。成功要求：**箱体最低点离地至少 0.12 m、左右 rubber_hand 均与 Box 有超过 1 N 的过滤接触力、箱体正向 z 与世界 z 点积 > 0.9、箱子速度 < 0.25 m/s，连续保持 0.5 秒**。最低点由旋转后包围盒计算，倾倒、抛起或单手碰撞不会直接计为成功。成功结束回合，超时为 12 秒。

训练使用单 GPU 固定学习率 PPO，暂不支持多 GPU、RND、镜像增强。timeout 使用 reset 前的深度与本体历史 bootstrap，reset 后重新渲染并清理对应环境历史。

## 数据与迁移范围

当前训练直接使用项目根目录 `findbox/` 的 **17 段、4628 帧**动作：11 段 `loco_direction`、3 段 `pickUp`、3 段 `carryWith`。按三个组 **40% / 40% / 20%** 采样，组内各片段等权。`carryWith` 提供持箱姿态先验，任务仍然只做找箱与拾起，不增加搬运或放下阶段。

`findbox/amp_manifest.json` 固定每个片段的 SHA256、帧数、29 关节顺序、60 Hz 原始帧率和 xyzw 四元数约定。17 个文件与 PhysHSI 同名源片段逐字节一致，帧率来自其 `carrybox_config.py`，关节顺序来自 `joint_id.txt`；运行不再依赖源项目路径。旧 `assets/motions/carrybox/pickUp` 仅保留此前的参考归档，当前 AMP 不读取该副本。

AMP 每帧为绝对关节位置29、关节速度29、根坐标重力方向3、根坐标角速度3，10帧共640维。live 按关节名重排为数据集顺序；expert 先把 xyzw 转为 wxyz，逐片段重算关节速度及最短四元数差分角速度，然后按60→50 Hz插值。不使用片段中的箱子、末端位置、根位置或根线速度，也不把AMP组送入actor/critic。没有参考动作初始化、行为克隆或数据播放速度扰动。

复用项目 LSGAN AMP 判别器与梯度惩罚，判别器有独立 Adam（默认学习率1e-4）。对完整窗口，训练奖励为：

```text
reward = 0.75 * task_reward + 0.25 * 2.0 * step_dt * amp_style_reward
```

`amp_style_reward` 在[0,1]；乘控制周期0.02s与环境按秒定义的奖励一致，默认风格项每步最多0.01。初始窗口不足10个真实帧时使用原task_reward，并跳过这些窗口的判别器训练。结束回合使用reset前的末帧窗口计算风格分数，并把同一个窗口存入判别器训练缓存；不会用新回合状态代替终止状态。

视觉位姿标签仍由仿真在线生成；动作片段本身不含深度图，不直接用作视觉监督。更详细的实现与验证记录见 [AMP 接入记录](amp/README.md)。

## 训练与播放

在已配置 Isaac Sim / Isaac Lab 的 Python 环境中：

```bash
python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-CarryBox-v0 \
  --num_envs 128 --device cuda:0 --headless --enable_cameras \
  --max_iterations 30000 --seed 42 --run_name depth_pose_amp_scratch
```

`--enable_cameras` 必须保留。真实渲染比踢球解析深度消耗更多显存，128 是起始配置，需按可用显存调整；不直接沿用 4096 环境。

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-CarryBox-v0 \
  --num_envs 4 --enable_cameras \
  --checkpoint /path/to/carrybox/model_200.pt
```

恢复训练使用同任务和 `--resume --checkpoint /path/to/model.pt`。当前 carrybox checkpoint 为 schema=2，保存位姿头、共享编码器、PPO/AMP 优化器、AMP 判别器及归一化统计量、数据身份与随机数状态。训练恢复会校验数据集，不能直接恢复此前无AMP的schema=1模型或踢球checkpoint。播放和导出不加载动作数据集，策略输入仅为本体历史和深度历史。

## 验证

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p 'test_carrybox*.py' -v
bash scripts/rsl_rl/smoke_carrybox.sh
```

smoke 使用 4 个真实 RTX/物理环境、2 次 PPO+AMP 更新、强制 timeout、AMP终止窗口/reset检查、checkpoint 恢复和 JIT/ONNX 导出。运行记录见 `smoke.json`、`smoke.log`；生成的随机 smoke 模型只用于管线检查。

尚未长时间训练或测量拾箱成功率。密集奖励的系数、地面拾取难度和无手指 G1 的双手夹持稳定性需要后续训练评估；短时管线通过不代表策略已经学会找箱或搬起。

AMP接入验证结果：CPU 9 项通过；4 个 RTX 环境、2 次 PPO 更新、12 个 timeout 均通过，左右手真实过滤接触及箱子视野变化已验证。JIT/ONNX 输出与原策略一致。接触探针人为制造重叠以检查接线，不代表正常夹持载荷。
