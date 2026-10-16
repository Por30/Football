# Kickball / CarryBox 相机交叉核对 · 2026-10-16

两条训练线的名义安装都匹配官方G1 rev_1_0，但目前不能宣称训练深度与实机完全一致。Kickball v4/v5及CarryBox wall3–5仍使用58°垂直视场；足球MuJoCo新增官方参考profile为55.2°，没有自动同步到训练。此次只读核对源码、正式run保存配置和既有验证记录，未修改生产配置、模型或进程，未启动仿真。

## 安装与官方依据

相对于torso_link：xyz=(0.0576235, 0.01753, 0.42987)m，即前5.76235cm、左1.753cm、上42.987cm；光轴下俯47.6°。这是[官方G1 rev_1_0的d435_joint](https://github.com/unitreerobotics/unitree_ros/blob/5994d4faef0a9cadd3287f8de0199a67eeb2a259/robots/g1_description/g1_29dof_rev_1_0.urdf#L562)名义安装，坐标不是离地高度，也不是逐台设备已标定的深度光心。另一版g1_29dof.urdf的安装z为0.41987m；实机型号/版本仍需对应。

[官方G1图示](https://doc-cdn.unitree.com/static/2024/10/15/ff0591fcc6bc476bab77ebca2f92f198_1715x2363.png)标注垂直55.2°、光轴相对竖直42.4°。[官方相机例程](https://support.unitree.com/home/en/G1_developer/depth_camera_instruction)选择D435i深度640×480 Z16/60fps，并从设备读取内参；这个示例模式不代表所有G1的出厂服务或用户部署都使用同一模式。

CarryBox使用world/+X朝前的相机四元数，旧Kickball v4用ROS光学坐标/+Z朝前，两者数值不同不代表安装方向错误；转换后都约下俯47.6°。v4旧四元数存在舍入和非单位误差，既有解析s2s为重现旧策略保留该数值约定；v5 profile使用单位四元数。

补充精确说明：wall系列reset时相机位置扰动是随机单位方向乘0.01m，即位移长度固定1cm；此前笼统说“±1cm位置误差”不应理解成三个轴独立均匀采样±1cm。角度扰动当前为0°。

## 各路径实际配置

H×V为水平×垂直视场，数值按当前内参/孔径计算。所有路径的距离范围均为0.1–3m。名义FOV不等于逐台实测。

| 路径 | 分辨率/历史 | 名义H×V FOV | 采集与策略 | 输出及遮挡 |
|---|---|---|---|---|
| Kickball v4训练及同任务Isaac play | 48×27 / 8帧 | 约89.16°×58° | 50Hz | 沿射线距离，米；仅球体，机身/地面/障碍不遮挡 |
| Kickball v5默认训练及同任务Isaac play | 48×27 / 8帧 | 89.16°×58° | 50Hz | Warp光轴Z，米；机器人全部可见刚体几何、球、地面 |
| Kickball MuJoCo默认scene，加载无深度契约的旧v4导出 | 640×480全画幅缩为48×27 / 8帧 | 约69.76°×55.2°，水平为名义推导 | 60Hz采集，50Hz策略取最新帧 | 光轴Z，米；完整可见机身和模型中静动态环境遮挡；旧模型输入分布发生变化 |
| Kickball MuJoCo加载带契约的v5导出 | 跟随导出profile | 跟随导出profile；旧nominal仍89.16°×58° | 跟随导出profile | scene模式；外部profile不匹配会拒绝，不会静默替换 |
| CarryBox wall3 / wall4 / wall5训练及同任务Isaac play | 48×27 / 4帧 | 89.16°×58° | 50Hz | Warp光轴Z再除以3；机身、箱子、地面、平台及已配置的墙/柱遮挡 |
| CarryBox-v0旧基线 | 48×32 / 4帧 | 79.61°×58.11° | 50Hz策略；传感器update_period=0 | RTX光轴Z再除以3；实际场景可见表面遮挡 |

v4的89.16°/58°是配方名义值：其射线使用整数像素和中心(W/2,H/2)，相对v5的OpenCV整数像素中心((W-1)/2,(H-1)/2)还存在半像素偏移。CarryBox Warp的u+0.5配合cx=W/2与v5整数u配合cx=(W-1)/2等价，不能仅比较cx数值判定不一致。

Warp并非自动扫描任意新增障碍：机器人刚体及地面自动纳入，其余物体来自object_names。当前足球v5是Ball，wall系列为Box、Wall、存在的Cylinder及Platform；以后新增其他障碍须注册为射线目标。MuJoCo scene则遍历模型可见几何。以上是源码与已有遮挡验收核对，本次没有重跑遮挡仿真。

## 训练与部署的主要差异

1. 足球v5训练入口默认读取camera_nominal.json，仍是58°、50Hz；官方参考camera_unitree_g1_d435i.json当前是MuJoCo的回退默认。加载v5导出时，MuJoCo优先使用模型内嵌profile。这两条路径不可混称“足球相机已全部对齐”。
2. 官方参考profile由55.2°、640×480、方形源像素和中心主点假设推导fx=fy≈459.078px；缩为48×27后fx≈34.431、fy≈25.823px。当前训练fx=fy≈24.355px。因此不能只把58改成55.2，并继续按48/27直接推出水平FOV；必须先确定实机源流及crop/resize，再变换K。69.76°水平FOV也是上述假设的推导值，不是官方公布的通用实测值。
3. 60Hz官方参考profile不能直接塞进当前v5训练：训练lazy采集按20ms观测触发，profile校验要求20ms的整数倍；MuJoCo单独实现了物理tick采集/50Hz消费。若训练也采用60Hz，需要同步传感器时序与观测契约。
4. 足球v4是射线距离，v5和CarryBox是光轴Z；CarryBox额外除以3，且4帧历史，而足球8帧。共用相机来源不意味着可以互换策略输入。v4旧权重直接用新scene官方profile播放已被标记为输入分布变化，不能用这一路播放性能判断原训练是否收敛。
5. CarryBox当前正式wall5保存配置intrinsics=null，使用孔径和焦距生成射线。其checkpoint环境契约记录深度尺寸/几何/噪声等，但未完整记录名义K、名义mount、采集周期；现有导出路径也未提供足球v5式完整深度profile。后续相机变更须显式版本化和补齐导出元数据，不能假定旧checkpoint校验能发现所有相机差异。

## 证据与边界

[evidence.json](evidence.json)保存读取时间、正式run相机配置、官方来源、两profile及FOV/K计算和19个源文件hash。关键路径：

- 足球正式v4：logs/rsl_rl/agilekickball_v4/2026-10-12_13-48-41_return_to_sender_20261012_v3init/params/env.yaml；perceptual_ball_env_cfg.py、mdp/perception.py。
- 足球v5：agilekickball_v5_env_cfg.py、kickball_depth.py、kickball_randomized_camera.py、camera_nominal.json。
- 足球s2s：scripts/sim2sim/scene_depth.py的select_profile；[官方参考profile与既有31项/闭环验证](../../agilekickball_v5/official_g1_camera_20261016/README.md)。
- 搬箱子正式wall5：logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a/params/env.yaml；carrybox_walled_env_cfg.py与carrybox_wall5_env_cfg.py；[已有Warp/RTX遮挡对照](../warp_20261014/README.md)。
- 旧CarryBox基线实际内参：[baseline.json](../depth_audit/baseline.json)。

未获得实机CameraInfo/get_intrinsics、get_depth_scale、光学外参和确切裁剪/缩放配置，两项目均不能标为hardware calibrated。建议后续以同一份实机相机profile对齐几何及采集时序，同时保留各任务自己的深度归一化和历史长度。此次结论是配置审计完成，非相机修复完成、仿真重验通过或实机部署验收。
