# Wall5 revision17：空手倾倒排查、训练反馈修复与重启

2026-10-19。工程验收与行为能力分开记录。下文描述本次修改后的训练实现；正式运行身份、短训结果与验收回执见本目录 JSON。

## 排查证据与结论范围

检查时旧 PID114186 已不存在，没有可停止的训练进程，GPU已释放；没有发送停止信号。旧日志与模型完整保留。锁定该run最后的 `model_6600.pt`（SHA256见 selection.json），以原revision15契约严格加载，在相同初态下独立进程各测32个空手首回合：

|控制|首回合平均步数|平均秒数|倾倒|
|---|---:|---:|---:|
|6600均值动作|13.78125|0.275625|32/32|
|6600采样动作|13.53125|0.270625|32/32|
|保持初始参考关节角|40.3125|0.80625|31/32（另一个高度失败）|

前两组全部在首次push之前结束。64个策略回合中55个只触发pitch、6个同时触发pitch/roll、3个只触发roll；因此61/64涉及前倾超过1.1rad，单纯放宽roll不会解决这个问题。因此本次快速reset的直接触发是姿态阈值，推扰不是它的直接原因；参考保持也会倒，不能称为稳定行走控制器。初态检查、逐步关节目标和奖励见 mean/sample/reference.json。只统计首回合，未把reset后的移动计入。baseline_replay脚本在改代码前执行，重放时须配套before中的revision15源码；当前revision17会正确拒绝旧契约，不能直接混用。

实测/代码确认了训练反馈问题，而非已经找到唯一的单行物理bug：

- 原walk用torso COM的朝箱速度，倾倒也可能得分；原standup仅箱已抬高时生效，空手没有连续直立反馈。6600采样时，walk约+0.02168/步，action_rate约−0.04110/步，torque约−0.01191/步；含原失败罚的task合计−0.05395/步。这里已将RewardManager内部的每秒量乘0.02，尚未乘0.75或加入AMP。
- checkpoint双膝raw std约2.044/2.565，部分关节达到exp(1)=2.718。首步均值动作两膝约−3.582/−2.958，执行目标被推到接近物理伸直下限；执行层clamp不能给策略均值提供直接的回到可行域梯度。
- 原来是每次reset独立抽80%loco/20%hold。短loco与长hold使旧run近期约90%的已完成步数来自hold；因此总体mean episode length不能代表空手行走。
- GAE的done截断及timeout前critic状态没有发现错误。不能解释为“死掉抽到hold，直接得到hold未来收益”；问题在实际采样失衡及负反馈。
- 足球有持续站立反馈，主线又有历史权重初始化；它不构成与wall5从零训练的严格单因素对照。

## 本次改动

1. 增加持续平衡奖励；不要求原地、不奖励零水平速度。远箱时鼓励站高，箱旁解除高度要求以允许下蹲。
2. walk使用pelvis link的朝箱水平速度，并乘相同姿态/高度因子，减少倾倒与躯干摆动冒充行走。
3. 失败罚权重−10→−50：50Hz下单次raw task罚−1，AMP混合后−0.75。只罚当前fell/tipped，timeout不罚。
4. raw动作标准差上限从exp(1)降到1，初始仍1；每个PPO minibatch后约束。增加系数0.01的原始动作均值越界损失。执行目标仍做原来的硬限位保护。
5. 固定环境技能配额：4096中3277个loco、819个hold、0个pickup；部分reset保留所属技能，仍随机抽参考片段/帧。这是约80/20的**环境和采样步数比例**，不再是每次reset的概率。
6. 增加分技能实际采样比例、task各项、非reset环境速度/箱距日志；revision升为17。16是先前撤回的PD候选，本次没有恢复其PD、站姿或静止起点课程；动作正则和配额helper经独立验收后复用。

保持原PD、物理资产、全身碰撞、动作尺度、深度、AMP数据/奖励混合、辅助监督及roll0.5。共享reset与PPO只增加默认保持旧行为的可选入口；足球不走CarryBoxPPO。

## 观测、网络与输出

|数据|形状/内容|用途|
|---|---|---|
|本体|每帧93维：机体系角速度3×0.25、投影重力3、29关节相对默认角、29关节速度×0.05、上次29维动作；4帧=372|actor|
|深度|4×27×48，光轴深度0.1–3m，除3归一化|共享CNN输出128维latent供actor和辅助头|
|actor|372+128→512/256/256 MLP→29维Gaussian均值，另学29维log_std|推理输出29个位置目标残差|
|critic|当前本体93+pelvis link机体系线速度3+箱子相对xyz3/旋转6/尺寸3=108；独立512/256/256 MLP|仅训练value，不使用CNN|
|位姿标签|相机光学系xyz3+旋转6+可见mask1|只用于辅助监督，系数0.1；仅真实最近Box命中且目标光轴深度在0.1–3m|
|AMP|10帧×60=600|仅判别器和奖励|
|动作界标签|真实限位、逐环境默认偏置、scale与wrapper界换算的下/上界，29×2=58|仅训练正则，不进actor/critic/导出|

辅助头从深度latent回归9维箱位姿，位置MSE及考虑正方箱对称性的旋转损失；不可见样本不回传该损失。深度延迟/冻结时标签和mask一起延迟/冻结。任务技能、search标记、阶段不加入策略/价值输入。critic的特权状态属于wall5训练端例外。

控制：物理200Hz（dt=0.005），policy50Hz（decimation4）。raw动作经wrapper±9裁剪，`q_target=q_default+0.25*action`，再裁剪到每关节物理限位，交给隐式PD；不是力矩策略。训练正则对未裁剪Gaussian均值计算，PPO的采样分布/log-prob保持一致。

PD沿用原G1配置：hip150/2、knee300/4、ankle40/1、waist300/4，肩200/3、肘100/1、腕20/0.5（kp/kd）；armature0.01。真实PhysX读回和35个碰撞shape在smoke中核对。物理自碰撞关闭，视觉自遮挡开启。

## 深度管线与场景

Warp ray-cast，最近交点包含地面、箱子、墙、3圆柱和机器人可见连杆网格，障碍物及身体会遮挡。不是RGB渲染后估深，也不是直接喂箱子真值。

相机挂G1 torso_link，名义相对位置(0.0576235,0.01753,0.42987)m，向下约47.6°；48×27、垂直FOV58°、水平约89.2°、50Hz、0.1–3m。此安装沿用本地G1适配；**当前58°垂直FOV仍不等于先前官方图示55.2°，实机标定一致性不能在本次排查中宣称已完成**。本次没有改变相机。

深度噪声：高斯std0.06m；边缘阈值0.15m、边缘丢失5%、孔洞2%；距离相关噪声0.024–0.09m；10%概率延迟1帧，0.2%概率触发最长15帧（含起始帧）的冻结。每回合相机位置偏差半径0.01m，旋转扰动当前0°。

墙0.2×8×3m，距机器人3–4m、全圆bearing；3圆柱半径0.15m/高1.8m，距机器人2.2–3.2m、全圆bearing。均可碰撞，reset后不主动移动。使用6轴锁定刚体以适配本机Sim4.5；无额外避障奖励。

箱子0.30×0.30×0.25m，基准质量0.8kg，每回合乘0.1–1.5（0.08–1.2kg）。无支撑台。

## AMP与初始化

数据为 `source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/`，13段：11行走、1地面起始的完整拾箱03、1持箱。旧原始数据保留。AMP抽样组权重40/40/20与RSI环境配额80/0/20是两套不同分布。

每帧60维：pelvis相对较低脚踝link的高度1、29关节角、左右手/脚/头5个link位置15、pelvis link机体系线速度3、角速度3、去yaw的根旋转6、箱子相对位置3。远箱xy封顶0.7m且z置0。与参考数据使用相同关节名映射/坐标约定。

判别器600→512→256→1；running mean/variance跨时间槽共享，归一化后截断±10；LSGAN损失加0.5梯度惩罚，学习率5e-5。每回合reset的第一帧重复填满历史，从第一条转移开始计奖励；终止转移使用reset前AMP历史。style=`max(1−0.25*(D−1)^2,0)`。

RSI随机抽本技能片段和帧，初始化根姿态、源线/角速度、关节角/速度；去yaw，按实际G1脚碰撞hull进行向上的5mm地面间隙修正。没有本次新增的静止起点或参考动作控制器。loco箱子前方±45°、0.7–2m，倾斜±30°且箱底贴地5mm。loco中2%为search：bearing±60–180°、距离0.9–2m。hold保留参考手边箱子高度，**不是所有reset的箱子都在地面**；这是用户要求20%hold后的现行设计。pickup RSI为0，但AMP仍包含完整拾箱动作。

箱子yaw课程按当前进程首个训练迭代为锚：0→0°、10000→10°、20000→30°、30000→180°，分段线性。20秒回合，最多1000policy步。

## 奖励的实际计算

令 `u=exp(-10*(g_x²+g_y²))*clamp(-g_z,0,1)`，`h`为pelvis离地高度；距箱大于0.7m时 `b=u*exp(-20*max(0.65-h,0)²)`，否则 `b=u`。这是连续形状因子，不是额外状态机或终止条件。

|项|权重|实际作用|
|---|---:|---|
|locomotion_stability|+5|奖励b；不要求水平静止/原地|
|walk_task|+1|`b*[exp(-5*(0.85-v_towards)^2)+0.5*exp(-0.75*abs(bearing))]`；距箱<0.7m时括号改1.5|
|carryup_task|+1|距箱≤0.7m时，双手中心接近、手箱实际接触、箱高接近0.64m的组合|
|standup_task|+0.4|箱高>0.6m、姿态/手距等满足瞬时条件后，鼓励根/头高度及持箱稳定|
|stable_grasp|+0.2|近箱低位时的手端接近、双手接触及手臂平稳|
|slow_pickup|−0.0005|近箱且箱高<0.55m时全身关节速度平方和|
|arm_speed_pickup / arm_acc_pickup|−0.02 / −0.00002|下蹲拾箱期双臂速度>1rad/s、加速度>20rad/s²的平方excess均值|
|grip_force_cap|−0.02|双手接近箱子时，手箱接触力超过7N的excess|
|held_hand_speed / held_hand_acc|−0.02 / −0.00002|箱高>0.55m且双手中心距箱<0.15m时，对同样阈值惩罚|
|search_turn|+0.5|只对search起点、bearing>45°、距箱>0.7m，奖励朝向改善和正确方向yaw转动|
|waist_yaw_penalty|−0.5|腰yaw偏离默认角的L1|
|dof_acc / action_rate|−1e-7 / −0.03|关节加速度平方和 / 相邻wrapper裁剪后的动作差平方和|
|torques / dof_vel|−1e-4 / −2e-4|关节力矩 / 速度平方和|
|dof_pos_limits / dof_vel_limits|−5 / −0.001|位置软限位（膝伸直允许物理下界）/速度超限|
|undesired_contacts|−1|髋、膝不期望接触|
|early_failure|−50|当前fell/tipped失败一次，排除timeout|

上述所有RewardManager项都乘policy dt=0.02一次。最终训练奖励：

`r = 0.75 * (0.02 * Σ(weight_i * term_i)) + 0.125 * style`

AMP style此处不再乘dt。该系数不是“AMP必然占75%”，实际占比取决于各项数值，task为负时也不宜用简单百分比解释。

动作界损失为各关节均值超出raw可行区的平方excess和，再按batch平均，系数0.01；它是优化器损失，不是环境奖励。

## reset、终止与成功

- `abs(roll)>0.5rad`（约28.65°）或 `abs(pitch)>1.1rad`（约63.03°）立即tipped。
- pelvis高度<0.2m或实际head COM高度<0.4m立即fell。
- 20秒timeout。NaN/Inf直接抛异常以停止问题运行。
- 不因走近箱子或找到箱子而reset；成功也不立即reset。
- 严格成功统计：箱底离地≥0.12m、双手各有>1N箱接触、箱体竖直程度>0.9、箱速度<0.25m/s，连续25policy步（0.5秒）。该统计比standup奖励的瞬时门控严格。
- actor/critic历史按reset清空；timeout用reset前108维critic状态bootstrap，真正失败不bootstrap到新回合。

## PPO与验证边界

4096环境，每轮24步；5epochs×4minibatches；gamma0.99、GAE lambda0.95、clip0.2、value_coef1、grad_norm1、entropy0.01。初始lr3e-4、KL目标0.01自适应，范围1e-5–1e-2。raw std初始1，上限1、下限exp(−5)。模型每200轮保存；正式计划40000轮、seed42、fresh。

CPU验证包括奖励几何、坐标平移、失败罚时序、动作界梯度、逐minibatch std、标签隔离、固定配额和旧路径默认值。真实4环境检查PPO/AMP 2＋1轮、原物理参数、部分reset、timeout、严格恢复、错误契约/超界std拒绝及导出。512×200短训检查真实学习更新与采样比例，并报告首末窗口行为。它们都不能证明长期行走或拾箱已经收敛。

首轮CPU有一个测试fixture漏传原基类要求的fixed schedule，修正测试调用而没有放宽生产保护；同时只读复核发现显式warm-start旧权重可绕过std上限，已补迁移投影和记录。保留失败回执，严格load仍拒绝超界，不静默更改恢复权重。正式启动不使用warm-start。

首版512×200 pilot的stability权重2仍不足，已保留attempt1完整结果；本次只将该奖励权重调至5（理想直立+0.10 raw task/步），其余反馈/物理参数不变，按同seed、同规模重新验证。实际倾斜状态下贡献小于这个上限，不能据此宣称已经消除负收益或会走路。

[两版512环境短训曲线](pilot_comparison.png)：每25轮窗口的已完成loco回合长度、扣除失败事件后的持续task收益、动作限位比例和std。它不是独立行走/拾箱成功率。

## 最终工程验收与正式运行快照

2026-10-19T22:05:18.077863+09:00：wall5 revision17训练反馈修复已完成工程检查并从零启动4096环境正式run，PID254358；检查至17轮，最近10轮平均3.919秒、最慢3.940秒。旧6600回放确认空手约0.27秒倾倒，采样噪声膨胀、缺少空手平衡反馈和实际采样偏向hold构成明确训练缺口；未发现GAE跨回合泄漏。新增平衡反馈及walk姿态门控、std≤1/动作均值界正则、固定80/20环境配额；PD、roll0.5、深度和13段AMP保持。39项CPU、4环境PPO/AMP 2＋1轮恢复导出、512环境200轮fresh检查通过。正式训练进行中，长期站走/拾箱能力尚未验证。

新反馈权重5的512×200轮pilot，首25轮loco已完成回合均长28.48步，末25轮46.49步；末窗口tipped比例98.940%。这是一段训练采样统计，不是独立站走成功率，不能据此认定会走路。权重2与5的同seed对比见[pilot_comparison.json](pilot_comparison.json)。首版反馈权重2的CPU失败fixture及其仿真通过结果全部保存在attempt1；原测试断言未放宽。

正式目录：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_21-59-02_wall5_v17_loco_feedback_fresh_20261019_215857`，seed42、40000轮，从零初始化，未加载旧模型或docs短训模型。首model_0确认revision17、actor500输入/critic108、AMP13段60维、优化器step20、Normalizer count61440、固定3277loco/819hold配额与std≤1。原始PID退出原因未从日志确定，本次没有向不存在的旧进程发送信号。

查看训练：

```bash
tail -f '/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v17_loco_feedback_fresh_20261019_215857.log'
```

实际启动参数（已在运行，无需重复启动）：

```bash
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/train.py --task Template-Perceptual-Ball-CarryBox-Walled5-v0 --num_envs 4096 --device cuda:0 --headless --seed 42 --max_iterations 40000 --run_name wall5_v17_loco_feedback_fresh_20261019_215857
```

运行环境设置与去重/资源检查见launch.sh/launch.py。源码快照和SHA、数据manifest身份见launch.json；正式启动检查见snapshot.json。时间、PID、迭代均为带时间快照，下次操作需重新核对真实进程。
