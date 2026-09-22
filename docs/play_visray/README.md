# Play 深度视场可视化

在播放命令末尾加 `--visray` 开启；不加则关闭。仅影响调试显示，不改训练、策略输入、球速或物理状态。

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-AgileKickball-v0 \
  --num_envs 4 \
  --checkpoint /home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v0/2026-09-20_18-02-42_learning_fix/model_25000.pt \
  --ballspeed 0.4 3 \
  --visray
```

- 绿色细射线：从实际虚拟相机安装点出发，按深度像素方向抽样显示，包含四周边界，随躯干姿态更新。
- 绿色小点：全部像素的深度端点；背景像素位于最大量程。
- 明亮较大的绿点：未饱和的深度返回点；v0 无深度噪声时对应球面命中点。

当前 v0/v1 为 48×27 像素、垂直 FOV 58°、沿射线量程 0.1–3.0 m。显示复用感知项的实际 ray_x/y/z、torso_link 世界姿态、相机 offset 和最新深度历史帧；不是另估一个近似相机。像素边界射线经过最外层像素中心，因此显示的是采样覆盖范围。

当前深度是解析的球面相交，不包含地面、机身或其他物体遮挡。背景绿点只是远量程端点，不应当作真实场景点云；射线可能穿过地面或机身。加入噪声的同类任务中，绿点反映实际观测噪声。

无需为 GUI 播放额外加 `--enable_cameras`：默认使用 debug_draw 覆盖显示。截图/视频或无窗口离屏渲染另需渲染支持。所有播放环境均显示；4环境为5184点、288条抽样射线，每步替换旧图元。退出播放清理图元。此模块使用 debug_draw 的全局点/线接口，勿与另一个也逐帧清空该接口的调试覆盖层同时使用。

兼容 AgileKickball-v0/v1 的即时解析深度。不支持带传感器延迟的 Soccer-v3 深度项；该项若要投影深度点，需要历史采样时刻的相机位姿，当前会明确报错。

验证命令：

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_play_visray.py
bash scripts/rsl_rl/smoke_play_visray.sh
```

边界测试覆盖开关与ballspeed组合、球面相交端点、欧氏距离、安装与躯干旋转、不同环境位置、最新帧选择、绿色属性、图元清理、非有限像素过滤，以及输入历史和随机数状态不变。真实仿真使用上述v0模型和4个环境，验证图元计数、实际渲染截图与退出清理。详见 `smoke.json`、`visray.png` 和 `receipts.json`。
