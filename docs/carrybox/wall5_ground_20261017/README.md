# Wall5 地面拾箱数据与全贴地 reset · 2026-10-17

本次按“只保留从地面开始的完整拾箱片段”处理：AMP继续学习后续抬起，reset只使用离地前且接触检查通过的起点。该解释已在执行时明示；异步澄清未收到答复，不记作用户明确确认。新增独立、可撤回的数据profile，原数据未删除或改写。

## 数据和生效范围

wall5的AMP与RSI统一使用[`assets/motions/findbox/ground_pickup/`](../../../source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/README.md)，schema1、dataset_revision4、`findbox_ground_pickup_v1`。

| 数据 | 修改 |
|---|---|
| `pick_up_01.pt` | 从新profile排除：参考箱底最低约0.225m，无地面起点 |
| `pick_up_02.pt` | 从新profile排除：参考箱底最低约0.089m，无地面起点 |
| `pick_up_03.pt` | 完整129帧保留，箱子从地面抬起，张量/文件字节不变 |
| 行走11段 | 保留，字节不变 |
| `hold_box_01.pt` | 300帧保留，仅作AMP持箱先验，不作wall5 reset起点 |

新profile合计13段、3785帧/60Hz；AMP组权重仍40/40/20%，60→50Hz、10帧窗口。原上级15段、manifest、文件名映射和根`findbox/`旧快照全部保留并校验hash。CarryBox基线、wall3/wall4仍使用原15段及原reset逻辑；football没有改动。数据筛选记录见[profile_record.json](profile_record.json)，可用[prepare_profile.py](prepare_profile.py)复现新profile。

## Wall5 reset

- 分布改为loco70%、地面pickup30%、hold0%。hold概率非零时明确报错。
- 所有箱子按旋转后的最低点离各自地面5mm放置，速度清零。倾斜箱按三维旋转计算投影半径，不把箱心简单设成固定半高。
- loco保留前方/视野外位置、倾斜及yaw课程；pickup保留参考XY和机器人姿态/速度，但箱子Z强制贴地。
- `Platform`从wall5场景与Warp目标中同步移除，无抬高的支撑面。
- G1实际脚凸包的接地修正保留；不为了降箱子而把机器人向下平移。
- 机器人全身碰撞保留，自碰撞仍关闭。奖励、push、相机、本体/深度/AMP维度和终止条件未调整。

源参考箱高使用`base_height + 0.05 + box_pos_local.z`。初始20帧中位箱底在±2cm内才认定为地面起点；首次比初始中位抬高5mm之前的连续前缀作为几何候选，并保留后继源帧供速度计算。该条件给pickup03产生0–60帧候选，另外两段无候选。

随后实际检查全身G1与箱子的碰撞：

| 检查 | 结果与处理 |
|---|---|
| 候选0–60 | 34帧起右膝/股关节穿入箱子，最大authored凸包穿插约21.0mm；首20ms箱速最高2.398m/s，首次检查失败 |
| 无初始凸包重叠0–33 | 32/33帧仍出现0.801/1.038m/s初始箱速；说明仅无几何重叠不足以排除物理接触冲量 |
| 最终0–31 | 作为实际RSI范围；配置和manifest记为半开区间`[0,32)`，继续用逐帧物理检查验收 |

原始失败证据：[61帧几何/速度](reset_geometry_initial_fail.json)、[首次回执](receipts_initial_fail.json)。进一步速度证据：[34帧逐帧数据](reset_geometry_34frame_velocity_probe.json)。没有放宽断言或删除失败记录；AMP仍保留完整129帧，只收紧RSI起点。完整参考轨迹并未因此获得全身碰撞可执行性的保证，也未证明策略已能稳定拾取。

## 兼容性和验证

wall5环境契约升为revision11，包含实际RSI manifest hash、ground开关、帧范围、平台状态，保留原全身碰撞profile。旧revision9/10模型不允许严格resume；显式weights-only可以迁移策略，但PPO/AMP和课程需重建。新数据同样有独立AMP manifest身份检查。原wall3/4环境契约不变。

冻结命令：

```bash
bash docs/carrybox/wall5_ground_20261017/check.sh
bash docs/carrybox/wall5_ground_20261017/smoke.sh
```

CPU检查覆盖原数据hash、13段完整抬起、AMP窗口/权重、非法几何、无候选拒绝、不同地面高度/倾斜的partial reset、实际RSI身份以及原AMP/wall/G1 reset回归。GPU短测为4环境：逐帧实际机器人位姿、35个authored凸包与箱子的SAT、首20ms物理响应、loco随机yaw/tilt、无平台及Warp目标、partial/自动reset的状态和terminal历史、小规模PPO/AMP更新与新checkpoint恢复、旧契约和RSI单独变化拒绝。

最终两条命令均PASS：27项CPU；4环境逐32帧最大authored凸包穿插0、首20ms箱速0.1962m/s、手箱力0N，8次强制自动reset及partial reset通过，PPO/AMP更新2轮＋恢复后1轮。策略、判别器及两优化器状态有限。没有4096吞吐或长期成功率结论。

最终结果以[receipts.json](receipts.json)、[smoke.json](smoke.json)、[reset_geometry.json](reset_geometry.json)为准。SAT基于最终USD定义的凸包与实时关节位姿，并非声称逐顶点读取了PhysX cooked网格。首20ms检查用当前参考关节角作PD目标，不代表任意策略动作下接触稳定。

模型与TensorBoard工件仅保存在本诊断目录，不能作正式训练或成功率证据。没有启动/重启CarryBox正式训练，也没有停止football。后续应在新revision11环境独立训练和评估完整地面找箱拾取。
