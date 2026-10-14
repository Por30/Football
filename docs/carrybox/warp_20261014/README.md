# Wall4：G1动态Warp深度迁移与4096性能验收

2026-10-14 16:01 JST：Warp迁移完成，正式训练PID2348537已核验到iteration18；4096环境×24步、PPO 4 epochs×4 minibatches及完整AMP保持，热身后平均4.023秒、最慢4.078秒，达到6秒目标。新model_0.pt为schema2/revision5/warp，策略和AMP参数有限。尚未完成长训或证明拾箱收敛。 首次启动的日志目录问题已修，全部24项CPU和GPU验收复跑通过后才重新启动。

## 为什么football快

本地AgileKickball-v4正式末轮约2.47秒（collection约1.21、learning约1.26）。它的深度是GPU批量解析ray–sphere，只包含球体，不含地面/机身/墙柱的真实网格遮挡；另一个soccer分支的TimedDepth不是当前Agile主线。此次借鉴的是headless无RTX的训练路径，没有复制其遮挡简化，也没有修改足球源码或配置。

## 最终实现

- walled默认WarpDepthCamera，继承IsaacLab SensorBase；CameraData保留distance_to_image_plane、世界位姿及内参接口。原TiledCamera仍可由`CarryBoxWalled4EnvCfg(depth_backend='rtx')`选择，用于同场景对照。
- 43组几何：36个有可见几何的G1刚体/link，加箱子、墙、3圆柱、平台和地面。8个无可见几何的link明确列在manifest。遍历实例代理、有效visibility/render purpose；将全部视觉局部变换及scale烘焙到link坐标，未使用碰撞代理替代视觉网格。
- 每个几何只构建一次Warp BVH，全环境共享；重复几何按内容hash共享mesh。采样时批量读取当前PhysX link/rigid变换，将ray逆变换到各link局部空间求最近命中。相机和物体都使用link frame，而非质心frame。
- 48×27、50Hz、像素中心u+0.5/v+0.5；相机仍为G1 torso_link/CarryDepth的名义D435外参。使用光轴near/far平面0.1–3m，从近截面起射，返回光轴深度，miss为3m。Torch/Warp使用同一CUDA stream。
- 开启lazy sensor更新，只在需要观测时采集；reset后保留terminal先采逻辑，再刷新articulation kinematics并标记所选camera行过期。无需RTX整场景重渲染，50Hz和reset首帧语义保持。
- actor/critic均为4帧本体+4帧深度；箱子位姿只进入辅助监督、奖励和reset。AMP数据仍为根findbox，4096×24、4 epochs×4 minibatches、奖励/控制/噪声/延迟/冻结均未减少。
- 地面视觉尺寸从300m扩大到2000m，覆盖64×64、13m间距的4096场景及边界；物理地面原本为无限平面。原300m视觉地面不能覆盖最外围环境。这项变化在新RTX/Warp对照中使用相同地面，不改变碰撞。

主要实现：`carrybox_raycast.py`、`carrybox_warp_camera.py`、walled配置及MDP reset/contract、`train_carrybox_walled.sh`。正式启动脚本移除RTX的`--enable_cameras`依赖；不使用FSD、不改Isaac系统安装。

## 验证证据

24项CarryBox CPU检查通过，新增实际Warp CPU kernel测试覆盖光轴/near/far、最近遮挡、动态物体、subset写入。

4环境RTX/Warp同时采集：初始reset、16次动态步、逆序[3,1] partialreset、可见箱子、墙/柱挡箱与隐藏箱移动、回看机器人自遮挡。所有案例最大深度差0.00016427m（0.164mm），>2cm像素比例为0。独立PhysX torso×局部mount验证相机位姿；安装扰动与原相机一致。预设验收为内表面最大2mm、所有像素>2cm比例<1%；实际全部像素最大误差也远低于2mm。

原geometry验收继续检查三种技能初始化、loco视野外搜索、观测维度及成对标签、墙柱实际碰撞位置、平台支撑和遮挡。旧脚本私有RTX `_view.get_local_poses`读取改为Warp `_offset_pos`分支，所有断言原样保留。Task补充这个harness路径，原任务文本留档，没有以跳过检查修复接口不兼容。

4096 headless无RTX传感器：6轮更新，保存/加载，再6轮；旧RTX checkpoint直接resume被契约拒绝，显式warm-start通过；policy和AMP参数有限。复跑热身后10轮均值4.099秒、最慢4.166秒；完整阶段是collection约2.5–2.6秒，加全部PPO/辅助/AMP更新约1.54–1.59秒。旧RTX正式最近10轮17.255秒，本次短测约4.2倍吞吐；不同训练窗口对比，不作为逐轨迹严格A/B或成功率结论。

独立4步profile总0.413秒，物理调用约0.234秒；原RTX约2.588秒且render约2.107秒。profile为host调用时间，不表示独立GPU kernel耗时。

[原样测试回执](test_receipts.json)、[RTX对照](compare4/result.json)、[碰撞/遮挡](geometry/geometry.json)、[完整4096结果](scale4096/result.json)、[分项profile](scale4096/profile.txt)、[比较汇总](comparison.json)、[源码hash](source_hashes.json)。

第一次生产候选缺少可见Sphere支持，硬失败，没有静默漏掉；补充高精度Sphere三角化后RTX对照通过。另一次为旧测试脚本RTX私有接口不兼容，仅适配harness。所有失败日志/回执保留。

## 契约和使用边界

checkpoint schema仍为2，migration_revision升为5，加入depth_backend、depth_geometry及depth_clip。新Warp checkpoint可完整resume；旧RTX revision4不能直接resume。正式只从旧正式model_0.pt显式`--warm_start_carrybox`迁移encoder/actor/critic/辅助头，PPO、AMP与课程状态重建。旧run85轮中未保存的部分无法恢复。

此sensor针对当前G1和这些场景资产验收，不是任意USD通用导入器。支持当前Mesh/Cube/Sphere视觉类型；其他可见类型硬失败。未实现旧Camera的所有便利接口，如set_world_poses_from_view或list/NumPy world setter，现有训练与验收使用Tensor setter。实机名义安装保留，但未获得实机标定文件，不能宣称硬件标定已验证。

当前已知拾取动作目标范围不匹配仍未处理；提速不等于任务收敛。本次没有teacher/student、特权critic、降低频率或删自遮挡。

## 运行命令

当前已有正式训练进程，勿重复启动。查看日志：

```bash
cd /home/cao/perceptual_ball
tail -n 100 -F logs/rsl_rl/g1_carrybox_depth/walled4/warp_20261014_155653/train.log
```

独立验收脚本（占用GPU，正式运行时不要并发）：`bash scripts/rsl_rl/benchmark_carrybox_warp.sh`。[正式启动记录](launch.json)，包括实际启动参数和原正式权重来源。正式输出在`logs/rsl_rl/g1_carrybox_depth/walled4/`，验证产物留在本目录。

[深度对照图](compare4/depth_comparison.png)包含无遮挡箱子、墙遮挡及机身自遮挡，图中差值单位为毫米。

正式warm-start入口第二次生产修复：仅在train.py的CarryBox分支写initialization.json前添加os.makedirs，与相邻足球分支一致。CPU回归直接执行真实CLI AST分支，在不存在的嵌套run目录验证写入；24项及完整GPU验收重跑通过。[失败启动记录](failed_launch.json)。

[正式训练验收快照](formal_health.json)记录实际18轮、配置、初始化来源和AMP数据身份。[新checkpoint目录](/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_15-56-58_wall4_4096_warp_20261014_155653)。初始化记录明确只迁移旧正式策略与辅助头，优化器/AMP重新初始化；旧日志与失败启动均保留。
