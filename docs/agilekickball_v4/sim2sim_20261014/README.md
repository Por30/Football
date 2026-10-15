# AgileKickball v4 · MuJoCo s2s（2026-10-14）

工程接口已完成，8项CPU检查及500步闭环通过；接球回传稳定性尚未验收。未进行真机/DDS控制、真实视觉验收或训练。当前正式v4权重保持不变，TorchScript导出逐张量核对与model_49999.pt一致。

## 仓库更新与编译

- `/home/cao/unitree_mujoco` 的main从备份记录的旧HEAD快进到 `1eb6642`（10个上游提交）；高度扫描等Go2定制保留。param.h头文件与命令选项冲突已合并。
- `/home/cao/unitree_rl_lab` 已包含远端main `4960b84`；保留本地提交 `631136f` 及Go2未提交修改。没有切到IsaacLab3.0等开发分支。
- 两个C++目标已编译；G1可执行程序为 `/home/cao/unitree_rl_lab/deploy/robots/g1_29dof/build/g1_ctrl`。
- 修复G1 main.cpp的静态键盘线程初始化，使 `--help` 不再因thread析构异常abort；键盘仍在正式控制入口启动。
- 原始diff、未提交文件tar和HEAD记录在 [repo_backup](repo_backup/)，MuJoCo更新前stash也保留。没有提交或推送。
- [provenance.json](provenance.json)记录完整提交、模型hash、训练URDF来源。C++模拟器使用MuJoCo3.3.6；独立Python s2s使用已有umr环境的MuJoCo3.3.7与Torch2.4.1。

## 运行

在 `/home/cao/perceptual_ball` 下打开MuJoCo窗口：

```bash
/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py \
  --duration 60 --physics-dt 0.005 \
  --output docs/agilekickball_v4/sim2sim_20261014/viewer_run.json
```

2026-10-15新增手动球速控件，随深度窗口自动打开，命令不变：

- **Ball speed [m/s]**：默认范围0.1–6，拖动后用于后续发球；`--speed`设置初始值，超出默认范围时滑块自动扩展。
- **Apply now**：立即改变当前球的水平速度大小，保留当前位置、水平运动方向及竖直速度，匹配滚动角速度；静止球默认向-x运动。这是一次速度修改，后续仍受碰撞/摩擦影响。
- **Re-serve**：以选定速度从(2,.15,.11)m重新发球，只重置球，不重置机器人与策略历史。
- **Serve / Actual XY**：分别显示发球设定值和当前实际水平速度。正常回合恢复/跌倒逻辑继续运行。

UI事件在下一控制步的观测之前执行，记录到JSON的`ball_speed_commands`；人工发球单独计入`manual_serves`。`--no-depth-window`同时禁用这些控件，`--headless`保持无窗口。

[球速接口回执](ball_speed_20261015/receipts.json)：原8项检查及新增4项检查通过（含真实桌面双窗口100控制步，自动拖动滑块、立即应用、重新发球及关闭深度窗口后继续运行）。[GUI短测记录](ball_speed_20261015/gui_smoke.json)只证明接口运行，不作为接球成功率或稳定迁移证据。

无窗口使用 `--headless`。脚本默认physics_dt=.002；上述命令显式使用与训练一致的.005。策略控制周期始终.02秒。2026-10-14已用软件OpenGL完成真实桌面双窗口短测：100控制步、20次深度刷新，无错误。

**当前Kickball通过独立Python runner直接控制MuJoCo，使用官方G1模型。编译好的g1_ctrl仍是官方部署控制器，没有接入Kickball双输入或相机DDS；不能直接拿它启动真机Kickball。**

输入是`flat[1,864]`和`depth[1,8,27,48]`，输出29关节原始动作。本体历史按term-major再oldest→newest；reset重复首帧；last_action保留网络动作。五末端取link原点，head采用训练URDF固定变换恢复site。root角速度先取世界轴再转pelvis link frame，避免MuJoCo惯性局部轴混用。PD每物理步更新，受官方ctrlrange与joint actuatorfrcrange共同约束。

v4深度为torso相机的解析球面射线距离，米制，无地面/机身遮挡；没有接真实相机或v5场景深度。球默认从(2,.15,.11)m以2m/s滚入，可用`--speed`或窗口控件调速。回合结束条件与恢复门控沿用训练阈值：球距anchor>3m、越过后方-.3m或速度<.15m/s后等待；稳定.3s且冷却.4s才再发，恢复超时5s记录并reset。`--serve-mode fixed`保留最初4秒强制发球诊断；默认recovery。

本runner用于初步部署诊断，并非完整训练环境/成功率评估器：固定发球位置、可手动调整球速，无随机课程；只记录接触控制步，不把它当踢球次数或回传命中；不因root平移超过.6m立刻reset，记录越界并令稳定标记失败，方便诊断；跌倒/恢复超时会reset并计数。

## 验证结果

[冻结测试回执](test_receipts.json)：两个官方目标build/help、8项数值CPU检查、500步真实TorchScript+MuJoCo闭环均PASS。单位检查包含最终checkpoint权重、关节映射、历史顺序、非零角速度坐标、FK、解析深度、动作/力矩边界和恢复门控。

| 场景 | 控制步 | 跌倒 | 球–机器人接触控制步 | 最大离站距离 | 最低root高度 |
|---|---:|---:|---:|---:|---:|
| 默认.002s，10秒 | 500 | 0 | 2 | 0.358m | 0.621m |
| 默认.002s，60秒 | 3000 | 0 | 2 | 0.358m | 0.621m |
| 训练.005s，60秒 | 3000 | 1 | 63 | 0.676m | 0.381m |

[10秒smoke](smoke.json)、[60秒默认步长](rollout60.json)、[60秒训练步长](rollout60_training_dt.json)含逐段轨迹、hash、饱和次数、耗时和实际模型参数；对应.log记录完整执行输出。CPU推理中位数约0.32ms。额外两个60秒诊断命令均实际执行并exit0，未将它们混入冻结测试回执。

`interface_smoke_pass`只判断是否完整执行且无数值故障。`stable_for_full_duration`只检查跌倒、恢复超时、.6m离站阈值与末态balance，不证明踢球或回传成功。默认步长60秒只有2个接触控制步；训练步长接触增加但出现1次跌倒，**不能宣布任务稳定迁移或真机可用**。初版固定发球与角速度修正前的失败证据保存在 `initial_fixed_serve_*`，不与最终结果混用。

## 模型差异与下一步

训练URDF总质量33.341kg，官方MJCF35.112kg；hip_roll训练139Nm/官方88Nm，ankle及waist_roll/pitch训练35Nm/官方50Nm；waist_pitch范围训练±.62rad/官方±.52rad，腰部link位置、被动摩擦、脚接触几何也不同。生成场景保留官方惯量与力矩边界，局部增加球/地面/head site并禁用机器人自碰撞；未扩大电机力矩。PhysX restitution=.5与MuJoCo接触参数尚未标定，球阻尼也未完全对齐。

下一步应先做同一固定发球条件下的IsaacLab对照与机器人/球接触参数对齐，区分原策略问题和迁移差异；再补回传目标门、接球失败与恢复的完整统计。真实视觉需单独走v5/相机标定路径。当前没有启动任何正式训练，也没有改动CarryBox任务。

## 深度图可视化（2026-10-14）

[12秒视频](depth_visualization/depth.mp4) · [预览图](depth_visualization/depth_preview.png) · [原始米制深度](depth_visualization/depth_raw.npz) · [数值与视频信息](depth_visualization/depth_info.json)

实际策略输入的只读副本：大图为最新27×48帧，下排为8帧历史（相邻20ms，左旧右新）；颜色范围固定为0.1–3m，灰色表示未命中、输入值3m。右侧记录最近命中距离和命中像素。这里仍是v4球体解析深度，不含场景/机身遮挡。

```bash
/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py \
  --headless --duration 12 --physics-dt 0.005 \
  --output docs/agilekickball_v4/sim2sim_20261014/depth_visualization/run.json \
  --depth-output docs/agilekickball_v4/sim2sim_20261014/depth_visualization
```

采集频率10Hz，策略仍为50Hz；MP4为1200×700、120帧/12秒。NPZ字段`time_s`与`depth_m[120,8,27,48]`对应每个视频帧，保留原始浮点深度而非颜色值。采集只复制现有网络输入，不额外调用observe；120个记录时刻的机器人/球轨迹与既有不采集的run完全一致。视频已解码核验帧数，8项原有CPU检查通过。预览选择命中像素最多的t=4.4s帧（19/1296像素），不是单独合成图。

## 同步实时深度窗口

图形启动默认同时打开 `Kickball - Live policy depth` 窗口，无需额外参数：

```bash
/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --duration 60 --physics-dt 0.005
```

大图为当前策略输入，下排为8帧历史；10Hz刷新，策略仍为50Hz。显示仿真时间、最近距离和命中像素数。关闭深度窗口不停止MuJoCo；仿真退出时回收窗口。`--no-depth-window`只关闭深度显示；`--headless`不创建任何窗口。`--depth-output`仍可用于录制文件。

[双窗口短测](depth_live_smoke.json)与[检查回执](depth_live_receipts.json)：已有8项CPU检查通过，软件OpenGL下2秒/100控制步完成、深度实际刷新20次。图像读取实际网络输入，不额外推进历史或改策略数值。
