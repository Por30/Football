# Wall5 地面拾箱数据 profile

从上级revision3数据筛选，原数据原路径保留。此profile为schema1、dataset_revision4、`findbox_ground_pickup_v1`：13段、3785帧、60Hz。

- 行走：原11段，字节不变。
- 拾取：仅`pick_up/pick_up_03.pt`，保留0–128全部129帧，包含从地面接近、抬起及之后的动作；不是仅保留尚未离地帧。
- 持箱：原`hold/hold_box_01.pt`，300帧，供AMP学习保持。wall5不再从hold姿态reset。

`pick_up_01/02`为较高起点，排除出本profile；它们完整保留在上级`pick_up/`。没有平移、裁帧、拼接或改写动作张量。组采样概率仍为行走40%、拾取40%、持箱20%，完整动作按60→50Hz生成10帧AMP窗口。

wall5的AMP与参考初始化均显式指向本目录；CarryBox基线、wall3/wall4仍使用上级15段，不切换。wall5 reset是行走70%、地面拾取30%、hold0%。箱高条件得到0–60帧候选，但34帧以后与全身膝碰撞体穿插，第32、33帧也会产生物理接触冲量，因此实际reset只采样0–31帧；所有箱子按旋转后的最低点离地5mm放置，场景无支撑台。参考筛帧与AMP完整动作是两个不同用途。

旧checkpoint不能作为新环境完整恢复；wall5环境契约revision11，新训练会记录本manifest hash。旧模型只能显式weights-only迁移，保留旧数据不意味着新旧训练合同相同。

[AMP manifest](amp_manifest.json) · [文件名映射及排除记录](filename_mapping.json) · [源数据](../README.md) · [工程记录](../../../../../../../docs/carrybox/wall5_ground_20261017/README.md)
