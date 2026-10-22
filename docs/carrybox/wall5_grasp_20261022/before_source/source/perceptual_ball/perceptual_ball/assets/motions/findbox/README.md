# FindBox AMP 数据集

2026-10-17：wall5专用[ground_pickup](ground_pickup/README.md)新增地面拾取profile（13段、3785帧），拾取只使用完整`pick_up_03`；本目录15段及其manifest保持原样，继续供CarryBox基线、wall3/wall4使用。wall5的AMP与RSI均显式切换到子目录，旧模型需要显式weights-only迁移。

这是整理后的正式数据目录，与同级`../kick/`足球AMP数据并列。15段、4155帧、60Hz；抱箱片段5秒。AMP与walled参考初始化默认使用本目录。

```text
assets/motions/
├── kick/                         # 足球AMP（保留原样）
├── findbox/                      # 本数据集
│   ├── locomotion/               # 11段行走
│   ├── pick_up/                  # 3段拾箱
│   ├── hold/hold_box_01.pt        # 300帧、5秒抱箱
│   ├── amp_manifest.json
│   └── filename_mapping.json
└── carrybox/                     # 旧拾箱归档，不作为默认数据
```

命名使用小写下划线；同类重复动作用两位序号，转向角用三位度数045/090/135。动作张量逐字节保留，不因更名或复制发生变化。

| 新文件 | 原文件名 | 帧数 | 视频 |
|---|---|---:|---|
| [hold/hold_box_01.pt](hold/hold_box_01.pt) | `carryWith/carrywith1.pt` | 300 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/carryWith/carrywith1.mp4) |
| [locomotion/walk_turn_left_045.pt](locomotion/walk_turn_left_045.pt) | `loco_direction/B10_-_walk_turn_left_(45)_stageii.pt` | 253 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B10_-_walk_turn_left_%2845%29_stageii.mp4) |
| [locomotion/walk_turn_left_135.pt](locomotion/walk_turn_left_135.pt) | `loco_direction/B11_-_walk_turn_left_(135)_stageii.pt` | 289 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B11_-_walk_turn_left_%28135%29_stageii.mp4) |
| [locomotion/walk_turn_right_090.pt](locomotion/walk_turn_right_090.pt) | `loco_direction/B12_-_walk_turn_right_(90)_stageii.pt` | 263 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B12_-_walk_turn_right_%2890%29_stageii.mp4) |
| [locomotion/walk_turn_right_045.pt](locomotion/walk_turn_right_045.pt) | `loco_direction/B13_-_walk_turn_right_(45)_stageii.pt` | 256 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B13_-_walk_turn_right_%2845%29_stageii.mp4) |
| [locomotion/walk_turn_right_135.pt](locomotion/walk_turn_right_135.pt) | `loco_direction/B14_-_walk_turn_right_(135)_stageii.pt` | 321 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B14_-_walk_turn_right_%28135%29_stageii.mp4) |
| [locomotion/walk_turn_around_01.pt](locomotion/walk_turn_around_01.pt) | `loco_direction/B15_-_walk_turn_around_(same_direction)_stageii.pt` | 329 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B15_-_walk_turn_around_%28same_direction%29_stageii.mp4) |
| [locomotion/stand_to_walk_01.pt](locomotion/stand_to_walk_01.pt) | `loco_direction/B1_-_stand_to_walk_stageii.pt` | 342 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B1_-_stand_to_walk_stageii.mp4) |
| [locomotion/walk_to_stand_01.pt](locomotion/walk_to_stand_01.pt) | `loco_direction/B2_-_walk_to_stand_stageii.pt` | 340 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B2_-_walk_to_stand_stageii.mp4) |
| [locomotion/walk_to_stand_02.pt](locomotion/walk_to_stand_02.pt) | `loco_direction/B2_-_walk_to_stand_t2_stageii.pt` | 293 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B2_-_walk_to_stand_t2_stageii.mp4) |
| [locomotion/walk_forward_01.pt](locomotion/walk_forward_01.pt) | `loco_direction/B3_-_walk1_stageii.pt` | 456 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B3_-_walk1_stageii.mp4) |
| [locomotion/walk_turn_left_090.pt](locomotion/walk_turn_left_090.pt) | `loco_direction/B9_-_walk_turn_left_(90)_stageii.pt` | 214 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/loco_direction/B9_-_walk_turn_left_%2890%29_stageii.mp4) |
| [pick_up/pick_up_01.pt](pick_up/pick_up_01.pt) | `pickUp/pickup1.pt` | 192 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/pickUp/pickup1.mp4) |
| [pick_up/pick_up_02.pt](pick_up/pick_up_02.pt) | `pickUp/pickup2.pt` | 178 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/pickUp/pickup2.mp4) |
| [pick_up/pick_up_03.pt](pick_up/pick_up_03.pt) | `pickUp/pickup3.pt` | 129 | [查看](../../../../../../outputs/carrybox/findbox_hold_20261014/pickUp/pickup3.mp4) |

持箱片段保留旧carrywith1的0–20帧，之后重复旧第20帧姿态至300帧；静止段速度为0。

manifest schema=1、dataset_revision=3。显式`group`维持历史AMP/RSI语义：locomotion→loco_direction，pick_up→pickUp，hold→carryWith；组采样概率仍为40/40/20%。checkpoint schema仍为2，但manifest身份随命名改变，旧完整AMP状态不能静默恢复到本目录。

根目录`findbox/`保留为修订2兼容快照；显式指定该路径仍加载旧命名。首次17段原始数据备份及旧视频保持原样。本次未启动或切换训练。

[迁移记录与验证](../../../../../../docs/carrybox/amp_layout_20261014/README.md) · [旧新文件名映射](filename_mapping.json) · [AMP manifest](amp_manifest.json)

从仓库根目录重新录制指定片段：

```bash
bash scripts/visualize_findbox.sh --individual --clip hold/hold_box_01.pt --output outputs/carrybox/findbox_named_review
```

需要读取旧目录时可显式加`--dataset findbox`并使用旧相对文件名。
