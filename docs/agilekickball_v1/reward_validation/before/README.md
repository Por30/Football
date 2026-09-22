# AgileKickball-v1：基于 v0 的渐进来球速度（2026-09-22）

任务 ID：`Template-Perceptual-Ball-AgileKickball-v1`。

本版替换旧的成功率阶段课程。直接继承 AgileKickball-v0 的奖励、观测、动作、网络、PPO、AMP、深度监督、初始近距离来球和连续球回合；不再使用主动脚速/回球距离/恢复成功联合判定来控制课程，也没有成功窗口、挑战区间混合或自动降级。v0 源文件未改。

## 速度与距离

`e = exposure_offset + mean(incoming_steps)`，单位为每环境平均的有效来球控制步。球活跃、其平面速度指向机器人且该环境未终止时计数；空等、恢复、并行环境总数不加速课程。控制周期 0.02 s。课程由原 v0 的 episode-reset 回调更新，仅影响后续发球，不改变飞行中球的速度。

| 平均来球步 e | 均匀采样速度（m/s） | 发球距离（m） |
| --- | --- | --- |
| 0 | 0.4–0.8 | 0.5–0.7 |
| 60,000 | 0.4–1.1 | 1.3–2.0 |
| 120,000 | 0.4–1.4 | 1.3–2.0 |
| 240,000 | 0.4–2.0 | 1.3–2.0 |
| 360,000 | 0.4–3.5 | 1.3–2.0 |
| ≥480,000 | 0.4–5.0 | 1.3–2.0 |

前 240,000 步的速度公式与 v0 相同：`upper = 0.8 + 1.2 * e / 240000`。随后 `upper = 2 + 3 * min((e - 240000) / extension_ramp_steps, 1)`，默认 `extension_ramp_steps=240000`，配置位置 `agilekickball_v1_env_cfg.py`。距离完全沿用 v0：前 60,000 步从 `(0.5,0.7)` 线性变到 `(1.3,2.0)`。

速度下限始终 0.4，所有速度统一均匀采样，保留慢球练习。曝光反映练习量，不代表已掌握该速度；本版按用户要求不以成功率卡住升级。

**50,000 次 PPO iteration 不等于 480,000 来球步。** 每轮采样 24 个控制步，若来球占比为 30%，50,000 轮约累计 360,000 来球步，上限约 3.5 m/s；占比 40% 时才约达到 5 m/s。具体以日志曝光与速度上限为准，不承诺固定轮数达到顶速。

## 连续发球与 reset

- Episode reset：沿用 v0 初始化机器人并立即发首球，起步不等待恢复。
- 球回合结束：沿用 v0 的越界/越过机器人/低速条件。进入恢复等待，机器人继续由策略控制。
- 下一球：满足身体恢复判据连续 0.3 s，且等待至少 0.4 s，才仅重置球；不重置机器人。
- 身体判据：重力投影 xy 范数 <0.15、z<−0.98；根部线速度 <0.25 m/s、角速度 <0.5 rad/s；高度 0.7–0.9 m；两脚 link 高度 −0.03–0.12 m。保持与 v0 相同。
- v1 去掉全身 29 关节**瞬时**速度 RMS<1.5 rad/s 这一附加条件，避免探索噪声让稳定身体长期不能再接球。关节速度仍需有限值。这是恢复流程修复，不是新的踢球奖励。
- 恢复等待达到 5 s 仍失败则 episode reset；跌倒等原终止条件优先，终止步不得恢复发球。Episode 最长 60 s。

原踢球奖励仍使用 v0 的碰撞/向外速度代理指标，可能包含被动反弹；日志 `kick_proxy_successes` 不能解读为严格主动踢球成功率。

## 日志和 checkpoint

保留 `AgileKickball/serves`、`initial_serves`、`recovered_serves`、`waiting_fraction`、来球/近脚曝光及原监督误差日志。新课程看：

- `AgileV1/speed_upper_m_s`：当前发球速度上限。
- `AgileV1/course_incoming_steps_per_env`：当前分布所用的来球曝光快照。
- `AgileV1/speed_progress`：总曝光进度（不是成功率）。
- `AgileV1/distance_min_m`、`distance_max_m`。

新课程用 `agile_speed_curriculum`、schema 2 保存平均曝光和配置；加载时清空本进程曝光计数，避免重复相加，允许并行环境数变化。Play 加载后冻结课程所用曝光快照，后续 reset 不会加难。`--ballspeed MIN MAX` 仍从首球起覆盖所有采样，包含连续重发，临时覆盖不写入课程 checkpoint。

旧 strict v1 checkpoint 会被显式拒绝（包括 play），不能把其阶段/窗口当作新课程进度。需要重放旧模型时使用归档对应代码；本次从零训练。合法 v0 checkpoint 加载接口仍可读取其曝光，但下面的启动命令不加载任何旧模型。

## 从头训练

在已有 Isaac Lab / ball 环境的项目目录运行：

```bash
python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-AgileKickball-v1 \
  --num_envs 4096 \
  --device cuda:0 \
  --headless \
  --max_iterations 50000 \
  --seed 42 \
  --run_name v0_gradual_speed_scratch
```

不要加 `--resume`。新运行保存到 `logs/rsl_rl/agilekickball_v1/` 下带新时间戳的目录；与旧 `success_curriculum_scratch` 分开比较。修改代码不会改变已经运行的 Python 进程。

新模型播放示例（替换 checkpoint 路径）：

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-AgileKickball-v1 \
  --num_envs 4 \
  --checkpoint /absolute/path/to/new/model_10000.pt \
  --ballspeed 0.4 1.0
```

## 验证与历史

本版验证见 `simple_speed_validation/`，包括实际从零策略的一次 PPO 更新、真实仿真速度端点、课程存取与播放冻结，以及同一旧停站策略在随机动作下新旧恢复门控的对照。短跑只能验证更新和发球流程，不能证明从零收敛或 5 m/s 踢球能力。

`strict_curriculum_archive_20260922/` 是替换前的源码、配置、测试、smoke 和说明快照；其中成功窗口测试属于旧合同，不适用于本版。`validation/` 是旧 strict 版预训练 v0 权重 smoke，`training_audit_20260922/` 是旧训练诊断，都不是当前实现的收敛证明。旧审计脚本依赖当时 strict 状态字段，应在对应归档环境运行。
