# FindBox AMP 接入

CarryBox 默认已启用 AMP，数据目录为仓库根目录 `findbox/`，由代码按仓库位置解析，不依赖启动时的工作目录。原始17个动作文件保持不变；新增 `findbox/amp_manifest.json` 补齐 schema 和 hash。

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

启动命令不变，完整示例见[任务说明](../README.md)。可以通过Hydra覆盖 `agent.algorithm.amp_coef`、`agent.algorithm.amp_reward_scale`、`agent.algorithm.amp_lr`、`agent.algorithm.amp_data_dir`；更改AMP奖励契约后需新开训练，不允许静默接续旧契约。没有启动长期训练。

验证包含：真实17片段、合成恒速运动/符号翻转、重力与关节映射、边界及坏数据拒绝、信息隔离、terminal评分和训练缓存一致、冷启动窗口屏蔽、AMP实际参数更新、optimizer/checkpoint恢复、无数据集推理。RTX smoke另外检查640维live状态、终止窗口及reset历史，与原深度/位姿、物理接触和导出测试共同执行。具体结果见`test_receipts.json`及上级`smoke.json`。两次短更新仅验证管线，不证明动作自然度或拾箱成功率已提升。
