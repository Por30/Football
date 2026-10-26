# AgileKickball v4 model49999 demo

已完成指定最终checkpoint的单机器人demo：**30秒、1920×1080、25fps、H.264 MP4，30.59 MiB**。完整750帧解码与关键画面检查通过。

[播放/下载MP4](../../../outputs/football/agilekickball_v4_demo_20261026/agilekickball_v4_model49999_demo_30s_1080p.mp4) · [关键帧拼图](../../../outputs/football/agilekickball_v4_demo_20261026/contact_sheet.jpg)

原始连续播放，seed42、均值动作，保留全部重置与任务过程。仅改变旁观相机和直射照明；原任务物理、奖励、观测与重置不变。

- 模型：`logs/rsl_rl/agilekickball_v4/2026-10-12_13-48-41_return_to_sender_20261012_v3init/model_49999.pt`
- 任务：`Template-Perceptual-Ball-AgileKickball-v4`
- 原模型课程：0.4–6 m/s、发球距离1.3–2 m、回传门半宽0.2 m。没有球速覆盖。
- 推理方式：复用`BallRegressionOnPolicyRunner.load(load_optimizer=False)`和`get_inference_policy`，按`play.py`在加载课程后重置；不进行训练或重新导出模型。
- 控制50Hz，隔2步采集1帧、25fps，实际模拟时间30秒；额外渲染不推进物理，无变速或插帧。
- 这是一段单seed仿真展示，不是独立总体成功率评估。

模型SHA256、当前源码身份与录像配置见[selection.json](selection.json)。回放记录见[recording.json](recording.json)，完整解码检查见[video_validation.json](video_validation.json)，执行回执见[receipts.json](receipts.json)。

复现命令（已有完整录像时仅执行校验，原输出不覆盖）：

```bash
bash docs/agilekickball_v4/demo_20261026/record_and_check.sh
```

已检查1秒与10秒原分辨率画面，以及0.04/1/2/5/10/15/20/25/30秒九帧拼图。机器人全身与白球均可辨；25秒关键帧可见伸腿回踢。固定斜侧视角无UI、debug线或字幕遮挡。机器人保持在画面内；本次完整30秒无回合终止/重置。控制记录显示25次足部击球、25次回传门命中（半宽0.2m）、24次恢复后再次发球。全部750帧保留，无剪辑、变速、补帧。单seed展示，不作总体成功率推断。

首次在RGB采集器创建前预热，首帧为空导致检查失败；修正为先创建采集器再预热，原失败记录保存在`attempt1_renderer_warmup/`。第二次完整录制和解码通过，未更改策略或任务参数。

录制前后核对原Kickball v11训练PID3814037持续存在，未发送停止/重启信号。训练状态见[录制前](formal_before.json)和[录制后](formal_after.json)，是带时间的快照。
