# wall5 全身碰撞体与可视化 · 2026-10-17

wall5现已改为35个有实体外壳连杆的全身凸包碰撞。PhysX实测每台机器人35个shape，旧版30个；44个刚体和29个关节保持。仅修改wall5生成路径，共享G1 USD、football、wall3/wall4保留。

## 查看结构

- [交互式碰撞结构](collision_structure.html)：可离线打开，拖动旋转、滚轮缩放、逐连杆隐藏、正面/侧面切换、新旧对比。
- [四视图PNG](collision_structure.png)：旧版与新版斜视、新版正视、侧视。
- [交互页面实际浏览器截图](interactive_preview.png)。

```bash
firefox /home/cao/perceptual_ball/docs/carrybox/wall5_fullbody_20261017/collision_structure.html
```

蓝色是保留的22处，橙色是新增7处，绿色是替换6处。图像从最终USD碰撞定义提取凸包，使用资产参考姿态；不是把外观模型涂色当碰撞图。PhysX cooking可能简化凸包，未宣称图中顶点与cooked网格逐点一致。凸包会填平凹部。

## 改了哪些部位

| 处理 | 连杆 |
|---|---|
| 新增7处外壳凸包 | pelvis、waist_yaw_link、waist_roll_link、head_link、左右wrist_yaw_link、logo_link |
| 替换6处简化体 | 左右knee_link的两个方块改为整段小腿凸包；左右shoulder_pitch/shoulder_roll的4个小圆柱改为肩部外壳凸包 |
| 保留22处 | 原有髋、踝、脚、骨盆外壳、躯干、肩yaw、肘、腕roll/pitch与橡胶手凸包 |

原小腿两方块没有覆盖完整35.51cm的小腿外壳；此次覆盖整段。头部保留正确link内偏移（z约0.325–0.531m），没有误放在腰部附近的head_link原点。

空的相机/IMU/palm坐标系和pelvis_contact_link可视标记不虚构碰撞体。掌部实体由rubber_hand覆盖，机器人没有手指自由度。物理自碰撞仍为False；全身对外碰撞不会阻止手臂穿过自身躯干。

生成方式：复用wall生成函数，再对13处禁用原collisions，在同link下建立full_body_collisions实例根，内部引用该link的visuals，设置CollisionAPI/convexHull及invisible/proxy。保留所有局部变换，不复制RigidBodyAPI或质量属性，也不写共享USD。新增碰撞不进入Warp视觉集合；原可见网格、相机和深度时序不变。

## 验证结果

两条冻结命令均PASS，[回执](receipts.json)。

1. CPU实际执行生产spawn：35个实体link的全部视觉顶点与最终凸包输入顶点一一对应，证明配置几何覆盖；不是只检查AABB。22处原碰撞输入点不变，脚底reset支撑仍使用原几何。全部link的Warp可见顶点、面索引和digest不变；质量、COM、惯量、关节属性及共享USD hash不变。[几何清单](geometry.json)
2. 4环境PhysX基线/新版比较：44刚体、29关节，质量与惯量一致；shape由30到35，各13处改动link恰有一个shape。所有13处球探针均有目标link过滤接触力，头、腰、腕、肩、小腿实际参与碰撞。[基线](baseline.json)、[新版运行时](runtime.json)、[接触与回放](smoke.json)
3. 行走/拾取/抱箱三类RSI观测和状态有限，原有depth/proprio/AMP维度保持；旧model_20600显式仅权重迁移后200个policy步通过（4环境，2次reset）。策略参数不变、优化器更新0；新契约保存恢复通过。短测不代表收敛、成功率或4096环境性能验收。
4. 原wall5六项CPU学习/接口测试通过。交互HTML在Firefox中实际加载并截图，无外部CDN依赖；未做全浏览器兼容测试。

首次CPU命令在绘图阶段因matplotlib需要facecolors参数而失败，修正后仅重跑原CPU命令；已PASS且未改的PhysX检查没有重复执行。[首次回执](receipts_initial.json)、[绘图失败日志](geometry_initial_fail.log)、[CPU重跑回执](receipts_geometry_retry.json)。只读专家审查通过，见[审查记录](expert_review.json)。

## checkpoint兼容性与训练状态

新环境`migration_revision=10`，碰撞profile为`g1_visual_convex_hull_full_body_v1`，记录实际self_collisions开关。历史wall5 model_20600等属于revision9：默认严格play/resume会拒绝，不能当成相同物理任务直接续训。要用旧策略查看新碰撞环境，须在`play.py`命令中显式加入`--carrybox_weights_only`；它加载策略、编码器、价值和辅助头权重，PPO/AMP优化器及课程重新初始化。这是在新物理环境播放旧权重，不是历史环境复现。

示例（已配置Isaac Lab的Python环境）：

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-CarryBox-Walled5-v0 \
  --num_envs 2 --device cuda:0 --real-time --rendering_mode performance \
  --checkpoint /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a/model_20600.pt \
  --carrybox_weights_only \
  env.sim.physx.gpu_found_lost_pairs_capacity=262144 \
  env.sim.physx.gpu_found_lost_aggregate_pairs_capacity=262144 \
  env.sim.physx.gpu_total_aggregate_pairs_capacity=262144
```

没有启动、停止或重启正式训练；本次产物中的model.pt仅为未更新权重的兼容性短测文件，不能当作新正式模型。4096性能与新碰撞下长期学习未验证。

复核命令：`bash docs/carrybox/wall5_fullbody_20261017/check_geometry.sh`和`bash docs/carrybox/wall5_fullbody_20261017/smoke.sh`。后者需要可用GPU显存至少4GiB，两个隔离进程总时限580秒，不启动正式训练。
