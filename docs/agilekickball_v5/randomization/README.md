# v5 Kp/Kd 与深度随机化

2026-10-14完成实现与短测。v5默认开启；仅修改v5专属配置与传感器，v4、Wall4、共享G1资产、奖励、动作和足球critic保持。没有启动v5正式训练。

| 参数 | 默认范围 | 采样时机 |
|---|---|---|
| Kp倍率 | U[0.9,1.1] | 每回合、每环境、每关节独立 |
| Kd倍率 | U[0.9,1.1] | 每回合、每环境、每关节独立，与Kp独立 |
| 深度比例 | U[0.99,1.01] | 每回合、每环境 |
| 深度偏置 | U[-5,5] mm | 每回合、每环境 |
| 基础高斯标准差σ₀ | U[1,5] mm | 每回合采参数，每新深度帧采像素噪声 |
| 距离噪声系数c | U[0,0.001] m⁻¹ | σ(z)=σ₀+c·z²，z单位m；有效距离内σ约1–14mm |
| 随机缺失概率 | U[0,0.005] | 每回合采概率，每帧各像素采样 |
| 边缘额外缺失概率 | U[0,0.02] | 相邻像素深度差>0.1m的边缘；每帧采样 |

这些范围是保守的工程初值，**不是实机标定结果**。当前实机内外参、实际噪声统计与控制器增益仍需核对。

G1名义Kp/Kd为髋150/2、膝300/4、踝40/1、腰300/4、肩200/3、肘100/1、腕20/0.5（Kp单位Nm/rad，Kd单位Nm·s/rad）。使用Isaac Lab官方`randomize_actuator_gains`，每次以`default_joint_stiffness/damping`重新缩放，防止跨回合累乘；同时更新actuator模型、asset buffer和PhysX属性。回合中保持固定。

深度先完成完整场景最近交点求解，再保存独立clean buffer，最后对有效命中加scale/bias/Gaussian和缺失扰动，输出仍为0.1–3m光轴米制。原miss保持3m，缺失像素也设3m，不会显示遮挡物后面的球。边缘判定使用相邻像素，不从图像一侧绕回另一侧。

加噪发生于v5传感器的capture回调，重复读同一帧不会重新采样；低频相机保持上一噪声帧。reset仅清所选环境的图像并重采参数，其他环境不受影响。原相机安装、光线求交、8帧历史及辅助真值监督不变，随机参数不进入actor或critic观测。

随机化合同独立于真实`camera_profile`，放在checkpoint/export的`depth_contract.training_randomization`，包含nominal关节名称/Kp/Kd、范围和采样规则。新revision为`scene_depth_gain_noise_20261014`；旧无噪声v5验证模型、不同范围/开关不能当作相同实验精确恢复。模型恢复不保存进行中回合的物理现场或噪声帧，也不声称逐帧完全重演。

`training_only=True`表示扰动不进入导出的实机预处理/策略；**默认play仍使用随机化仿真，并不会因为load_optimizer=False自动关闭**。实机输入仍用原米制预处理，控制器使用核定的固定增益，不在实机上额外随机采样。

启动新实验仍使用：

```bash
bash scripts/rsl_rl/train_agilekickball_v5.sh
```

按需调整新实验的增益范围，或创建无扰动对照：

```bash
bash scripts/rsl_rl/train_agilekickball_v5.sh \
  'env.kp_scale_range=[0.95,1.05]' 'env.kd_scale_range=[0.95,1.05]'
bash scripts/rsl_rl/train_agilekickball_v5.sh \
  env.randomize_gains=False env.randomize_depth=False
```

深度范围位于`AgileKickballV5EnvCfg.depth_randomization`，可通过如`'env.depth_randomization.bias_m_range=[-0.003,0.003]'`覆盖。精确resume/play需与模型训练合同相同的参数。正式产物仍在`logs/rsl_rl/agilekickball_v5/`。

验证：CPU范围、单位、缺失/边缘、距离噪声统计与子集reset通过；4环境中PhysX/asset/actuator增益三方一致、连续reset不漂移、关闭增益恢复nominal；同帧多读一致、40ms周期保持噪声帧、逆序subset reset隔离通过。18组clean-depth/RTX对照最大差异0.164mm，原2mm/1%阈值未放宽。PPO/AMP执行2轮，新runner恢复后再执行1轮；错误随机化合同/旧revision被拒绝，live/JIT/ONNX动作对比通过。

4环境并发短测计时：增益重采样平均3.24ms/次reset，深度加噪平均0.171ms/帧；包含GPU同步的局部计时，不代表4096环境性能。未做正式训练、成功率评估或实机实验。Wall4进程2348537在18:20 JST仍运行，未停止/重启。

[最终回执](attempt2_receipts.json)、[结果与合同](validation/result.json)、[测试日志](validation/run.log)、[工程交接](../../../agent/handoff/agilekickball-v5-randomization.md)。attempt1失败证据保留：原遮挡测试使用固定世界点，随机化改变RNG与姿态后某一环境的机器人未位于视线内；测试改为相对实际torso放置相机和隐藏球，断言与精度要求不变。
