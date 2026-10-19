# wall5 roll0.5正式从零训练

wall5已按用户新指令从零正式启动，PID114186，4096环境、seed42、40000轮，无resume/warm-start。检查时间2026-10-19T14:31:55.348542+09:00，迭代1→16；最近10轮平均3.802秒、最慢3.900秒。首checkpoint确认revision15＋roll0.5、RSI80/0/20、13段60维AMP、独立108维critic；actor仍深度＋本体，增量push与1.0/multiply摩擦已生效。优化器及AMP统计是全新初始化，参数有限。生产代码未修改，先前未通过的loco控制候选未启用。训练进行中，尚未证明站走或拾箱收敛。

用户在此前修复候选撤回、随后将roll改为0.5rad之后明确要求重新启动。此次执行现有配置；没有重新试参、复用失败候选或把旧静止验收改为通过。

Run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_14-25-38_wall5_v15_roll05_fresh_20261019_142533`。

查看终端日志：

```bash
tail -f '/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v15_roll05_fresh_20261019_142533.log'
```

本次实际启动命令（正在运行，不应重复执行）：

```bash
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/train.py --task Template-Perceptual-Ball-CarryBox-Walled5-v0 --num_envs 4096 --device cuda:0 --headless --seed 42 --max_iterations 40000 --run_name wall5_v15_roll05_fresh_20261019_142533
```

启动期指标（分技能mean_steps是累计统计，不能当作近期独立成功率）：

- `Skill/loco_mean_steps`：27.7255
- `Skill/hold_mean_steps`：31.5421
- `Skill/loco_success_fraction`：0.0000
- `Skill/hold_success_fraction`：0.0000
- `AMP/style_reward`：0.1790
- `Reward/amp_per_step`：0.0224
- `Mean episode length`：27.3500

完整启动验收见[snapshot.json](snapshot.json)和[真实回执](receipts.json)；PID、命令、AMP manifest hash、8个相关源码hash见[launch.json](launch.json)，对应源码保存在`source_snapshot/`。首model_0的PPO/AMP优化器step均20，Normalizer count61440，确认fresh；没有从docs验证模型加载权重。最近10轮均在6秒内。

roll0.5的14项CPU检查沿用[前一变更验收](../wall5_roll05_20261019/README.md)，推扰/摩擦的仿真与更新恢复沿用[revision15检查](../wall5_push_20261019/README.md)。此次冻结命令`bash docs/carrybox/wall5_roll05_start_20261019/verify.sh`仅只读验证新正式进程。启动成功不代表此前快速倾倒已修复，后续应持续看loco/hold各自长度、朝箱移动和地面拾取成功，不能只看总回合长度。

时间/PID/迭代是上述时刻快照，后续操作前重新核对实际状态；本任务没有停止其他进程。
