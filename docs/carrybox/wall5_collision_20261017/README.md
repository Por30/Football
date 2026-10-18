# CarryBox wall5：G1碰撞体核对 · 2026-10-17

当前wall5继承wall4/wall3的G1生成路径：本地29自由度、无手指资产；载入后只在临时场景中替换4个肩部圆柱。保存的正式run配置也记录相同spawn函数和关闭自碰撞。

离线检查统计：28个带碰撞几何的link、30个几何叶节点，wall5转换后为26个Mesh（凸包近似）＋4个Cube。这是USD定义与原生产生成函数的内存执行结果，未启动PhysX cooking或读取运行中训练stage，不能当作底层shape数量的实测。

| 部位 | 当前碰撞几何 | 说明 |
|---|---|---|
| 髋、踝、脚、骨盆外壳、躯干 | 各link网格convexHull | 非逐三角形动态碰撞；每个link分别取凸包 |
| 左右膝/小腿knee_link | 每侧2个长方体 | 9×7×10cm和5×4×10cm；不是完整小腿外壳 |
| 左右shoulder_pitch | 圆柱形Mesh凸包 | 半径3cm、长5cm，32段圆柱网格 |
| 左右shoulder_roll | 圆柱形Mesh凸包 | 半径3cm、长3cm，32段圆柱网格 |
| shoulder_yaw、elbow、wrist_roll、wrist_pitch | 各link网格convexHull | 保留原资产 |
| left/right_rubber_hand | 各1个网格convexHull | 无独立手指关节/碰撞体；两侧各轴包围尺寸约13.18×6.66×10.65cm，非长方体形状 |
| 头部head_link | 无独立碰撞体 | 有可见网格，但没有自己的物理接触几何 |
| waist_yaw/waist_roll、wrist_yaw/palm等 | 无独立碰撞体 | 周围分别有torso和rubber_hand等其他link的碰撞几何 |

脚部碰撞网格在link坐标下的包围尺寸约20.82×7.56×5.90cm，实际使用凸包，并非上述尺寸的长方体。

**物理自碰撞关闭**：`enabled_self_collisions=False`。机器人各连杆之间不启用关节体自碰撞；机器人与箱子、地面、墙和圆柱的碰撞仍保留。因此不能依靠当前物理自碰撞约束阻止手臂穿过躯干。

**深度自遮挡保留**：Warp从可见三角面构建光线目标，包括头部和机器人其他可见表面。物理碰撞凸包和深度可见表面不是同一套几何；有视觉遮挡不等于启用了物理自碰撞。

碰撞API多数加在各link的`collisions`父Xform上；只检查叶Mesh的CollisionAPI会漏报。肩部转换在生成时解除对应collisions实例，对4个Cylinder写入同尺寸32段Mesh并设`convexHull`，共享USD不修改。此路径属于wall3/4/5；不能因此推断football也做了相同替换。

## 证据与边界

[逐link路径、尺寸与hash](geometry.json)、[执行日志](audit.log)、[PASS回执](receipts.json)。使用现有USD库在CPU解析，AST提取未修改的`spawn_walled_robot`原函数体，只替代初始加载/prim查找接口以指向临时stage。验证28个碰撞父节点、30个几何叶节点、仅4肩部改变、替换前后包围尺寸一致、原资产/源码hash不变。

首次审计脚本名`inspect.py`遮蔽Python标准库inspect导致导入失败，已改名`audit_geometry.py`；原失败回执保留[receipts_initial_fail.json](receipts_initial_fail.json)，原冻结命令重跑通过。没有更改生产代码、训练、配置或资产。

复核命令：`bash docs/carrybox/wall5_collision_20261017/inspect.sh`。本次只回答碰撞几何配置，不构成抓取稳定性或训练收敛评估。
