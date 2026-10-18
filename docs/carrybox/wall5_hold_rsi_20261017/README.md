# Wall5 hold RSI比例调整（revision13）

2026-10-17，用户明确要求“改成0.2是hold”。默认`reference_init=True`：100% reset使用RSI，技能概率由80/20/0改为 **loco80%、pickup0%、hold20%**。这不是AMP专家组权重；AMP仍为0.4/0.4/0.2，13段数据逐字节保留。

hold按“已经抱住箱子”的参考状态初始化，箱子保留手边参考高度；loco仍箱底离地5mm。新增wall5显式`held_box_reference_reset=True`，允许hold越过旧的全贴地限制。未开启该选项的旧ground配置继续拒绝hold；wall3/4及football行为保持。无平台、全身碰撞、深度、60维AMP、PPO配方不变；pickup安全范围0–31仍保留，但默认概率为0。

环境契约升级revision13、记录held_box_reference_reset及新的box_reset_profile；run_name为walled5_task_amp_v13_hold_rsi。revision12的完整resume会因reset契约不同被拒绝；网络形状与revision12一致，需要迁移时只能显式weights-only使用已有入口，不能把当前进程热切换成新配置。此次没有启动/停止/重启正式训练。

验证：14项CPU；4环境48次随机初始化观测到loco41、pickup0、hold7（有限随机样本，不要求恰好80/20）。loco贴地；hold箱底约0.731m，手中心到箱心最大约0.0542m。覆盖hold原始0–20帧和重复尾部298帧、各首20ms物理步骤、partial与自动reset；状态与观测有限，历史数据hash保持。测试不包含PPO更新或长期持箱稳定性。首20ms箱速最高约1.64m/s，存在接触瞬态，不能把此次reset通过等同于稳定抓握/收敛；未额外调整接触体或控制器。

回执：[receipts.json](receipts.json)，实测：[smoke.json](smoke.json)。

```bash
bash docs/carrybox/wall5_hold_rsi_20261017/check.sh
bash docs/carrybox/wall5_hold_rsi_20261017/smoke.sh
```
