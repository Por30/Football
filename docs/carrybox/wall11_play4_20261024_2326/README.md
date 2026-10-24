# Wall11 model9500 四机器人回放

wall11 model_9500四机器人20秒同步回放完成，1080p/25fps、seed42均值动作，保留深度噪声、墙柱、物理扰动和全部reset。3个loco与1个默认地面箱起点均出现拾箱并站立持箱，四机均到20秒正常超时，无提前失败终止；严格保持最长0.90/1.40/0.20/0.00秒，均未达连续2秒成功。

[播放视频](../../../outputs/carrybox/wall11_play4_20261024_2326/wall11_model_9500_4robots_20s_preview.mp4)（19.8 MiB），[原始视频](../../../outputs/carrybox/wall11_play4_20261024_2326/wall11_model_9500_4robots_20s.mp4)，[关键帧拼图](../../../outputs/carrybox/wall11_play4_20261024_2326/contact_sheet.jpg)。

模型于2026-10-24 23:26 JST选取：当时正式wall11 24步run最新完整`model_9500.pt`；完整路径、SHA256与7份生产源码身份见[selection.json](selection.json)。严格加载schema2/walled11 revision1，未修改权重或生产任务。4环境、1000控制步（50Hz），4独立高位旁观相机同步采集500帧；渲染不推进物理，逐步验证角标深度等于actor实际带噪输入。

| 机器人 | 起点 | 箱底最高离地/m | 严格保持最长/s | 回合终止 |
|---|---|---:|---:|---|
| 1 | loco，地面箱 | 0.736 | 0.90 | 20秒超时 |
| 2 | loco，地面箱 | 0.658 | 1.40 | 20秒超时 |
| 3 | loco，地面箱 | 0.681 | 0.20 | 20秒超时 |
| 4 | 默认站姿，地面箱 | 0.704 | 0.00 | 20秒超时 |

已查看初始画面、5/10/19.96/20秒原分辨率关键帧，以及0.04/1/2/5/10/15/19.96/20秒关键帧拼图。四个机器人、箱子、三圆柱和墙可辨，带噪深度角标显示实际actor输入。前三格为loco RSI地面箱起点，第四格为default地面箱起点。四格均出现接近、下探并从地面抬箱，后段维持持箱站姿。四个完整回合均在20秒正常超时，无提前tipped/fell等失败终止；末帧已随机reset，第四格改为明确标注的hold参考起点。严格保持计数与视觉持箱不同：最长分别0.90/1.40/0.20/0.00秒，均未达到连续2秒成功。全部500帧保留；此单seed录像不作总体成功率结论。


录像执行与原始/预览视频完整解码检查通过，均为1920×1080、25fps、500帧、20秒。见[receipts.json](receipts.json)、[video_validation.json](video_validation.json)、[delivery.json](delivery.json)、[per_robot_behavior.json](per_robot_behavior.json)。保留所有回合，没有剪辑、变速或插帧。

正式训练PID2723259保持同一进程，核验期间从iteration 9513推进到9553；见[formal_before.json](formal_before.json)与[formal_after.json](formal_after.json)。本次仅录制与验证，未结束长训或进行独立成功率评估。
