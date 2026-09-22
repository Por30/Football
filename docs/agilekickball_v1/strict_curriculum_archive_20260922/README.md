# AgileKickball-v1：成功率驱动速度课程

新任务：`Template-Perceptual-Ball-AgileKickball-v1`。直接继承当前 AgileKickball-v0，v0 任务仍可独立运行。v1 的 actor/critic 观测维度、合成深度、网络、奖励、PPO 配置、默认站姿首球和恢复门控均沿用 v0。新增的严格课程成功不改变 v0 的 kick_bonus 奖励定义。

## 速度阶段与采样

下限始终为 **0.4 m/s**，阶段编号从 0 开始，上限依次为：

| stage | 速度上限 m/s | 50%挑战球的采样区间 m/s |
| --- | ---: | --- |
| 0 | 0.8 | 全部球0.4–0.8，全部标记为挑战球 |
| 1 | 1.2 | 0.8–1.2 |
| 2 | 1.6 | 1.2–1.6 |
| 3 | 2.0 | 1.6–2.0 |
| 4 | 2.5 | 2.0–2.5 |
| 5 | 3.0 | 2.5–3.0 |
| 6 | 3.5 | 3.0–3.5 |
| 7 | 4.0 | 3.5–4.0 |
| 8 | 4.5 | 4.0–4.5 |
| 9 | 5.0 | 4.5–5.0 |

stage≥1 时，另一半球在 `[0.4, 上一阶段上限]` 均匀采样，保留慢球复习。50%是独立抽样概率，不保证每一小批恰好一半。速度为初始水平发射速度，实际到达速度会受滚动/碰撞影响。

v1 发球距离固定 **1.3–2.0 m**，不再沿用 v0 从0.5–0.7 m逐渐增加距离的曝光课程；这是此前同一策略能有效踢球的距离范围。保持距离不变，让成功率课程集中提高速度。5 m/s下理想到达锚点时间约0.26–0.40秒，不是实测触球时间，也不代表策略已掌握高速球。

## 晋级条件

每个统计窗口同时满足以下样本数才结算：

- 至少4096个**当前阶段已结算球局**；
- 其中至少1024个当前阶段挑战球；
- 整体成功率≥80%，挑战球成功率也≥80%，该窗口才算达标。

连续两个互不重叠窗口达标，而且当前阶段已经运行至少1000个控制步（20秒仿真时间），才升一级。驻留按全局控制步计，不乘环境数。窗口按完整控制步提交的批次累加，可以超过最低样本数，超出部分全部计入本窗口，不挑成功球、不重复使用、不丢弃。失败窗口清零连续达标数。未达驻留门槛时仍结算窗口，之后需要新的达标窗口触发晋级。

晋级清除阶段驻留、连续窗口计数和新阶段统计，最终封顶stage9；不自动降级。只影响之后发出的球，不改变飞行球。每球保存发出时的stage和挑战标签，旧阶段在途球仍结算到运行总计，但不推进新阶段窗口。

## 课程成功与分母

同一个球局必须依次满足：

1. 原v0的球速度突变/向外回球候选成立：水平速度变化>0.15 m/s、向外速度>0.4 m/s等原条件。
2. 球心距最近脚link<0.30 m，且该脚相对机器人根部的速度沿向外方向>0.5 m/s。位置与速度均使用body_link世界坐标表达。
3. 从候选击球点沿当时冻结的向外方向，球推进至少0.5 m；横向滑动和发球瞬移不算。
4. 此后球结束、机器人通过原恢复门控，在真正重新发球前结算成功：连续稳定0.3秒且恢复等待至少0.4秒。

稳定判据和v0相同；跌倒、episode时限结束、恢复超时5秒等终止优先，将开放球局结算为失败。未完成球局暂不进入分母，结算一次后绝不重复计数。reset先处理旧球，再创建新球记录。恢复门控拒绝重发时，不结算旧球也不伪造新球。

以上仍是**运动学接触代理**，没有新增真实足部接触传感器，不能作为真机接触成功率。v0奖励中的被动反弹漏洞并未在此次更改；但只有满足更严格动作、回球、恢复条件的球才能帮助v1晋级。

## checkpoint、播放与日志

新checkpoint保存版本化课程配置、stage、驻留步数、连续达标窗口数、未完成统计窗口和最后窗口。加载时校验schema、配置及计数关系，防止错用阈值；更改阈值后直接恢复旧v1课程会明确报错。

不保存物理环境快照，因此旧进程尚未结束的球标记为运行截断（`truncated_on_load`），不冒充成功或失败；新进程重新reset创建球局。播放恢复阶段但冻结窗口/驻留/晋级；评估球局仍可记录运行总计。恢复训练重新启用课程更新。

v0 checkpoint没有成功率课程字段：加载v0策略/优化器/AMP时，v1课程明确从stage0开始，不将v0曝光计数解释为成功。无需修改或复制旧checkpoint。训练入口已支持显式绝对checkpoint路径，保持独立`agilekickball_v1`日志目录。

主要TensorBoard标签：

- `AgileV1/stage`、`speed_upper_m_s`、`stage_steps`、`passing_windows`；
- `AgileV1/window_total`、`window_successes`、`window_challenge`、`window_challenge_successes`；
- `AgileV1/window_success_rate`、`window_challenge_success_rate`（分母>0时才写）；
- `AgileV1/last_window_*`：最近完整窗口统计；
- `AgileV1/settled_rounds`、`curriculum_proxy_successes`、`open_rounds`、`truncated_on_load`、`updates_enabled`。

运行总计从本进程起算；课程窗口和阶段随checkpoint恢复。`AgileKickball/kick_proxy_successes`仍是旧v0宽松代理，不要用它判断v1是否应晋级。已有分层位置/速度RMSE、P95与辅助更新指标继续保留。

## 推荐训练命令

从现有v0的model_25200继续学习，4096环境、**本次额外50000轮**：

```bash
python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-AgileKickball-v1 \
  --num_envs 4096 \
  --device cuda:0 \
  --headless \
  --max_iterations 50000 \
  --seed 42 \
  --run_name success_curriculum \
  --resume \
  --checkpoint /home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v0/2026-09-20_18-02-42_learning_fix/model_25200.pt
```

网络/优化器及日志iteration编号继承checkpoint，v1成功率课程从stage0开始。若要完全从头训练，去掉最后两项`--resume`和`--checkpoint ...`，迭代号从0开始。固定较远发球距离对尚未学会站稳的随机策略更困难，因此建议使用已学v0策略。

恢复已经训练的v1时，把checkpoint换成`logs/rsl_rl/agilekickball_v1/.../model_*.pt`的绝对路径；阶段和窗口会自动恢复。播放：

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-AgileKickball-v1 \
  --num_envs 4 \
  --checkpoint /home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v1/<运行目录>/<模型文件.pt>
```

初次训练可通过Hydra覆盖启动事件参数，例如`env.events.setup_kickball_state.params.success_threshold=0.85`；窗口阈值配置是checkpoint合同的一部分，恢复时必须匹配。

## 验证结果与边界

32项CPU回归通过，包含v0原行为、课程回滚加载、主动/被动事件区分、恢复后一次结算、终止优先、部分reset、方向投影、两窗口/挑战/驻留门槛、旧阶段结果隔离、所有速度阶段和5m/s封顶、checkpoint校验、播放冻结。

16环境真实IsaacLab smoke通过：10个构造阶段的实际写入发球速度均在范围内，最高采样4.88465 m/s；手动放到stage9只为验证高速采样和物理运行，不能称为成功晋级。用现有v0权重自然运行stage0的400步，结算30球，其中29球达到严格课程代理成功，0次episode终止。样本量不足4096且驻留不足1000步，stage仍为0，未绕过晋级门槛。自然小样本96.7%不能外推为训练收敛率。

新任务可完成一次PPO/辅助/AMP更新，loss有限；保存加载、播放冻结和每球分母守恒验证通过。训练入口的显式文件路径分支已加入；本次短训练验证通过runner执行，未启动4096环境长训练。

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py
bash scripts/rsl_rl/smoke_agilekickball_v1.sh
```

原始结果`validation/smoke.json`，日志`validation/smoke.log`，最终回执`test_receipts.json`。首次smoke的验证脚本在inference模式内加载Adam导致更新异常，已将更新前最终加载移到普通上下文；未改变生产算法或验收断言，失败回执保留。此次未改善此前发现的近脚深度盲区，也未证明5 m/s球能稳定踢回。

## 播放时指定来球速度

`play.py` 支持可选参数 `--ballspeed MIN MAX`，单位m/s。例如：

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-AgileKickball-v1 \
  --num_envs 4 \
  --ballspeed 0.4 5.0
```

未指定checkpoint时仍按原播放逻辑选择该任务最新checkpoint，也可追加`--checkpoint /绝对路径/model_XXXX.pt`。

指定后，第一球、恢复后重发、episode reset均在该范围均匀采样；v1不再使用阶段的挑战/复习混合采样，课程更新保持冻结，距离不受此参数影响。`--ballspeed 2.0 2.0`表示固定2m/s。要求有限正数且MIN≤MAX，非法参数在启动仿真前报错。未传参数时保持原来的checkpoint课程行为；覆盖只在当前播放进程生效，不写回checkpoint。

13项针对性回归通过（含原v1课程与播放加载回归）；此参数改动未另行运行GUI或长训练。
