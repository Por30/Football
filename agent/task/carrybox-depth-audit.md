---
task_id: "carrybox-depth-audit"
language: "zh-CN"
axes: ["P"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "确认当前深度管线与实机G1部署的安装位置是否一致，并验证训练深度正确且受障碍遮挡。"
allowed_paths: ["scripts/audit_g1_depth.py", "scripts/audit_g1_depth.sh", "docs/carrybox/depth_audit", "projects/findbox/README.md", "projects/football/README.md", "projects/README.md", "agent"]
forbidden_scope: ["更改生产相机或足球训练配置", "启动长期训练或操作既有训练", "连接/操作真实设备", "把URDF一致当作实机标定完成", "继续无关PPO GPU故障修复"]
development_modes: ["SENSOR_DRIVER", "SIMULATOR_EXTENSION"]
steps: ["核对资产来源、URDF及部署配置", "冻结帧坐标和光轴深度检查", "在三个FindBox变体做确定性RTX遮挡及相机跟随测试", "区分足球解析管线与FindBox管线", "记录证据及实机未决项"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python scripts/audit_g1_depth.py --geometry-only"}, {"command": "bash scripts/audit_g1_depth.sh"}]
stop_conditions: ["原范围两次修复后审计仍失败", "测试需干扰既有训练或真实硬件"]
safeguards: ["用训练配置和生产观测函数检查，确定性探针显式关扰动", "证明近障碍遮挡后方箱子且移除遮挡恢复", "区分安装模型/版本差异/实机内参和预处理", "不改变已有失败的walled训练验收状态"]
expert_required: false
device_actions: []
real_device_authorized: false
---

只审计深度感知路径。FindBox使用真实RTX传感器，足球现有解析球面管线不含其他物体遮挡。以资产转换记录的PhysHSI G1 URDF作为模型依据，对比本地Unitree URDF版本；实机配置路径已向用户询问。使用静态渲染及有限reset检查，避免重跑已知失败的PPO长链路。
