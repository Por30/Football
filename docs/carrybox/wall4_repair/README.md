# Wall4 运行故障修复（2026-10-13）

**工程修复和正式规模验收通过，正式wall4已排队等待football结束。** 2026-10-13 23:54 JST：后台等待器PID **2300674**，就绪状态READY、运行状态WAITING_FOOTBALL；足球PID2056902约48693/50000轮，未被停止或重启。实时状态以队列 `status.json` 为准。此前失败证据保留在 `wall4_queue/`，不能据旧文档判断实时状态。

## 故障与最终实现

1. 原运动学平台从初始地下位置重置后，首个控制步将箱子弹至十余米，速度达到数百 m/s。本机 Isaac Sim 4.5 GPU 后端不支持 `set_kinematic_targets` 或 `set_disable_simulations`。只写 pose 并未消除重置冲量。
2. USD 静态几何方案能更新 RTX 位置，但实际撞墙测试穿透；显式 `flush_changes()` 也未解决。本方案已弃用，短训输出不能作为有效验收。
3. 最终墙、圆柱、平台使用禁重力的动态刚体，XYZ 平移和旋转六个轴全部锁定（mask=7）。只在 reset 通过 PhysX tensor 写位姿及零速度，回合内不写位置、不推进额外仿真步。它们保持静止并参与真实碰撞；没有用大质量或关闭碰撞替代。
4. G1 资产实例内部四个肩部原生 Cylinder 参与 `ConvexCore` GPU 接触路径。只在 walled 的 spawn 阶段将左右 shoulder pitch/roll 的碰撞圆柱换为同半径、同长度的 32 边凸包网格，保留局部变换、材质及 visual。原 USD 文件和足球机器人 spawn 配置未改。
5. 128 环境、13 m 间距的可视地面扩大为 300×300 m。迁移环境契约 revision=3，记录 `locked_rigid_6dof` 与 `convex_hull_32`；CarryBox checkpoint schema 仍为2。旧失败烟测的环境契约不兼容，不能作为正式初始化模型。

观测、AMP、奖励、RSI 比例、课程和控制频率保持原任务设计。actor 与 critic 仍只读取本体和深度，箱子真值仅用于辅助监督/奖励/reset。

## 验收内容

`bash scripts/rsl_rl/validate_carrybox_runtime.sh` 串行执行：

- wall3、wall4 各自独立的4环境几何进程：三技能RSI、部分环境reset隔离、相机本地安装偏差、观测/标签配对、RTX墙柱遮挡、实际撞墙撞柱及平台支撑。
- wall3、wall4 各自全新4环境训练进程：20轮真实 `runner.learn`，多次reset，PPO/AMP更新，保存/恢复后再训2轮，跨变体恢复拒绝与显式warm-start检查。
- wall4 128环境、20秒正常回合、默认4 epochs/4 minibatches：50轮训练＋恢复后2轮。记录显存，若空闲显存低于1 GiB仅停止本次测试进程，保护football。

所有阶段必须同时满足进程正常退出、JSON PASS、结束标记及日志无 PhysX/CUDA/内存错误。某些原诊断进程即使返回0也包含PhysX错误，因此单独的 `result.json` 绝不是就绪证据。

正式训练仍遵守 football 完成后串行启动。队列核对足球进程身份、最终49999模型与日志，再检查源码/数据/验收hash；资源释放后重复128环境预检，随后只启动一次40000轮wall4。正式输出在 `logs/rsl_rl/g1_carrybox_depth/walled4/`，本目录所有模型仅供验证，不能当作任务成功率或正式训练结果。

## 验收结果

三条冻结命令均PASS：[最终回执](test_receipts_attempt2.json)。第一次验收发现静态USD碰撞不同步，失败回执保留为 `test_receipts_attempt1.json`；随后没有删除或放宽实际碰撞断言。

| 验证 | 结果 |
|---|---|
| CPU合同 | 19项通过 |
| wall3，4环境 | 20＋恢复2轮，105次reset，最大箱速3.94m/s |
| wall4，4环境 | 20＋恢复2轮，106次reset，最大箱速3.65m/s |
| wall4，128环境正式配置 | 50＋恢复2轮，5147次reset，最大箱速5.82m/s |
| 128环境显存 | 与football并行短测期间总峰值21888MiB，比测试前增加6222MiB，空闲始终超过1GiB保护线 |
| 碰撞与RTX | 墙前箱心停在x=1.25m，柱前约1.20m；平台上箱心z=1.125m；墙/柱中心深度分别1.40/1.353m，后方箱子移动不泄漏 |

[wall3几何](walled3/geometry.json)、[wall3训练](walled3/smoke.json)、[wall4几何](walled4/geometry.json)、[wall4训练](walled4/smoke.json)、[128环境训练](scale128/smoke.json)、[显存](scale128/memory.json)。128环境checkpoint通过CPU重新加载检查，schema/variant/迭代及所有浮点张量有限性正常。

已停止原等待器2280644并保存其配置快照，重新绑定当前源码、原始数据、GPU身份和成功回执；新等待器2300674确认WAITING_FOOTBALL心跳。**尚未开始正式wall4训练，也没有独立任务成功率结论。** 正式启动前队列还会在football释放GPU后重复50＋2轮128环境预检。

## 查看串行训练

```bash
cat logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/status.json
```

`WAITING_FOOTBALL` 是等待现有足球训练；`PREFLIGHT` 是足球结束后的128环境复核；`RUNNING` 才表示正式wall4已启动；`COMPLETED` 需要正式最终模型及日志通过校验。`BLOCKED` 会保存原因，等待器不会反复重启失败训练。`config.json` 保存训练命令及源码/数据/验收hash，`registration.json` 保存等待器身份；这些文件中的PID、时间和状态以最新内容为准。

正式训练日志启动后位于同目录 `train.log`，实际checkpoint位于上一级自动创建的时间戳run目录。本次工程修复、短训通过、正式训练完成和独立成功率评估是四个不同状态。
