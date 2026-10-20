# 项目看板

2026-10-20：[wall5三维任务距离修正](../docs/carrybox/wall5_distance3d_20261020/README.md)：wall5 revision18将任务门控统一为骨盆到箱心XYZ距离0.7m，行走方向/AMP封顶仍为XY；43项CPU及4环境PPO/AMP 2＋1轮、严格恢复/旧契约拒绝通过。仅实现与短测，未重启；检查时正式PID254358仍为revision17、迭代14676，新版尚未正式训练或证明抱箱成功。

2026-10-20：[wall5最新model14200的20秒play录像](../docs/carrybox/wall5_play14200_20261020/README.md)：revision17、单环境loco配额、均值动作、原课程yaw18.4°/推扰1.00，严格契约/权重核对、500帧完整解码及关键帧检查通过。已检查0.04、1、2、5、10、15、19.96和20秒关键帧，主体和箱子清晰可见。机器人在前1–2秒走近箱子，随后主要在箱旁站立和小幅调整，箱子仍在地面，没有完成抱起。第999步相对首步水平位移约1.05m，距箱约0.33m。全强度推扰配置下，此段未出现倾倒/低高度终止，唯一reset发生在1000步20秒超时；仅代表该单起点回放，不作为成功率评估。 正式训练进程保持，视频不作成功率结论。

2026-10-20：[wall5最新model2800的20秒play录像](../docs/carrybox/wall5_latest_play_20261020/README.md)：revision17、单环境loco配额、均值动作、原课程yaw2.8°/推扰0.45，严格契约/权重核对、500帧完整解码及关键帧检查通过。已检查0.04、1、2、5、10、15、19.96和20秒画面，机器人与箱子清晰可见。此段空手起点回放能向箱子移动，前两秒接近后主要在箱旁站立；第999步相对首步水平位移约1.33m，距箱约0.41m。箱子仍在地面，没有完成抱起。整段没有倾倒/低高度终止，唯一reset发生在第1000步，是20秒超时；这不能代替多起点稳定行走评估。 正式训练进程保持，视频不作成功率结论。

2026-10-19：[PhysHSI与wall5 reset只读对照](../docs/carrybox/wall5_physhsi_reset_20261019/README.md)：PhysHSI实际20%默认站姿＋80% RSI，RSI根速度覆盖为±0.2；当前wall5保留参考速度，11段相同loco数据的起始水平速度均值0.743m/s、P95 1.071m/s。动作缓存预填仅影响最初0–20ms，两边roll0.5/pitch1.1相同。CPU来源/数据核验通过；未改生产或重启训练，因果尚需物理对照。

2026-10-19：[wall5 revision17空手倾倒修复与重启](../docs/carrybox/wall5_reset_bug_20261019/README.md)：旧6600均值/采样各32回合全部约0.27秒倾倒；新增平衡反馈、walk姿态门控、std≤1/动作均值界正则和固定80/20环境配额，原PD/roll0.5/深度/AMP保持。39项CPU、4环境更新恢复导出及512×200短训通过；正式4096 fresh PID254358，检查17轮、平均3.919秒/轮。训练进行中，尚未验证稳定行走/地面拾箱。

2026-10-19：[wall5 roll0.5 model5200站走回放](../docs/carrybox/wall5_roll05_eval_20261019/README.md)：检查时最新模型，均值/采样各32个loco首回合均在1秒内倾倒reset，平均0.454/0.420秒，全部在首次push前；尚未学会稳定行走。近期250轮loco约19.7步、hold约700步，完成步数约90%来自hold。严格契约/权重/初态核对及诊断两项PASS；PID114186继续训练，过程中已生成model5400，本结果仅针对5200。

2026-10-19：[wall5 roll0.5正式重启](../docs/carrybox/wall5_roll05_start_20261019/README.md)：4096环境fresh、roll0.5，PID114186，检查迭代16，最近10轮平均3.802秒/最慢3.900秒；首checkpoint确认revision15、非对称AC、RSI80/0/20及13段60维AMP。用户明确重启，原控制候选保持撤回；训练进行中，未证明收敛。

2026-10-19：[wall5 roll阈值0.8→0.5rad](../docs/carrybox/wall5_roll05_20261019/README.md)：按用户要求收紧为双向侧倾28.65°，pitch仍1.1rad；同步checkpoint契约，14项CPU检查通过。仅revision15基础单参数变更，未恢复已撤回的loco控制候选，未启动训练或证明站走修复。

2026-10-19 13:23 JST：[wall5空手起点修复候选未通过](../docs/carrybox/wall5_loco_fix_20261019/README.md)：固定80/0/20环境配额、静止起点课程及动作范围正则候选通过39项CPU检查；物理检查初始0/16、两次修正后仍仅1/16撑满5秒。PPO短训/4096性能未执行，启动门禁阻止正式run。候选完整归档，5个源码按hash恢复本次修改前revision15，原有改动保留；未启动新训练，未修复完成。

2026-10-19：[wall5空手起点立即倾倒诊断](../docs/carrybox/wall5_loco_early_20261019/README.md)：rev14 model11200同初态五组16环境回放通过，策略首回合9–11步全部pitch超限，参考/默认控制平均40–53步，均未稳定行走。首步左膝16/16、右膝14/16目标限位；近期loco约10.6步、hold约936步，已完成回合步数约96%来自hold。仅诊断；原PID4038923检查时已退出、日志止于11304轮，原因未知，本次未停止或重启，revision15尚未正式训练。

2026-10-19：[wall5 rev14专用play命令](../docs/carrybox/wall5_rev14_play_20261019/README.md)：新增独立归档播放入口，model11200严格权重加载、环境契约及既有录像源码hash检查通过；默认4环境、均值动作、原rev14推扰/摩擦。仅CPU验证，未启动GUI/GPU仿真或操作正式训练。

2026-10-19：[wall5 revision14 model11000的20秒play录像](../docs/carrybox/wall5_play11000_20261019/README.md)：单环境均值动作、原rev14物理/噪声、满推扰/yaw12°；严格模型/环境契约匹配，500帧25fps完整解码通过。开头loco倾倒重置后进入hold参考起点，未展示地面拾箱成功；原正式PID4038923保持运行。

2026-10-19 12:08 JST：[wall5推扰/摩擦核验与revision15](../docs/carrybox/wall5_push_20261019/README.md)：rev13实际10637轮；model10600三组回放loco均约13步且首次push前pitch超限，hold原推扰/增量/无推扰约886/970/1000步。仅wall5改增量push和地面/default摩擦1.0/multiply，21项CPU、三组回放及4环境2＋1轮更新恢复导出通过。当前正式PID4038923仍为revision14、检查10779轮，未重启；revision15尚未正式训练，未证明拾箱收敛。

2026-10-19 00:42 JST：[wall5非对称AC与4096从零重启](../docs/carrybox/wall5_asymmetric_20261019/README.md)：revision14仅critic使用108维本体/线速度/箱位姿尺寸真值，独立MLP；actor仍372维本体＋4帧深度。31项CPU、4环境2＋1轮更新恢复导出及正式启动核验通过；旧PID3812053已停止，新PID4038923，检查至15轮，最近10轮平均3.813秒/最慢3.830秒。AMP13段/RSI80-0-20保持，训练进行中，未证明收敛。

2026-10-18 21:59 JST：[当前wall5 AMP数据集可视化](../docs/carrybox/wall5_amp_visualization_20261018/README.md)：实际run与model_0确认ground_pickup的13段（11行走/1地面拾箱/1持箱）；完整63.08秒MP4、13个分段及HTML浏览页已生成，3785帧/60fps和源hash对应检查通过。复用hash一致的G1录像，仅CPU处理；AMP40/40/20，RSI80/0/20，训练PID3812053保持运行。

2026-10-18 13:16 JST：[wall5改为从零正式训练](../docs/carrybox/wall5_fresh_20261018/README.md)：按用户明确要求停止恢复运行PID3810947，新PID3812053，4096环境、40000轮、fresh，无resume/warm-start。首checkpoint优化器step20与Normalizer count61440确认全新初始化；检查迭代11→14，最近10轮平均3.801秒、最慢3.830秒。保留性能优化/revision13/RSI80-0-20；旧产物保留，训练进行中，未证明收敛。

2026-10-18 13:08 JST：[wall5性能优化与正式恢复](../docs/carrybox/wall5_perf_20261018/README.md)：RSI合并写入、AMP批量native插值及同批CNN复用，4096同配置平均7.254→3.870秒/轮；31项CPU与4096完整更新/部分reset/恢复通过。新PID3810947，正式最近10轮平均3.902秒、最慢3.940秒，检查迭代12→15。保持revision13/RSI80-0-20/全部遮挡与学习配置，从原正式model0恢复；旧70轮中未落盘部分无法恢复。训练进行中，未证明收敛。

2026-10-18 12:33 JST：[wall5 revision13正式启动核验](../docs/carrybox/wall5_start_20261018/README.md)：用户启动PID3804340，4096环境、fresh；实测迭代8→10，model_0契约/参数/优化器正常，RSI80/0/20及60维AMP已生效。第1–10轮平均7.001秒、最慢7.21秒，未达到6秒目标；仍在训练初期，未证明收敛。只读检查，未操作训练。

2026-10-17：[kickball v5默认关闭Kp/Kd随机化与深度噪声](../docs/agilekickball_v5/no_randomization_20261017/README.md)：复用固定增益和clean-depth路径，保留场景自遮挡及任务学习参数；旧带扰动checkpoint需显式保留原开关。本次未启动或重启训练；22:35 JST只读复查原v5 PID3429618已退出，无train/play进程。

2026-10-17：[wall5 RSI改为80/0/20](../docs/carrybox/wall5_hold_rsi_20261017/README.md)：按用户要求20%改为hold，pickup为0；loco箱子仍贴地，hold保留参考手边箱高。revision13，14项CPU和4环境reset短测通过；未启动/重启训练，未验证持箱稳定性。

2026-10-17：[wall5 revision12训练端修订](../docs/carrybox/wall5_training_v12_20261017/README.md)：60维任务AMP＋running normalization、可见范围pose监督coef0.1、KL自适应PPO/std1/entropy0.01/5 epochs/MLP512-256-256、roll0.8＋一次性失败罚、reset80/20/0；同步修正RSI连杆速度语义。保留13段数据、0–31地面起点、全身碰撞和无特权actor/critic。38项CPU及4环境2＋1轮更新/恢复/导出通过；未正式训练或证明收敛，旧网络不兼容需fresh。

2026-10-17：[wall5地面拾箱数据与全贴地reset](../docs/carrybox/wall5_ground_20261017/README.md)完成：独立ground_pickup profile保留13段（完整地面pickup03，排除高位01/02），原15段不变。reset70/30/0，箱底离地5mm、移除平台；全身碰撞验证后pickup仅采0–31帧。27项CPU、4环境全部32帧物理检查、PPO/AMP 2＋1轮及恢复通过，revision11；未启动正式训练或证明收敛。

2026-10-17 12:49 JST：[wall5拾取失败与reset核对](../docs/carrybox/wall5_pickup_reset_20261017/README.md)：旧revision9日志止于20786轮，近100轮约556步，loco累计成功0；AMP占净混合奖励约91.7%，稳定抓握奖励近零。核对了60/30/10参考初始化、pickup支撑台与地面起点差异、28.65°横滚终止及成功不reset。当前无CarryBox训练进程，revision10全身碰撞尚未正式训练；CPU只读审计通过，未改参或重启。

2026-10-17：[wall5全身碰撞与结构可视化](../docs/carrybox/wall5_fullbody_20261017/README.md)完成：新增7处、替换肩/小腿6处，35个实体连杆全覆盖；PhysX实测shape30→35，13处接触探针、质量/惯量/深度不变及4环境回放/新契约恢复通过。可交互HTML与四视图PNG已保存。wall5升revision10，旧revision9仅显式weights-only迁移；自碰撞仍关闭，未启动正式训练或验证收敛。

2026-10-17：[wall5 G1碰撞体核对](../docs/carrybox/wall5_collision_20261017/README.md)：离线USD＋原生成函数确认28个带碰撞link、26个凸包Mesh＋4个膝部Cube；双手为凸包、头部无独立碰撞体。物理自碰撞关闭，Warp视觉自遮挡保留。仅审计，未改资产/配置/训练。

2026-10-16 21:57 JST：[wall5回合长度诊断](../docs/carrybox/wall5_length_20261016/README.md)：约7396轮、近100轮290步；model7200的16环境四组纯推理显示，有push时采样/均值动作约277/240步，无push约531/546步。全部loco成功0，无push仍经常远离箱子；AMP约占净混合奖励75%，旧普遍3步reset未复现。两条诊断命令通过，未改参或停止/重启正式训练；短测不代表正式成功率。

2026-10-16：[Kickball / CarryBox相机交叉核对](../docs/carrybox/camera_crosscheck_20261016/README.md)：两训练线名义安装匹配官方G1 rev_1_0，但足球v4/v5与wall3–5仍是58°垂直FOV；官方图示55.2°目前仅在足球部分MuJoCo路径应用。v4无自遮挡，v5/wall有现有场景遮挡；实机标定、训练/s2s profile和时序对齐待完成。本次仅审计，未改生产配置或进程。

2026-10-16：[足球s2s官方G1相机对齐](../docs/agilekickball_v5/official_g1_camera_20261016/README.md)完成：官方D435i例程640×480 Z16/60fps、图示55.2°/下俯47.6°，物理tick绝对相位采集，50Hz策略取最新帧。31项检查、2秒100控制步/121采集与独立审计通过，漏采0；旧v5训练profile及checkpoint契约保留，名义K不标实测。

2026-10-16：[足球s2s完整场景深度](../docs/agilekickball_v5/sim2sim_scene_20261016/README.md)完成：默认scene光轴Z、完整机身/地面/环境最近表面，复用v5相机profile与严格契约；28项检查（含GUI、遮挡/动态物体/采集保持）及100步CPU闭环/20帧视频通过。旧v4权重仅作分布变化诊断；实机标定和任务稳定性待验证，未启动训练。

2026-10-16：[wall5早期AMP占比核对](../docs/carrybox/wall5_start_20261016/README.md#amp早期占比核对第5574轮)：第55–74轮AMP占净混合奖励约47.3%，style0.098、D expert/policy loss0.0198/0.0669、有效率100%，量级符合差异文档X2参考；仍以倾倒结束、拾箱成功0，尚不能判断收敛；只读检查，未改参或重启。

2026-10-16 13:49 JST：[wall5正式训练启动核验](../docs/carrybox/wall5_start_20261016/README.md)：用户启动PID2996727，4096环境、40000轮、fresh；已完成第12轮，热身后10轮平均4.244秒、最慢4.36秒。model_0为schema2/revision9/35维AMP/15段数据，策略与D有限且优化器有更新，AMP有效率100%；训练进行中，未证明收敛。

2026-10-16：[新增wall5：X2/G1差异文档的AMP阶段A](../docs/carrybox/wall5_20261016/README.md)。基于wall4 revision8，AMP改为每步上限0.125、35维原始本体特征、D正则化与较低学习率、reset首步参与奖励和更新。PPO/深度/任务几何保持；50项CPU、4环境3＋1轮恢复导出通过。未正式训练或验证收敛/4096耗时；12:35 JST原wall4 PID2660033仍运行。

2026-10-15：[足球快球跌倒诊断](../docs/agilekickball_v4/speed_fall_20261015/README.md)完成：固定场景4/6m/s复现；4m/s无球机器人碰撞仍1.60秒跌倒，单独恢复训练hip-roll上限也未修复。接触前抬腿限幅及踢后支撑恢复失稳已取证；训练速度课程已到6m/s。8项接口检查与CPU诊断通过，不等于策略稳定；未改生产控制器或训练。

2026-10-15 13:10 JST：[G1站立reset排查、接地修复与wall4正式重启](../docs/carrybox/g1_reset_20261015/README.md)：旧model_14000真实横滚超限（1600回合均3步）；另修复G1参考初始化脚底穿地，wall3/wall4共同revision8按实际足部碰撞几何补足5mm间隙。G1相机位姿/身体与障碍遮挡、44项CPU、16环境更新恢复导出、4096验收通过。新wall4 PID2660033，4096环境fresh、核验iteration12，正式热身平均4.238秒/轮、最慢4.33秒；训练进行中，未证明收敛。

2026-10-15：[足球s2s球/深度一致性核对](../docs/agilekickball_v4/sim2sim_parity_20261015/README.md)完成：球0.43kg/0.11m一致；相机非单位四元数逆变换已修，384姿态命中mask零差异、最大误差0.0166mm，12项检查与两次10秒闭环通过。球阻尼/接触及G1质量、力矩、相机基准仍有差异，未证明接球改善或稳定迁移。

2026-10-15：新增[旧wall4模型显式仅权重播放](../docs/carrybox/play_v6_20261015/README.md)，model_14000在当前revision7环境的4环境命令已提供；实际权重CPU兼容检查通过，未启动GUI或训练。默认严格恢复规则保留。

2026-10-15：[wall3/wall4公共修复与正式命令](../docs/carrybox/wall_parity_20261015/README.md)：revision7统一实际头部COM、膝限位惩罚、物理动作目标裁剪、RSI60/30/10、搜索/yaw/推扰课程及训练配方。默认wall3仅墙，wall4墙加3圆柱，其他行为一致；41项CPU及两任务4环境更新/恢复/导出通过。未启动新版正式训练，未证明收敛；旧wall4 PID2448113仍使用revision6。

2026-10-15：[wall4不收敛诊断](../docs/carrybox/convergence_20261015/README.md)：13691轮快照及16环境纯推理确认行走起点约3步倾倒，保持reset角约39步；直接抱箱轨迹占有效样本；发现head_link腰部原点误作头部高度及专家膝角与软限位惩罚冲突。仅关闭push未修复，AMP训练style近零。已完成诊断，生产修复待做；PID2448113保持运行，未修改或重启训练。

2026-10-15：足球MuJoCo深度窗口新增球速滑块、立即应用与重新发球，显示设定/实际水平速度；8项原检查和4项新增检查（含实际GUI交互100步）通过。[使用方式与证据](../docs/agilekickball_v4/sim2sim_20261014/README.md)。仅接口验证，未形成稳定迁移或真机结论。

2026-10-14 21:13 JST：[wall4 handoff修订与新版AMP重启](../docs/carrybox/handoff_20261014/README.md)：完整X2奖励/G1适配、RSI80/0/20、双向roll、深度/物理随机化及wall动作范围修复完成；35项CPU、4环境更新/恢复/导出及4096完整更新通过（平均4.295秒、最慢4.318秒）。旧PID2348537已停止，新PID2448113已核验到iteration30，正式热身后平均4.230秒、最慢4.300秒，首个checkpoint schema2/revision6及15段AMP身份一致；15段AMP，旧model_4200仅作权重迁移。未证明收敛。

2026-10-14 20:46 JST：CB-017[新版AMP默认配置复核](../docs/carrybox/amp_default_20261014/README.md)通过，基线/wall3/wall4及RSI均用规范15段；两组CPU PASS。当前旧wall4进程model_4000.pt仍记录17段，未切换正式训练。

2026-10-14：FB-006补充实时深度窗口，MuJoCo图形启动默认启用；真实桌面双窗口短测通过，未改变策略/训练。

2026-10-14：FB-006足球MuJoCo深度可视化完成，[12秒策略输入视频](../docs/agilekickball_v4/sim2sim_20261014/depth_visualization/depth.mp4)及原始深度已保存；未改变控制或训练。

2026-10-14更新：FB-004足球MuJoCo部署接口实现完成，官方仓库同步、G1编译及8项CPU/500步闭环通过；FB-005接球回传稳定迁移待完成，60秒训练步长诊断出现1次跌倒。未启动训练或真机。[s2s记录](../docs/agilekickball_v4/sim2sim_20261014/README.md)。

更新时间：2026-10-15 13:10（G1接地适配修复，wall4 revision8正式启动，Asia/Tokyo）。项目管理员：用户；具体开发与验证结果写入对应项目记录。

本仓库维护两个独立任务，共享G1资产、Isaac Lab运行环境和通用训练入口。`findbox`与`football`是并列项目标识；源码和已有产物保留稳定路径，由各项目入口统一索引。

## 并列项目入口

| 项目 | 入口目录 | 范围 |
|---|---|---|
| `findbox` | [findbox/](findbox/README.md) | 深度找箱、抬起保持、位姿辅助监督、FindBox AMP及walled变体 |
| `football` | [football/](football/README.md) | AgileKickball接球、回传和恢复站稳 |

`carrybox → findbox`是旧文档入口的兼容符号链接，不是第三条项目线。根目录`findbox/`保留旧命名数据快照；当前规范数据在Python包`assets/motions/findbox/`，与足球`kick/`并列。现有`carrybox_*`源码、`CarryBox`任务ID、CB任务编号和`carrybox-*`工程记录均归属findbox，保留原名以兼容已有引用。共享的`source/`、`scripts/`、`tests/`与资产不归属于任一任务的子目录；具体模块归属由下表和各入口索引。

## 当前工作

| 编号 | 项目 | 工作项 | 状态 | 验收或下一步 |
|---|---|---|---|---|
| FB-001 | [足球](football/README.md) | v4回传任务实现与工程验证 | 完成 | 已有状态回归、真实仿真及4096环境短训记录 |
| FB-002 | 足球 | v4正式训练至50000次迭代 | 完成 | 最终model_49999.pt、日志49999/50000及进程退出已核验；独立评估待做 |
| FB-004 | 足球 | v5场景光轴深度与机器人自遮挡 | 仿真通过；实机待标定 | [继承v4回传/AMP，独立ID和深度契约](../docs/agilekickball_v5/README.md)；历史4环境更新/恢复/导出、18组遮挡对照通过；10月17日已有正式run，22:35复查进程已退出，未证明训练完成或收敛 |
| FB-007 | 足球 | v5 Kp/Kd与深度训练随机化 | 已按要求默认关闭 | [10月17日关闭记录](../docs/agilekickball_v5/no_randomization_20261017/README.md)；保留显式开关兼容旧模型，历史随机化短测保留，新默认配方未启动训练 |
| FB-003 | 足球 | 固定球速和固定±0.2m目标门的独立评估 | 待开始 | 分开报告回传命中、恢复站稳及失败情况 |
| CB-001 | [搬箱子](findbox/README.md) | 真实深度拾箱、无特权actor/critic、位姿辅助头 | 完成 | CPU与真实仿真管线通过 |
| CB-002 | 搬箱子 | FindBox动作数据接入AMP | 完成 | 初次17段接入及PPO/AMP更新、恢复/导出已通过；当前15段修订见CB-016 |
| CB-003 | 搬箱子 | 正式训练 | revision14已退出，未完成 | 2026-10-19核验PID4038923已不存在，日志止于11304轮；[loco约10.6步倾倒诊断](../docs/carrybox/wall5_loco_early_20261019/README.md)完成，控制/训练修复待做，revision15未正式训练；退出原因未知 |
| CB-011 | 搬箱子 | 不收敛根因诊断与跌倒奖励修复 | 完成 | [历史终止标记跨回合漏罚已修，21项CPU与真实回放通过；新重训见CB-003](../docs/carrybox/convergence_20261014/README.md) |
| CB-015 | 搬箱子 | G1/X2深度后端与计时核对 | 完成 | [同源码profile分项](../docs/carrybox/depth_timing_20261014/README.md)：本地为RTX，Warp后端未迁移；无新增GPU试验，正式训练继续 |
| CB-014 | 搬箱子 | 4096完整迭代≤6秒 | 完成 | [Warp动态43几何迁移](../docs/carrybox/warp_20261014/README.md)：RTX差异≤0.164mm，24项CPU/碰撞/完整更新恢复通过；正式热身后均值4.023秒、最慢4.078秒 |
| CB-013 | 搬箱子 | 4096相机位姿读取性能优化 | 完成 | 同规模环境步减少23.2%，22项CPU/真实几何/4096更新恢复通过；正式训练继续 |
| CB-012 | 搬箱子 | RSI动作范围对齐与基础技能验证 | 部分完成 | [wall专属clip9已覆盖全部15段及默认角扰动](../docs/carrybox/handoff_20261014/README.md)；独立基础技能评估待做 |
| CB-018 | 搬箱子 | wall4分技能失败与AMP/奖励冲突诊断 | 诊断完成；修复见CB-019 | [日志、纯推理、实际USD软限位证据](../docs/carrybox/convergence_20261015/README.md)；未改变正式训练 |
| CB-019 | 搬箱子 | wall3/wall4共用修复、仅障碍不同 | 实现与短测完成 | [revision7与4096环境正式命令](../docs/carrybox/wall_parity_20261015/README.md)；41项CPU、两任务更新恢复导出通过；未启动新版正式训练、未验证收敛 |
| CB-020 | 搬箱子 | G1站立reset/相机/构型复核与正式重启 | 实现/验收/启动完成 | [revision8接地适配](../docs/carrybox/g1_reset_20261015/README.md)，旧策略倾倒与脚底穿地分别取证；实机光心标定及独立收敛评估待做 |
| CB-021 | 搬箱子 | wall5 AMP阶段A对照任务 | 实现/短测完成 | [50项CPU、4环境3＋1轮更新恢复及导出通过](../docs/carrybox/wall5_20261016/README.md)；保留wall4，wall5未正式启动、未验证收敛或4096速度 |
| CB-004 | 搬箱子 | 独立拾箱成功率评估 | 待开始 | 使用双手接触+离地+持续保持的任务成功判据 |
| CB-008 | findbox / football | 深度安装与遮挡管线核对 | 完成 | [FindBox三变体RTX遮挡通过；Football解析深度无场景遮挡；实机标定待提供](../docs/carrybox/depth_audit/README.md) |
| CB-006 | 搬箱子 | G1 FindBox walled3/walled4迁移 | 完成 | [19项CPU、两变体4环境20＋2轮、wall4 128环境50＋2轮及真实碰撞/遮挡通过](../docs/carrybox/wall4_repair/README.md) |
| CB-005 | 搬箱子 | FindBox动作可视化 | 完成 | [当前wall5的13段/63.08秒/60fps](../outputs/carrybox/wall5_amp_20261018/index.html)，源hash/完整解码通过；[其他变体的15段录像](../outputs/carrybox/findbox_hold_20261014/README.md)和旧17段保留 |
| CB-016 | 搬箱子 | carrywith1开头抱箱延长与AMP整理 | 完成 | [原0–20帧保留、重复第20帧至5秒](../docs/carrybox/amp_hold_20261014/README.md)；有效11/3/1共15段，旧17段全量备份，AMP/RSI检查通过；未切换正式训练 |
| CB-017 | 搬箱子 | AMP数据规范命名与kick并列存放 | 完成 | [assets/motions/findbox规范目录](../source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md)；15段字节不变，AMP/RSI默认一致、CPU检查通过；旧路径保留，未切换训练 |

“完成”描述该工作项的工程验收；短仿真通过不等于策略已学会任务。正式训练进度和评估结果分别记录。

CB-009：2026-10-13首次登记的[football→wall4等待](../docs/carrybox/wall4_queue/README.md)曾被GPU故障阻塞，该页保留历史证据。CB-010已完成[运行修复、正式规模验收及队列重新登记](../docs/carrybox/wall4_repair/README.md)。

CB-007：2026-10-13完成项目入口整理，findbox与football并列；兼容旧入口，未移动数据、模型或源码。此次整理没有更新训练运行状态，未解决CB-006的GPU故障。

## 资源归属

| 资源 | football | findbox |
|---|---|---|
| 主任务ID | `Template-Perceptual-Ball-AgileKickball-v4` | `Template-Perceptual-Ball-CarryBox-v0` |
| 数据 | `assets/motions/kick/`、`unitree_g1_retarget/` | `assets/motions/findbox/`；默认行走/拾起/抱箱40/40/20%，根findbox为兼容快照 |
| 正式输出 | `logs/rsl_rl/agilekickball_v4/` | `logs/rsl_rl/g1_carrybox_depth/` |
| 设计与验证 | `docs/agilekickball_v4/` | `docs/carrybox/` |
| 工程工件前缀 | `agilekickball-*` | `carrybox-*` |
| 主要测试 | `test_agilekickball_v4.py`、`test_state_feedback.py` | `test_carrybox.py`、`test_carrybox_amp.py`、`test_carrybox_walled.py` |

`assets/`路径相对于`source/perceptual_ball/perceptual_ball/`。足球历史输出按原版本目录保留；`*_smoke`、`docs/**/smoke_model.pt`属于验证产物。

## 每次工作的记录方式

1. 确定所属项目及看板工作项；涉及共享代码时标明两条任务的影响。
2. 实现和验证使用对应项目的数据、task ID和checkpoint版本，产物进入该项目目录。
3. 更新项目入口的状态日期、验收证据、下一步；长期训练启动或结束后记录run目录和checkpoint。
4. 在`agent/`沿用对应任务前缀保存需要的工程交接，随后更新本看板。

状态统一使用“待开始 / 进行中 / 完成 / 阻塞 / 历史”。阻塞项需记录具体原因和恢复条件。PID和迭代数只是检查时快照；判断当前运行状态时重新读取进程与日志。

## 共享改动和运行边界

共享G1资产、CNN编码器、AMP判别器、train/play入口及导出器的改动，需要检查另一任务是否受影响。专项改动优先放在各任务自己的模块。两条任务checkpoint分别管理；足球v3→v4使用显式warm start，CarryBox当前schema=2含AMP训练状态。

项目管理工作只更新索引与记录。训练的启动、停止、恢复和资源分配按用户的实际任务指令执行；整理目录时保留已有训练进程、checkpoint、数据和历史证据。
