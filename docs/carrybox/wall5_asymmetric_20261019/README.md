# Wall5非对称Actor–Critic与正式重启（2026-10-19）

用户明确要求仅critic使用特权信息。wall5已升级revision14，actor及部署接口保持深度与本体；critic独立MLP，无深度输入，也不向深度CNN反传value loss。

| 分支 | 实际输入 | 网络 |
|---|---|---|
| Actor | 4帧本体93×4=372；4帧27×48深度 | 原CNN输出128，与本体拼成500；MLP512/256/256→29动作 |
| Critic | 当前本体93＋机体线速度3＋箱子相对位置3＋相对旋转6＋完整尺寸3=108 | 独立MLP108→512→256→256→1 |
| 辅助位姿头 | actor深度latent128 | 原9维位姿预测，保留可见性配对mask及coef0.1 |

本体93为角速度3（×0.25）、投影重力3、关节位置偏差29、关节速度偏差29（×0.05）、上一动作29。critic用当前帧；actor保持4帧历史，不含线速度。critic新增速度为pelvis link原点的机体系速度m/s；箱子位置为同坐标系米制相对位置，旋转为pelvis逆姿态乘箱子姿态的旋转矩阵前两列，尺寸为箱子局部完整边长（当前0.30×0.30×0.25m）。critic真值不施加相机遮挡、延迟或AMP的0.7m截断；这些真值不会进入actor、pose head输入或部署导出。

只修改三个wall5生产文件。新增critic_state观测、独立critic类、PPO快路和reset前critic快照；timeout bootstrap取本回合终止状态，避免使用重置后的箱子/机器人状态。新模型环境契约为schema2/revision14，旧revision13完整resume及完整权重warm-start因critic形状/契约变化不兼容；本次按用户要求fresh。

AMP仍为ground_pickup的13段、60维×10窗口、running normalization；AMP采样40/40/20，RSI80/0/20，奖励/PPO超参/深度/全身碰撞均保持。wall3/wall4、CarryBox-v0和football生产接口未改。

验证：31项CPU通过（含6项非对称专用检查）；4环境真实PPO/AMP完整配方2＋恢复1轮通过，含强制timeout、部分reset、终止快照、有限更新、严格恢复、TorchScript/ONNX导出与wall4配置隔离。正式4096检查于2026-10-19T00:42:58.492209+09:00通过：迭代0→15，最近10轮平均3.813秒，最慢3.830秒。

旧PID3812053已停止，旧模型保留至`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_13-10-42_wall5_v13_perf_fresh_20261018_131037/model_10600.pt`。新PID4038923，4096环境、seed42、40000轮、从零初始化；首model_0中PPO/AMP优化器均step20，AMP Normalizer count61440，确认没有继承旧训练状态。训练已启动，尚无收敛结论。

新run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706`

```bash
tail -f '/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v14_asymmetric_fresh_20261019_003706.log'
```

启动过程中旧进程退出后的GPU显存释放有短暂延迟，复查空闲后才启动。首个新进程因未加载Isaac Sim环境在导入阶段退出、没有训练迭代；补齐显式setup_conda_env.sh及导入预检后启动当前run。失败回执、日志和诊断均保留，没有盲目循环重启。CPU首次检查仅测试脚本误用元数据键num_clips，修正为实际clip_count后通过，原失败记录保留。

证据：production_changes.json记录三个生产文件hash；expert_review.md为独立只读审查；receipts.json为三条冻结命令最终回执，smoke.json为真实仿真，snapshot.json为正式运行快照，launch.json/stopped_run.json记录进程身份。验证模型仅在本docs目录，正式run没有加载它。
