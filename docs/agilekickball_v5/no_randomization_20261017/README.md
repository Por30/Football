# v5 默认关闭增益随机化与深度噪声

2026-10-17按用户要求完成。`AgileKickballV5EnvCfg.randomize_gains`和`randomize_depth`由`True`改为`False`。使用现有关闭路径：每次reset的Kp/Kd倍率固定为1，回到名义增益；深度随机器直接返回clean深度，不加比例、偏置、高斯噪声或缺失。场景光轴米制、自遮挡、相机参数、回传奖励、AMP、网络及优化器配方保持。

仅修改v5默认配置；现有随机化实现和范围保留，以兼容历史实验。历史GPU smoke显式开启两个开关，继续检查其原有带扰动场景；它不代表新默认配方的GPU验收。

## 新训练与旧checkpoint

新启动直接使用默认命令，无需额外开关：

```bash
bash scripts/rsl_rl/train_agilekickball_v5.sh
```

本次没有执行该命令，也没有停止、重启或恢复训练。默认训练/播放均关闭扰动；显式Hydra覆盖仍优先。

旧带扰动模型的`depth_contract.training_randomization`记录两个`enabled=True`，新默认记录`False`；精确恢复会拒绝不同合同。未改revision或放松合同检查。若仅需恢复历史带扰动实验，必须显式匹配旧配置，例如：

```bash
bash scripts/rsl_rl/train_agilekickball_v5.sh \
  --resume --checkpoint /absolute/path/to/old_v5/model.pt \
  env.randomize_gains=True env.randomize_depth=True
```

该命令保留旧随机化，不能用于把旧训练切换成无扰动。需要无扰动时使用新实验；本次没有新增权重迁移入口。播放旧模型同样需匹配其保存的开关与范围。

## 验证与状态

既有CPU检查通过（含v5深度预处理、关闭噪声逐元素一致、随机化边界以及v4/state-feedback回归），[机器回执](receipts.json)：

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p 'test_agilekickball_v5*.py' -v
```

本次未启动GPU仿真，未验证新默认配方的正式训练或成功率。历史4环境关闭增益/噪声路径验收见[随机化记录](../randomization/README.md)。

运行状态仅为快照：10月17日22:31 JST曾核验正式run `logs/rsl_rl/agilekickball_v5/2026-10-17_12-22-23/`，checkpoint `model_11800.pt`为旧带扰动合同，训练指标约11994轮。22:35 JST再次只读检查，原PID3429618已退出，无train/play进程；本次未操作进程，不据此认定50000轮完成或收敛。
