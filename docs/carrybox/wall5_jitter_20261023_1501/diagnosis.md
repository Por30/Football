# 同初态抖动检查

本次证据支持：自碰撞确实影响部分姿态和运动，尤其持箱上肢，但不能统一解释所有空手抖动。更直接可见的控制异常是膝目标长期越过伸展侧下限、踝目标逐控制周期明显变化。尚未识别出统一根因，不能把关闭自碰撞或延迟当作已经验证的训练修复。

固定rev27 model2200、seed42、default/loco/loco/hold四起点，确定性均值动作。原配置录像与两个独立诊断进程分别仅关闭自碰撞或取消动作延迟。核对root/q/qd、全部刚体状态、机器人材质、PD、延迟缓存、事件时钟和所有初始观测，最大差均为0；实际配置契约仅允许self_collisions差异，取消延迟通过reset后index=4实现，保持原随机数消耗。三个条件都跑满20秒，仅最后一步timeout。

在原scene.update完成后读取200Hz实际状态、延迟后目标及内部pair接触力，核验时间戳、4000步、有限值和body映射。50Hz原始action及裁剪后目标另存。分析采用共同首回合2–20秒，排除启动瞬态；不跨reset差分或FFT。视频25fps，运动频率来自200Hz轨迹。

| 机器人/起点 | 原配置腿部加速度RMS | 仅关自碰撞 | 仅取消延迟 |
|---|---:|---:|---:|
| 1 默认 | 126.56 | 84.08 | 101.43 |
| 2 loco | 62.08 | 79.29 | 50.16 |
| 3 loco | 76.33 | 78.13 | 76.60 |
| 4 hold | 106.24 | 61.74 | 86.75 |

单位rad/s²，12个腿关节的200Hz速度差分RMS；是运动急促程度的描述，包含接触冲击，不等同于纯抖动指标。关闭碰撞后Robot1/4分别下降约34%/42%，Robot2/3反而上升约28%/2%；取消延迟后三个样本下降约18–20%，一个几乎不变。不同条件会改变闭环轨迹与移动速度，例如hold平均根部水平速度从0.144降到0.061m/s，因此不能只凭RMS下降宣布唯一因果。目标/运动仍有明显变化。

原配置的实际延迟为15/15/10/10ms。2–20秒内部pair力>1N的物理步比例为0.222%/0.056%/5.389%/100%。空手主要是偶发手/腕与髋接触；持箱主要是torso与shoulder_roll、shoulder_yaw、elbow、wrist_roll接触。持箱最大pair力在该窗口内中位数约293N，95分位376N，峰值494N；全20秒的1091N峰值属于另一统计窗口，不能混用。关闭自碰撞后所有内部pair力归零；原配置非零、body映射正确且足部净力非零，排除了“视图全零无效”的情况。pair为多接触点向量合力，不能直接代表几何穿透深度。

膝关节**指令裁剪**是另一项确认的异常：三个空手样本左右膝越界后裁到−5°的比例分别为92.22%/97.44%、100%/97.11%、90.78%/90.44%。Robot2左膝在分析窗口的目标恒为−5°；这不表示实际关节绝对不动或每个时刻都发生限位碰撞。标志来自50Hz控制周期，200Hz记录会连续保留4步，不能当作4次独立决策。`analyze_details.py`逐样本确认所有饱和膝目标都位于下限。空手踝pitch目标相邻20ms变化RMS约2.7–4.1°，实际踝运动速度谱在2–25Hz范围内的峰值约3.7–9.0Hz。这说明指令与真实运动确有较快变化，不能仅由25fps画面解释；其与抖动的因果和时序贡献仍需进一步隔离。

![目标饱和与踝运动](../../../outputs/carrybox/wall5_jitter_20261023_1501/target_saturation.png)

碰撞几何也有需要独立核对的细节：当前`carrybox_physhsi.py`把肩部Cylinder转换为Capsule时保留半径0.03m及height 0.05/0.03m。按本机USD Capsule定义，height不含端部半球，轴向总长成为0.11/0.09m。原PhysHSI也设置`replace_cylinder_with_capsule=True`，但本地Gym文档未明确替换时长度映射，尚不能证明两边导入后的几何不一致，不能称为已确认尺寸bug。shoulder_yaw、elbow、wrist_roll也并非这四个胶囊，不能把全部上肢接触都归因于转换。参考：`source/perceptual_ball/perceptual_ball/carrybox_physhsi.py`，`/home/cao/isaacsim/kit/dev/fabric/include/usdrt/scenegraph/usd/usdGeom/capsule.h`，`/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox_config.py`。

后续优先核查长期目标饱和、踝动作变化与抖动的时序关系，再单独核查持箱肩部碰撞几何。PD与深度噪声本次未做单因素隔离；尚不能给出已验证的调参修复。生产源码、模型和正式训练均保持，本轮只交付录像与诊断。

原始证据：[三条件汇总](jitter_analysis.json)、[目标细节](target_details.json)、[完整裁剪统计](target_clipping.json)、[动作/状态/接触轨迹](baseline_trace.npz)、[内部接触映射](baseline_trace.json)、[关闭自碰撞初态核验](no_self.json)、[取消延迟初态核验](no_delay.json)、[录像](README.md)。两条冻结检查均通过，正式训练不是诊断进程，视频也不是总体成功率评估。
