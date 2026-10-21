# Wall5 最新checkpoint：四机器人高位镜头

选取时最新完整模型：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-20_13-49-44_wall5_v19_g1_semantic_fresh_20261020_134939/model_5600.pt`，revision19。选取时间2026-10-20T19:30:23.234485+09:00；录制期间训练继续推进，本视频固定使用该模型。

[观看20秒MP4](../../../outputs/carrybox/wall5_play4_high_20261020/wall5_rev19_model5600_4robots_high20s.mp4) · [关键帧拼图](../../../outputs/carrybox/wall5_play4_high_20261020/contact_sheet.jpg)

录制model_5600.pt，4环境同步20秒、1920×1080/25fps四宫格，旁观相机基准高度5.8m（上次3.85m）。保留默认3个loco/地面箱起点和1个明确标注的hold参考起点。每个机器人reset次数分别为[1, 1, 1, 1]，没有裁剪失败片段。

同一次play创建4个环境，统一批量策略推理和50Hz物理控制；每两个控制步，四台独立旁观相机同时渲染同一物理时刻，合成一帧四宫格。不是四次回放拼接；所有自动reset均保留。每格960×540，合成1920×1080，25fps/500帧/20秒。

相机跟随各自机器人与箱子的中点，从墙的对侧俯视。目标高0.6m、镜头高偏移5.2m、水平偏移3.6m，因此基准镜头距地5.8m；机器人远离箱子时按距离扩大取景。焦距30mm、水平aperture20.955mm。每帧检查渲染前后物理时间、控制步计数与机器人位置完全一致。实际相机轨迹见camera_trajectory.json。

**前三格为空手起点，第四格为持箱参考初始化。第四格开场已有箱子不代表学会了从地面抱起。** 保留任务的固定RSI配额[0,0,0,2]、原13m环境间距、碰撞/墙/圆柱/深度噪声与遮挡。每格右下角是对应actor收到的最新深度帧；旁观相机位置不影响actor输入。

严格核对完整环境契约并加载原权重，恢复checkpoint第5600轮的yaw课程5.60°、增量推扰强度1.00；seed42、均值动作、无训练/优化器更新。

## 表现与回合

已检查0.04、1、2、5、10、15、19.96和20秒关键帧，四个机器人、箱子及深度角标清晰可见，旁观镜头已升高。前三个空手起点均走到箱旁后主要站立与小幅调整，未完成地面拾箱；1号后段有明显后仰。4号从持箱参考姿态开始，本段箱子中心高度约0.76–0.85m，不能算作从地面抱起。四个环境均没有倾倒或低高度终止，唯一reset均发生于第1000步、20秒超时，最后一帧保留了reset后的画面。这仅代表这四个起点的均值动作回放，不作为成功率评估。

| 机器人 | 参考起点 | reset次数 | 原因 | 窗口末回合已执行 |
|---|---|---:|---|---:|
| 1 | 空手/地面箱 | 1 | tipped=0, fell=0, timeout=1 | 0.00s |
| 2 | 空手/地面箱 | 1 | tipped=0, fell=0, timeout=1 | 0.00s |
| 3 | 空手/地面箱 | 1 | tipped=0, fell=0, timeout=1 | 0.00s |
| 4 | 持箱参考 | 1 | tipped=0, fell=0, timeout=1 | 0.00s |

这是四个环境的一段回放，不作为成功率评估；持箱参考起点需与地面拾箱分开理解。

完整解码与四格主画面检查PASS：500帧、20.0秒，文件约17.19MiB。源代码/模型hash和模型权重不变。后台PID570043在2026-10-20T19:42:18.557446+09:00核对仍为原命令=True，本次未停止、重启或调参。

第一次录制已生成完整视频，但结束时调用当前Replicator版本的`annotator.detach([HydraTexture])`触发清理异常。仅停止该失败录制子进程679979，后台训练PID570043未操作；失败回执、日志与视频保留在docs/outputs各自的`attempt1_cleanup_error/`。按本机接口修正为无参detach并显式释放render product后，以相同模型/seed/配置重新完整录制和验证，没有筛选成功轨迹或放宽检查。

[选择记录](selection.json)、[回合和配置](recording.json)、[轨迹](trajectory.json)、[相机轨迹](camera_trajectory.json)、[视频检查](video_validation.json)、[执行回执](receipts.json)。

复现命令（已有视频不会被覆盖；再次录制需新目录）：

```bash
cd /home/cao/perceptual_ball
bash docs/carrybox/wall5_play4_high_20261020/record_and_check.sh
```
