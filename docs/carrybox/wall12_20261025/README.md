# FindBox wall12：带噪深度的箱子位姿辅助回归

2026-10-25。独立任务 `Template-Perceptual-Ball-CarryBox-Walled12-v0` 已实现，44项CPU检查及16环境24步、2＋1轮更新/严格恢复/导出短测通过。尚未启动wall12正式训练，未评估拾箱成功率、位姿回归精度或4096环境耗时。

## 相对wall11的变化

在原128维深度CNN特征上启用现有 `128→128→9`、ELU的pose head，预测箱子在相机光学坐标系中的位置xyz（米）及旋转矩阵前两列（6维，按列展开）。它只读取4帧带噪深度的CNN特征；位姿预测不会拼接到actor输入。CNN同时接受PPO、时间平滑和位姿辅助损失的梯度。

训练标签为12维：`xyz3 + rot6 + 实际箱体尺寸3`。最后3维只用于确定长方体旋转对称，不是预测目标，也不进入actor或critic的新输入。相机光学坐标约定为X右、Y下、Z前；标签取当前实际相机/箱体位姿，detach后存入rollout，保持米制，不按3m范围裁剪。

```text
4×27×48带噪深度 → CNN → 128维特征 ┬→ 拼接558维本体 → actor → 29维动作
                                   └→ pose head → xyz3 + rot6（仅训练）
仿真箱位/姿态/尺寸 → 配对标签 → pose loss → 回传CNN和pose head
```

损失为：

`L_aux = 1.0 × (MSE(position_xyz) + min_S MSE(predicted_rot6, first2columns(R_target @ S)))`

S枚举24个行列各一个±1、行列式+1的轴置换，只允许保持实际箱子尺寸的旋转。一般长方体有4种，恰好两轴等长有8种，正方体有24种；尺寸容差atol=1e-6 m、rtol=1e-5。非方形箱子的90°长宽交换不能作为等价姿态。共享旧方底箱D4损失保持原样。

全部当前配对帧参与监督，包括遮挡、远处及相机后方；不按可见性筛样本。这里“全部”指wall10/11现有更新索引：24步采样中的前23步，最后一步用于相邻配对和回报计算。监督当前真实观测，不给时间平滑构造的mixed观测额外套用当前标签。

## 时序与学习器

wall12在同一capture中生成带噪深度及位姿标签，每环境每控制步只更新一次。先读标签或先读深度结果一致，重复读取不重复抽噪声；partial reset只失效对应环境的深度与标签缓存。重置历史用新回合首帧填充。终止观测仍保存reset前深度供AMP及timeout bootstrap，辅助loss使用rollout里动作前的current观测标签，不误用next/terminal/reset后的标签。

wall10初始化原本冻结pose head且从Adam排除。wall12显式解冻并将其补入同一个Adam的policy参数组：保持三组参数及权重衰减0/.001/.1，AMP优化器仍是同一个对象，pose head只出现一次。恢复时保留pose head权重、Adam动量/步数与自适应学习率。

复用现有current＋mixed合批CNN前向，取current对应latent给pose head；不detach视觉特征、不另跑一次CNN。每轮仍为5 epochs×4 minibatches=20次联合更新。新增日志：`Loss/pose_position`、`Loss/pose_rotation`、`Loss/pose_aux_weighted`、`Loss/pose_samples`（样本次数包括5个epochs）。

## 保留的训练接口与配方

| 项目 | wall12 |
|---|---|
| Actor | 本体93×6=558，带噪深度4×27×48；无标签/位姿预测反馈 |
| Critic | 独立123维特权MLP，结构和输入排列保持wall11 |
| AMP | 原60×10特征、15段FindBox数据、LSGAN与联合Adam |
| 任务 | 接近、抬箱、原地严格保持2秒；20秒回合 |
| 随机化 | 原RSI比例、变尺寸箱、显式PD/动作延迟/推扰、本体噪声、深度噪声 |
| 场景 | 随机墙与3圆柱，原初始化净空规则 |
| 默认训练 | 4096环境×24步，20000轮，500轮保存，5×4更新 |
| 部署 | JIT/ONNX只包含CNN和actor，只接收本体与深度 |

实际配置逐项比较仅改变wall12身份、配对capture/reset函数、标签函数、runner/algorithm分派和aux系数；奖励、成功/失败阈值、相机安装/FOV与其余训练参数保持wall11。完整基础流程见[wall11说明](../wall11_20261024/README.md)，其中训练状态属于历史快照。

checkpoint继续schema2，并独立记录walled12/revision1及frame、单位、标签/预测维度、尺寸对称、配对规则、辅助系数和无actor反馈。wall11 checkpoint不能直接作为wall12完整resume，本次未迁移权重。验证模型仅位于本目录，不是正式训练模型。

## 使用

从零启动正式训练（本次未执行）：

```bash
cd /home/cao/perceptual_ball
CARRYBOX_VARIANT=12 bash scripts/rsl_rl/train_carrybox_walled.sh \
  --run_name wall12_depth_pose_aux
```

默认4096环境、24步。模型进入 `logs/rsl_rl/g1_carrybox_depth/walled12/<时间戳_run_name>/`。同版本恢复可在训练命令加 `--resume --checkpoint /绝对路径/wall12/model_500.pt`。

播放已训练的wall12模型：

```bash
CARRYBOX_VARIANT=12 bash scripts/rsl_rl/play_carrybox_walled.sh /绝对路径/wall12/model_500.pt 4
```

现有wall10、wall11和足球入口保留。当前共享wall10 PPO已有的辅助hook来自工作区先前修改，本任务直接复用，没有再次改动该共享模块；原足球v11分派与未提交代码保留。

## 验证证据与边界

- 44项CPU检查通过：尺寸对称4/8/24与非方箱90°反例、非轴对齐姿态右乘、标签detach、距离/前后不筛选、梯度同时进入CNN和pose head、current latent复用、标签/critic/AMP对actor隔离、同Adam成员无重复、恢复与非有限值停止；含wall10/11、CarryBox/AMP及足球既有回归。
- 16环境真实仿真24步、2轮更新＋保存/严格恢复后1轮通过。actor、critic、CNN、pose head、AMP均有实际参数更新；联合Adam步数40→60，pose动量精确恢复。
- 深度/标签两种读取顺序、同一步缓存与RNG、独立相机坐标变换、partial reset、终止前后配对通过。存入rollout的标签等于动作前当前观测。
- 每次学习update仅20次CNN调用，与20个minibatch一致；每次同时编码current+mixed，新增辅助头没有额外CNN调用。
- 实际wall11 `model_19999.pt`作为wall12严格恢复被拒绝；旧wall11学习器仍能加载原权重且pose head保持冻结。篡改辅助frame的checkpoint也被拒绝。
- JIT/ONNX导出通过，ONNX图输入仅flat和depth，导出无pose/critic参数，导出动作与实时actor一致。

三次短测辅助位置MSE为0.24770/0.20155/0.22622，旋转MSE为0.16338/0.15073/0.14292。数据随rollout变化，这些值仅证明训练链路运行，不能作为精度提升或收敛结论。

首次仿真在恢复状态检查时因Adam步数标量被map_location从CPU迁至GPU而失败；检查修正为步数精确数值比较、动量仍要求同设备且精确相等。未更改生产代码或损失断言，失败回执、日志、验证模型保存在`attempt1/`。随后原样重跑两条冻结命令均PASS。

证据：[receipts.json](receipts.json)、[smoke.json](smoke.json)、[CPU日志](cpu.log)、[仿真日志](smoke.log)、[源码身份](source_identity.json)。本次实现与短测完成；正式训练、4096性能和独立成功率/位姿精度评估尚未执行。
