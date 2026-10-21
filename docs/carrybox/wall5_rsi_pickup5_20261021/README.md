# Wall5 RSI：从loco划出5%给pickup

wall5默认RSI由loco80% / pickup0% / hold20%改为75% / 5% / 20%；从loco让出5个百分点给地面pickup。

固定环境配额保持：4096环境为3072 loco、205 pickup、819 hold（离散取整约75% / 5.005% / 19.995%）。每个环境的技能类别在reset时保持，类内重新采样参考帧。20环境为15/1/4；只有4环境时仍是3/0/1，无法覆盖5%的pickup，验证因此使用20环境。

pickup仍只用`ground_pickup/pick_up/pick_up_03.pt`第0–31帧，机器人从对应拾取姿态初始化，箱底离地5mm，无平台。hold仍保留手边参考箱高。AMP专家采样仍40/40/20，数据、网络、观测、奖励、物理及wall3/wall4/football未改。

本次只改wall5配置一行及配额函数的过期说明。migration_revision仍19，因为算法和schema未改；完整环境契约已有`reset_probs`和`reset_skill_probabilities`记录实际比例，两项由[0.8,0,0.2]变为[0.75,0.05,0.2]。短测确认其他契约项完全相同，旧80/0/20模型直接完整resume会被拒绝。若需保留旧模型播放语义，应显式使用原比例；迁移到新比例训练可用既有显式weights-only warm-start入口，不能伪装成同契约resume。

验证通过：实际4096配额及分段边界；20环境4次全量reset均为15/1/4，loco/pickup箱底5mm、hold保留高位；pickup局部reset不改其他环境的根状态、关节角或箱子；强制pickup超时后的自动reset/观测/奖励有限；pickup可用帧池恰为0–31；旧checkpoint严格恢复拒绝；其余生产Python文件hash不变。未进行PPO更新或长期成功率评估。

后台PID570043于2026-10-21T12:42:49.157757+09:00核对仍为原训练命令=True。本次未停止或重启，它仍使用启动时的80/0/20。新默认75/5/20在下一次创建环境/启动训练时生效。

[实测](check.json) · [执行回执](receipts.json) · [进程快照](formal_status.json)

复查命令：`bash docs/carrybox/wall5_rsi_pickup5_20261021/check.sh`。
