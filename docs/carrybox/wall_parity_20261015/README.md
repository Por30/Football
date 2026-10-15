# Wall3 / Wall4 公共修复与场景区分（2026-10-15）

已实现并通过41项CPU检查、两变体各4环境的真实碰撞/遮挡、三技能初始化及PPO/AMP更新、恢复、JIT/ONNX导出。未启动新正式训练，未证明修复后收敛；新版4096环境速度尚未重新实测。旧wall4 PID2448113仍运行revision6，不会热加载这些修改。

用户要求两任务只保留障碍物差异。旧wall3/wall4其实具有相同墙柱，差异来自搜索和yaw课程。本次已询问场景划分，未收到额外选择，采用已告知的默认方案：wall3只有1面墙；wall4为相同墙加3根圆柱。平台是两任务共同的参考动作支撑物，不属于新增圆柱差异。任务ID、日志目录和checkpoint变体身份分别保留。

| 项目 | wall3 | wall4 |
|---|---|---|
| 墙 | 0.2×8×3m，距root 3–4m | 相同 |
| 圆柱 | 无 | 3根，r=.15m/h=1.8m，距root 2.2–3.2m |
| 深度几何组 | 40 | 43 |
| 搜索初始化/奖励 | loco中2%，search_turn +0.5 | 相同 |
| yaw课程 | 0/10000/20000/30000轮→0/10/30/180°，进程锚点 | 相同 |
| RSI | loco/pickup/hold=60/30/10% | 相同 |
| 训练 | 初始action std=.2，entropy=.001，24步/4epochs/4minibatches，40000轮 | 相同 |

`to_dict()`逐项对比已验收：环境差异仅variant身份、圆柱数量/资产及depth object_names；runner差异仅experiment_name/run_name。

## 公共修复

- 奖励和失败判定统一采用**head_link质心的世界位置减env origin高度**。IsaacLab `body_com_pos_w`包含完整旋转变换；不把腰部附近的link原点冒充头部。保留0.8/0.85/0.4m阈值以及root/roll/pitch其他终止条件，以隔离此次坐标修正。头部COM不是头顶/最低点。
- wall专属关节位置惩罚仅将双膝lower bound从soft lower改为实际hard lower；其他关节和上限仍用原soft limits。实际硬限制和共享G1资产未修改。真实环境hold示范样本惩罚从原先约1.479降到0.001652（残余来自示范轻微超出物理下限，不隐藏该部分）。
- wall专属JointPositionAction先按原scale=.25和随机化后的default offset计算目标，再按解析joint IDs对应的真实hard limits裁剪。原始action和观测语义不变。新`Control/physical_target_clipped_fraction`与原始±9 action裁剪是不同量。
- 两变体共用包含30%pickup的RSI，不再默认跳过拾取局部练习；参考数据与AMP专家40/40/20采样不变。pickup参考中有支撑台条件，不能把它当作独立地面拾箱评估。
- 新训练使用fresh初始化和较低初始噪声/熵系数。正式命令不包含resume/warm_start；不继承旧失败模型的动作均值和log_std。该配方是工程修订，不是已验证的收敛方案。
- 推扰按进程相对迭代：初始化至1000轮不施加，1000–5000轮线性增加，到5000轮使用原幅度；中间阶段在当前速度与原有界随机目标之间插值。零幅度直接跳过，不把root速度清零。深度噪声、延迟、自遮挡、50Hz/48×27与安装位置保留。
- 新增按reset前技能累计的回合数、成功分子/比例、平均步数、fell/tipped比例，以及已完成回合按长度可形成完整AMP窗口的步数。回合步数由独立计数器累计，避免runner随机初始化timeout年龄污染统计；它不是判别器实际抽样次数，未结束回合不纳入；全局AMP/style_reward和valid_fraction仍同时记录。只有loco起点的成功可作为完整地面找箱流程的候选，hold/pickup RSI必须单独解释。

actor/critic仍只用深度与本体，监督标签和AMP边界不变；未改足球、共享资产、CarryBox-v0或公共PPO/AMP。部署执行位置目标时也应复现本版hard-limit目标裁剪，导出的策略网络本身输出原始action。

## 兼容与验证

schema仍为2，环境revision升为7，契约记录头部COM、膝限位奖励、目标裁剪、共同课程/RSI和圆柱数量。旧revision6完整load/resume明确拒绝。显式weights-only接口仍为旧兼容功能，不用于本次正式命令；也不表示旧模型适合迁移。

[最终回执](final_receipts.json)：41项CPU PASS；wall3/wall4各3次新PPO更新+新runner恢复后1次更新，AMP实际优化器有更新且参数有限，数据身份为规范15段。两者分别通过墙/圆柱深度遮挡与真实碰撞、平台支撑、三技能reset、实际COM变换、位置目标hard limits、参考膝惩罚和旧契约拒绝。新统计不作为训练成功证据。

首次CPU检查发现旧queue单测mock缺新配置字段，补齐后修正一次测试缩进；未删除断言或改变其语义。原失败回执保留。最终CPU由同一冻结命令单独复查，GPU回执复用已通过结果；GPU通过后仅新增实际回合步数统计修正，使用包含随机timeout年龄的CPU回归验证，来源写入final_receipts.json。

[wall3结果](wall3/result.json) · [wall4结果](wall4/result.json) · [源码hash](source_hashes.json)。新配方仍需正式长训与独立完整拾箱成功率评估，不能承诺沿用旧版4.2秒/轮实测结果。

## Wall3 正式训练命令

先停止旧wall4释放GPU；本次没有代为停止。确认旧进程身份后可在原训练终端停止，或对核对后的训练PID发送SIGINT。随后在仓库根目录执行：

```bash
cd /home/cao/perceptual_ball
mkdir -p logs/rsl_rl/g1_carrybox_depth/walled3
set -o pipefail
CARRYBOX_VARIANT=3 bash scripts/rsl_rl/train_carrybox_walled.sh \
  --num_envs 4096 --max_iterations 40000 \
  --run_name wall3_common_v7_scratch \
  2>&1 | tee logs/rsl_rl/g1_carrybox_depth/walled3/train_wall3_v7.log
```

这是从头训练；不追加旧checkpoint参数。终端日志路径如上，模型和TensorBoard在walled3下自动创建的时间戳run目录。Warp深度无需`--enable_cameras`。复用相同终端日志名会覆盖该终端文件，可在多次运行时自行使用不同名字；模型目录按时间戳独立创建。
