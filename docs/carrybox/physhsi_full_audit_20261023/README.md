# 当前 wall5 与本地 PhysHSI G1 CarryBox：完整训练链路对照

源码/数据核验时间：2026-10-23 23:52 JST；2026-10-24收尾时补入独立wall10性能检查的新证据。主对照为 **wall5 revision28**；独立 wall10 只作迁移现状补充。本轮只读分析，未修改生产代码、数据、资产、checkpoint，未启动或停止训练。

**结论：两边已经共享 G1 资产来源和大部分拾箱/行走原始数据，但不是同一训练任务。** PhysHSI 是带噪声物体/目标状态输入的“接近→拾起→搬运→放下→松手站稳”；wall5 是深度输入的“找箱→拾起”，叠加了 X2 奖励门控、接触奖励、动作约束和不同的 PPO/AMP 实现。碰撞/reset 的局部迁移不能等价于整个 PhysHSI 训练配方。

本报告区分三类结论：源码/存档参数可确认的差异、CPU 数据与权重检查确认的事实、仍需物理回放才能确定的影响。**静态差异不等于已经证明的失稳原因。** 特别是原始力矩平方惩罚，rev17/rev22 能接近箱子时也已经存在，不能用它单独解释后续版本退化。

## 证据与版本边界

- [sources.json](sources.json)：PhysHSI 基类继承后的完整配置、resume 配置、wall5 正式 run 的 env/agent 参数、函数行号、USD 作者属性。
- [source_identity.json](source_identity.json)：47 个相关源码/资产文件 SHA256，防止把不同版本拼成一个配方。
- [data.json](data.json)：19/15 段数据逐文件 hash、帧数、采样权重、独立 URDF FK、两份 checkpoint 结构及 CPU 前向结果。
- [appendix.md](appendix.md)：逐关节 PD/限位、逐连杆质量/碰撞体、全部数据映射及源码入口。
- [receipts.json](receipts.json)：两条冻结 CPU 检查均 PASS；本轮未跑新仿真。
- [重构边界与验收](reconstruction.md)：哪些恢复、哪些保留、哪些原版行为不能照抄。

比较对象：

| 对象 | 锁定来源 | 能证明什么 |
|---|---|---|
| PhysHSI 基础任务 | `/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py` 与 `carrybox_config.py` | 本地当前有效实现；这是 **G1**，不是此前 X2 wall4 |
| PhysHSI 后续训练 | 同目录 `carrybox_resume_config.py` | 同环境类，AMP 系数和箱子倾覆终止等不同 |
| PhysHSI 资源模型 | `resources/ckpt/carrybox.pt`，内部 iter=65000，SHA 前缀 `4fd1b50b2c41` | actor738、critic126、联合优化器；没有完整 run 配方，不能证明它就是当前默认配置训练所得 |
| 当前 wall5 | `walled5/2026-10-23_17-35-18_wall5_v28_clean_camera_fresh_20261023_173513` 的 params 与 `model_5600.pt`，SHA 前缀 `b29e2e86d0db` | 正式 run 的 rev28 配方和已落盘权重；不凭旧 PID 推断仍在运行 |
| 独立 wall10 | 当前 `carrybox_wall10*` 源码及其独立检查记录 | 已实现另一个 PhysHSI 迁移分支，不是 wall5 的新别名；短测不代表正式收敛 |

`resources/config/carrybox.yaml` 是 **动作数据清单**，不是训练/部署全配置；`resources/ckpt/carrybox.pt` 是训练 checkpoint 字典，不是可直接当深度 actor 使用的 JIT 模型。`resources/` 之外的环境、motionlib、runner、PPO 与 AMP 必须一起核对。

## 1. 任务、场景与成功语义

| 细节 | PhysHSI G1 carrybox | 当前 wall5 rev28 |
|---|---|---|
| 完整目标 | 走到箱子、抬起、搬到 goal、放下、松手站稳 | 看深度找箱、接近、双手接触并抬起；没有搬运 goal/放下任务 |
| 任务状态输入 | actor 能获得带噪声箱子位姿、尺寸、goal；成功时 task 向量变为 −1 | actor 无箱子/目标真值、无显式阶段；训练 critic/AMP/辅助标签例外 |
| 障碍物 | 地面、箱子、起点平台、目标平台；没有墙和圆柱 | 一面墙 + 三圆柱 + 箱子 + 参考初始化用平台；参与碰撞与深度遮挡 |
| 普通箱子 XY | 相对 root，x/y **各自**在 ±[0.7,4] m 抽样；不是半径 0.7–4 m | 前方 bearing±45°，半径 0.7–2 m |
| 普通箱子 Z | `max(U[0,.65],box_half_z)+.01`；可以在平台上 | 考虑倾斜最低点贴地；pickup/hold RSI 可在空中，不保证所有 reset 贴地 |
| 普通箱子姿态 | 竖直，yaw 全圆 | 倾斜最大30°；yaw 课程 0→10→30→180°，锚点为有效训练0/10000/20000/30000轮 |
| 视野外初始化 | 没有专门 search 标记；actor 即使粗糙也有箱子方向信息 | loco 类中2%箱子放到左右±[60°,180°)，半径0.9–2 m；search_turn 专项奖励 |
| 平台 | 两个0.4×0.4×0.02 m固定平台 | 一个0.5×0.5×0.8 m六自由度锁定支撑体；不用时移到地下 |
| 墙 | 无 | 0.2×8×3 m，距机器人3–4 m、全圆bearing，长面朝向机器人 |
| 圆柱 | 无 | 三个r=.15、h=1.8 m，中心距机器人2.2–3.2 m，全圆bearing，静止 |
| 环境间距 | 10 m | 13 m |
| goal 初始化 | default/loco/pickup：相对箱→机器人方向偏±10–80°，距箱0.6–4 m；goal高度max(U[0,.4],half_z+.02)；carryWith另按x/y±[.5,4]采样 | 无 goal/目标平台 |
| 成功条件 | 箱到goal三维距离<.05 m且箱子重力投影XY范数<.1；训练时成功不终止 | 箱底离地≥.12 m、双手与箱接触、箱竖直度>.9、箱速<.25 m/s，持续25步=.5 s；成功不终止 |
| 成功统计局限 | 放置成功，和当前“抱起”不是同一指标 | pickup/hold RSI可直接处于持箱状态；成功必须按起点分组，不能等同于从地面拾起 |

源码：[源箱子/goal reset](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:843)、[当前场景](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py)、[当前成功指标](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py)。

## 2. 机器人资产、碰撞与物理

两边源头均为 PhysHSI 的 `g1_29dof.urdf`。当前 USD 保留固定关节，不能只读 URDF 文件名就断言仿真完全一致；spawn 覆写、材质、求解器和执行器仍不同。

| 细节 | PhysHSI | wall5 |
|---|---|---|
| 仿真框架 | Isaac Gym / PhysX | Isaac Lab / Isaac Sim / PhysX |
| 自由度 | 29；按关节名映射 | 同29；数据顺序与资产顺序显式映射 |
| 基础总质量 | URDF逐link和33.34114202 kg | USD作者质量和33.34114242 kg；最大单link差2.10e−7 kg |
| 自碰撞 | `self_collisions=0` 表示启用 | spawn显式启用；不是旧版关闭状态 |
| 碰撞几何 | 原URDF collision，肩圆柱替换胶囊；膝小盒子、足部mesh | rev24起回到这些碰撞几何，mesh用凸包，四肩圆柱替换胶囊 |
| “全身外壳” | 没有后来添加的外层全身hull | `spawn_wall5_full_body_robot`仍有定义但**未注册执行**，不能当当前有效资产 |
| pelvis /手掌测量点 | pelvis根无新增大凸包；实际手碰撞在rubber_hand，palm是位置端点 | 同类结构；visual外观、collision形状、深度遮挡网格是不同概念 |
| 相邻link过滤 | PhysX articulation默认会过滤直接由关节连接的父子碰撞；不是所有非相邻对都过滤 | 同样不能把“自碰撞开启”理解为所有link两两接触；不应推断自动排除全部固定链邻近体 |
| 物理/控制周期 | .005 s ×4= .02 s，200/50 Hz | 相同 |
| 求解器 | TGS，场景8 position/0 velocity | 机器人articulation 8/4；场景范围1–255/0–255，不能直接称全场景8/4 |
| damping | 机器人线/角阻尼.01 | 0 |
| 接触参数 | contact_offset=.01 m、rest_offset=0、bounce=.5 m/s、max_depenetration=1 m/s | bounce/max_depenetration对应；contact/rest未在任务显式覆写，需查运行形状默认值 |
| armature | .01 | .01 |
| 默认地面材质 | static/dynamic=.9 | static/dynamic=1，multiply；机器人无单独摩擦随机化 |
| 碰撞/接触惩罚 | 配置列了penalize_contacts_on，但有效reward scales没有collision项 | 当前undesired_contacts=None；早期“髋膝接触扣分”已移除 |
| 接触读数 | 全部rubber_hand净接触力，非仅箱子 | 左右手传感器按Box过滤，用于抓取门控 |

USD作者root原本写32/1、自碰撞False，但任务spawn会覆写，**不能据USD裸值误判正式任务**。本轮确认质量和形状来源，不宣称惯量烘焙、摩擦合成、接触力以及跨引擎运动已动态等价。逐link质量/碰撞见附录。

## 3. 控制、动作与延迟

| 细节 | PhysHSI | wall5 |
|---|---|---|
| 策略输出 | 29维关节位置偏移，`q_target=q_default+.25*a` | 同表达式 |
| PD执行 | 每5 ms显式计算力矩后clip，传入torque控制 | `ImplicitActuator`位置驱动由PhysX内部求解 |
| 显式公式 | `τ_pre=(Kp*kpf*(q_target−q)−Kd*kdf*qdot)*motor_strength+offset` | 当前无kpf/kdf/motor/offset随机项；隐式驱动不是这个显式离散公式 |
| 动作clip | ±100；无额外目标角硬clip | ±9，再把位置目标clip到URDF物理角限位 |
| 初始std | 1，直接训练std参数 | 1，训练log_std，范围exp(−5)～1 |
| 均值边界正则 | 无 | 系数.01，对超出可行动作边界的均值加罚 |
| 力矩/速度限制 | URDF各关节effort/velocity；显式计算后力矩截断 | 隐式执行器配置None，由导入资产限制提供；不是统一无限力矩 |
| 动作延迟 | 每物理步推进5槽，索引0–4→20/15/10/5/0 ms | 同样在每物理步推进5槽，不是每policy步延迟 |
| reset延迟缓存 | 用最终reset关节角减default填满 | 用最终reset绝对目标填满；表达形式不同但对应关系等价 |

两边名义PD相同：髋150/2、膝300/4、踝40/1、腰300/4、肩200/3、肘100/1、腕20/.5。**此前X2的膝150/5不适用于本地PhysHSI G1对照。** 原URDF不同关节effort为5–139 Nm，速度20–37 rad/s，逐关节数值见附录。

当前隐式执行器的`applied_torque`是IsaacLab用于奖励的估计量，不是从求解器测回的真实驱动力矩。即使两边奖励都叫torques，输入量的来源也存在差异。

源码：[源显式PD](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:737)、[当前延迟/clip](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py:11)、[IsaacLab隐式力矩说明](/home/cao/IsaacLab/source/isaaclab/isaaclab/actuators/actuator_pd.py:35)。

## 4. Reset / RSI / 历史缓冲

| 细节 | PhysHSI | wall5 |
|---|---|---|
| 是否RSI | 每次reset Bernoulli(.8) | 按env编号固定分配 |
| RSI内技能 | 权重[.8,.2,.2,0]会归一化为[2/3,1/6,1/6,0] | 同期望比例，固定每类env数量 |
| 总体比例 | default20%、loco53.333%、pickup13.333%、hold13.333% | 4096时819/2185/546/546；**不是旧75/5/20或80/0/20** |
| 片段时间 | 连续参考时间、完整拾箱片段，可在抬起途中开始 | 同为完整三pickup连续起点，旧0–31帧字段目前未使用 |
| 默认root | env原点+(2.3,0,.8)，yawπ；六维速度各轴U[−.5,.5] | 平移重定位到env原点、yaw0；六维速度同±.5 |
| RSI root | 参考姿态/位置；高度base_height+.05；root六维速度覆盖成±.2 | 去掉参考XY/yaw并配对变换箱子；高度同+.05；root六维速度同±.2 |
| RSI qdot | 使用数据joint_velocity | 相同，不是重新差分的qdot |
| 关节扰动 | q加U±.1 rad，clip90%软限位 | 同 |
| 足底安全高度 | 无最终关节扰动后的FK修正 | 最终FK检查原碰撞足底，只向上移至5 mm；配对箱子/活动平台一起移 |
| pickup平台 | motionlib用接触帧参考位置安排支撑，按接触索引开关 | 按当前参考箱位置、箱半高安排平台；仅接触前激活 |
| pickup/hold箱yaw | 参考根yaw，另随机加0或π | 去yaw后与机器人yaw对齐，没有这项随机π翻转 |
| hold片段 | 3段真实carryWith | 一个改造的静止hold片段 |
| actor/AMP历史 | `reset_idx`没有明确清掉对应obs/AMP滚动历史，可能混入旧回合 | partial reset清对应行，首帧重复填充；terminal AMP先取再reset |
| 动作历史 | reset把last_actions清零，但同次post_step末尾又写入终止动作 | manager reset清对应行；不要复制源历史泄漏 |
| 加速度历史 | reset清last_qdot后，post_step末尾会写入reset后的qdot | wall5使用Lab物理步joint_acc，与源20 ms差分不同 |

固定来源env可以保证空手/持箱的**控制步配额**，每reset抽样只保证**回合抽样概率**。某一类频繁失败时，这两种机制的训练状态占比并不等价。这是当前有意改动，不能称“完全恢复原版RSI”。

初始化顺序也有差别：当前继承的通用root/joint reset先执行，随后`reset_box→initialize_reference`再次写最终机器人状态；最终状态以后一写入为准，前一随机yaw不是本回合最终yaw。重构应去掉这类重复初始化并锁定最终写入点。

源码：[源reset](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:770)、[源post_step/reset顺序](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:250)、[当前初始化](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py:39)。

另一个源时序细节：`post_physics_step`先用缓存`feet_pos`组成end_effector_pos，之后才更新`feet_pos`。因此末端向量的足部位置可能落后一控制步，而AMP高度使用后续已更新的足位置。当前直接读刷新后的body link状态；不建议复制源的这种顺序问题。

## 5. 终止与时间边界

| 条件 | PhysHSI基础任务 | wall5当前 |
|---|---|---|
| 侧倾 | abs(roll)>.5 rad（28.65°） | 相同 |
| 前后倾 | abs(pitch)>1.1 rad（63.03°） | 相同 |
| root过低 | pelvis<.2 m | 相同测量名称/阈值，使用root link原点 |
| 头过低 | mid360_link<.6 m | 相同；不是旧head_link COM<.4387 |
| 髋过低 | 任意hip_yaw_link<.15 m | 相同 |
| 箱子飞走 | 箱子XY速度>3 m/s | 相同 |
| 时间 | `episode_length>1000`，可到1001控制步 | `>=1000`，1000步 |
| 成功终止 | 无 | 无 |
| 箱倾覆 | 基础False；resume启用投影重力z>−.05 | 无 |
| 接触终止 | terminate_after_contacts_on为空 | 没有新增身体接触终止 |
| 非有限数 | 源有检查/调试分支，不是统一恢复策略 | 当前检测到NaN/Inf会抛异常，停止训练进程；不能当普通reset |
| 跌倒惩罚 | 未注册 | early_failure=None，旧−50已去掉 |

源计算的`projected_gravity`某阈值不代表一定接入reset，必须看最终reset_buf。当前`reward_geometry`仍保留`fallen_pelvis=.2311/fallen_head=.4387`等旧字段，但**实际终止已经走PhysHSI函数**，这些字段不能当有效终止阈值。

还有一个当前测量点不一致：standup奖励通过`head_height()`读`head_link` COM，终止读`mid360_link`原点。中立姿态两者z约差10.3 mm，转动时不是固定世界高度偏移。应在重构中显式统一，不能只修改一个“头高系数”。

## 6. 观测：维度、坐标系、历史、噪声

| 细节 | PhysHSI | wall5 |
|---|---|---|
| actor单帧本体 | 108=角速3+重力3+q误差29+qdot29+末端15+动作29 | 93=前述内容去掉末端15 |
| actor任务输入 | 15=箱xyz3+箱rot6+尺寸3+goal xyz3 | 无真值任务输入，改为深度 |
| actor历史 | (108+15)×6=738 | 本体93×4=372；深度4×27×48经CNN为128；MLP输入500 |
| critic | 当前帧108+线速3+任务15=126 | 当前帧93+线速3+箱xyz3+rot6+尺寸3+末端15=123 |
| 机体系 | 主要速度/重力/末端/箱/goal在torso坐标，位移原点仍pelvis | pelvis坐标；参考link速度转换避免把COM速度直接当link原点速度 |
| 角速/qdot尺度 | .25 / .05 | 相同 |
| critic线速尺度 | ×2 | ×1 |
| 旋转6D | x、z两列 | critic/辅助标签x、y两列；AMP用x、z；各自可重建但不能直接混用权重 |
| 本体均匀噪声，已乘scale | 角速±.075、重力±.05、q±.02、qdot±.1、末端±.05；action无 | 当前enable_corruption=False，本体无附加噪声 |
| 观测clip | ±100 | wall5本体观测组未配置同样clip |
| critic网络 | 独立512/256/256 ELU | 同隐藏层、独立MLP，无深度CNN |
| actor网络 | 738→512→256→256→29 ELU | 深度CNN+372→500→512→256→256→29 ELU |

PhysHSI的“视觉”是给状态加退化，**不是实际深度感知**：

- 以`d455_link`为相机参考，标签四个上角点都在视野且朝向/距离满足条件才`can_see_tag`；HFOV每reset85–90°、VFOV55–60°，最大距离2.5 m。没有场景网格射线检测，不模拟身体/墙遮挡。
- 每环境抽`thresh_tag=.7–2 m`；远处/从未见到的箱子用coarse状态。位置offset XY±.2 m、Z±.4 m（代码额外乘2），再每步xyz噪声±.05 m；coarse姿态先设默认方向再加±5°扰动。
- 曾经见过且近于.65 m但现在看不到时，用零箱位置/默认姿态；成功后actor task15置−1。goal仍作为带噪声输入。

因此“同一动作数据在PhysHSI能学会”不能直接推出“无真值深度actor用同样轮数必然学会”。去掉箱子真值改变了可观测性，也增加了CNN需要学出的目标。

源码：[源观测](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:431)、[源可见性几何](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:1030)、[当前critic](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py)。

wall5完整Observation字典还包含训练支路：`proprio`372、`perception`4×27×48、`critic_state`123、`amp`600、`box_pose_target`10（xyz3+rot6+可见标记1）、`action_bounds`58（29个下界+29个上界）。actor只读取前两组；有一个字段存在于字典中不等于进入actor。

## 7. 当前深度与辅助监督

当前确实是Warp ray-cast，不是RGB渲染后提深度。48×27、50 Hz、4帧、光轴方向深度`distance_to_image_plane`，单位米，范围.1–3，缺失填3。

挂在`torso_link`，offset位置(0.0576235,0.01753,0.42987) m，world约定四元数wxyz=(.91495,0,.40355,0)，名义向下约47.6°。VFOV58°，由48/27宽高比得HFOV约89.16°。这是当前carrybox实际配置；不能把football v5的另一组FOV参数套过来，也不能用PhysHSI的标签可见性FOV证明它已与实机标定完全一致。

ray target包括地面、机器人visual mesh、Box、Wall、Cylinder0/1/2、Platform。最近交点决定深度，因此有自遮挡与障碍遮挡；视觉mesh与碰撞mesh不同是有意设计。rev28关闭高斯/距离相关/孔洞/边缘丢失/延迟/冻结/安装误差，**关闭噪声没有关闭几何遮挡**。

CNN：Conv16/32/64，3×3 stride2 padding1，ELU，maxpool2，展平384→256→128。四帧作为通道，不是四次独立编码后再拼接。

辅助头128→128→9，回归相机系xyz米+rot6。位置MSE加箱体D4对称旋转的最小MSE，coef=1，**当前全部配对帧监督**；可见性标记仅诊断。标签用于损失，不拼入actor；critic也不使用该CNN。

这一点与用户更早的“coef=.1且只可见”版本不同。当前网络仍可能在箱子被遮挡/超3 m时被要求预测完整真值；这是可观测性与损失尺度风险，需要分可见/不可见记录损失，不能仅根据历史某轮辅助损失峰值断言本轮失败原因。

PhysHSI完全没有这条深度CNN与pose auxiliary loss链路。独立wall10当前aux=0，同样不能称与wall5网络训练目标一致。

源码：[深度camera](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py)、[最近交点内核](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_raycast.py)、[当前辅助损失](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py:40)。

## 8. 数据：原文件、选段和概率

| 内容 | PhysHSI实际manifest | wall5当前manifest |
|---|---|---|
| 总量 | 19段，5007帧，60 Hz | 15段，4155帧，60 Hz |
| loco | 11段，每段weight1 | 同11段，字节hash完全一致 |
| pickup | 3段192/178/129帧，每段weight4 | 同3段，完整499帧，字节hash完全一致 |
| carry/hold | carrywith1/2/3为256/194/323帧，weights5/2/5 | 仅hold_box_01=300帧；原carrywith1前21帧后重复frame20，后续速度清零 |
| putdown | 两段141/238帧，每段weight5 | 无 |
| AMP组概率 | loco24.44%、pickup26.67%、carry26.67%、putdown22.22% | loco40%、pickup40%、hold20%，组内均分 |
| RSI与AMP | putdown RSI为0，但仍参与判别器专家 | 不含putdown；不要拿RSI比例当AMP概率 |

独立FK每片段最多取32个均匀帧、五端点逐个检查：三pickup最大误差<1.44e−7 m；loco/hold上肢/头的最大差约3.81 mm，足端约数值精度。这支持端点语义大体对应，没有X2第五端点差.31 m那种错误；**不宣称所有数据逐帧零误差**。当前15段中14段和原文件完全相同，hold是有意改造。

源`base_height`与当前按双踝世界相对高度得到的专家高度，在本次抽样上数值一致到浮点误差；实现公式不同，不应把它列为已发现的大幅高度偏差。

## 9. AMP：同60维仍有大量实现差异

| 细节 | PhysHSI | wall5 |
|---|---|---|
| 每帧60维 | height1+joints29+ends15+**box3**+lin3+ang3+rot6 | height1+joints29+ends15+lin3+ang3+rot6+**box3** |
| 关节速度 | 不在60维中 | 同样不在；不能把“无qdot”单独认作当前漏项 |
| 箱位置截断 | XY>.7 m时缩到半径.7，z=0 | 相同门限 |
| 坐标系 | 专家主要用pelvis姿态；在线end/box/速度用torso，存在waist运动时的帧差异 | 专家和在线尽量统一pelvis；不是照抄源全部frame选择 |
| rot6 | 去yaw后的根姿态x/z列 | 相同定义 |
| window | 10帧、按50 Hz取样，跨度.18 s | 相同 |
| 时间倍率 | 60/50×U[.95,1.05]，一个batch共享NumPy倍率 | 固定60/50，无倍率扰动 |
| 插值顺序 | 先算各原生帧60维，再线性插特征 | 先插原始状态/最短路归一化四元数，再算非线性旋转/截断特征 |
| 时间抽样边界 | 全片段phase采样后clip尾部窗口，索引用phase×length | 只在完整窗口有效起点区间采样，避免跨片段/尾部clip堆积 |
| 专家角速 | 解包Euler差分后转body | shortest quaternion difference转body |
| 判别器 | 600→512→256→1 ReLU | 相同宽度 |
| 初始化 | 第一层默认；后续linear权重U[−1,1] | trunk Kaiming，head U[−.01,.01] |
| 归一化 | 无 | running mean/var，ε1e−4，±10截断；启动专家样本初始化，逐轮更新 |
| 判别损失 | LSGAN expert→+1、policy→−1；专家梯度惩罚.5 | 同大类目标，但作用于归一化输入，梯度尺度不同 |
| 判别器优化 | 与PPO同一个Adam，trunk/head WD=.001/.1，共享自适应lr | 独立Adam，固定5e−5，AC先更新再AMP；D梯度clip10 |
| AMP历史reset | 未明确清空，可能跨回合 | 清除本环境历史并重复reset帧，不跨回合；terminal帧先保存 |
| 每步追加/计数 | 本地PhysHSI源码每步正常追加、episode length正常+1 | 同正常一次；**此前X2双计数/双追加问题不能套到这里** |

双方基础混合相同：`r_final=.75*r_task+.125*style`，`style=max(0,1−.25*(D−1)^2)`；任务奖励已经乘policy dt=.02，style不再乘dt。源resume改成`.7*task+.15*style`，wall5当前没有这个阶段。

“AMP占80%”应从实际task/style回报统计计算，不能把amp_coef=.25误读成最终回报恒定占25%或75%。当前AMP并非未接入；本轮检查的是实现差异，不替代最新动态判别器有效性/因果消融。

源码：[源motionlib](/home/cao/PhysHSI/legged_gym/legged_gym/envs/motionlib/motionlib_carrybox.py:94)、[源AMP](/home/cao/PhysHSI/rsl_rl/rsl_rl/modules/amp.py)、[当前特征](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_wall5.py:100)、[当前AMP优化](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py:61)。

## 10. 全部有效正则奖励

以下weight均是乘dt前的配置值，非每步最终贡献。两边都没有把总任务奖励强制截成非负。

| 奖励 | PhysHSI有效定义 | wall5有效定义 |
|---|---|---|
| dof_acc −1e−7 | `sum(((qdot_prev−qdot)/.02)^2)` | Lab `joint_acc_l2`，来自物理步更新；不同差分时间窗 |
| action_rate −.03 | `sum((a_prev−a)^2)` | 相同主形式，reset边界处理不同 |
| torques −1e−4 | `sum((tau_applied/Kp_nominal)^2)` | `sum(tau_applied^2)`；隐式力矩估计量 |
| dof_vel −2e−4 | `sum(qdot^2)` | 相同 |
| dof_pos_limits −5 | 超90%软限位线性excess和 | 大体同，但膝伸直端改用硬下限例外 |
| dof_vel_limits −.001 | 超80%URDF速度的excess和，不封顶 | 超100%速度，每关节excess上限1 |
| torque_limits −.03 | **未clip的computed tau**超95%effort的excess和 | 未注册此项 |
| alive | 无 | weight3，有效步raw+.06；AMP混合后+.045 |
| early_failure / collision | 无有效项 | 都已None；旧−50及髋膝接触罚不生效 |

力矩项同τ下，wall5/PhysHSI每关节倍率为Kp²，即400～90000，不是统一一个倍率。这个差异值得恢复源语义，但不能解释所有历史版本之间的退化，因为旧可接近版本同样用了原始τ²。

## 11. 任务奖励：公式和门控逐项对照

两边都是并行计算多个有门控的奖励，并非“完成阶段A才允许阶段B”的严格状态机。下列距离明确区分XY/XYZ，`h`为箱心世界高度，`d_h`为双掌中心到箱心距离。

### PhysHSI有效任务项

1. **walk_task，weight1**：`exp(−5*(.85−朝箱XY速度)^2)+.5*exp(−.75*abs(bearing))`。机器人到箱 **XY<.7 m** 时饱和1.5，箱到goal XYZ<.05 m也饱和。位置接近指数项权重0。速度取torso世界XY。
2. **carryup_task，weight1**：`.7*exp(−3*d_h²)+2*exp(−3*max(.72−h,0))`。root→box XY>.7时归零；箱到goal XY<.6时高度项给满；箱到goal XYZ<.05时给满2.7。没有强制双手实际接触，也没有单独左右掌表面误差。
3. **relocation_task，weight1**：`.5*朝goal方向 +1*朝goal速度 + exp(−10*箱到goal XYZ距离)+1*放箱高度项`。箱底高于起始platform>.05 m或箱XY离起点>.5 m才开启；离goal XY<.6才奖励放箱高度；机器人goal距离<.65时速度项给满；放置成功给满3.5。角速度跟踪和机器人到goal距离项权重均0。
4. **standup_task，weight.2**：只有放置成功才开启。`.5*头高奖励 + exp(−.3*sum(abs(q−qdefault))) + .5*平均双手无接触`。mid360目标1.15 m，头高exp系数2、超过目标饱和。root高度项权重0。

因此原版standup强调**放下后松手站稳**，不能将这个函数原封不动用于“抬起后一直抱着”。源`hand_contact=0`不是有效抓握奖励；`hand_free`看rubber_hand全部接触。

### wall5有效任务项

| 项 / weight | 当前实际计算与门控 |
|---|---|
| walk_task / 1 | travel=`clamp((XY−.60)/.20)`；travel×[目标速度.85指数+.5×朝向指数×clamp(朝箱速度/.85)]；加`.2*exp(-((XY-.52)/.12)^2)*heading`站位奖；减`.5*clamp((.40−XY)/.15)^2`拥挤罚；后两项乘(1−lift) |
| carryup_task / 1 | `1.5*reach*XYZ_gate + .5*平均接触 +1.5*双侧接触 +2.5*双侧接触*lift` |
| reach几何 | 两掌分别到有朝向箱体表面的外侧距离，4 cm容差后`exp(−mean_error/.18)`，再乘对侧掌位置因子；不是只看掌中心 |
| reach门控 | XYZ≤.90 m全开，.90–.98线性淡出，≥.98为0；contact/lift项不再受此距离门控 |
| 接触/lift | 手箱力>1 N有效，5 N饱和；bilateral=min(左右接触)×opposite；lift由箱底离地.01到.25 m线性增长；双手未接触不奖励lift |
| stable_grasp / .2 | 双侧接触乘臂速度/加速度平滑项 |
| slow_pickup / −.0005 | 全关节qdot²；近箱/低箱且真实双手接触时才开启 |
| arm_speed_pickup / −.02 | 双臂abs(qdot)超过1 rad/s的平方excess均值；下蹲且双手接触 |
| arm_acc_pickup / −2e−5 | 双臂abs(qddot)超过20 rad/s²的平方excess均值；同门控 |
| grip_force_cap / −.02 | 近手条件下平均`max(手箱力−7 N,0)` |
| held_hand_speed / −.02 | 与上速度excess同阈值；箱心>.635697 m且双手中心距箱<.15 m；不要求接触 |
| held_hand_acc / −2e−5 | 同held门控、加速度阈值20 |
| waist_yaw_penalty / −.5 | waist_yaw相对默认角L1 |
| search_turn / +.5 | search标记、bearing误差>45°、XYZ>.90时，`.7 exp(−.75error)+.3 tanh(max(期望方向*yaw_rate,0))` |
| standup_task / .4 | 箱心>.695779、pelvis重力XY范数<.2、head COM>.877429、手中心距箱<.3时开启；根高目标.762752、头高目标.932268，指数系数6.9223/7.2940，加机体/箱子低速度项；无显式双手接触门控 |

standup其余尺度：root低门槛.577843、门控跨度.184910；crouch root<.693411且box<.671746；slow pickup低箱界.635697。旧`carryup_box=.743844`等字段仍保留，但rev23后的carryup已用表面/接触/lift新公式，不应把旧高度指数当当前carryup有效项。

这些门控使用了XYZ距离、XY站位、掌中心、单掌表面、接触力、箱心高、箱底高等不同量。它们并未形成统一“接近→伸手→抓稳→抬起”的阶段定义。重构需要统一几何含义，并检查奖励交接处是否出现低谷；不能仅把所有`.7`替换为一个新数。

源码：[源四个任务奖励](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:1966)、[当前grasp公式](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_wall5.py:13)、[当前继承standup/force cap](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py:12)。

## 12. 随机化：声明和实际生效分开

| 项 | PhysHSI实际生效 | wall5 rev28 |
|---|---|---|
| 箱尺寸 | 创建时base(.3,.3,.25)×离散scale；CPU按原torch.arange实测XY=.7～1.4，Z=.6～1.4，共576格 | 固定(.3,.3,.25) |
| 尺寸分配 | 先覆盖全部格，再补足/打乱；不是每reset改尺寸 | 无尺寸随机化 |
| 箱质量 | density U[10,100] kg/m³×体积，创建时固定 | 基础.8 kg，每reset乘[.1,1.5]→.08–1.2 kg并重算惯量 |
| 箱/平台材质 | `random_props=False`，声明的摩擦/弹性范围未启用 | 箱startup static[.3,2]、dynamic[.4,1.5]、restitution[0,.2] |
| 机器人摩擦 | startup[.1,1.5] | 无对应随机化，继承default材质 |
| 机器人弹性 | startup[0,1] | 无对应随机化 |
| link质量 | startup×[.8,1.2] | 无 |
| torso COM | startup三个轴±.1 m | x±.025，y/z±.05 m |
| 额外payload | 配置[-2,5]，但实际被后续link_mass循环覆盖 | 无；重构不能把源无效项当生效项新增 |
| Kp/Kd | 每reset逐关节×[.9,1.1] | 无 |
| motor strength | 每reset×[.9,1.1] | 无 |
| torque offset | 每reset±5%effort limit | 无 |
| 姿态扰动 | reset q±.1及根速度±.5/.2 | 对应保留，另有最终足底修正 |
| 外部扰动 | `push_robots=False`，但disturbance=True：**每8控制步=.16 s**，torso局部XYZ各±50 N，单物理步施力 | 每1–3 s向root COM世界速度加增量，XYZ最大(.5,.5,.2)m/s，角速(.52,.52,.78)rad/s；5000轮前0，10000轮爬升，到15000轮满 |
| 课程 | 没有当前箱yaw/推扰迭代课程，action_curriculum=False | yaw和推扰按有效训练迭代变化；warm-start锚点需保留契约 |

源配置写XY scale上限1.3，但`.arange(low, high+step, step)`浮点边界在本机返回1.4。报告同时保存声明与实测，不默默把1.3当实际最大值。这个差异也影响wall10当前7×7×9=441格与源576格是否严格一致。

外力N与速度突变m/s不是同一物理量，频率和施加点也不同；不能只比较配置叫不叫push。源若只看`push_robots=False`会误判成“训练没有扰动”。

## 13. PPO、优化顺序、时序损失与采样预算

| 项 | PhysHSI | wall5 |
|---|---|---|
| 环境数 | 4096 | 4096 |
| rollout | 100步/环境=2 s | 24步/环境=.48 s |
| 每轮采样 | 409600 transitions | 98304 transitions |
| 实际PPO训练样本 | 前99步=405504；第100步用于下一帧配对/GAE | 全24步=98304 |
| epochs×minibatches | 5×4 | 同 |
| 初始lr | 1e−3 | 3e−4 |
| lr调度 | adaptive KL=.01，1.5倍率，范围1e−5～1e−2 | 相同调度原则；只调AC，不调独立AMP固定lr |
| gamma / lambda | .99 / .95 | 同 |
| PPO clip/value clip | .2 / 开启 | 同 |
| entropy / value coef | .01 / 1 | 同 |
| AC grad norm | 1 | 同 |
| policy/value smooth | **1/9、1/90** | 无 |
| smooth输入 | `s+α*(s_next−s)`，α=(1−done)×U[−1,1]，含反向外推，不只插值 | 无 |
| AMP优化器 | 同一个Adam中的三组，参与同一次backward/step | AC20次更新后，AMP另20次更新 |
| 其他损失 | 无pose/head bound loss | pose auxiliary1 + action mean bound .01 |
| advantage | 全rollout归一化 | 同为全局，不按minibatch重新归一 |
| minibatch排列 | 一个perm复用各epoch | 按当前RSL实现；与源固定排列/RNG轨迹不保证一致 |
| timeout bootstrap | 源使用transition当前V值补reward | 使用reset前terminal critic观测估值，避免错用reset状态 |
| 训练总轮数 | base20k；resume配置50k，README建议两阶段 | 当前40k fresh |
| save / seed | 每500轮 / seed1 | 每200轮 / seed42 |

同样“5000轮”，源采集步数约为wall5的4.167倍；不能直接比较轮数或每轮秒数来断言训练快慢/学习率问题。深度还增加CNN、raycast和辅助监督开销。源100步rollout迁入深度任务后需重测显存和吞吐，而不是预设仍须与旧24步同为6秒以内。

源资源模型65000轮保存的联合Adam三组lr均5.0625e−5；wall5 model5600的AC lr为1.1390625e−4。它们只是存档瞬时状态，不是初始学习率，也不能据此证明哪个模型更会走路。

源码：[源PPO](/home/cao/PhysHSI/rsl_rl/rsl_rl/algorithms/him_ppo.py:182)、[源时序采样](/home/cao/PhysHSI/rsl_rl/rsl_rl/storage/him_rollout_storage.py:145)、[当前PPO](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py:193)。

## 14. 保存、恢复、play和部署边界

PhysHSI checkpoint保存actor/critic、AMP、联合optimizer、iter/infos；资源模型没有完整env/data hash/传感器契约。当前schema2额外保存环境revision、输入/深度/AMP契约、数据元信息、RNG、独立AMP状态。**同为60维AMP或123维critic不意味着可以严格恢复**：字段顺序、坐标系、尺度、网络历史都必须匹配。

PhysHSI标准play脚本会设置test模式、默认箱reset、关闭delay/disturbance/push并把回合改10秒，测试成功阈值还放宽到箱goal距离.1/倾斜.2。当前很多wall5录像保留20秒、参考起点、原课程。这些录像不能直接作为相同条件成功率对照。

部署actor边界：当前372本体+4帧米制深度输入，不包含critic123、AMP600、pose标签、阶段或真值箱位置。PhysHSI actor738依赖箱/goal估计，不能只把它权重放到当前depth actor就称已迁移。相机外参、光轴z、深度单位/裁剪、关节顺序、位置offset和控制延迟要随导出契约交付。

## 15. 已有独立 wall10：哪些恢复了、哪些仍不等价

wall10已存在，ID为`Template-Perceptual-Ball-CarryBox-Walled10-v0`。本轮读取其源码和既有短测回执，**没有将它替换wall5或启动正式训练**。

| 范围 | wall10当前状态 |
|---|---|
| 控制 | 源显式PD、逐关节Kp/Kd/motor/offset随机化、URDF effort双路径限制、0–20ms物理步延迟、动作±100、无额外qtarget硬clip |
| 正则 | 恢复τ/Kp平方、速度80%、力矩95%未clip超限、20ms速度差分；无alive、无额外arm/waist/search/grip罚 |
| PPO/AMP | 100步、5×4、lr1e−3 adaptive、同一Adam三组、无AMP归一化、源初始化、1/9与1/90时序平滑 |
| 网络 | 93×6本体+4帧深度，MLP输入686；critic123顺序为93本体+15末端+线速3×2+箱12，rot6改x/z；aux0 |
| 数据 | 仍是当前15段，不是源19段；单静止hold。源片段weight落到保留集合，11:12:5，即39.29/42.86/17.86% |
| 场景/任务 | 单墙固定后方x=−3.5、无圆柱；前方地面箱；删goal/putdown，改为抬起原地保持2秒 |
| 成功 | 双手接触、箱底>.10、箱心≥.70、箱up>.8、robot up>.95、mid360>1.05、root XY速<.15、yaw速<.3、箱速<.15、箱XY漂移<.35，持续2秒；成功只计统计，不触发reset |
| 材质/物理 | 地面.9；机器人摩擦/弹性/质量/COM恢复源范围；机器人8/0、阻尼.01，但不能说全场景所有接触默认等价 |
| 变尺寸深度 | 箱体按实际每env尺寸单独求交，与其他遮挡取最近值，不拿一个共享箱网格代替全部尺寸 |
| 内存优化 | 当前源码确定性CNN执行块8192，逻辑随机块256，按完整minibatch比例累积梯度；不能把256理解为PPO minibatch大小 |

仍需显式处理的差异：

1. 源在线用torso、wall10仍用pelvis；应先定义一致的坐标契约，而不是机械保留源专家/在线frame不一致。
2. 源XY尺寸实际arange到1.4、全网格覆盖；wall10 integer采样到1.3，独立抽441格。
3. 源窗口索引phase×N、wall10×(N−1)，RNG也不同；窗口尾部概率要有明确选择。
4. wall10 reset首步强制previous_qdot=0；源虽reset清零，但post_step后会写回reset qdot。首步acc惩罚不完全一致。
5. wall10仍用log_std参数化而源用std，且时序平滑扩展到depth图像混合；这不是原状态MLP的完全等价实现。
6. partial reset不跨回合历史、terminal bootstrap修正、足底5mm修正是当前保留的防错措施，不应为了“像源”撤掉。
7. 当前数据和任务都删除搬运/放下；源后阶段amp=.3和box tilt termination也未复制。
8. 早期29项CPU、16环境2+1轮/恢复/导出之外，收尾时另一个性能任务已补齐34项CPU和4096规模短测，四个wall10源码hash与本轮快照一致。100步完整更新约18.49 s/轮，24步约4.41 s/轮；属于性能与更新检查，仍不是稳定行走/地面拾箱的收敛证明。

详细来源：[wall10实现记录](../wall10_20261023/README.md)、[新性能验收及边界](../wall10_perf_20261023/README.md)、[wall10任务配置](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall10_env_cfg.py)、[wall10 PPO](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py)。本轮只读取这些既有结果，没有重复运行GPU测试。

## 核验范围与仍未知的内容

本轮完成47个文件身份锁定、源配置继承展开、正式run配置核对、USD作者属性检查、19/15段数据/hash/FK检查，以及源/当前checkpoint CPU网络前向。两条冻结检查均通过。

尚未验证：两引擎实际接触/惯量响应的一致性、某项差异对抖动/倾倒的独立因果、资源model65000真实完整训练配置、4096深度100步rollout长期运行稳定性、wall10长期学习。4096规模的短测吞吐已有独立证据；历史录像只能说明所录起点行为，不能代替收敛结论。

建议重构以明确的任务模块和接口契约为边界，保留当前深度actor的用户目标，恢复经核验的控制/优化语义，并把删掉goal后的奖励重新闭合。具体改动顺序与验收见[reconstruction.md](reconstruction.md)。
