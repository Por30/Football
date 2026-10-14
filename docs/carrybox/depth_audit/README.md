# G1深度位置、坐标和遮挡审计

2026-10-13。结论：**FindBox的名义相机安装与当前G1模型一致，CUDA/RTX场景遮挡及训练观测归一化通过独立验证；尚无实机标定文件，不能确认具体实机的完整部署管线一致。Football仍为只计算球面相交的解析深度，不包含环境/自身遮挡。** 本次没有更改生产环境、资产或正在运行的足球训练。

## 安装位姿证据

训练资产转换记录：`source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/config.yaml`，其URDF来源为`/home/cao/PhysHSI/legged_gym/resources/robots/g1/urdf/g1_29dof.urdf`。`d435_joint`相对`torso_link`：

- 平移（米）：`[0.0576235, 0.01753, 0.42987]`，即前5.76235cm、左1.753cm、上42.987cm。
- RPY（弧度）：`[0, 0.8307767239493009, 0]`，下俯47.6°。
- FindBox的world-convention四元数为wxyz=`[0.91495, 0, 0.40355, 0]`，舍入造成的角度差约0.00094°。

独立仿真还读取了已加载USD资产的`d435_link`相对torso位置，与配置一致；对机器人root施加平移和yaw后，虚拟相机保持相同相对安装位姿。测试没有重设一个与训练无关的外置相机。

本机`unitree_rl_lab/.../g1_29dof_rev_1_0.urdf`与上述安装一致；同目录的另一份`g1_29dof.urdf`则为z=`0.41987m`，低1cm。因此“G1”名称不足以唯一确定实机外参。来源路径、hash和数字比较见[geometry.json](geometry.json)。URDF的D435安装link还不能替代实机深度光心到torso的标定变换。

world相机坐标约定是X前、Z上；ROS光学坐标是Z前、X右、Y下。FindBox由Isaac Lab转换约定，监督标签也使用实际相机的ROS光学坐标。Football的四元数以ROS光学约定给出，数值虽不同，名义前向方向与FindBox近似一致。

## 实测内参与数据定义

| 配置 | 图像W×H | fx=fy（像素） | cx,cy | HFOV / VFOV |
|---|---|---|---|---|
| CarryBox-v0 | 48×32 | 28.8000 | 24,16 | 79.611° / 58.109° |
| Walled3 / Walled4 | 48×27 | 24.3546 | 24,13.5 | 89.160° / 58.000° |

以上来自传感器实际`intrinsic_matrices`，不只读取配置字段。当前Isaac相机内参计算用horizontal_aperture及输出宽度确定fx，并假定方形像素；walled配置的宽高比正确生成58°垂直视场。

FindBox读取`TiledCamera.data.output['distance_to_image_plane']`，即米制**光轴Z深度**，非法/无穷值取3m，裁剪0.1–3m后除以3，形成4帧历史。辅助标签和深度经过配对的延迟/冻结缓存。渲染在前，生产观测函数只归一化/扰动，不用箱子标签生成观测，也没有删除障碍或透视箱子的逻辑。

## CUDA/RTX遮挡证据

[基线结果](baseline.json)、[wall3结果](walled3.json)、[wall4结果](walled4.json)均PASS。每种配置使用1个真实G1环境，加载生产相机和观测函数；基线额外加入与walled相同的测试障碍。所有障碍有实际渲染几何。

| 中心像素探针 | 基线 | wall3 / wall4 |
|---|---:|---:|
| 箱子无遮挡 | 0.875000m | 0.875000m |
| 墙在箱子前 | 0.450000m | 0.450000m |
| 圆柱在箱子前 | 0.328496m | 0.321440m |
| 遮挡状态移除后方箱子，中心深度最大变化 | 0m | 0m |
| 移走遮挡物，恢复箱子读数最大误差 | 0m | 0m |

还验证：相机前方平行墙面的中部大块像素均为0.45m（证明输出是光轴深度而非斜射线长度）；空场地面形成正确渐变；生产`perception`最新帧与原始渲染深度经裁剪/除3后逐像素一致；箱子位置标签在光学坐标中为预期的`[0,0,1]`。

深度对照图（越暗越近）：

- [Walled4遮挡对照](walled4.png)
- [Walled3遮挡对照](walled3.png)
- [CarryBox-v0遮挡对照](baseline.png)

原始深度数组保存为各变体的`*_depth.npz`。地面、机器人和障碍都在RTX可见场景中；本次定量遮挡断言覆盖墙和圆柱，未单独构造机械臂自遮挡探针。

## 验证边界与部署待核对项

这是**确定性静态几何/渲染审计**：walled探针关闭RSI、安装扰动、深度噪声、延迟和冻结，保留生产观测函数/历史布局和相机几何；没有执行PPO。因此不能把本次PASS写为walled完整训练恢复，此前CB-006的PhysX CUDA700问题仍待排查。正式walled配置安装随机误差为±5mm/轴、±2°/轴，不会每回合恰好处在名义位姿。

初次CPU仿真设备下的TiledCamera探针得到零深度，未通过；最终使用与训练相同的CUDA:0路径通过。保留[初次失败回执](initial_cpu_render_receipts.json)，没有将CPU路径标成可用。

实机尚需用户指定部署/标定配置，以核对：实际G1版本和安装改动、`torso→depth_optical_frame`变换、深度stream的CameraInfo/K与畸变、是否对齐到RGB、裁剪/缩放如何调整内参、原始深度单位到米的转换、无效像素及0.1–3m裁剪、除3归一化、帧率与4帧历史时序。本机搜索的项目和G1部署目录未定位到本任务的这套实际深度输入配置；不能把名义URDF匹配当成实机标定完成。这里没有连接或操作真实机器人。

Football当前主线使用`mdp/perception.py:synthetic_ball_depth_image`，仅依据球面相交产生深度，单位为沿射线距离（米）；没有地面、墙、人或机身遮挡，与FindBox的完整RTX/光轴深度管线不同。本次没有改变其训练接口或checkpoint。

## 复现

```bash
cd /home/cao/perceptual_ball
/home/cao/ENTER/envs/ball/bin/python scripts/audit_g1_depth.py --geometry-only
bash scripts/audit_g1_depth.sh
```

[冻结测试回执](test_receipts.json)均PASS。脚本使用现有Isaac环境，渲染检查结束后退出，不启动训练。
