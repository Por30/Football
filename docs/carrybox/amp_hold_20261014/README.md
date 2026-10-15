# CarryWith 开头抱箱保留与 AMP 整理

2026-10-14，按用户要求只保留carrywith1开头并延长抱箱姿态，移出carrywith2/3，重新逐PT录制全部有效动作。

- [修改后的抱箱视频（5秒）](../../../outputs/carrybox/findbox_hold_20261014/carryWith/carrywith1.mp4)
- [全部15段独立视频、预览、帧范围](../../../outputs/carrybox/findbox_hold_20261014/README.md)
- [新AMP manifest](../../../findbox/amp_manifest.json)
- [原17段完整数据与旧manifest](original_dataset/)
- [精确编辑与源帧映射记录](edit_record.json)
- [CPU与视频执行回执](test_receipts.json)

## 数据变更

原carrywith1为256帧。结合画面与关节差分，开头0–20帧是站立抱箱，约27帧后关节运动明显增加。保留原0–20帧，随后重复原第20帧至300帧，60Hz共5秒。时长询问未收到不同选择时采用已告知的5秒默认值。

| 新帧（0起始，含首尾） | 来源 | 处理 |
|---|---|---|
| 0–19 | 原0–19 | 所有字段原样保留 |
| 20 | 原20 | 姿态保留，速度置零，作为静止段起点 |
| 21–299 | 原20 | 机器人、关节、末端及箱体位置一起重复；三类速度持续为零 |

置零字段为`base_linear_velocity`、`base_angular_velocity`、`joint_velocity`。保持完整字段集合、float32、xyzw和29关节顺序。所有位姿的拼接连续，静止尾段没有循环回跳；由AMP重新差分得到的关节速度为零，根角速度在浮点容差内为零。这是用户要求的合成静止参考，并非新的采集动作。

当前有效集合为行走11、拾箱3、抱箱1，共15段、4155帧；组采样权重仍为40/40/20%。14段行走/拾箱文件逐字节不变。`carrywith2/3`从根findbox移出，保存于`excluded_from_active/`，且完整旧数据快照也含它们。原始carrywith1在快照中保留，现有路径`findbox/carryWith/carrywith1.pt`用于修改版。

manifest格式schema仍为1，新增dataset_revision=2、dataset_version=`carrywith1_prefix_hold_v1`及来源记录；新manifest SHA-256为`a6240ca6a4c0991a35860c8f336d48e067bcfd6968930876b8a88177c5dda507`，旧manifest为`eef4d55d77eb26b46fd1be58da628edd07920f5e02198a7636c2e83253e5cb3c`。

## 验证与训练兼容性

AMP测试检查15段分组、组权重、静止窗口、全字段帧映射、保留数据不变、旧17段快照可加载、坏hash拒绝、完整AMP参数更新和checkpoint恢复契约。walled测试覆盖参考初始化合同。两组CPU测试通过；15段视频完整解码4155帧、60fps、960×720、源hash通过。视频是当前G1的运动学回放，箱体朝向和支撑台仍为示意；未执行新的策略训练或成功率评估。

checkpoint仍为schema=2，但旧17段训练checkpoint携带旧manifest身份，不能直接在新数据上完整恢复AMP优化器/统计状态，已有拒绝检查保留。旧快照按原manifest可独立加载。本次没有重启或切换训练；正在运行的AMP和RSI均缓存了启动时的数据，不会读取本次更新。walled RSI固定读取根findbox，后续版本切换必须同时处理AMP与RSI，不能仅修改AMP目录就声称二者一致。

修改脚本`prepare_dataset.py`保留为可重现记录，只接受原manifest身份且拒绝覆盖已存在的备份，不应在当前修改版上重复执行。

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_amp.py -v
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_walled.py -v
/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_hold_20261014
```

单段重新录制可使用`bash scripts/visualize_findbox.sh --individual --clip carryWith/carrywith1.pt --output outputs/carrybox/findbox_hold_review`，输出应选新目录。旧17段视频及其源PT索引保留，源链接已指向原始备份。
