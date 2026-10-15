# 搬箱子新 AMP 默认数据验收

2026-10-14 20:46 JST：本次核对用户要求的新版数据已在先前目录迁移中接入；未重复修改源码。CarryBox-v0、Walled3-v0、Walled4-v0 的训练默认使用 `source/perceptual_ball/perceptual_ball/assets/motions/findbox/`。基线 PPO 配置与算法默认引用 `DEFAULT_DATASET_PATH`，两个 walled 变体继承该配置；walled 的 `initialize_reference` 也使用相同默认 MotionLibrary，并从 library.root 读取位姿。

新版为 manifest schema=1 / dataset_revision=3，行走11、拾箱3、抱箱1，共15段4155帧；抱箱5秒。AMP组采样40/40/20%，原始60Hz按50Hz控制重采样。 actor/critic的深度+本体输入、位姿辅助监督和纯本体AMP边界保持。

[两组CPU测试回执](test_receipts.json)均PASS，覆盖数据hash、规范/兼容路径、AMP实际更新及checkpoint检查、三技能参考初始化。复用已有实现与测试，无新增GPU仿真或正式训练。

## 当前正式进程与新默认的区别

[只读快照](runtime_snapshot.json)：PID2348537仍存在，最新已保存model_4000.pt记录旧17段/4628帧、manifest hash以eef4d55d开头；新默认hash以59ade1b9开头。运行进程缓存不随磁盘配置变化，因此本次完成的是默认配置验收，并未将运行中的旧训练切换到新版。

旧完整checkpoint不能通过新数据的严格身份校验。后续若用户要求切换当前训练，应先核对实时进程和最新正式checkpoint，再使用现有 `--warm_start_carrybox /绝对路径/model_N.pt` 迁移策略编码器、actor/critic及辅助头；PPO、AMP与课程从头初始化，另建run。不要以 `--resume` 绕过数据身份检查，也不要直接重复启动占用GPU的4096环境任务。

新启动wall4使用默认数据的配方（当前已有训练，不要并发运行）：

```bash
bash scripts/rsl_rl/train_carrybox_walled.sh --num_envs 4096 --max_iterations 40000 --run_name wall4_findbox_named_v3
```

本次没有启动、停止或重启训练；数据变更的学习收益尚未评估。
