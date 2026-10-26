# wall13：静止持箱 AMP 数据入口

此页保留 **revision 1 的历史实现与验证记录**。当前 wall13 已升级为 revision 3，直接拼接预测位姿9维，Actor输入695维；最新结构、说明图、检查与训练状态见[当前说明](../wall13_concat_20261026/README.md)。中间的128维融合方案见[revision2记录](../wall13_feedback_20261026/README.md)。下文“复用 wall12 学习器”等描述仅适用于旧 revision 1。

2026-10-26，实现和16环境短测完成，未启动wall13正式训练。独立任务为`Template-Perceptual-Ball-CarryBox-Walled13-v0`，继承wall12。

用户要求“AMP数据集换成修改后搬起箱子后稳定站着的版本，其他不变”。本地找到的对应数据是`source/perceptual_ball/perceptual_ball/assets/motions/findbox/`，revision3、`findbox_hold_v1_named`。**这份数据已经被wall12正式model19999使用，wall13没有改变训练数据内容。** 已向用户询问是否另有新版路径；未获得不同路径前，按找到的匹配版本显式配置。若指另一份修改数据，仍需提供其路径后再接入，不能把当前wall13称为一次不同数据集的对照实验。

数据共15段、4155帧、60Hz：11段行走、3段拾箱、1段静止持箱。`hold/hold_box_01.pt`为300帧、5秒；保留原carrywith1第0–20帧，从第20帧起固定姿态，线速度/角速度/关节速度为0。没有carrywith2/3和putDown。已有数据、manifest、文件名映射及兼容快照保持原样。

- Manifest SHA-256：`59ade1b9cbff54e5f62c34028923428efa7b76a21f1866aeab2954799f8d3ee8`
- Hold SHA-256：`ac0e873274b3425925b218ccbd682e59590210363754c39bc78092231be273e8`
- 实际AMP沿用wall12/10的逐片段权重：行走1、拾箱4、持箱5。因此组概率为11/28、12/28、5/28；不是manifest里兼容保留的40/40/20组权重。

生产改动仅新增wall13配置与环境薄封装、Gym注册，以及train/play shell允许版本13。环境配置与wall12只差`walled_variant`；runner配置只差`experiment_name`和`run_name`，显式指定的`amp_data_dir`与wall12默认值相同。环境类仅更改checkpoint身份及`Wall13/`日志前缀，继承全部任务行为；继续复用`CarryBoxWall12OnPolicyRunner`和`CarryBoxWall12PPO`。

任务仍为接近箱子、搬起、稳定站立保持2秒。深度噪声、墙柱干扰、参考初始化RSI、奖励、课程、控制和域随机化保持wall12。Actor仍是558维本体历史加4×27×48深度；critic123维，AMP60×10；训练端位姿辅助监督系数1.0。正式默认4096环境、24步、5×4更新、20000轮。数据与标签均未增加actor输入。

定向检查`validate.sh`通过：注册入口实际加载；所有片段哈希核验；持箱静止尾段及真实AMP窗口恒定；全部env/runner配置差异断言；16环境×24步、20个minibatch更新；actor/critic/CNN/pose head及AMP均更新且损失有限；schema2保存与严格恢复、pose Adam状态恢复；旧wall12 checkpoint被wall13严格恢复拒绝。证据见[smoke.json](smoke.json)、[smoke.log](smoke.log)、[receipts.json](receipts.json)。短测模型只在本目录，不是正式训练或成功率证据；未重测完整4096环境性能或收敛。

正式启动命令（本次未执行）：

```bash
cd /home/cao/perceptual_ball
CARRYBOX_VARIANT=13 bash scripts/rsl_rl/train_carrybox_walled.sh
```

正式日志目录为`logs/rsl_rl/g1_carrybox_depth/walled13/`。训练后回放wall13自身checkpoint：

```bash
CARRYBOX_VARIANT=13 bash scripts/rsl_rl/play_carrybox_walled.sh /absolute/path/to/wall13/model_N.pt 4
```

检查时后台足球v11 PID3814037仍运行，本次未发停止信号或修改足球代码。工程记录：`agent/{plan,task,report,handoff}/carrybox-wall13-20261026.md`。
