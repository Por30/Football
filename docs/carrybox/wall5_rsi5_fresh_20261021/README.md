# Wall5 新RSI75/5/20从零正式训练

旧PID570043已停止，最后日志迭代23309、model_23200.pt及全部历史日志保留。新wall5以RSI75/5/20、4096环境、seed42、40000轮从零启动，PID1032672；检查至41轮，近10轮平均3.873s、最慢4.280s。首模型确认新RSI、schema2/revision19、全新优化器/Normalizer；正式训练进行中，尚未验证抱起成功。

启动核验时间：2026-10-21T13:04:46.031473+09:00。用户明确要求停止当前训练并重新启动新训练；本次按已说明的fresh方式执行，无resume、warm-start或checkpoint输入。其他revision19训练配方保持，未额外修改拾取奖励。

原进程完整命令与start_ticks核对后发送SIGINT，确认退出和显存释放再启动新进程。旧日志与模型均保留；最后落盘模型之后的训练尾部没有保存成新checkpoint。新启动前可用显存23094MiB，13段ground_pickup数据hash全部核对。

新RSI固定配额为3072 loco、205 pickup、819 hold。pickup仅第0–31帧，箱底5mm、无平台；hold保持手边参考箱高。AMP专家仍40/40/20、60维特征，actor深度＋本体，critic独立108维MLP，roll阈值0.5。完整模型契约与已通过的20环境reset验收一致；新日志实际transition比例也已核对为3072/4096、205/4096、819/4096。

首个model_0.pt中PPO与AMP优化器step均为20，AMP Normalizer count=61440，参数/优化器均有限；配置resume=false，说明新进程从零开始。已观察至少16个完整迭代，并检查近10轮均小于6秒。生产源码hash未变化，快照在source_snapshot/。

首次启动验收的完整契约比较遇到存储格式差异：torch checkpoint保留随机化范围的tuple，短测JSON将其转换成list。统一为JSON表示后，完整契约所有字段一致；检查范围与断言数值保持。失败回执保留在attempt1_contract_format/，仅重跑只读验收，没有再次启动、停止或修改训练。

正式run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_12-57-08_wall5_v19_rsi75_5_20_fresh_20261021_125703`

首个checkpoint：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_12-57-08_wall5_v19_rsi75_5_20_fresh_20261021_125703/model_0.pt`

查看日志：

```bash
tail -n 100 -f "/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v19_rsi75_5_20_fresh_20261021_125703.log"
```

查看进程：

```bash
ps -p 1032672 -o pid,etime,args
```

只读复查：

```bash
cd /home/cao/perceptual_ball
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_rsi5_fresh_20261021/verify.py
```

[停止记录](stopped_run.json) · [启动记录](launch.json) · [启动核验](snapshot.json) · [回执](receipts.json)。launch.json用于防重复启动；后续操作前重新核对进程。本次完成启动，不代表40000轮结束或已学会搬箱。
