---
task_id: "carrybox-wall5-jitter-20261023-1501"
language: "zh-CN"
axes: ["L", "C", "E"]
risk_tier: "T2"
allowed_paths: ["docs/carrybox/wall5_jitter_20261023_1501", "outputs/carrybox/wall5_jitter_20261023_1501", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-jitter-20261023-1501.md", "agent/task/carrybox-wall5-jitter-20261023-1501.md", "agent/report/carrybox-wall5-jitter-20261023-1501.md", "agent/handoff/carrybox-wall5-jitter-20261023-1501.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "录制一下最新ckp play的效果 为什么感觉走路一抖一抖的 是自碰撞有问题吗"
development_modes: ["MODEL_DEPLOYMENT", "SIMULATOR_EXTENSION"]
forbidden_scope: ["不改生产源码、奖励、数据、模型或正式训练进程", "不剪掉失败、不把持箱初始化当成抓起", "不把单seed四环境当成功率或唯一因果证明"]
steps: ["锁定模型和实际训练身份", "复用四相机录像并添加200Hz诊断记录", "同初态分别仅关闭自碰撞或动作延迟回放", "比较接触、目标、运动频率并检查视频", "保存结论和项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_jitter_20261023_1501/record_and_check.sh"}, {"command": "bash docs/carrybox/wall5_jitter_20261023_1501/compare_and_check.sh"}]
stop_conditions: ["源码/模型契约不匹配则停", "初态不匹配不作配对结论", "内存不足或非有限数则停，范围内最多两次修复保留证据", "初态不匹配、接触映射/零值有效性不明、时间戳错误或非有限值时停止对应配对归因", "冻结测试最多两次范围内修复并保留失败证据"]
safeguards: ["源和模型哈希不变、无优化器更新", "关闭碰撞/延迟仅诊断进程，契约差异显式记录", "检查初始化一致，按回合截断排除reset跃变", "机器人内部pair接触与地面/箱子接触分开，终止原因真实记录", "4环境20秒，50Hz动作与200Hz物理时间分别记录", "scene.update后采样并核验时间戳；立即复制tensor，50Hz和200Hz分开", "内部pair按body匹配、排除对角线、汇总去重；净合力为零不绝对证明无几何接触", "按共同首回合前缀比较，排除前2秒启动和跨reset差分/FFT", "关闭碰撞内部pair应为零；若两边都零检查映射和有效性，保留量测限制", "频率来自200Hz记录；25fps可能混叠，不能当步态频率", "记录PD估计力矩语义，闭环差异不等于唯一根因"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["Checkpoint→act_inference→物理目标裁剪→五槽物理延迟→ImplicitActuator→PhysX；scene.update后采样"], "critical_interfaces": ["50Hz原始action、processed_actions与200Hz实际joint_pos_target分别记录", "零延迟是index4；applied_torque是PD估计，不是求解器实测力矩", "每env独立RigidContactView机器人内部body×body过滤，dt=.005"], "invariants": ["同model/hash、均值策略、源不变；全部初态/对象/材质/PD/延迟缓存/事件时钟/观测匹配", "固定default/loco/loco/hold；持箱起点不能算拾箱"], "smallest_change_locus": ["只改本次docs录像和回放脚本，生产不变"], "mandatory_safeguards": ["scene.update后采样并核验时间戳；立即复制tensor，50Hz和200Hz分开", "内部pair按body匹配、排除对角线、汇总去重；净合力为零不绝对证明无几何接触", "按共同首回合前缀比较，排除前2秒启动和跨reset差分/FFT", "关闭碰撞内部pair应为零；若两边都零检查映射和有效性，保留量测限制", "频率来自200Hz记录；25fps可能混叠，不能当步态频率", "记录PD估计力矩语义，闭环差异不等于唯一根因"], "minimal_tests": ["bash docs/carrybox/wall5_jitter_20261023_1501/record_and_check.sh", "bash docs/carrybox/wall5_jitter_20261023_1501/compare_and_check.sh"], "blockers": ["初态不匹配、接触映射/零值有效性不明、时间戳错误或非有限值时停止对应配对归因", "冻结测试最多两次范围内修复并保留失败证据"]}
---

录制当前最新完整checkpoint四机器人20秒MP4，并用同模型同初态的自碰撞/动作延迟单因素只读回放检查抖动。记录200Hz目标、关节速度和内部接触力，分辨显示采样、控制输出与接触；不改训练。
