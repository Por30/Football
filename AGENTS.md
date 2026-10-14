# 仓库协作约定

## 两条项目线

先读根README及`projects/README.md`，再读所涉项目入口：

- 足球 / football：`projects/football/README.md`。当前主线AgileKickball-v4，v3为初始化基线，其他版本保留历史兼容。
- 找箱/搬箱子 / findbox：`projects/findbox/README.md`。已验证基线CarryBox-v0 + FindBox AMP，checkpoint schema=2；walled3/walled4迁移的验收状态以项目入口为准。

`projects/findbox/`与`projects/football/`是并列项目入口；`projects/carrybox`仅为findbox旧入口兼容别名。根目录`findbox/`是原始数据目录，不能与项目入口混用。CarryBox源码名、Gym ID、日志路径及历史工件前缀沿用原名称。

用户当次指令优先；这些约定用于明确归属和保存证据，不增加额外审批步骤。

## 修改范围与信息边界

优先修改对应任务模块。G1资产、通用CNN/AMP、train/play和export是共享代码，修改前检查两条任务调用路径，并针对实际影响验证。

CarryBox的actor/critic只能使用深度与本体；位姿标签只进入辅助监督，AMP本体窗口只进入判别器/奖励。不得把箱子真值或任务阶段加入策略/价值输入。足球现有critic配置独立，不能因搬箱子要求擅自改变足球训练接口。

保留Gym task ID、已有源码导入路径、数据路径和checkpoint路径，除非用户要求迁移。`findbox/*.pt`及其子目录动作文件是搬箱子原始数据；当前AMP使用根目录findbox，不使用assets下旧pickUp参考副本。数据更改须同步manifest和兼容性说明。

## 运行与记录

进度文档中的PID、迭代数、模型路径是带日期的快照。涉及启动或恢复训练时先只读核对实际进程、日志、checkpoint版本和资源，执行用户已授权范围内的工作；不得因旧文档写“正在运行”就推断实时状态。

正式产物分别写入`logs/rsl_rl/agilekickball_v4/`和`logs/rsl_rl/g1_carrybox_depth/`。验证模型留在对应docs目录，不能作为正式训练或成功率证据。项目管理/文档整理本身不意味着启动、停止或重启训练。

工程记录沿用`agent/{plan,task,report,handoff}/`，足球用`agilekickball-*`前缀，搬箱子用`carrybox-*`前缀。完成任务实现、验证或训练状态变化后，更新对应project入口及总看板，明确区分实现完成、短测通过、正式训练结束和独立评估结论。

保留工作区已有未提交改动、训练数据、模型和历史记录；不做无关清理。测试选择见各project入口；文档变更检查路径与命令即可，不自动启动GPU训练或完整仿真。
