# Kickball MuJoCo完整场景深度 · 2026-10-16

2026-10-16后续更新：根据用户指定官方G1资料，[s2s默认相机已改为D435i官方示例640×480 Z16/60fps及55.2°垂直视场](../official_g1_camera_20261016/README.md)。以下28项/100次采集结果对应此前50Hz名义profile；可显式传`--camera-profile /home/cao/perceptual_ball/docs/agilekickball_v5/camera_nominal.json`复现该相机定义。原v5导出仍优先使用其自身profile。

当前s2s默认`scene`：对MuJoCo中可见机器人网格、球、地面，以及其他静态/动态环境geom求最近表面。原球体解析模式保留为`--depth-mode analytic`，历史审计和快球诊断已显式固定该模式。未修改正式训练、checkpoint、共享G1资产或真实设备。

## 使用

任意目录启动现有v4权重的场景深度诊断（默认scene，窗口标签为optical Z）：

```bash
/home/cao/ENTER/envs/umr/bin/python \
  /home/cao/perceptual_ball/scripts/sim2sim/kickball_mujoco.py \
  --duration 60 --physics-dt 0.005 --speed 2
```

`--camera-profile /absolute/path/camera.json`可指定实机标定profile，字段沿用[v5配置](../camera_nominal.json)。v5导出模型有深度契约时，默认使用其嵌入profile；显式覆盖不一致、profile缺失、错误深度语义/顺序/归一化/几何版本、v5搭配analytic均拒绝。`--export-dir`要求由play导出的完整部署manifest，包含关节顺序、动作scale/offset与控制周期。

当前默认仍加载已正式训练的v4 model_49999对应policy.pt。**v4原训练输入为仅球体解析射线距离；新输入含完整场景且是光轴Z，启动提示和JSON均记录`depth_distribution_shift=true`。这只支持诊断，不表示旧权重已经适应场景视觉。** 要验证任务性能，应使用场景深度训练的v5策略。此次没有启动训练。

已有v5验证目录的manifest只有深度契约，缺少关节/action部署元数据，不能直接作为完整`--export-dir`。本次接入测试使用真实v5验证policy.pt和深度契约，从同G1任务v4补入部署元数据生成临时manifest，仅验证load/inference，不改变这些原文件。

## 深度与时序

- 相机复用v5 world约定：相对torso_link的wxyz安装姿态，+X光轴、+Y左、+Z上；内参经同一crop/resize换算，整数像素中心。
- 输出float32、27×48、光轴Z米制、0.1–3m，无命中/远处为3m，不除以3。未使用v4的旧半像素射线网格。
- 原生射线求交直接使用完整可见网格三角形及当前geom位姿；支持模型中其他静态/动态geom，不按球位置/分割筛选。机器人重复碰撞代理仅在独立感知model中排除；世界/物体geom不会因此删除。默认模型含36个机器人可见geom＋球＋地面，无collision-only机器人fallback。
- 保留torso自身遮挡。查询包含静态几何；近面前表面不会隐藏near后有效表面，并保留同一闭合物体的出口。离轴far cutoff按射线距离扩展，最终输出按光轴Z裁剪。
- profile采集周期须为20ms整数倍，期间保持上一帧；8帧历史仍每20ms旧→新滚动，reset重复新首帧。JSON保存实际采集时刻，窗口/视频10Hz只复制现有网络输入。
- scene统计名为`valid_depth_frames`与各表面的命中像素步数，不把地面命中称为球可见性；诊断表面ID不会进入策略。

实现：[scene_depth.py](../../../scripts/sim2sim/scene_depth.py)、[runner](../../../scripts/sim2sim/kickball_mujoco.py)、[profile验证/硬件预处理](../../../source/perceptual_ball/perceptual_ball/kickball_depth.py)。[MuJoCo 3.3.7原生求交API](https://mujoco.readthedocs.io/en/3.3.7/APIreference/APIfunctions.html#ray-casting)用于可见geom最近表面求交；不需要OpenGL来产生策略深度。

## 验证与查看

[28项检查及短闭环回执](receipts.json)全部PASS，覆盖真实GUI球速控件与场景标签、已有接口/最终v4权重一致性、旧解析重放、光轴离轴平面、近裁剪两种情况、机身挡球、隐藏球移动、静动态物体、真实G1抬臂网格遮挡、相机姿态、采集保持/reset、契约拒绝和物理参数不变。初版单位测试使用1500×0.001并要求浮点结果严格等于1.5，实际float32为1.500000119；将单位已知样本改为可精确表示的1250→1.25，保留原严格断言。失败与最终回执分别保存，未改生产预处理运算。

[100控制步闭环](smoke.json)：2秒、物理步长5ms、100次采集、无数值错误/跌倒/恢复超时。命中像素步数：机身1090、地面115932、球513；默认场景未添加障碍，额外环境为0。接口运行通过不代表接球/回传稳定；`stable_for_full_duration=false`，不得当作任务成功证据。

[实际策略深度视频](depth/depth.mp4) · [策略输入预览](depth/depth_preview.png) · [原始8帧历史](depth/depth_raw.npz) · [视频校验](depth/depth_info.json)

[三场景遮挡对照](occlusion_preview.png) · [数值与真实机身挡球核对](occlusion_samples.json) · [原始快照](occlusion_samples.npz)。三列依次为站立、抬臂、额外墙体；下排表面归属仅用于诊断。实际G1机身遮挡区域内移动后方球体，深度保持完全相同。可复现：

```bash
/home/cao/ENTER/envs/umr/bin/python \
  /home/cao/perceptual_ball/docs/agilekickball_v5/sim2sim_scene_20261016/make_occlusion_preview.py
```

## 实机一致性的剩余边界

默认profile仍为`nominal_unverified`；需要实际相机型号/流模式、CameraInfo、光学中心相对torso的外参、裁剪/缩放及时间戳/掉帧数据才能核对实机。没有用名义参数或模拟随机化冒充实测标定。

MuJoCo使用官方G1可见几何和理想球面，v5训练用训练USD和显式球面三角网格，两者几何/运动学仍有既有差异。本次实现完整场景遮挡和相机语义，不声称跨引擎像素完全相等，也未验证真实相机噪声、反光/透明表面和任务迁移成功率。
