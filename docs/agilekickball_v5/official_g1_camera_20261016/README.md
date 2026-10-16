# Kickball s2s按官方G1相机资料对齐 · 2026-10-16

s2s默认使用独立的[camera_unitree_g1_d435i.json](../camera_unitree_g1_d435i.json)：D435i、640×480 Z16、60fps采集，50Hz策略读取最新帧；完整机身/球/地面/静动态环境遮挡保留。原camera_nominal.json及既有v5训练/导出契约保持不变，v5策略仍优先使用其自身嵌入的profile。

## 官方来源及实际配置

| 内容 | 使用值 | 来源与性质 |
|---|---|---|
| 相机型号 | RealSense D435i | [官方Depth Camera Routine](https://support.unitree.com/home/en/G1_developer/depth_camera_instruction) |
| 深度流 | 640×480、Z16、60fps | 同一官方C++例程选择的模式；不宣称所有出厂服务都强制使用此模式 |
| 相对torso安装 | (0.0576235, 0.01753, 0.42987)m | [官方rev_1_0 URDF](https://github.com/unitreerobotics/unitree_ros/blob/5994d4faef0a9cadd3287f8de0199a67eeb2a259/robots/g1_description/g1_29dof_rev_1_0.urdf#L562)，已按commit锁定 |
| 光轴下俯角 | 47.6° | 上述URDF pitch=0.8307767239493009rad；与官方图中光轴相对竖直42.4°一致 |
| 垂直FOV | 55.2° | [官方About G1](https://support.unitree.com/home/en/G1_developer/about_G1)的[D435i视场图](unitree_d435i_fov.png) |
| source K | fx=fy≈459.07766px，cx=319.5、cy=239.5 | **名义推导**：由55.2°、480高、方形源像素/中心主点假设得到；不是官方公布的逐台厂测内参 |
| 策略输入 | 完整640×480 nearest-exact缩放为48×27，8帧，光轴米制 | 项目预处理；fx/fy分别按宽/高比例缩放，主点按像素中心变换，不裁掉官方垂直视场 |
| 深度设备单位 | 名义0.001m/sample | 项目名义值，实机应读取设备get_depth_scale()；Z16本身只定义整数格式，不保证固定单位 |
| 深度范围/控制 | 0.1–3m；策略50Hz、固定物理步长 | 项目策略约定，不冒充相机物理能力 |

官方网页为SPA；已从其公开目录API找到官方CDN正文，读取并核对例程中的深度流配置与get_intrinsics调用。链接、文档SHA256、URDF commit与安装事实、官方图及字段来源记录在[official_sources.json](official_sources.json)。没有将RGB流848×480的分辨率误当深度流。

安装参考为官方URDF的d435_joint/d435_link。它不等于已针对某台设备标定的深度光学中心；profile保留`nominal_unverified`。官方例程明确从当前设备流读取内参，公开资料没有一组可用于所有G1设备的固定厂测fx/fy/cx/cy。将这些名义值标为calibrated会夸大证据。

## 60Hz相机与50Hz策略

每次reset以新首帧建立相位，计划时刻为t0+n/60；每个固定物理tick结束后，若到期则先用mj_kinematics更新积分后的几何再采集。策略每20ms仅读取最近实际采集帧，8帧历史仍按policy tick滚动。普通重新发球不重置相机相位。

采集落在第一个不早于计划的物理tick，保留实际时间戳和量化延迟，不修改physics_dt、不插值或伪造帧。physics_dt大于采集周期时拒绝运行；跳时会记录真正缺失的计划帧。60Hz与50Hz之间自然产生的未消费覆盖帧单独统计，不算漏采。

旧训练的lazy相机只在50Hz观测时更新，不能直接承诺60Hz；所以profile验证默认仍拒绝非20ms整数倍，只有带物理tick采集的s2s显式开启该能力。没有静默改变已有v5训练、恢复契约或旧模型深度定义。新官方profile目前用于s2s，若训练也采用60Hz，需要另行对齐训练传感器调度并形成新的训练契约。

## 验证与使用

[三条冻结命令回执](receipts.json)全部PASS：31项既有/新增检查、2秒真实策略闭环与视频、独立官方参数/时序审计。新增检查覆盖640×480硬件预处理、60/50Hz异步采集、非policy tick动态几何的mj_kinematics与mj_forward一致性、漏帧/重复读取与物理步长拒绝；原遮挡、旧解析重放、v5嵌入profile、物理不变和GUI检查保留。

[2秒闭环](smoke.json)使用5ms物理步长：121次采集（含t=0和t=2两个端点），100个policy tick消费100个不同帧，20帧在消费前被下一次采集覆盖，最后1帧等待下一policy tick；真正漏采0。最大采集量化延迟3.333ms、最大policy帧龄10ms。无数值错误/跌倒；这不是接球/回传成功率或真实相机曝光/USB延迟验证。[独立审计](audit.json)。

[实际策略输入视频](depth/depth.mp4) · [预览](depth/depth_preview.png) · [原始8帧深度](depth/depth_raw.npz)

```bash
/home/cao/ENTER/envs/umr/bin/python \
  /home/cao/perceptual_ball/scripts/sim2sim/kickball_mujoco.py \
  --duration 60 --physics-dt 0.005 --speed 2 \
  --output /home/cao/perceptual_ball/docs/agilekickball_v5/official_g1_camera_20261016/viewer_run.json
```

不加camera-profile时，v4权重使用此新默认profile，启动和结果继续标记输入分布变化；v5完整部署导出始终采用其源profile。显式`--depth-mode analytic`可复现旧球体解析输入。未启动正式训练、修改checkpoint或操作真实硬件；当前旧v4权重并未通过新深度分布的任务稳定性验收。
