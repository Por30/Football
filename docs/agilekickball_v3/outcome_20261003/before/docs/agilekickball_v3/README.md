# AgileKickball-v3：更远发球与更宽接球区域

独立任务 `Template-Perceptual-Ball-AgileKickball-v3`，revision=`wide_serve_aim035_20260928`。
基于当前v2 `v1_speed_only_20260925`，只调整空间参数组，速度课程、奖励、恢复、观测、动作和PPO/AMP继承v2。

| 空间参数 | v2 | v3 |
|---|---|---|
| 起步发球距离 | 0.5–0.7 m | 0.5–0.7 m |
| 最终发球距离 | 1.3–2.0 m | 1.3–3.0 m |
| 来球横向目标偏移 | ±0.25 m | 从±0.25 m渐进到±0.35 m |
| 机器人离开初始站位的终止半径 | 0.6 m | 1.2 m |
| 球离开初始站位的结束半径 | 3.0 m | 4.0 m |

距离和横向偏移使用原来的平均来球曝光E推进：`p=min(E/60000,1)`，发球距离为`[0.5+0.8p, 0.7+2.3p]` m，横向目标偏移为`±(0.25+0.1p)` m。球速仍先从0.4–0.8 m/s起步，按v2近期恢复发球表现解锁扩展，最高均匀采样0.4–6.0 m/s。球速覆盖上限不表示已掌握该速度。

距离从episode初始站位anchor测量。目标偏移沿“发球点到anchor方向”的垂线均匀采样；不是固定世界坐标Y，也不是球的最终落地位置。发球方位角保持相对初始朝向±0.35 rad。anchor在episode内固定，不跟随机器人；允许机器人移动1.2 m，但保留原站立奖励，仍有回到初始站位的软激励。

球结束半径扩至4 m，给3 m发球及踢回后留空间。越过初始站位后方0.3 m、低速停止等其他球结束规则沿用v2。恢复仍要求连续稳定0.3 s、最少等待0.4 s，5 s恢复超时结束episode；跌倒、倾斜、自碰及非有限检查保留。环境间距仍为12 m。

## 训练与播放

```bash
python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-AgileKickball-v3 \
  --num_envs 4096 --device cuda:0 --headless \
  --max_iterations 50000 --seed 42 \
  --run_name wide_serve_aim035_20260928_scratch
```

默认从零训练；本次实现未启动长训练。v3使用独立日志目录`logs/rsl_rl/agilekickball_v3`，独立checkpoint键`agile_v3_wide_serve_curriculum`，序列化格式仍为schema5，config记录v3 revision和空间参数。旧版±0.75m的v3及v2 checkpoint不能直接用`--resume`或作为v3播放checkpoint；版本不匹配会在模型权重加载前拒绝。未实施跨任务权重迁移。

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-AgileKickball-v3 \
  --num_envs 4 --checkpoint /path/to/v3/model.pt \
  --ballspeed 0.4 6 --visray
```

播放恢复并冻结存档中的空间及速度课程；`--ballspeed`只覆盖速度，不自动提升空间课程。TensorBoard使用`AgileV3/`前缀，包括距离上下限、`aim_half_width_m`、`robot_anchor_max_m`以及继承的速度/恢复课程指标。

## 验证

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py
bash scripts/rsl_rl/smoke_agilekickball_v3.sh
```

回归包含旋转/平移站位下的发球距离、目标偏移、球速、部分reset、球结束边界、机器人移动边界、旧checkpoint拒绝、课程resume/play冻结及原v2/v1回归。真实CPU仿真使用16环境、两次新策略PPO更新，并检查实际3 m、6 m/s来球首步有效及注册的移动终止项。构造最终课程状态只用于功能测试，不证明宽范围高速接球已经学成。

2026-09-28：横向终点收窄为±0.35m，起点仍为±0.25m。本次运行既有CPU回归；`validation/`中仿真记录属于9月27日±0.75m版本，本次未重跑真实仿真。新验证回执见`aim035_20260928/`。
