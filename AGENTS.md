# 仓库协作约定

## 两条项目线

先读根README及`projects/README.md`，再读所涉项目入口：

- 足球 / football：`projects/football/README.md`。当前主线AgileKickball-v4，v3为初始化基线，其他版本保留历史兼容。
- 找箱/搬箱子 / findbox：`projects/findbox/README.md`。已验证基线CarryBox-v0 + FindBox AMP，checkpoint schema=2；walled3/walled4迁移的验收状态以项目入口为准。

`projects/findbox/`与`projects/football/`是并列项目入口；`projects/carrybox`仅为findbox旧入口兼容别名。根目录`findbox/`是原始数据目录，不能与项目入口混用。CarryBox源码名、Gym ID、日志路径及历史工件前缀沿用原名称。

用户当次指令优先；这些约定用于明确归属和保存证据，不增加额外审批步骤。

## 修改范围与信息边界

优先修改对应任务模块。G1资产、通用CNN/AMP、train/play和export是共享代码，修改前检查两条任务调用路径，并针对实际影响验证。

CarryBox默认actor/critic只使用深度与本体；位姿标签用于辅助监督，AMP窗口只进入判别器/奖励。2026-10-19按用户明确要求，wall5 revision14改为非对称AC：actor仍只用深度与本体，critic独立MLP使用当前本体、机体线速度及箱子相对位姿/尺寸真值（108维）；2026-10-21按用户明确要求，wall5 revision22在原108维尾部追加双掌/双踝/mid360连杆原点相对骨盆位置15维，critic为123维；辅助监督系数1.0、全部配对帧，可见性仅作诊断。这是仅wall5训练端的例外，特权输入不得进入actor或部署导出。2026-10-17按用户明确要求，wall5 revision12的训练专用AMP使用60维任务特征（含箱子相对位置/末端位置等）与Normalizer；其他CarryBox沿用原AMP及无特权actor/critic。任务阶段不加入策略/价值输入。足球现有critic配置独立，不能因搬箱子要求擅自改变足球训练接口。

保留Gym task ID、已有源码导入路径、数据路径和checkpoint路径，除非用户要求迁移。2026-10-14按用户要求规范命名并迁移后，FindBox AMP与walled参考初始化默认使用`source/perceptual_ball/perceptual_ball/assets/motions/findbox/`，与足球`assets/motions/kick/`并列。根目录`findbox/`保留为旧命名兼容快照，不与项目入口混用；`assets/motions/carrybox/`仍只是旧pickUp归档。数据更改须同步manifest、文件名映射和兼容性说明。

## 运行与记录

进度文档中的PID、迭代数、模型路径是带日期的快照。涉及启动或恢复训练时先只读核对实际进程、日志、checkpoint版本和资源，执行用户已授权范围内的工作；不得因旧文档写“正在运行”就推断实时状态。

正式产物分别写入`logs/rsl_rl/agilekickball_v4/`和`logs/rsl_rl/g1_carrybox_depth/`。验证模型留在对应docs目录，不能作为正式训练或成功率证据。项目管理/文档整理本身不意味着启动、停止或重启训练。

工程记录沿用`agent/{plan,task,report,handoff}/`，足球用`agilekickball-*`前缀，搬箱子用`carrybox-*`前缀。完成任务实现、验证或训练状态变化后，更新对应project入口及总看板，明确区分实现完成、短测通过、正式训练结束和独立评估结论。

保留工作区已有未提交改动、训练数据、模型和历史记录；不做无关清理。测试选择见各project入口；文档变更检查路径与命令即可，不自动启动GPU训练或完整仿真。
