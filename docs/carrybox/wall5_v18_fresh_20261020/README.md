# wall5 revision18 从零正式重启

旧revision17 PID254358已退出，历史日志和model_14800.pt保留。新版revision18三维距离训练已从零启动，4096环境、seed42、40000轮，PID553495；检查至16轮，最近10轮平均3.718秒、最慢3.750秒。首模型确认XYZ距离0.7m、schema2/revision18、非对称AC及13段60维AMP，优化器/Normalizer为全新初始化。正式训练进行中，尚未证明抱箱成功。

时间：2026-10-20T12:54:25.123895+09:00，Asia/Tokyo。用户明确要求停止当前训练并从头开始。
SIGTERM后旧进程尚未退出，核对PID完整命令和进程起始时间后发送SIGINT；
确认进程消失、显存释放后才启动新训练。旧模型和日志未删除。
[停止记录](stopped_run.json)、[启动记录](launch.json)、[正式运行验收](snapshot.json)。

新训练采用上一任务已验证的revision18：骨盆连杆原点到箱心XYZ距离，
0.7m奖励门控；水平行走方向、AMP水平封顶、RSI固定80/0/20、
roll0.5、13段ground_pickup数据、actor深度＋本体、独立108维特权critic保持。
本次不改生产源码或超参。启动前比对revision18源码hash、已有43项CPU和4环境
PPO/AMP测试记录，并核验13个数据文件hash；启动时无其他train/play进程，
可用显存23066MiB。

命令没有resume、warm_start或checkpoint参数；保存配置resume=false。
首个model_0.pt中策略和AMP优化器均为20个更新步，AMP Normalizer count=61440，
匹配全新训练的首轮更新；参数和优化器有限值检查通过。
源代码快照见source_snapshot/，hash见launch.json。

正式run：

```text
/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-20_12-48-36_wall5_v18_distance3d_fresh_20261020_124832
```

首个模型：

```text
/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-20_12-48-36_wall5_v18_distance3d_fresh_20261020_124832/model_0.pt
```

查看实时日志：

```bash
tail -n 100 -f "/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v18_distance3d_fresh_20261020_124832.log"
```

查看进程：

```bash
ps -p 553495 -o pid,etime,args
```

验收命令（只读核验现有训练，不会重新启动）：

```bash
bash docs/carrybox/wall5_v18_fresh_20261020/verify.sh
```

启动脚本有launch.json防重复保护，不应再次执行。下一次操作前重新核对实际PID、
命令和日志；此处迭代数是时间快照。启动核验不代表收敛或地面拾箱成功。
