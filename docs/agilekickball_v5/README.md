# AgileKickball v5 · 场景深度与自遮挡

2026-10-17更新：按用户要求，默认关闭Kp/Kd随机化和全部深度噪声（`randomize_gains=False`、`randomize_depth=False`）；保留场景光轴深度和自遮挡。旧带扰动模型不能直接按新默认值精确恢复，详见[关闭记录与兼容说明](no_randomization_20261017/README.md)。下方2026-10-14训练状态与默认开关为历史记录。

2026-10-14更新：默认开启[Kp/Kd与深度随机化](randomization/README.md)，revision更新为`scene_depth_gain_noise_20261014`。4环境更新/恢复/导出及随机化隔离验收通过。以下初版深度证据保留为历史；旧验证模型不能直接恢复到新合同。

2026-10-14：新增 `Template-Perceptual-Ball-AgileKickball-v5`，继承 v4 的接球、回传给发球者、恢复站稳、速度/方向课程及 AMP。v4 ID、模型、奖励和观测接口保留。v5 尚未启动正式训练；4环境短测已通过，实机标定验收待完成。

| 项目 | v4 | v5 |
|---|---|---|
| 深度 | 球解析求交，沿射线距离 | Warp 可见网格求最近交点，光轴 Z |
| 场景遮挡 | 无机身/地面遮挡 | G1 全部有可见几何的刚体连杆、Ball、ground |
| 输入 | 48×27、8帧、米 | 48×27、8帧、米；不除以3 |
| actor | 本体历史＋CNN＋预测球状态反馈 | 保持路由；不加入真值可见性mask |
| critic | 本体＋机器人速度＋球真值 | 保持足球独立critic设计 |
| AMP与奖励 | 原有接球回传配方 | 继承 v4 |
| 版本 | `agile_v4_return_curriculum` | `agile_v5_scene_depth_curriculum`，绑定完整深度契约 |

v5将球的可见表面显式写为64×64 UV球三角网格，保留原来的理想Sphere碰撞体、半径、质量与物理材质。默认RTX隐式Sphere细分和Warp高精度球面有毫米到厘米差异，提高RTX细分仍不能保证同一表面；显式视觉网格让渲染与ray-cast使用同一几何。该改动仅属于v5，未改v4或Wall4。

传感器共享每个几何的 Warp BVH，每次采集读取 PhysX 刚体位姿；机身、手臂、腿、球和地面参与同一次最近求交，未删减自遮挡连杆。当前足球场景没有墙/柱；未来添加物体时必须将其刚体根加入 `object_names` 并重新验证，不能假定任何新物体自动可见。邻近环境的几何不参与本环境的求交。

名义参数来自本地 G1 rev_1_0 的 d435 安装关节：torso_link 下位置 `(0.0576235, 0.01753, 0.42987)m`，向下 pitch `0.8307767239493009rad`。默认48×27、垂直58°、near/far=0.1/3m、采集周期0.02s。`world` 相机约定为 +X光轴、+Y左、+Z上；内参使用 OpenCV 整数像素中心。原 v4 的 ROS optical quaternion 不直接复制到 world 约定。

[相机配置](camera_nominal.json)明确标记 `nominal_unverified`。目前没有实机序列号/型号对应的 CameraInfo、光学中心外参、实际流模式、裁剪/缩放、时间戳与掉帧数据，**尚不能声明与实机完全一致**。50Hz、58°及0.001m设备单位均是当前名义配方，不是实测结果。需要用真实校准文件替换这些参数，确认实际机器人是否为rev_1_0（本地另一URDF相机高度相差1cm）。

部署预处理函数 `perceptual_ball.kickball_depth.preprocess_hardware_depth` 接受已校正、未对齐到RGB的光轴深度 `[N,H,W]`：设备单位→米，非有限/非正数→3m，clip到0.1–3m，裁剪，nearest-exact缩放。相应 K 用半像素中心公式同步变换。调用方负责真实采集时间戳、掉帧/陈旧帧处理，以及每个policy tick的8帧旧到新历史；当前未实现实机驱动，也未用未实测的噪声/延迟参数冒充传感器特性。当前lazy采集仅支持20ms整数倍周期；30Hz等不能直接填入profile，会明确拒绝，需要另行实现采集/保持时序，避免30Hz被悄悄量化成25Hz。

旧feedback中“存在有效像素”的数学门控保留，但v5只解释为有效深度的新近程度与预测不确定性，**不是球可见性**。v5指标使用 `valid_depth/active_valid_depth`，不报告误导性的 `visible/active_visible` 分组。位置/速度辅助监督及有界动作修正仍由原网络实现。

checkpoint保存完整profile、光轴语义、网格版本、8帧顺序及反馈含义；恢复和play必须契约相同。旧v2/v3 warm-start对v5显式拒绝，v4模型也不能当v5精确恢复。当前v5脚本从头训练，未实现旧深度权重迁移。JIT/ONNX导出manifest包含同一depth_contract。现有`--visray`仅支持旧解析深度，v5暂不支持该选项。

从项目根目录启动命令（本次未执行正式训练）：

```bash
bash scripts/rsl_rl/train_agilekickball_v5.sh
# 提供实机标定profile后：
bash scripts/rsl_rl/train_agilekickball_v5.sh env.camera_profile_path=/absolute/path/g1_depth.json
# 恢复仅限相同v5契约：
bash scripts/rsl_rl/train_agilekickball_v5.sh --resume --checkpoint /absolute/path/v5/model.pt
```

正式产物独立写入 `logs/rsl_rl/agilekickball_v5/`；v4原目录保留。运行前核对GPU资源。2026-10-14验收时Wall4正在同一GPU训练，4环境短测允许短暂资源竞争，不将并发短测耗时作为4096环境速度结论。

验证命令：

下方GPU smoke保留历史随机化验收场景，显式开启两个开关；它不代表当前默认无扰动配方。

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v5.py -v
bash scripts/rsl_rl/smoke_agilekickball_v5.sh
```

验证模型只保存在 `docs/agilekickball_v5/validation/`，不得作为正式训练或成功率证据。2026-10-14 17:57 JST验收：两组CPU回归通过（包含v4/state-feedback与CarryBox回归）；4环境、18组RTX/Warp对照通过，最大差异0.152mm，内部像素最大0.142mm，超过2cm像素为0。包括12步运动、逆序部分reset、球移动、机身遮挡和隐藏球移动不影响被挡像素；独立理想球面2mm断言通过。38组几何=36个有可见表面的G1刚体连杆+球+地面。

完整PPO/AMP执行2轮后新建runner恢复并再执行1轮，权重有限；缺失/不同相机契约和旧warm-start被拒绝。live/JIT/ONNX动作比较通过，manifest保存相机契约。未测v5的4096环境迭代速度，未做正式训练或成功率评估。继承的PPO初始学习率仍为v4的1e-5，不能把这次运行验证当作从头训练已能收敛的证明。

[最终回执](attempt7_receipts.json)、[结构化结果](validation/result.json)、[可见球/机身遮挡深度图](validation/depth.png)、[工程交接](../../agent/handoff/agilekickball-v5-depth.md)。此前失败日志与回执完整保留：参考相机pose刷新配置、隐式Sphere细分差异、并发录像OOM，以及同一runner的inference-buffer恢复测试方式。最终测试保持原2mm/1%阈值，改用实际启动方式的新runner恢复；未改变v4或Wall4数值配置。
