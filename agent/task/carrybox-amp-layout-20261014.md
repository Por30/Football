---
task_id: "carrybox-amp-layout-20261014"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["ML_DATA_PIPELINE"]
original_request: "把整理好的新的数据命名规范好 放到和kickball amp数据集相同的并列路径下"
allowed_paths: ["source/perceptual_ball/perceptual_ball/assets/motions/findbox", "source/perceptual_ball/perceptual_ball/carrybox_amp.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/visualize_findbox.py", "tests/test_carrybox_amp.py", "tests/test_carrybox_walled.py", "docs/carrybox/amp_layout_20261014", "docs/carrybox/amp/README.md", "docs/carrybox/dataset_visualization/README.md", "README.md", "AGENTS.md", "projects/findbox/README.md", "projects/README.md", "agent/plan/carrybox-amp-layout-20261014.md", "agent/task/carrybox-amp-layout-20261014.md", "agent/report/carrybox-amp-layout-20261014.md", "agent/handoff/carrybox-amp-layout-20261014.md"]
forbidden_scope: ["修改动作张量、足球数据/加载器/配置", "更改旧findbox或原始备份、旧视频", "启动停止重启训练或GPU仿真", "改变策略观测、奖励或采样语义"]
steps: ["确认kick并列目录和FindBox的AMP/RSI读取路径", "以小写下划线命名建立15段新标准目录及旧新映射", "更新AMP与RSI默认加载路径并兼容旧manifest和显式旧路径", "更新录像工具默认数据路径且保留历史验证", "验证逐文件字节相等、命名/分组、AMP更新与RSI实际初始化", "更新入口、兼容说明和工程交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_amp.py -v"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_walled.py -v"}, {"command": "/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_hold_20261014"}]
stop_conditions: ["旧新文件hash不同", "AMP与RSI默认路径不一致", "修改范围涉及训练或足球", "两次范围内修复后验证仍失败"]
safeguards: ["15段总4155帧不改动，hold仍300帧5秒", "旧findbox修订2和原始修订1备份保留", "manifest显式group保留旧语义40/40/20，旧无group格式继续支持", "新默认指向assets/motions/findbox，显式findbox仍读取旧目录", "kick两份PT及旧carrybox归档hash保持", "manifest更名导致新身份，拒绝旧完整AMP恢复，不伪造兼容", "不热切换当前进程"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

L轴T2数据迁移。规范目录locomotion/pick_up/hold，manifest用显式group保存历史采样/RSI组语义。检验相同窗口逐元素相等、坏组拒绝、在非仓库cwd解析以及实际CPU RSI初始化；不启动仿真。
