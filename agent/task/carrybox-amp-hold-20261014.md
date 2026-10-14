---
task_id: "carrybox-amp-hold-20261014"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["ML_DATA_PIPELINE"]
original_request: "carrywith 只保留1的开头部分 并重复抱住箱子的帧 然后重新整理amp数据集合 并录制视频"
allowed_paths: ["findbox", "docs/carrybox/amp_hold_20261014", "docs/carrybox/amp/README.md", "docs/carrybox/dataset_visualization/README.md", "scripts/visualize_findbox.py", "tests/test_carrybox_amp.py", "outputs/carrybox/findbox_hold_20261014", "projects/findbox/README.md", "projects/README.md", "agent/plan/carrybox-amp-hold-20261014.md", "agent/task/carrybox-amp-hold-20261014.md", "agent/report/carrybox-amp-hold-20261014.md", "agent/handoff/carrybox-amp-hold-20261014.md"]
forbidden_scope: ["启动、停止、恢复或改变正式训练", "改变足球、共享资产、策略观测或奖励", "丢失原始数据或旧manifest", "更改行走或拾箱动作"]
steps: ["核对carrywith1抱箱起始帧及AMP/RSI读取路径", "保存完整旧数据快照并制作0–20帧前缀加静止抱箱延长段", "整理为15段有效AMP清单并同步hash和版本", "验证数据/AMP更新/检查点与RSI合同", "逐段直接录制新版15段60fps视频并校验", "更新项目、变更与兼容性记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_amp.py -v"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_walled.py -v"}, {"command": "/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_hold_20261014"}]
stop_conditions: ["原始备份或hash验证失败", "冻结帧姿态/速度语义无法确认", "GPU资源不足", "两次范围内修复后验证仍失败"]
safeguards: ["旧17段完整备份可单独加载用于原checkpoint兼容", "新schema仍为1，manifest身份修订且训练恢复拒绝旧hash", "仅有效carryWith变为1段，行走/拾箱14段逐文件hash不变", "保留0–20原始姿态，重复第20帧至300帧，尾段三类速度为0", "维持60Hz、xyzw、29关节顺序及40/40/20组权重", "现有训练的内存数据不热切换", "每个源帧对应一个60fps视频帧"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

仅L轴数据流水线T2：生产AMP与RSI读取路径已检查，核心算法不改。测试包含数据结构/静止速度、真实AMP更新/恢复、RSI合同，以及真实渲染完整解码。有效carrywith2/3移入可加载旧数据快照；保留carrywith1原路径和旧视频。
