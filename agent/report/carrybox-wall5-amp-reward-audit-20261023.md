---
task_id: "carrybox-wall5-amp-reward-audit-20261023"
language: "zh-CN"
axes: ["L", "C", "E"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-amp-reward-audit-20261023.md", "agent/plan/carrybox-wall5-amp-reward-audit-20261023.md", "agent/report/carrybox-wall5-amp-reward-audit-20261023.md", "agent/task/carrybox-wall5-amp-reward-audit-20261023.md", "docs/carrybox/wall5_amp_reward_audit_20261023/README.md", "docs/carrybox/wall5_amp_reward_audit_20261023/analysis.json", "docs/carrybox/wall5_amp_reward_audit_20261023/analyze.py", "docs/carrybox/wall5_amp_reward_audit_20261023/analyze_attempt1.py", "docs/carrybox/wall5_amp_reward_audit_20261023/analyze_retry.log", "docs/carrybox/wall5_amp_reward_audit_20261023/artifact_validation.json", "docs/carrybox/wall5_amp_reward_audit_20261023/attempt1/current_initial.pt", "docs/carrybox/wall5_amp_reward_audit_20261023/attempt1/current_physical.npz", "docs/carrybox/wall5_amp_reward_audit_20261023/attempt1/current_trajectory.npz", "docs/carrybox/wall5_amp_reward_audit_20261023/attempt1/probe.py", "docs/carrybox/wall5_amp_reward_audit_20261023/attempt1/probe.sh", "docs/carrybox/wall5_amp_reward_audit_20261023/attempt1/probe_current.log", "docs/carrybox/wall5_amp_reward_audit_20261023/attempt1/receipts.json", "docs/carrybox/wall5_amp_reward_audit_20261023/cpu_retry_receipts.json", "docs/carrybox/wall5_amp_reward_audit_20261023/cpu_retry_task.md", "docs/carrybox/wall5_amp_reward_audit_20261023/current.json", "docs/carrybox/wall5_amp_reward_audit_20261023/current_curve.json", "docs/carrybox/wall5_amp_reward_audit_20261023/current_initial.pt", "docs/carrybox/wall5_amp_reward_audit_20261023/current_physical.npz", "docs/carrybox/wall5_amp_reward_audit_20261023/current_trajectory.npz", "docs/carrybox/wall5_amp_reward_audit_20261023/current_video_frames.jpg", "docs/carrybox/wall5_amp_reward_audit_20261023/evidence.png", "docs/carrybox/wall5_amp_reward_audit_20261023/expert_brief.json", "docs/carrybox/wall5_amp_reward_audit_20261023/findings.md", "docs/carrybox/wall5_amp_reward_audit_20261023/finish.py", "docs/carrybox/wall5_amp_reward_audit_20261023/formal_status.json", "docs/carrybox/wall5_amp_reward_audit_20261023/no_delay.json", "docs/carrybox/wall5_amp_reward_audit_20261023/no_delay_initial.pt", "docs/carrybox/wall5_amp_reward_audit_20261023/no_delay_physical.npz", "docs/carrybox/wall5_amp_reward_audit_20261023/no_delay_trajectory.npz", "docs/carrybox/wall5_amp_reward_audit_20261023/old_curve.json", "docs/carrybox/wall5_amp_reward_audit_20261023/old_video_frames.jpg", "docs/carrybox/wall5_amp_reward_audit_20261023/probe.py", "docs/carrybox/wall5_amp_reward_audit_20261023/probe.sh", "docs/carrybox/wall5_amp_reward_audit_20261023/probe_current.log", "docs/carrybox/wall5_amp_reward_audit_20261023/probe_no_delay.log", "docs/carrybox/wall5_amp_reward_audit_20261023/probe_rev22.log", "docs/carrybox/wall5_amp_reward_audit_20261023/probe_summary.json", "docs/carrybox/wall5_amp_reward_audit_20261023/receipts.json", "docs/carrybox/wall5_amp_reward_audit_20261023/repair.md", "docs/carrybox/wall5_amp_reward_audit_20261023/rev22.json", "docs/carrybox/wall5_amp_reward_audit_20261023/rev22_initial.pt", "docs/carrybox/wall5_amp_reward_audit_20261023/rev22_physical.npz", "docs/carrybox/wall5_amp_reward_audit_20261023/rev22_trajectory.npz", "docs/carrybox/wall5_amp_reward_audit_20261023/selection.json", "docs/carrybox/wall5_amp_reward_audit_20261023/summarize.py", "docs/carrybox/wall5_amp_reward_audit_20261023/summary_replot.log", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "854f20bfde9bb2235cdf2fd99f32b4af776a8aafa5fcb4dfd4adf4336dd36909"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_amp_reward_audit_20261023/analyze.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "7da2975aff13cc827f1357215ac2d1ff70ef14ed448bd6ef75ab650504a0fcf8", "stdout_sha256": "241ad122d9c27bbe46ffafc3cba76e20d883b69063592037d1a9eff687c517ea", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_amp_reward_audit_20261023/probe.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8058a06480dfd233e2b0bc9653137eedfbc29e458eb548e17f582523b781d72a", "stdout_sha256": "5c11e1f77f9e311419cb9fbb2a94caffec59c864e99f6f20da2fba96fb278686", "stderr_sha256": "a090fe76f1c04dd8ca0468ba8d43656517a08e193b1165def23f1f7d3995a74c", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

rev22对照只读诊断：AMP实际更新/混合已核验；当前空手接近停滞、膝目标饱和和奖励衔接问题见证据。未改参数或重启，未将单项认定为唯一训练根因。

# Wall5 rev28 对照 rev22：AMP、接近停滞与奖励衔接

2026-10-23，只读诊断。核对用户指定rev22 model6400视频、当前rev28 model4800视频和两轮正式日志，并以32环境进行当前策略、旧策略权重、当前策略取消动作延迟三组20秒回放。所有初态（机器人/物体、PD/材质、延迟缓存、事件时钟及观测）匹配；使用同一当前AMP和冻结Normalizer统一评分。没有调整生产训练。

**用户指出的退化成立。** 指定旧视频的三个空手机器人在约2秒内到达骨盆距箱子水平0.26–0.32m。当前视频两个loco起点虽先移动约0.7m，之后停在约0.74–0.83m并往复摆动；默认站姿起点也未有效接近。之前仅用“有靠近”描述，容易让人误以为正在正常完成行走阶段，现予更正。两视频起点/课程不同，不能直接做单因素因果对照。

**AMP已接通、确实在训练，反馈对当前采样轨迹较弱。** model4800→5000中判别器optimizer步数96020→100020，参数变化L2=1.983，Normalizer计数196669440→204861440；不是仅有配置开关。仿真逐步执行实际`_process_amp`，验证终止AMP替换、全部样本有效和`mixed=0.75×task_raw+0.125×style`；任务weight×dt只应用一次。

以下为两次正式训练4700–4799轮平均。`loco`日志合并默认和行走起点，reset分布不同；AMP行是全体样本，不能当作单独loco分数。奖励单位为每个20ms控制步、已乘任务权重和dt、尚未乘0.75混合系数。

| 指标 | rev22 | rev28 |
|---|---:|---:|
| 空手walk | +0.02836 | +0.00533 |
| 空手carryup | +0.009992 | +0.000155 |
| 空手torques | −0.00796 | −0.01548 |
| 空手action_rate | −0.00921 | −0.01631 |
| 空手alive | 未注册 | +0.06000 |
| AMP style（全体） | 0.02294 | 0.02089 |
| AMP实际混合贡献（全体） | +0.00287 | +0.00261 |
| 整体mean episode length | 793.86 | 920.79 |

rev28全体AMP占净混合奖励约8.5%，不是此前历史版本的75%–93%。专家窗口style约0.9996–1.0，训练expert/policy loss约0.00076/0.00379，判别器很容易区分两类。但rev22能接近时style也低，不能仅凭低AMP分数确定退化原因。回放采用均值动作，分数高于训练采样动作；不可混用这两个分布的数值。

**分段奖励实际执行正确，但已经不再是原X2式走近后给满值的设计，衔接存在低谷。** rev23开始，walk的travel系数按水平距离0.80→0.60m从1降至0；reach按三维距离0.98→0.90m才逐渐开启。以站立骨盆高0.773m、地面箱中心高0.125m为例，reach到水平约0.735m才开始非零。因此进入0.8m后行走收益已经减少，伸手收益却尚未出现或很弱。

保持朝向正确、朝箱速度0.85m/s、上述高度差不变，当前walk的每步奖励在水平0.80/0.65/0.60/0.52m处分别约0.0300/0.00874/0.00256/0.00400；旧公式同条件为0.0300。此为公式切片，不包含力矩等成本或完整抓取收益。当前回放共同有效片段中reach门控有73.5%的时间为0，carryup仅0.000444/步，没有双手接触。

远处walk依赖瞬时朝箱速度，没有净距离减少项；正向运动获奖、反向运动接近零，往复摆动也能得分。alive延长回合的效果明显，但所有存活动作都获得它，不能只凭+0.06的大小宣称它单独导致不走。这些结构更支持“接近与伸手之间形成局部停滞”，尚未用单项重训证明唯一因果。

**同初态诊断确认原地运动，并排除部分过强归因。** 32环境中23个空手起点；下表取三组共同首回合前缀、去除前2秒和reset行，共7483个配对控制步样本，来自13个环境。样本按控制步平均；早结束环境的有效片段更短，不能代表全部23个起点都能生存到20秒。

| 配对片段指标 | 当前策略 | rev22策略放入当前场景 | 当前策略仅取消延迟 |
|---|---:|---:|---:|
| 水平距箱 m | 0.789 | 0.451 | 0.724 |
| 水平速度模长 m/s | 0.422 | 0.070 | 0.352 |
| 朝箱有符号速度 m/s | −0.0017 | +0.0226 | +0.0005 |
| 同一当前AMP的style | 0.189 | 0.352 | 0.222 |
| 完整mixed/步 | 0.0691 | 0.0857 | 0.0739 |
| 腿关节加速度RMS rad/s² | 84.96 | 78.99 | 71.65 |
| 左/右膝目标裁剪比例 | 98.3%/99.1% | 96.2%/96.8% | 99.1%/99.4% |

当前水平速度不低，朝箱净速度却近零，确实是往复运动。取消0–20ms物理动作延迟后加速度RMS下降15.7%、踝目标步间变化RMS从2.40°降至1.92°，但仍停滞且没有双手抓取。延迟是放大因素，单独取消没有解决任务。加速度包含运动和接触冲击，不是纯抖动指标。膝目标长期裁剪值得处理，但旧策略也大量裁剪；不能把它单独当作新退化原因，更不能把目标裁剪直接等同于实际关节限位碰撞。

同一当前判别器对更接近的旧策略评分更高，且上述配对片段的完整混合回报也更高。因此不能声称“AMP只奖励抽搐”或“整个目标必然更喜欢原地不动”。另一方面，旧策略在当前场景的23个空手首回合只有8个超时，其余12个倾倒、3个头过低；当前策略为21个超时、2个倾倒。旧策略转入新碰撞/reset/延迟场景有明显稳定性代价，不能直接替换旧权重并宣称已经修好。

![奖励曲线与配对轨迹](evidence.png)

图左只展示三组都活满20秒的8个空手起点，固定同一批环境避免提前终止造成均值跳变；这是选择后的行为展示，上述全部23个起点的失败数量必须一起看。右图为固定速度、朝向、高度差的walk函数切片，不代表完整优化目标。

**还发现阶段含义不一致。** 当前没有串行任务状态机，各项按不同几何条件并行相加：新carryup的lift要求双手接触，但继承的standup只看箱高、身体直立、头高和双手中点距离；继承的held_hand_speed/acc也没有双手接触门控。高处pickup参考/支撑平台可能触发这些项，因此“所有抬起/保持奖励都意味着已经抓住箱子”并不成立。这些问题不直接解释远箱空手抖动。接触力>1N处还存在奖励及平滑惩罚开关的跳变；本轮空手共同片段没有接触，不能把该跳变归因于眼前的原地摆动。

**建议优先修复范围：** 保留已验证的接地/reset修复，先统一接近与伸手的几何门控、消除0.8m到抓取站位间的收益低谷，并用净接近进度避免往复运动获得持续接近奖励；抓取/抬起/standup门控统一到实际双手接触和箱底离地。动作延迟及膝目标饱和单独验证，不与奖励、AMP权重、PD同时改。当前证据不支持单纯增加训练时间、调高PPO学习率或盲目放大AMP系数就能解决。

源码证据：`carrybox_wall5.py:33–68`（walk/reach/接触组合），`mdp/carrybox_wall5.py:55–98`（注册调用/接触平滑），`rsl_rl_extensions/carrybox_wall5.py:225–266`（AMP更新与混合），`mdp/carrybox_x2_rewards.py:48–55`（继承standup），`mdp/carrybox_walled.py:348–353`（继承held门控），均相对`source/perceptual_ball/perceptual_ball/`。具体奖励、checkpoint差异和所有原始回放数组保存在本目录。

所有诊断已完成；无待恢复进程。后续优化需要单独任务，保留此处原始证据。
