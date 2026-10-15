# FindBox AMP 接入

2026-10-14规范目录与命名：[当前数据目录及旧新文件名对照](../../../source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md)，[迁移与兼容性记录](../amp_layout_20261014/README.md)。新目录15段与根findbox修订2逐字节相同，显式group维持旧采样语义。

CarryBox 默认已启用 AMP，默认数据目录为Python包 `assets/motions/findbox/`，与足球`kick/`并列；AMP和walled RSI默认路径一致，不依赖工作目录。根目录`findbox/`保留旧命名兼容快照。2026-10-14按用户要求整理为15段：行走11、拾箱3、抱箱1。`carrywith1`保留原0–20帧后重复第20帧至300帧（5秒），静止段速度为0；`carrywith2/3`已移出有效数据并归档。14段行走/拾箱文件hash不变。详见[修改、备份与兼容性说明](../amp_hold_20261014/README.md)。manifest schema仍为1，抱箱内容修订为dataset_revision=2，当前规范命名目录为revision=3；原17段完整数据及旧manifest保留在该记录的`original_dataset/`。

| 设置 | 当前值 |
|---|---|
| 行走/拾起/持箱样本概率 | 0.4 / 0.4 / 0.2；组内片段等权 |
| 原始采样率 → 控制采样率 | 60 → 50 Hz |
| 单帧 / 窗口维度 | 64 / 640（10帧） |
| AMP 输入 | 29关节位置、29关节速度、3维重力方向、3维根角速度 |
| 判别器 | 项目现有512→256 LSGAN + 梯度惩罚 |
| 判别器学习率 | 1e-4 |
| 奖励混合 | 0.75×任务奖励 + 0.25×2×dt×风格分数 |
| actor / critic | 仍然只有深度和原本体观测 |
| 位姿监督 | 原9维相机坐标位姿头与PPO共同更新 |

数据加载器用关节名字而非仿真DOF索引定义顺序，expert/live共享打包函数。角速度使用短弧四元数差分，处理q/-q符号变化；关节速度逐片段差分，不沿用来源帧定义不明确的速度字段。窗口按最旧到最新排列，固定速度重采样，不跨片段边界。旧末端数据和box字段不会读取或进入AMP。

AMP训练对每个动作后的窗口评分。done环境从`terminal_observations['amp']`取回重置前窗口，判别器读取相同缓存。重置后最初8个控制步因真实历史不足不参与AMP，任务奖励仍正常生效；第9步已有reset帧加9步的新帧。policy、pose与AMP梯度分属PPO优化器和AMP优化器，动作先验通过风格奖励影响策略。

checkpoint schema从1升级到2。含双方optimizer、判别器及其统计量、manifest hash与采样契约。恢复训练首次收集transition时才读取并校验数据；播放/导出只依赖checkpoint，无需`findbox`。既有无AMP模型需另做显式权重迁移，此接入不允许把它当完整AMP训练状态恢复。

本次数据修订改变manifest身份：旧17段checkpoint不能直接按完整AMP状态恢复到新15段数据。旧数据备份可供原契约加载核对。当前已运行进程缓存的数据不会热切换，本次没有重启或迁移训练；walled的RSI默认从规范assets目录加载，新进程须与所选AMP版本保持一致。

启动命令不变，完整示例见[任务说明](../README.md)。可以通过Hydra覆盖 `agent.algorithm.amp_coef`、`agent.algorithm.amp_reward_scale`、`agent.algorithm.amp_lr`、`agent.algorithm.amp_data_dir`；更改AMP奖励契约后需新开训练，不允许静默接续旧契约。没有启动长期训练。

初次接入验证（历史）包含：真实17片段、合成恒速运动/符号翻转、重力与关节映射、边界及坏数据拒绝、信息隔离、terminal评分和训练缓存一致、冷启动窗口屏蔽、AMP实际参数更新、optimizer/checkpoint恢复、无数据集推理。RTX smoke另外检查640维live状态、终止窗口及reset历史，与原深度/位姿、物理接触和导出测试共同执行。具体结果见`test_receipts.json`及上级`smoke.json`。两次短更新仅验证管线，不证明动作自然度或拾箱成功率已提升。新版15段的数据与AMP/RSI检查见[本次记录](../amp_hold_20261014/README.md)。
