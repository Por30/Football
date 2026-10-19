# 当前wall5 AMP可视化（2026-10-18）

[完整63.08秒MP4](../../../outputs/carrybox/wall5_amp_20261018/wall5_amp_all.mp4) · [交互分段浏览](../../../outputs/carrybox/wall5_amp_20261018/index.html) · [缩略图总览](../../../outputs/carrybox/wall5_amp_20261018/overview.png) · [片段时间表](../../../outputs/carrybox/wall5_amp_20261018/README.md)

当前正式run的agent.yaml、env.yaml与model_0数据契约均确认使用`source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/`。13段为11段行走、1段完整地面拾箱03、1段持箱；3785原生帧，60fps，63.083秒。全部视频为1倍速，另提供13个独立MP4及本地HTML播放器。

- AMP采样：行走40% / 拾箱40% / 持箱20%；当前训练为60维任务AMP。
- RSI初始化：行走80% / 拾箱0% / 持箱20%，与AMP采样权重分别设置。
- 拾箱保留完整129帧，包括抬起阶段；排除的是两个高处拾箱片段。持箱保留原0–20帧，之后重复第20帧至300帧/5秒。
- 来源：源PT逐段SHA-256与`outputs/carrybox/findbox_hold_20261014/recording.json`完全一致，因此复用对应G1原生60fps逐帧画面，更换规范名称、标题及页脚。未运行额外GPU仿真，也未修改源数据或既有录像。
- 展示含义：运动学参考回放，不能作为当前策略表现或物理成功率。箱子位置来自源记录；源数据缺少箱体旋转，箱体朝向借用机器人yaw，参考支撑为示意。本视频不展示wall5的reset修正、障碍或深度。

验证于2026-10-18T21:59:21.220615+09:00通过：13个源PT及对应旧视频哈希一致；13段视频完整解码3785帧，合辑完整解码3785帧；每段首/中/末帧与旧源对应画面核对，重编码后画面平均绝对误差最大1.699/255；合辑39个抽检帧与分段逐像素相同。已人工检查新预览与总览标签。

正式训练PID3812053在验证时仍运行；本次没有停止、重启或调整训练。训练身份/源文件hash/每段帧区间见输出index.json，解码验证见verification.json，冻结命令回执见本目录receipts.json。视频中动作数量或时长不代表训练采样比例。

`build.py`为此次CPU导出与验证脚本，已有产物可用`--verify-only`检查；其中实时训练身份检查针对上述PID/run，训练结束后需以保存的身份记录解释该检查，勿把进程退出误解为视频损坏。
