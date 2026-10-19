# wall5 roll终止改为0.5rad

2026-10-19，按用户指令完成单参数变更。wall5现在使用`abs(wrap_to_pi(roll)) > 0.5`，左右侧倾均生效；pitch仍为`abs(pitch) > 1.1`，高度、超时及失败奖励权重不变。源码见[carrybox_wall5.py](../../../source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py)。wall3/4原本就是0.5，足球未修改。

| roll阈值 | 角度 | 含义 |
|---|---:|---|
| 原0.8rad | 45.84° | 允许更大侧倾，留出更多恢复时间，也可能继续采集已明显失衡的状态 |
| 新0.5rad | 28.65° | 侧倾终止更早，减少大倾角状态，也减少自行恢复的机会 |

例如侧倾0.6rad（34.38°），新阈值触发tipped，旧阈值不会仅因roll触发。严格大于，不是大于等于；同一状态轨迹下，收紧roll不会延后侧倾终止。训练后的回合长度和成功率仍需实测，不能把改小阈值当作控制更稳定的证明。此前model11200主要因pitch前倾超限快速reset，这次没有改变pitch条件，因此不构成该问题已修复的证据。

在revision15基础上只改roll参数，并同步checkpoint契约中的`roll_termination`和`roll_limit`；不启用此前已撤回的revision16控制候选。旧0.8契约checkpoint与新环境不同，现有严格加载会拒绝直接resume；复现旧模型应使用对应归档环境，权重迁移需明确采用warm-start。

既有wall5训练边界测试更新到±0.499/±0.501rad。冻结命令`bash docs/carrybox/wall5_roll05_20261019/check.sh`运行14项CPU检查全部通过，见[回执](receipts.json)。未运行GPU仿真或训练，未启动、停止或重启任何训练。
