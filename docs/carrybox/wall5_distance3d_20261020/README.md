# wall5 revision18：任务距离改为三维

已实现并通过工程短测。按用户提供的 [x2g1differ.md 第3.9节](../../../x2g1differ.md) 和 [handoff.txt 奖励公式](../../../handoff.txt)，wall5 的任务距离从水平 XY 改为骨盆连杆原点到箱心的 XYZ 欧氏距离，单位米，阈值仍为 0.7。未在已检索目录找到原始 X2 环境源码，因此依据交接说明对齐公式，不宣称重新运行验证了 X2。

`distance = norm(box.root_pos_w - robot.root_link_pos_w, dim=-1)`。本机 IsaacLab 的 `root_pos_w` 就是 `root_link_pos_w` 的别名；共享奖励中的旧属性和 wall5 专用属性使用同一原点，4环境读回核对通过。

| 使用位置 | revision18 的距离条件 |
|---|---|
| walk_task 近箱饱和值 1.5 | XYZ < 0.7 m，仍乘现有平衡系数 |
| carryup_task 拾取奖励 | XYZ ≤ 0.7 m |
| slow_pickup | XYZ < 0.7 m 且箱高 < 0.55 m |
| stable_grasp、arm_speed_pickup、arm_acc_pickup | XYZ < 0.7 m，骨盆高 < 0.60 m，箱高 < 0.58 m |
| search_turn | XYZ > 0.7 m，同时满足原 search 标记和 bearing > 45° |
| locomotion_stability 近箱高度豁免 | XYZ ≤ 0.7 m |

行走速度仍投影到归一化的水平朝箱方向，bearing 仍为水平角；未误用三维距离去缩小水平速度。AMP 的箱子水平 0.7 m 封顶和远处 z=0 保持；手到箱距离本来就是三维。初始化半径、held门控、成功条件、reset、观测、PPO、权重、相机与数据保持。显式开关仅 wall5 默认开启；wall3/wall4 保留 XY，足球未修改。

日志 `Motion/loco_survivor_box_distance_m` 从本版开始跟随 XYZ 任务距离，新增 `Motion/loco_survivor_box_distance_xy_m` 用于水平距离对照。跨 revision 比较旧指标时需区分语义。

骨盆高 0.78 m、地上箱心高 0.125 m 时，XYZ 0.7 m 对应水平距离约 0.247 m；降低骨盆后水平容许距离变大。这与 X2 的距离公式一致，但机器人高度不同，实际水平门槛也不同。旧 model14200 录像999个未重置采样中，XY < 0.7 有974个，XYZ < 0.7有182个；第999步分别为0.3304/0.7402 m。因此那一帧在新规则下仍属于远箱。此项只重算旧轨迹几何，不是新版策略效果评估：[数值及来源hash](prior_trajectory_geometry.json)。

验证：43项CPU检查通过，覆盖高度差、0.7严格/包含边界、平移不变、零水平距离、水平速度投影、旧任务默认值及既有AMP/AC边界。4个真实Isaac环境验证三维门控/奖励/日志，执行PPO和AMP 2轮＋严格保存恢复后1轮，actor、critic、深度CNN、辅助头及判别器优化器正常更新，数值有限，输入维度保持。4个控制状态的XY距离为0.33/0.20/0.60/0.50m，对应XYZ为0.7334/0.6849/0.7353/0.6562m，拾取奖励门控为关/开/关/开。[回执](receipts.json)、[仿真结果](smoke.json)。短测模型仅在本docs目录，不是正式模型或收敛证据。

首次短测失败是测试构造静止状态时使用COM速度写入接口，已有连杆速度缓存未同步；增加异常输出定位后改用显式连杆状态接口。两次失败日志和回执保留，原断言未放宽，生产reset/速度管线未改。[修正说明](repair_notes.json)。

checkpoint 契约升为 `migration_revision=18` 并记录XYZ距离、端点、阈值和XY方向语义；新版严格恢复通过，合成revision17旧契约在带/不带优化器两种严格load下均拒绝。现有revision17训练不能直接按新版 `--resume`；需要新训练进程。若明确选择沿用旧网络权重，已有 `--warm_start_carrybox <checkpoint>` 是显式仅权重迁移入口，不等同恢复旧优化器/课程。本次未执行权重迁移或重启。

正式训练状态快照：2026-10-20T12:30:44.883528+09:00，PID254358仍为revision17，日志迭代14676；本次未停止、启动或重启正式训练，已经运行的Python进程不会自动加载本次源码变更。revision18尚未正式训练，也未证明能抱箱。[实时核对快照](formal_status.json)。

复核命令（仅短测）：

```bash
bash docs/carrybox/wall5_distance3d_20261020/check.sh
bash docs/carrybox/wall5_distance3d_20261020/smoke.sh
```
