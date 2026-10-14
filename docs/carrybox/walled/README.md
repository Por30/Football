# G1 FindBox walled3 / walled4

2026-10-14最新：正式训练与队列已按用户要求停止。已发现并修复跨回合跌倒惩罚泄漏，环境契约revision=4；动作范围/拾取参考不匹配仍待处理。21项CPU及真实回放通过，不代表收敛；见[不收敛诊断与完整当前设计](../convergence_20261014/README.md)。下文10月13日GPU验收为历史运行证据。

迁移依据是用户提供的 X2 复现说明。本机未找到所述 X2 任务源码，因此这是**在本地 G1 CarryBox 基线上按说明迁移**，不是 X2 父任务完整奖励的逐行复刻。新增配置逐层继承：`CarryBoxEnvCfg → CarryBoxWalled3EnvCfg → CarryBoxWalled4EnvCfg`。原 CarryBox-v0 和足球主线保留。

| 版本 | Gym ID | 正式输出根目录 |
|---|---|---|
| 基线 | `Template-Perceptual-Ball-CarryBox-v0` | `logs/rsl_rl/g1_carrybox_depth/` |
| wall3 | `Template-Perceptual-Ball-CarryBox-Walled3-v0` | `logs/rsl_rl/g1_carrybox_depth/walled3/` |
| wall4 | `Template-Perceptual-Ball-CarryBox-Walled4-v0` | `logs/rsl_rl/g1_carrybox_depth/walled4/` |

## 验收状态（2026-10-13）

2026-10-13运行修复已通过wall3/wall4的4环境几何验收，以及各20轮PPO/AMP＋恢复后2轮训练。墙柱真实碰撞与RTX遮挡一致，平台重置冲量已消除；128环境验收正在执行。最新状态、根因证据及完整回执见[运行修复记录](../wall4_repair/README.md)。此前CUDA700失败日志保留为历史，不能作为当前状态。

## 观测与网络输出

下列维度不含 batch/environment 维度。wall3/wall4 完全一致；基线深度高度仍为32。

| 通道 | 组成、形状 | 用途 |
|---|---|---|
| `proprio` | 每帧角速度3（×0.25）、重力方向3、关节相对默认角29、关节相对默认速度29（×0.05）、上一动作29，共93；4帧展平 **372** | actor与critic |
| `perception` | 光轴深度48×27；4帧 **4×27×48**；范围0.1–3m，除以3归一化，非法/无返回取最远距离 | actor与critic共享CNN |
| `box_pose_target` | 相机ROS光学坐标系位置xyz（米）+旋转矩阵前两列6D，共 **9** | 仅辅助监督 |
| `amp` | 绝对关节角29、关节速度29、重力方向3、本体角速度3；10帧 **640** | 仅AMP判别器与风格奖励 |

CNN把4帧深度编码为128维。actor、critic各自的MLP输入都是372+128=500维。actor输出29维关节目标偏移，实际目标为默认角+0.25×动作，动作裁剪±5；critic输出一个价值标量。辅助头只从深度latent预测9维位姿，并不把预测值单独回灌actor。训练时共享编码器接收PPO和辅助损失；位置MSE与考虑正方形箱体D4对称性的旋转6D损失合并，辅助权重0.5。

箱子真值、search标记、初始化技能、yaw课程值、接触力和任务阶段都不进入actor/critic。AMP也不含箱子、root位置或root线速度。标签随深度采集时刻配对，延迟/冻结同步；部分环境reset只清空这些环境的历史，terminal深度和AMP窗口保留用于正确bootstrap及判别。

## 物理任务与场景

G1原有29关节、visual及PD控制不变；walled场景内四个肩部碰撞圆柱改为同尺寸凸包，共享资产文件未改，物理dt=0.005s，decimation=4，控制50Hz。回合20秒。固定箱体0.30×0.30×0.25m、1.125kg。任务仍是找箱、接近、双手接触、抬起保持，没有搬运目的地或放下阶段。

loco箱子在root前方±45°、0.7–2m；随机roll/pitch各±30°，yaw按课程采样，使用旋转后最低点对齐地面。墙尺寸0.2×8×3m，中心半径3–4m、全圆bearing，长面朝机器人。3个圆柱半径0.15m、高1.8m，中心z=0.9m，独立半径2.2–3.2m、全圆bearing；墙柱和平台采用禁重力、平移/旋转六轴锁定刚体，reset通过tensor写位姿和零速度，回合内静止、可碰撞。此为本机4.5对运动学重置冲量及静态USD碰撞不同步的兼容实现。环境间距13m，可视地面300×300m。

深度使用本项目真实RTX TiledCamera，因此所有墙、柱、平台和箱体的渲染几何自动遮挡；不需要X2 ray caster的target字符串列表。墙中心可能在3m量程之外，部分回合墙不可见是正常裁剪。相机保留G1头部D435安装位置与47.6°下俯角，调整为48×27、垂直58°、每0.02s更新。圆柱采用同半径/高度的32边圆柱网格与convexHull碰撞：早期仅替换场景圆柱没有解决CUDA700；本次进一步替换实例内部的四个G1肩部碰撞圆柱后，持续训练通过。

用户说明没有传感器扰动幅度，本地显式选择：每回合安装平移各轴±5mm、转角各轴±2°；深度逐像素高斯噪声σ=1cm；延迟均匀0–2控制步；可交付帧以1%概率触发后续1–3步冻结。reset不继承上一回合冻结。以上可在变体配置中调整，恢复checkpoint会校验这些参数。

## 初始化、AMP与数据边界

每回合参考初始化技能概率为loco 80%、pickUp 15%、carryWith 5%。组内均匀抽片段、均匀抽原始帧，按关节名映射到G1；原始60Hz动作重建关节/角速度。root高度使用`base_height+0.05m`校正地面，移除参考root yaw，保留roll/pitch与本体姿态。

数据的`box_pos_local`是**世界朝向的root相对位移**，随相同yaw变换移动。原数据没有箱子四元数/支撑台模型，因此pickup/carry使用机器人yaw作为箱子姿态代理，并保持直立以保留参考手位；**yaw/tilt课程仅作用于loco普通箱子初始化**。pickup平台使用contact_index估计支撑高度并限制在采样箱子最低点下方；它是G1适配假设，不是从数据读取的真实平台。reset顺序为机器人/RSI→箱子/平台→墙→圆柱→相机/历史。

AMP仍读取根目录`findbox/`，17片段/4628帧，专家组权重为loco/pickup/carry **40/40/20%**。这和reset技能80/15/5%是不同概率。10帧窗口按60→50Hz重采样，reset后未积满的窗口不计AMP。完整窗口奖励混合为`0.75*任务奖励 + 0.25*2*0.02*风格奖励`。本地没有putDown参考，未伪造或引入旧assets副本。

## 奖励、课程与终止

父奖励沿用本地G1基线：接近1、双手靠近2、接触后离地6、成功100、动作变化-0.02、关节加速度L2 -1e-7、力矩L2 -1e-5、关节限位-5、当前失败事件-10（仅该transition，已修复历史终止标记泄漏）。Isaac Lab把各项乘以0.02s；成功奖励每回合仅一次，AMP混合前为+2。

成功要求双手与箱子接触均>1N、旋转后最低点离地≥0.12m、箱子局部Z与世界Z余弦>0.9、箱子线速度<0.25m/s，连续保持0.5秒。成功用于统计/一次奖励，**不终止回合**。RSI持箱初始化可能较快达到该条件，所以训练成功统计不能作为从地面自主找箱的独立成功率。

wall3新增held双臂速度/加速度excess平方均值惩罚：阈值1rad/s、20rad/s²，权重-0.02、-0.00002；双臂为14个shoulder/elbow/wrist关节。门控为箱子中心高度>0.55m且双手中心距箱心<0.15m。waist yaw相对默认角L1惩罚权重-0.5。没有applied-torque-limit或“1.5倍放宽”项；普通力矩L2保留。

wall3 yaw上限10°→180°，8000有效iteration线性增长。wall4替换为锚点(0,0°)、(10000,10°)、(20000,30°)、(30000,180°)，分段线性插值。只有runner真正开始learn才建立课程锚点，构造/播放阶段返回初值；PPO每次update后推进。按照本次迁移的进程锚点语义，**重新启动训练进程（包括resume）重新走yaw课程**，不会直接按checkpoint绝对iter跳级。checkpoint保存环境契约，统计记录`Curriculum/box_yaw_range_deg`。

wall4另对本回合loco环境以2%概率将箱子置于±[60°,180°)方位、0.9–2m，平台XY同步，每回合清空search标记。仅search标记、角度误差>45°且距离>0.7m时奖励：

`search_turn = 0.7*exp(-0.75*abs(error)) + 0.3*tanh(max(sign(error)*body_yaw_rate,0))`

权重+0.5，无独立搜索状态机或避障奖励。进入视野后继续原接近/拾起流程。按用户文字原样实现终止：超时、**有符号roll>0.5**、|pitch|>1.1、root高度<0.2m或G1 `head_link`高度<0.4m；未擅自改为|roll|。非有限状态直接报错停止，避免污染训练。

## 启动、恢复与迁移

以下为手动训练配方。当前用户要求保持停止，后台队列已退出；这些是配方文档，不表示本轮授权恢复训练。

```bash
cd /home/cao/perceptual_ball
# 默认wall4，从头训练；脚本配置本机Isaac环境
bash scripts/rsl_rl/train_carrybox_walled.sh --max_iterations 40000 --run_name walled4_scratch

# wall3
CARRYBOX_VARIANT=3 bash scripts/rsl_rl/train_carrybox_walled.sh --max_iterations 30000 --run_name walled3_scratch

# 同任务/同环境契约完整恢复，PPO和AMP状态恢复；yaw按新进程锚点重启
bash scripts/rsl_rl/train_carrybox_walled.sh --resume --checkpoint /absolute/path/to/walled4/model.pt

# wall3 -> wall4显式迁移：复制encoder/actor/critic/pose head，PPO、AMP与课程从头开始
bash scripts/rsl_rl/train_carrybox_walled.sh --warm_start_carrybox /absolute/path/to/walled3/model.pt --run_name walled4_from_walled3
```

默认128环境、seed42、CUDA:0，必须保留真实相机选项`--enable_cameras`（脚本已设置）。4环境持续短训已通过，128环境50＋2轮验收及后台队列见最新运行修复记录；当前football仍使用CUDA:0，正式wall4必须等它完成。

仍是checkpoint schema=2，新增`environment_contract`阻止隐式跨变体/传感器配置加载。原基线schema2不含该键仍可按原ID恢复；迁入wall变体须显式warm-start且模型形状匹配。播放wall变体默认含RSI reset，因此需要findbox；部署导出的actor只需深度与本体，不需要标签或数据集。未训练时播放默认yaw初值，如需满难度评估应在评估脚本显式设置课程迭代和纯loco初始化。

## 工程验证

冻结命令：

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p 'test_carrybox*.py' -v
bash scripts/rsl_rl/validate_carrybox_runtime.sh
```

最新结果以`../wall4_repair/test_receipts_attempt*.json`及`walled3/`、`walled4/`、`scale128/`报告为准；本目录旧回执为历史迁移失败记录。所有模型位于docs，只是管线验证。短测不证明已学会找箱/拾箱，不代替独立评估。完整代码入口为`carrybox_walled_env_cfg.py`、`mdp/carrybox_walled.py`和纯张量辅助`perceptual_ball/carrybox_walled.py`。

## 两条项目线的接口对照

足球AgileKickball-v4保持独立配置：actor读取108维本体的8帧历史（864）和8×27×48解析深度；108维包含本体基础93维和5个末端位置15维。critic读取本体108、root线速度3、球相对位置/速度6，共117维。足球AMP为10×60=600，球预测头输出6维状态均值及6维log标准差并用于受限动作反馈；最终输出同为29维关节目标偏移。其任务是接球→回传本轮发球者→恢复站稳后再发球，保留既有critic特权接口。

搬箱子则使用真实RTX深度，actor与critic对称，无球/箱真值输入，辅助头输出9维箱子位姿，AMP为纯本体640维。两者共享G1资产和训练工具，但数据、奖励、checkpoint契约、日志目录独立。
