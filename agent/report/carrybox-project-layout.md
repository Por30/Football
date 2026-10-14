---
task_id: "carrybox-project-layout"
language: "zh-CN"
axes: ["S"]
risk_tier: "T0"
status: "DONE"
changed_files: ["README.md", "AGENTS.md", "projects/README.md", "projects/findbox/README.md", "projects/carrybox", "projects/football/README.md", "agent/report/carrybox-project-layout-tests.json"]
tests: [{"command": "git diff --check", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "a312124218d179a42f4b5d46ff44d78244f8024da78b509b1cedd5501da6a42f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
task_contract_sha256: "4176881bd5e971f6233a33e4b7f4fd9c2b945da46d66995e2685433e71db2776"
artifact: "REPORT"
---

已将项目导航目录projects/carrybox迁为projects/findbox，与projects/football并列；旧carrybox入口为指向findbox的相对符号链接。根README、总看板、AGENTS及双方项目入口统一使用findbox/football作为项目标识。CarryBox任务/源码名、CB编号、历史工程前缀保持兼容。

补齐双方资源归属、findbox的walled代码索引和基线/walled播放数据依赖区别。根findbox数据、source/scripts导入路径及checkpoint路径均保持原位；没有操作训练或继续GPU故障排查，状态快照保留。

人工脚本核验37个本地Markdown链接均存在，两个入口同级，旧入口正确解析至新目录，17个原始动作文件及manifest仍在原处；git diff --check PASS。无需GPU仿真或训练。

后续以projects/findbox/README.md和projects/football/README.md作为并列入口；已有carrybox文档引用经兼容别名继续有效。walled验收阻塞仍归CB-006，不能因目录整理标为完成。
