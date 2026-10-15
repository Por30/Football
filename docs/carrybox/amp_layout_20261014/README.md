# FindBox AMP 规范命名与并列目录

2026-10-14按用户要求，已将整理好的15段数据以规范名称放到`source/perceptual_ball/perceptual_ball/assets/motions/findbox/`，与足球`assets/motions/kick/`并列。

[数据目录、全部文件及对应视频](../../../source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md) · [旧新名称映射](../../../source/perceptual_ball/perceptual_ball/assets/motions/findbox/filename_mapping.json) · [迁移hash记录](migration.json) · [测试回执](test_receipts.json)

## 结果

目录分为`locomotion/`（11段）、`pick_up/`（3段）、`hold/`（1段）。文件名均为小写下划线，重复动作编号为两位，转向角为三位度数。抱箱文件为`hold/hold_box_01.pt`，保持300帧、60Hz、5秒。全部15段总4155帧，与根findbox修订2逐字节相同；本次没有重新编辑动作张量。

新manifest的schema仍为1，dataset_revision=3，version=`findbox_hold_v1_named`；新增显式group和原source_file。目录名对应的历史运行时语义为`locomotion→loco_direction`、`pick_up→pickUp`、`hold→carryWith`，保留40/40/20组权重。旧manifest省略group时按原目录名识别；目录与group不匹配会拒绝加载。

## 加载与兼容性

`FindBoxMotionLibrary()`、CarryBox PPO/配置和walled参考初始化默认使用同一规范目录。RSI按其motion library实际root读取位姿文件，避免混用目录。录制工具也默认读取规范目录，并在新recording.json中保存dataset_path；已有15段视频验证仍使用旧根findbox身份，视频内容与新文件等价，无需重新渲染。

根`findbox/`保留旧命名15段完整快照，`FindBoxMotionLibrary('findbox')`或绝对旧路径继续加载它。修改前17段完整原始数据仍在`docs/carrybox/amp_hold_20261014/original_dataset/`。`assets/motions/carrybox/`旧拾箱归档及足球kick两段内容与加载器均未改动。

新manifest SHA-256为`59ade1b9cbff54e5f62c34028923428efa7b76a21f1866aeab2954799f8d3ee8`，旧15段manifest仍为`a6240ca6a4c0991a35860c8f336d48e067bcfd6968930876b8a88177c5dda507`。虽然张量不变，文件名和manifest身份改变，现有严格检查会拒绝把旧完整AMP checkpoint直接恢复到新manifest。没有修改checkpoint、绕过检查或自动启动/恢复训练。

显式覆盖AMP数据目录不会自动改写RSI数据版本；后续跨版本恢复需同时核对两者。当前新默认二者一致。运行中的旧进程不热更新，本次未发送训练进程信号。

## 验证

CPU检查通过：全部15段新旧字节一致；首末合法AMP窗口逐元素一致；归一化组概率相同；默认路径在不同cwd下不变；显式旧目录和原17段快照可加载；错误group被拒绝；AMP实际更新/恢复通过；新旧manifest完整恢复被拒绝。CPU实际调用walled `initialize_reference`覆盖行走/拾箱/抱箱三种技能，验证其使用新目录、状态有限且抱箱静止段速度为零。足球kick及旧carrybox归档hash保持。

已有15段60fps视频完整解码4155帧及源hash再次通过。本次是目录/命名迁移，没有启动GPU仿真或训练；不增加策略学习效果结论。

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_amp.py -v
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_walled.py -v
/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_hold_20261014
```
