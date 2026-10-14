# Football / Perceptual Ball

基于 Isaac Lab 与 RSL-RL 的 Unitree G1 踢球项目：深度感知、AMP 动作先验、连续来球、恢复平衡与来球速度课程。

## 获取和安装

模型资源与动作参考数据使用 Git LFS。先安装 Git LFS，并使用已经配置好 Isaac Sim / Isaac Lab 的 Python 环境：

```bash
git lfs install
git clone https://github.com/Por30/Football.git
cd Football
git lfs pull
python -m pip install -e source/perceptual_ball
python scripts/list_envs.py
```

仓库包含 G1 USD 及其依赖层、左右脚踢球动作参考数据；不包含本地训练 checkpoint、TensorBoard 日志或验证临时模型。`unitree_g1_retarget/` 保留动作重定向数据和演示。

## 当前任务

- `Template-Perceptual-Ball-AgileKickball-v0`：基础连续踢球与恢复发球任务。
- `Template-Perceptual-Ball-AgileKickball-v1`：在 v0 上增加渐进来球速度（0.4–5.0 m/s），修正恢复门控并加强踢球奖励。
- `Template-Perceptual-Ball-AgileKickball-v3`：基于当前 v2，最远发球渐进至 3 m、来球横向目标偏移至 ±0.35 m，机器人移动半径放宽至 1.2 m。见 [v3 说明与训练命令](docs/agilekickball_v3/README.md)。
- 其他注册任务和历史 Soccer-v2/v3 实现保留在源码中。

v1 当前采用有效来球曝光课程，不是早期的严格成功窗口课程。设计和版本差异见 [v1 说明](docs/agilekickball_v1/README.md)。

## 从头训练 v1

```bash
python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-AgileKickball-v1 \
  --num_envs 4096 \
  --device cuda:0 \
  --headless \
  --max_iterations 50000 \
  --seed 42 \
  --run_name v0_gradual_speed_kick_reward_scratch
```

默认从头训练，不需要 `--resume`。速度课程按实际来球曝光推进，50000 轮不保证达到最终速度。

## 播放和深度视场

把 checkpoint 路径替换为本机已有模型；任务版本须与模型对应：

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-AgileKickball-v0 \
  --num_envs 4 \
  --checkpoint /path/to/model_25000.pt \
  --ballspeed 0.4 3 \
  --visray
```

`--ballspeed MIN MAX` 覆盖播放来球速度，`--visray` 用绿色射线和采样点显示深度视场；省略对应参数即使用默认行为。当前深度是解析球面相交，并非完整场景深度。详见 [可视化说明](docs/play_visray/README.md)。

## 目录与验证记录

- `source/perceptual_ball/`：任务、感知、奖励、PPO/AMP 扩展及资源。
- `scripts/rsl_rl/`：训练、播放、诊断和有限仿真验证脚本。
- `tests/`：CPU 回归与感知/状态机边界测试。
- `docs/`：设计、训练审计、验证报告与可视化截图。
- `agent/`：工程计划、任务、报告与交接记录。

部分测试和诊断脚本保留开发机的 Isaac Lab 安装路径、历史 checkpoint 路径；在其他机器运行前需调整这些路径并准备相应模型。历史报告记录当时的验证结果，短仿真不代表长期训练收敛。

## AgileKickball v2

当前 revision=`v1_speed_only_20260925`、schema=5：完整继承v1的连续发球、恢复、奖励、深度和PPO，仅修改速度课程。先学基础来球，近期连续恢复发球和kick代理达到门槛后，逐步扩展至6m/s；表现下降时暂停提速。

```bash
python scripts/rsl_rl/train.py --task Template-Perceptual-Ball-AgileKickball-v2 --num_envs 4096 --device cuda:0 --headless --max_iterations 50000 --seed 42 --run_name v1_speed_only_20260925_scratch
```

从零训练，不添加 `--resume`，旧v2 checkpoint在权重加载前被拒绝。启动应打印上述revision，TensorBoard应有`AgileV2/schema=5`。详见 [v2设计及验证说明](docs/agilekickball_v2/DESIGN.md)。课程提供高速样本不代表策略已掌握高速踢球。
