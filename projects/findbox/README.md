# 找箱与搬箱子项目 · findbox

2026-10-20：[wall5最新model2800的20秒play录像](../../docs/carrybox/wall5_latest_play_20261020/README.md)：revision17、单环境loco配额、均值动作、原课程yaw2.8°/推扰0.45，严格契约/权重核对、500帧完整解码及关键帧检查通过。已检查0.04、1、2、5、10、15、19.96和20秒画面，机器人与箱子清晰可见。此段空手起点回放能向箱子移动，前两秒接近后主要在箱旁站立；第999步相对首步水平位移约1.33m，距箱约0.41m。箱子仍在地面，没有完成抱起。整段没有倾倒/低高度终止，唯一reset发生在第1000步，是20秒超时；这不能代替多起点稳定行走评估。 正式训练进程保持，视频不作成功率结论。

2026-10-19：[PhysHSI与wall5 reset只读对照](../../docs/carrybox/wall5_physhsi_reset_20261019/README.md)：PhysHSI实际20%默认站姿＋80% RSI，RSI根速度覆盖为±0.2；当前wall5保留参考速度，11段相同loco数据的起始水平速度均值0.743m/s、P95 1.071m/s。动作缓存预填仅影响最初0–20ms，两边roll0.5/pitch1.1相同。CPU来源/数据核验通过；未改生产或重启训练，因果尚需物理对照。

2026-10-19：[wall5 revision17空手倾倒修复与重启](../../docs/carrybox/wall5_reset_bug_20261019/README.md)：旧6600均值/采样各32回合全部约0.27秒倾倒；新增平衡反馈、walk姿态门控、std≤1/动作均值界正则和固定80/20环境配额，原PD/roll0.5/深度/AMP保持。39项CPU、4环境更新恢复导出及512×200短训通过；正式4096 fresh PID254358，检查17轮、平均3.919秒/轮。训练进行中，尚未验证稳定行走/地面拾箱。

2026-10-19：[wall5 roll0.5 model5200站走回放](../../docs/carrybox/wall5_roll05_eval_20261019/README.md)：检查时最新模型，均值/采样各32个loco首回合均在1秒内倾倒reset，平均0.454/0.420秒，全部在首次push前；尚未学会稳定行走。近期250轮loco约19.7步、hold约700步，完成步数约90%来自hold。严格契约/权重/初态核对及诊断两项PASS；PID114186继续训练，过程中已生成model5400，本结果仅针对5200。

2026-10-19：[wall5 roll0.5正式重启](../../docs/carrybox/wall5_roll05_start_20261019/README.md)：4096环境fresh、roll0.5，PID114186，检查迭代16，最近10轮平均3.802秒/最慢3.900秒；首checkpoint确认revision15、非对称AC、RSI80/0/20及13段60维AMP。用户明确重启，原控制候选保持撤回；训练进行中，未证明收敛。

2026-10-19：[wall5 roll阈值0.8→0.5rad](../../docs/carrybox/wall5_roll05_20261019/README.md)：按用户要求收紧为双向侧倾28.65°，pitch仍1.1rad；同步checkpoint契约，14项CPU检查通过。仅revision15基础单参数变更，未恢复已撤回的loco控制候选，未启动训练或证明站走修复。

2026-10-19 13:23 JST：[wall5空手起点修复候选未通过](../../docs/carrybox/wall5_loco_fix_20261019/README.md)：固定80/0/20环境配额、静止起点课程及动作范围正则候选通过39项CPU检查；物理检查初始0/16、两次修正后仍仅1/16撑满5秒。PPO短训/4096性能未执行，启动门禁阻止正式run。候选完整归档，5个源码按hash恢复本次修改前revision15，原有改动保留；未启动新训练，未修复完成。

2026-10-19：[wall5空手起点立即倾倒诊断](../../docs/carrybox/wall5_loco_early_20261019/README.md)：rev14 model11200同初态五组16环境回放通过，策略首回合9–11步全部pitch超限，参考/默认控制平均40–53步，均未稳定行走。首步左膝16/16、右膝14/16目标限位；近期loco约10.6步、hold约936步，已完成回合步数约96%来自hold。仅诊断；原PID4038923检查时已退出、日志止于11304轮，原因未知，本次未停止或重启，revision15尚未正式训练。

2026-10-19：[wall5 rev14专用play命令](../../docs/carrybox/wall5_rev14_play_20261019/README.md)：新增独立归档播放入口，model11200严格权重加载、环境契约及既有录像源码hash检查通过；默认4环境、均值动作、原rev14推扰/摩擦。仅CPU验证，未启动GUI/GPU仿真或操作正式训练。

2026-10-19：[wall5 revision14 model11000的20秒play录像](../../docs/carrybox/wall5_play11000_20261019/README.md)：单环境均值动作、原rev14物理/噪声、满推扰/yaw12°；严格模型/环境契约匹配，500帧25fps完整解码通过。开头loco倾倒重置后进入hold参考起点，未展示地面拾箱成功；原正式PID4038923保持运行。

2026-10-19 12:08 JST：[wall5推扰/摩擦核验与revision15](../../docs/carrybox/wall5_push_20261019/README.md)：rev13实际10637轮；model10600三组回放loco均约13步且首次push前pitch超限，hold原推扰/增量/无推扰约886/970/1000步。仅wall5改增量push和地面/default摩擦1.0/multiply，21项CPU、三组回放及4环境2＋1轮更新恢复导出通过。当前正式PID4038923仍为revision14、检查10779轮，未重启；revision15尚未正式训练，未证明拾箱收敛。

2026-10-19 00:42 JST：[wall5非对称AC与4096从零重启](../../docs/carrybox/wall5_asymmetric_20261019/README.md)：revision14仅critic使用108维本体/线速度/箱位姿尺寸真值，独立MLP；actor仍372维本体＋4帧深度。31项CPU、4环境2＋1轮更新恢复导出及正式启动核验通过；旧PID3812053已停止，新PID4038923，检查至15轮，最近10轮平均3.813秒/最慢3.830秒。AMP13段/RSI80-0-20保持，训练进行中，未证明收敛。

2026-10-18 21:59 JST：[当前wall5 AMP数据集可视化](../../docs/carrybox/wall5_amp_visualization_20261018/README.md)：实际run与model_0确认ground_pickup的13段（11行走/1地面拾箱/1持箱）；完整63.08秒MP4、13个分段及HTML浏览页已生成，3785帧/60fps和源hash对应检查通过。复用hash一致的G1录像，仅CPU处理；AMP40/40/20，RSI80/0/20，训练PID3812053保持运行。

2026-10-18 13:16 JST：[wall5改为从零正式训练](../../docs/carrybox/wall5_fresh_20261018/README.md)：按用户明确要求停止恢复运行PID3810947，新PID3812053，4096环境、40000轮、fresh，无resume/warm-start。首checkpoint优化器step20与Normalizer count61440确认全新初始化；检查迭代11→14，最近10轮平均3.801秒、最慢3.830秒。保留性能优化/revision13/RSI80-0-20；旧产物保留，训练进行中，未证明收敛。

2026-10-18 13:08 JST：[wall5性能优化与正式恢复](../../docs/carrybox/wall5_perf_20261018/README.md)：RSI合并写入、AMP批量native插值及同批CNN复用，4096同配置平均7.254→3.870秒/轮；31项CPU与4096完整更新/部分reset/恢复通过。新PID3810947，正式最近10轮平均3.902秒、最慢3.940秒，检查迭代12→15。保持revision13/RSI80-0-20/全部遮挡与学习配置，从原正式model0恢复；旧70轮中未落盘部分无法恢复。训练进行中，未证明收敛。

2026-10-18 12:33 JST：[wall5 revision13正式启动核验](../../docs/carrybox/wall5_start_20261018/README.md)：用户启动PID3804340，4096环境、fresh；实测迭代8→10，model_0契约/参数/优化器正常，RSI80/0/20及60维AMP已生效。第1–10轮平均7.001秒、最慢7.21秒，未达到6秒目标；仍在训练初期，未证明收敛。只读检查，未操作训练。

2026-10-17：[wall5 RSI改为80/0/20](../../docs/carrybox/wall5_hold_rsi_20261017/README.md)：按用户要求20%改为hold，pickup为0；loco箱子仍贴地，hold保留参考手边箱高。revision13，14项CPU和4环境reset短测通过；未启动/重启训练，未验证持箱稳定性。

2026-10-17：[wall5 revision12训练端修订](../../docs/carrybox/wall5_training_v12_20261017/README.md)：60维任务AMP＋running normalization、可见范围pose监督coef0.1、KL自适应PPO/std1/entropy0.01/5 epochs/MLP512-256-256、roll0.8＋一次性失败罚、reset80/20/0；同步修正RSI连杆速度语义。保留13段数据、0–31地面起点、全身碰撞和无特权actor/critic。38项CPU及4环境2＋1轮更新/恢复/导出通过；未正式训练或证明收敛，旧网络不兼容需fresh。

2026-10-17：[wall5地面拾箱数据与全贴地reset](../../docs/carrybox/wall5_ground_20261017/README.md)完成：独立ground_pickup profile保留13段（完整地面pickup03，排除高位01/02），原15段不变。reset70/30/0，箱底离地5mm、移除平台；全身碰撞验证后pickup仅采0–31帧。27项CPU、4环境全部32帧物理检查、PPO/AMP 2＋1轮及恢复通过，revision11；未启动正式训练或证明收敛。

2026-10-17 12:49 JST：[wall5拾取失败与reset核对](../../docs/carrybox/wall5_pickup_reset_20261017/README.md)：旧revision9日志止于20786轮，近100轮约556步，loco累计成功0；AMP占净混合奖励约91.7%，稳定抓握奖励近零。核对了60/30/10参考初始化、pickup支撑台与地面起点差异、28.65°横滚终止及成功不reset。当前无CarryBox训练进程，revision10全身碰撞尚未正式训练；CPU只读审计通过，未改参或重启。

2026-10-17：[wall5全身碰撞与结构可视化](../../docs/carrybox/wall5_fullbody_20261017/README.md)完成：新增7处、替换肩/小腿6处，35个实体连杆全覆盖；PhysX实测shape30→35，13处接触探针、质量/惯量/深度不变及4环境回放/新契约恢复通过。可交互HTML与四视图PNG已保存。wall5升revision10，旧revision9仅显式weights-only迁移；自碰撞仍关闭，未启动正式训练或验证收敛。

2026-10-17：[wall5 G1碰撞体核对](../../docs/carrybox/wall5_collision_20261017/README.md)：离线USD＋原生成函数确认28个带碰撞link、26个凸包Mesh＋4个膝部Cube；双手为凸包、头部无独立碰撞体。物理自碰撞关闭，Warp视觉自遮挡保留。仅审计，未改资产/配置/训练。

2026-10-16 21:57 JST：[wall5平均回合长度诊断](../../docs/carrybox/wall5_length_20261016/README.md)完成：正式PID2996727保持，检查到7396轮、近100轮约290步；16环境四组推理确认当前策略对push敏感，关闭后已完成回合均值约531–546步，但loco仍远离箱子且成功0。AMP仍有效，PPO lr=3e-4，未发现旧立即reset重现；任务接近/拾取学习及推扰课程需后续改进。本次仅诊断，生产训练未修改。

2026-10-16：[与Kickball交叉核对相机](../../docs/carrybox/camera_crosscheck_20261016/README.md)：wall3–5名义安装匹配G1 rev_1_0，当前正式wall5仍为89.16°×58°/50Hz/4帧、光轴深度除以3；官方垂直图示55.2°，实机K与光学外参未标定。原CarryBox-v0为48×32、79.61°×58.11°。仅核对，未改训练。

2026-10-16：[wall5早期AMP占比核对](../../docs/carrybox/wall5_start_20261016/README.md#amp早期占比核对第5574轮)：第55–74轮AMP占净混合奖励约47.3%，style0.098、D expert/policy loss0.0198/0.0669、有效率100%，量级符合差异文档X2参考；仍以倾倒结束、拾箱成功0，尚不能判断收敛；只读检查，未改参或重启。

2026-10-16 13:49 JST：[wall5正式训练启动核验](../../docs/carrybox/wall5_start_20261016/README.md)：用户启动PID2996727，4096环境、40000轮、fresh；已完成第12轮，热身后10轮平均4.244秒、最慢4.36秒。model_0为schema2/revision9/35维AMP/15段数据，策略与D有限且优化器有更新，AMP有效率100%；训练进行中，未证明收敛。

2026-10-16：[新增wall5：X2/G1差异文档的AMP阶段A](../../docs/carrybox/wall5_20261016/README.md)。基于wall4 revision8，AMP改为每步上限0.125、35维原始本体特征、D正则化与较低学习率、reset首步参与奖励和更新。PPO/深度/任务几何保持；50项CPU、4环境3＋1轮恢复导出通过。未正式训练或验证收敛/4096耗时；12:35 JST原wall4 PID2660033仍运行。

2026-10-15 13:10 JST：[G1站立reset排查、接地修复与wall4正式重启](../../docs/carrybox/g1_reset_20261015/README.md)：旧model_14000真实横滚超限（1600回合均3步）；另修复G1参考初始化脚底穿地，wall3/wall4共同revision8按实际足部碰撞几何补足5mm间隙。G1相机位姿/身体与障碍遮挡、44项CPU、16环境更新恢复导出、4096验收通过。新wall4 PID2660033，4096环境fresh、核验iteration12，正式热身平均4.238秒/轮、最慢4.33秒；训练进行中，未证明收敛。

2026-10-15：新增[旧wall4模型显式仅权重播放](../../docs/carrybox/play_v6_20261015/README.md)，model_14000在当前revision7环境的4环境命令已提供；实际权重CPU兼容检查通过，未启动GUI或训练。默认严格恢复规则保留。

2026-10-15：[wall3/wall4公共修复与正式命令](../../docs/carrybox/wall_parity_20261015/README.md)：revision7统一实际头部COM、膝限位惩罚、物理动作目标裁剪、RSI60/30/10、搜索/yaw/推扰课程及训练配方。默认wall3仅墙，wall4墙加3圆柱，其他行为一致；41项CPU及两任务4环境更新/恢复/导出通过。未启动新版正式训练，未证明收敛；旧wall4 PID2448113仍使用revision6。

2026-10-15：[wall4不收敛诊断](../../docs/carrybox/convergence_20261015/README.md)：13691轮快照及16环境纯推理确认行走起点约3步倾倒，保持reset角约39步；直接抱箱轨迹占有效样本；发现head_link腰部原点误作头部高度及专家膝角与软限位惩罚冲突。仅关闭push未修复，AMP训练style近零。已完成诊断，生产修复待做；PID2448113保持运行，未修改或重启训练。

2026-10-14 21:13 JST：[wall4 handoff修订与新版AMP重启](../../docs/carrybox/handoff_20261014/README.md)：完整X2奖励/G1适配、RSI80/0/20、双向roll、深度/物理随机化及wall动作范围修复完成；35项CPU、4环境更新/恢复/导出及4096完整更新通过（平均4.295秒、最慢4.318秒）。旧PID2348537已停止，新PID2448113已核验到iteration30，正式热身后平均4.230秒、最慢4.300秒，首个checkpoint schema2/revision6及15段AMP身份一致；15段AMP，旧model_4200仅作权重迁移。未证明收敛。

2026-10-14 20:46 JST：[新AMP默认配置复核](../../docs/carrybox/amp_default_20261014/README.md)通过：CarryBox基线/wall3/wall4及RSI默认均为规范15段数据，两组CPU检查PASS。实际PID2348537的model_4000.pt仍为旧17段缓存；本次未重启训练，后续切换需显式weights-only warm-start，不能完整resume旧AMP。

2026-10-14目录规范化：当前默认数据为[`assets/motions/findbox/`](../../source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md)，与足球`kick/`并列；使用`locomotion/`、`pick_up/`、`hold/`与小写下划线文件名。15段内容逐字节不变，抱箱仍5秒；AMP/RSI默认路径同步，旧根findbox保留兼容。schema=1、dataset_revision=3，迁移检查与CPU初始化通过，未切换训练。[迁移说明](../../docs/carrybox/amp_layout_20261014/README.md)。

2026-10-14数据修订：按用户要求将有效AMP整理为15段（行走11、拾箱3、抱箱1）；carrywith1保留原0–20帧并重复第20帧至5秒，carrywith2/3归档。schema=1、dataset_revision=2；旧17段全量备份保留。当前训练缓存不热切换，旧checkpoint不能直接完整恢复到新数据。详见[变更与兼容说明](../../docs/carrybox/amp_hold_20261014/README.md)。

2026-10-14 16:01 JST：Warp迁移完成，正式训练PID2348537已核验到iteration18；4096环境×24步、PPO 4 epochs×4 minibatches及完整AMP保持，热身后平均4.023秒、最慢4.078秒，达到6秒目标。新model_0.pt为schema2/revision5/warp，策略和AMP参数有限。尚未完成长训或证明拾箱收敛。[迁移与日志](../../docs/carrybox/warp_20261014/README.md)。下方为历史快照。

2026-10-14 15:12 JST：[G1/X2深度后端与分项耗时核对](../../docs/carrybox/depth_timing_20261014/README.md)：当前G1仍为RTX，X2的Warp多网格后端尚未迁移；复读同源码实测render调用占81.4%，正式最近10轮17.255秒。训练保持运行，未改teacher/critic/相机频率。

2026-10-14 15:09 JST：正式wall4 4096环境已从原正式model_0.pt恢复，PID2341959，检查到iteration2；后两轮17.62/17.42秒，schema2/revision4、策略与AMP有限值检查通过。6秒目标未达，训练尚未完成或证明收敛。[性能记录与日志](../../docs/carrybox/render6s_20261014/README.md)。下方状态为历史快照。

2026-10-14 14:41 JST：4096环境wall4相机位姿读取优化通过22项CPU、4环境运动/reset/遮挡及4096同规模速度和2+2 PPO/AMP恢复检查；原进程停止后从原正式model_0.pt恢复，新PID2336376。已检查到iteration2，正式后两轮21.16/20.90秒（此前约25.63秒）；同动作环境步耗时减少23.2%。保持4096、48×27/50Hz RTX遮挡、奖励、控制和AMP数据，尚未证明任务收敛。[性能记录与最新日志](../../docs/carrybox/performance_20261014/README.md)。下面4096旧run及128run均为历史。

2026-10-14 14:18 JST：按用户要求停止128环境训练（最后日志1798轮，model_1600.pt保留），4096环境wall4于14:06从头启动，PID2330803。实际环境配置4096已核对，检查到18/40000轮；平均回合37.23步，AMP有效比例76.86%，model_0.pt有限值及schema2/revision4、根findbox数据身份验收通过。尚未完成训练或证明收敛；动作目标范围问题仍未调整。[新日志与验收](../../docs/carrybox/scale4096_20261014/README.md)。下文128环境运行记录为历史。

2026-10-14 12:55 JST：用户重新授权后，修正跌倒奖励的wall4已从头启动，PID2322385；128环境、seed42、40000轮，AMP/RSI使用根findbox。检查到iteration24，平均回合32.92步、AMP有效比例77.47%，model_0.pt的schema2/revision4及有限值已核验。拾取动作目标范围问题未调整，未证明收敛。详见[本次启动与日志](../../docs/carrybox/restart_20261014/README.md)。下文停止/旧训练记录保留为历史。

2026-10-14此前停止记录：用户要求停止后，正式wall4及等待器均已停止，最后日志14695，模型保留至model_14600.pt。已确认跨回合跌倒惩罚泄漏导致早死/AMP窗口消失，并完成wall3/wall4专属修复（revision=4）；21项CPU和16环境纯推理回放通过。拾取参考与动作目标范围仍有不匹配，未重新训练，未证明收敛。详见[不收敛排查与当前设计](../../docs/carrybox/convergence_20261014/README.md)。下列运行/排队描述均为日期注明的历史快照。

2026-10-14 11:39 JST检查：正式wall4已于00:52启动，PID2307414，128环境、seed42、40000轮；当前约14632/40000，最新model_14600.pt。队列2300674状态RUNNING；run为`logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_00-52-12_wall4_afterfootball_20261013/`，终端日志为`logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/train.log`。football最终模型和退出检查、第二次128环境预检已通过。此为运行快照，未完成正式长训或独立成功率评估；下文10月13日等待状态为历史。

当前主线：`Template-Perceptual-Ball-CarryBox-v0`，checkpoint schema=2（含AMP）。流程是**深度找箱 → 双手接触 → 抬起并持续保持**。项目待办见[总看板](../README.md)。

## 项目归属

本目录是`findbox`项目的统一入口，与[football](../football/README.md)并列。已有`CarryBox` Gym ID、`carrybox_*`源码和`carrybox-*`工程记录属于本项目，保留原名称与路径。旧入口`projects/carrybox/`兼容指向本目录。

当前数据入口为[`assets/motions/findbox/`](../../source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md)；根目录[`findbox/`](../../findbox/)保留旧命名兼容快照。完整原始数据见[原17段备份](../../docs/carrybox/amp_hold_20261014/original_dataset/)。[`docs/carrybox/`](../../docs/carrybox/)保存本项目设计与验证；[`scripts/rsl_rl/`](../../scripts/rsl_rl/)中的`*carrybox*`为本项目脚本。G1资产和通用train/play由两个项目共享。

## Walled迁移（2026-10-13）

已新增G1 `CarryBox-Walled3-v0`、`CarryBox-Walled4-v0`，按walled3→walled4继承，保留无特权actor/critic与FindBox AMP。2026-10-13运行故障修复后，两变体均通过4环境几何验收、20轮PPO/AMP及恢复后2轮训练。128环境正式规模50＋恢复2轮验收也通过，共5147次reset；19项CPU合同通过。详见[运行修复与回执](../../docs/carrybox/wall4_repair/README.md)和[任务设计、完整观测与命令](../../docs/carrybox/walled/README.md)。

## 深度管线核对（2026-10-13）

[相机位姿、内参与遮挡审计](../../docs/carrybox/depth_audit/README.md)已通过：基线/wall3/wall4的CUDA/RTX相机与当前G1模型的D435名义安装一致，实测墙和圆柱遮挡后不泄漏后方箱子深度；策略最新深度帧与渲染归一化逐像素一致。实机标定/预处理配置尚未提供，不能宣称实机完全一致。后续运行修复另行验证了RTX位置与实际碰撞位置一致，训练状态以最新运行记录为准。

## Football结束后的wall4安排（2026-10-13）

用户已授权football完成后串行启动wall4。2026-10-13 23:54 JST已用有效验收替换旧阻塞登记：新等待器PID2300674，READY / WAITING_FOOTBALL；足球约48693/50000，正式wall4尚未启动。正式配方为128环境、seed42、40000轮、从头初始化；不使用docs中的验证模型。队列检查足球最终模型/日志/进程身份，确认资源释放后重复128环境预检并只启动一次。状态见[运行修复记录](../../docs/carrybox/wall4_repair/README.md)。walled迁移契约revision=3、checkpoint schema=2；原CarryBox-v0及football接口未改。

## 当前状态与下一步

截至2026-10-17 12:49 JST，没有CarryBox训练或play进程；旧wall5 revision9正式日志最后完成20786/40000轮，未完成预定训练。近100轮平均回合约556步，但loco累计拾箱成功仍0；pickup/hold的少量成功不代表完整地面流程。[最新诊断与reset逻辑](../../docs/carrybox/wall5_pickup_reset_20261017/README.md)。

当前wall5源码为revision15（增量推扰＋显式1.0/multiply摩擦），已通过短测，尚未正式启动。2026-10-19空手起点诊断时原正式PID4038923已退出，revision14日志止于11304轮；退出原因未知，本次未停止或重启。近250轮平均4.09秒、loco约10.6步、hold约936步；model11200五组对照确认策略明显加速前倾，控制基线也未稳定行走，详见页首诊断。critic独立108维特权MLP，actor深度＋本体，AMP13段/RSI80/0/20保持；所有旧模型保留，历史短测模型仅作工程验证。

## 配置与代码地图

源码均在`source/perceptual_ball/perceptual_ball/`下：

| 模块 | 路径 |
|---|---|
| 环境、观测、奖励、PPO/AMP参数 | `tasks/manager_based/perceptual_ball/carrybox_env_cfg.py` |
| 深度、标签、奖励和terminal历史 | `tasks/manager_based/perceptual_ball/mdp/carrybox.py` |
| wall3/wall4继承配置 | `tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py` |
| wall5配置与任务AMP | `tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py`、`mdp/carrybox_wall5.py`、`carrybox_wall5.py`、`rsl_rl_extensions/carrybox_wall5.py` |
| wall场景、参考初始化、奖励和深度扰动 | `tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py` |
| yaw课程、帧/标签配对缓存 | `carrybox_walled.py` |
| 抬起保持判据 | `tasks/manager_based/perceptual_ball/mdp/carrybox_state.py` |
| FindBox加载与AMP特征schema | `carrybox_amp.py` |
| actor/critic、位姿头、PPO/AMP及checkpoint | `rsl_rl_extensions/carrybox.py` |

CarryBox-v0及wall3/4的actor/critic只读取深度与本体。wall5 revision14按用户明确要求采用非对称AC：actor仍只读深度与本体，critic为当前本体＋机体线速度＋箱子相对位姿/尺寸真值的108维独立MLP，特权信息不进入actor或部署导出。wall5另保留训练专用60维任务AMP及可见性配对辅助监督，基线/wall3/4仍用原AMP。持箱参考不增加搬运目标点或放下阶段。

## 数据与产物

| 路径（仓库根目录起） | 用途 |
|---|---|
| `source/perceptual_ball/perceptual_ball/assets/motions/findbox/` | 基线及wall3/wall4的15段规范AMP/RSI数据：行走11、拾起3、抱箱1；dataset_revision=3 |
| `source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/` | wall5专用13段：行走11、地面拾起1、抱箱1；dataset_revision=4；当前revision13 RSI为80%loco/0%pickup/20%hold |
| `source/perceptual_ball/perceptual_ball/assets/motions/findbox/amp_manifest.json` | 60Hz/xyzw/29关节顺序、采样权重、显式group、片段hash |
| `findbox/` | 修订2旧命名15段兼容快照；显式指定仍可加载 |
| `source/perceptual_ball/perceptual_ball/assets/motions/carrybox/pickUp/` | 最初移植的参考归档，当前AMP不读取 |
| `logs/rsl_rl/g1_carrybox_depth/` | 正式训练输出；首次训练时创建 |
| `docs/carrybox/` | 设计与验证记录、临时smoke产物 |
| `docs/carrybox/amp/test_receipts.json` | 当前AMP接入的测试回执 |

数据重采样60→50Hz，行走/拾起/持箱采样概率40/40/20%。修改manifest或训练奖励契约需记录新版本；恢复训练检查数据身份。CarryBox-v0基线播放及策略导出不加载动作数据集；walled变体仿真播放的参考初始化需要findbox数据。

## 命令

在已配置Isaac Lab的环境、仓库根目录运行：

```bash
python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-CarryBox-v0 \
  --num_envs 128 --device cuda:0 --headless --enable_cameras \
  --max_iterations 30000 --seed 42 --run_name depth_pose_amp_scratch
```

相机参数`--enable_cameras`必须保留。基线128环境是初始配方；wall4规模验收见最新运行修复记录。足球当前也使用cuda:0，启动时需结合实际显存和运行状态安排资源。

恢复训练：在相同任务命令中增加`--resume --checkpoint /path/to/schema2/model.pt`。播放：

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-CarryBox-v0 \
  --num_envs 4 --enable_cameras --checkpoint /path/to/schema2/model.pt
```

验证：

```bash
python -m unittest discover -s tests -p 'test_carrybox*.py' -v
bash scripts/rsl_rl/smoke_carrybox.sh
```

smoke脚本使用当前开发机Isaac安装路径，可通过`ISAAC_SIM_PATH`、`ISAAC_LAB_PATH`和`BALL_PYTHON`覆盖。

## 设计、验证与交接

- [任务完整说明](../../docs/carrybox/README.md)
- [AMP接入说明](../../docs/carrybox/amp/README.md)
- [最新验证结果](../../docs/carrybox/smoke.json)
- [当前AMP交接](../../agent/handoff/carrybox-findbox-amp.md)
- [初次无AMP移植交接（历史）](../../agent/handoff/carrybox-depth-v0.md)

schema=1无AMP模型属于历史实现，不能直接恢复为当前完整AMP训练状态；足球checkpoint也不适用于本任务。

## 数据集可视化

2026-10-14抱箱修订版：[15段逐PT独立60fps视频](../../outputs/carrybox/findbox_hold_20261014/README.md)，抱箱段300帧/5秒，完整数据4155帧/69.25秒。下方17段录像属于修改前数据，源文件已完整备份。

2026-10-14后续：[逐PT直接独立录制17段60fps视频](../../outputs/carrybox/findbox_individual/README.md)，画面标注源帧号/时间，同名MP4、PNG和JSON便于数据调整。全4628源帧解码及hash校验通过；原数据未修改。此前30fps合辑及切片继续保留。

2026-10-14复核当前全部源数据和manifest与录像hash一致，并新增[17段独立MP4索引](../../outputs/carrybox/findbox_dataset/clips/README.md)：拾箱3、持箱3、行走11；全2318帧解码及与原录像对应检查通过。本次仅CPU视频处理，未调整训练。

2026-10-13已录制全部17段FindBox参考动作：[MP4视频](../../outputs/carrybox/findbox_dataset/findbox_dataset.mp4)，77.27秒、960×720、30fps，完整解码2318帧验证通过。片段时间索引和录制方法见[可视化说明](../../docs/carrybox/dataset_visualization/README.md)。这是数据集运动学回放，箱体yaw和支撑台为辅助示意。
