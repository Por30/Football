# 旧wall4 checkpoint在当前环境播放

新增显式--carrybox_weights_only播放选项，复用现有warm_start校验schema/shape/finite，仅导入策略权重。默认播放的严格契约检查保持，足球分支默认行为不变；误用选项到其他runner时报错。导出写入独立exported_current_env，避免覆盖旧环境导出。

实际model_14000.pt为revision6，当前环境为revision7。CPU已验证真实模型与当前模型结构匹配、权重完整导入及默认/显式/错误runner分支。未启动GPU播放或正式训练，未停止现有训练。此命令是在修复后的当前环境播放旧策略，不是revision6环境原样复现，也不能作为原训练环境评估。

```bash
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"

/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-CarryBox-Walled4-v0 \
  --num_envs 4 --device cuda:0 --real-time \
  --carrybox_weights_only \
  --checkpoint /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_21-08-12_wall4_handoff_v6_amp15_20261014_210808/model_14000.pt
```

需要有图形桌面的终端。Warp深度无需enable_cameras。
