# Wall5 revision14 独立播放命令

```bash
cd /home/cao/perceptual_ball
bash docs/carrybox/wall5_rev14_play_20261019/play.sh \
  /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/model_11200.pt \
  4
```

最后参数为1–4个环境，默认4；窗口关闭或Ctrl+C结束。脚本自行加载本机Isaac环境，无需额外conda激活。默认镜头对准env0，可在GUI移动视角查看其他环境。

使用先前20秒录像已验证的revision14归档配置/环境类，严格比较checkpoint契约和加载完整网络。旧直接设速度推扰与0.5/average摩擦保持，均值动作，seed42；此fresh run的课程以零锚点重建至checkpoint轮数（11200轮yaw12.4°、满推扰）。当前生产源码revision15不受影响；不创建optimizer或写导出/checkpoint。

本次CPU核对model11200严格加载、4×29有限输出、归档hash与前次20秒录像相同、模型环境契约匹配、Python及bash语法通过；[结果](check.json)和[回执](receipts.json)。此次未启动GUI/GPU仿真或操作正式训练，不能将CPU检查称为新GUI运行验收。
