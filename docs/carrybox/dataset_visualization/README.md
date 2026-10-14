# FindBox 数据集视频

2026-10-14后续：按逐段调整数据的需求，从每个原始PT分别直接录制[17段原生60fps视频](../../../outputs/carrybox/findbox_individual/README.md)。每个PT对应同名MP4、PNG预览和JSON帧记录，画面显示0起始源帧号及时间。全4628帧均保留，累计77.133秒，全部解码和源hash检查通过；见[独立录制回执](individual_test_receipts_20261014.json)。重录命令：`bash scripts/visualize_findbox.sh --individual --clip pickUp/pickup1.pt --output outputs/carrybox/findbox_pickup1_review`，省略`--clip`录制全部。输出目录必须为新目录；源数据仍未修改。

2026-10-14：核对当前根目录`findbox/`全部17个源文件及manifest的SHA-256，均与已有完整录像记录一致；复用该录像，新增[17段独立MP4及逐段索引](../../../outputs/carrybox/findbox_dataset/clips/README.md)。拾箱3段、持箱3段、行走11段，合计77.27秒，960×720、30fps、H.264/yuv420p。逐帧解码2318帧并与完整录像对应帧比较通过，最大单帧像素平均绝对误差2.314/255（来自重新编码）。查看[校验结果](../../../outputs/carrybox/findbox_dataset/clips/verification.json)及[执行回执](clip_test_receipts_20261014.json)。本次仅CPU视频处理，未启动仿真或调整训练。

输出：[findbox_dataset.mp4](../../../outputs/carrybox/findbox_dataset/findbox_dataset.mp4)。按拾起3段、持箱3段、行走11段顺序回放全部17个片段，画面标注来源文件、原速进度和回放性质。960×720，H.264 / yuv420p，30fps；原数据60Hz每隔一帧取样，保持1倍速。

这是数据集参考动作在当前G1模型上的运动学回放：按关节名对齐29自由度，源xyzw转换为wxyz，直接写入root/joint状态，再做正向运动学渲染。没有运行策略或动力学接触求解。

为便于观看，每段起始XY归零、起始yaw转为面向+x，摄像机跟随root XY。箱子位置来自`base_position + box_pos_local`；数据没有箱体旋转，因此展示yaw借用机器人yaw，尺寸固定0.30×0.30×0.25m。拾起片段中的支撑台高度由contact_index处箱子最低点推算，仅是辅助示意。这些物体字段没有进入AMP训练。

运行方法（仓库根目录）：

```bash
bash scripts/visualize_findbox.sh
/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py \
  --verify-only --output outputs/carrybox/findbox_dataset
```

脚本使用单机器人、CPU物理状态和GPU渲染；录制过程保留已有足球训练进程。安装路径可用`ISAAC_SIM_PATH`、`ISAAC_LAB_PATH`、`BALL_PYTHON`覆盖。

输出目录同时包含：`recording.json`（片段起止时间和源hash）、`verification.json`（逐帧解码/分辨率/帧率/hash校验）、`preview_01.png`至`preview_17.png`（各段中间帧）以及渲染日志。视频属于可视化产物，不是训练成功率或抓取稳定性证据。

实际校验结果：17段、2318帧、77.27秒；所有视频帧可解码，分辨率/帧率正确，源数据hash全部保持不变。首次渲染在视频编码关闭后遇到Replicator的detach列表参数兼容问题，已改为detach()；时间索引由完整录制日志恢复，并由全帧解码核对。

独立片段由`export_clips.py`按`recording.json`的精确帧数顺序生成，原完整录像保留。只需复核当前产物时运行：

```bash
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/dataset_visualization/export_clips.py --verify-only
```

去掉`--verify-only`可在片段尚不存在时导出；脚本拒绝覆盖已有MP4。`clips/index.json`记录每段来源、SHA-256、起始帧及帧数。
