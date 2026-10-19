---
task_id: "carrybox-wall5-roll05-eval-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "看一下最新训练的ckp 能否学会走路不摔倒"
development_modes: ["SIMULATOR_EXTENSION", "MODEL_DEPLOYMENT"]
allowed_paths: ["docs/carrybox/wall5_roll05_eval_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-roll05-eval-20261019.md", "agent/task/carrybox-wall5-roll05-eval-20261019.md", "agent/report/carrybox-wall5-roll05-eval-20261019.md", "agent/handoff/carrybox-wall5-roll05-eval-20261019.md"]
forbidden_scope: ["不改训练/数据/模型/PD/奖励/观察/终止，不停止暂停训练", "不加载历史rev14代替当前model5200", "不把持箱RSI/仅存活/漂移或诊断PASS当作行走成功"]
steps: ["锁定检查时最新model5200身份和实际训练状态", "审计近250轮分技能计数", "原环境严格加载后独立进程两模式各32个loco首回合20秒有界回放", "汇总终态存活与移动足端证据并核对原训练仍活跃", "更新项目和四工件，明确行为失败与诊断成功"]
tests: [{"command": "bash docs/carrybox/wall5_roll05_eval_20261019/check.sh"}, {"command": "bash docs/carrybox/wall5_roll05_eval_20261019/replay.sh"}]
stop_conditions: ["诊断失败范围内最多两次修复，禁止放宽断言", "checkpoint或source契约不匹配", "GPU余量不足、NaN/OOM或原训练异常", "初态/权重不一致或首回合步数统计不守恒"]
safeguards: ["锁定完整model5200路径大小SHA/iter/契约；不追逐训练中新文件", "两模式独立进程、同构造/reset种子，物理与actor观察比较；动作独立generator，后续随机流可能因reset分叉", "reset前alive掩码抓终态与足端轨迹/接触，不能累计后续回合位移", "存活不等于会走，结合移动/向箱改善/足端证据；箱旁停下不算失败", "GPU不足/OOM/NaN/契约错/训练异常停止诊断，不停止正式训练；并发回放可能暂时减速", "诊断PASS不等于行走成功；即便0/32也保留完整结果", "每模式报告1/5/10/20秒存活、首次失败分布、roll/pitch/fell/timeout/censored及push前失败", "20秒自然timeout与窗口右删失分开，不把删失当完成成功"]
expert_required: true
expert_brief: {"affected_call_path": ["CarryBoxWalled5EnvCfg → Wall5CarryBoxEnv → RSI/物理step → RslRlVecEnvWrapper → CarryBoxWall5ActorCritic", "Walled step前actual_episode_steps递增；原_reset_idx调用前采集真实终态"], "critical_interfaces": ["完整原环境contract精确匹配且strict=True加载后，才覆盖诊断实例loco=1", "actor372+4x27x48深度、独立critic108，原agent.obs_groups与动作链", "先set_iteration(0)再5200再reset，回读有效课程与push/yaw", "首次年龄与actual_episode_steps一致，终止前记录roll/pitch/root/head/XY及多标签"], "invariants": ["生产代码/训练PID/checkpoint/optimizer不变；eval/inference_mode，逐tensor权重前后相同", "保留revision15增量push/摩擦/roll0.5/pitch1.1/运动RSI速度/深度/全身碰撞", "均值为play，sample使用checkpoint log_std和独立generator", "每环境只计第一回合，alive限制push/存活/移动，reset后不计"], "smallest_change_locus": ["只新增docs诊断及工程/项目记录", "近250轮用累计steps/episodes差分，不把累计mean当近期均值", "两种模式各32环境最多1000步，不扩展PD/推扰调参对照"], "mandatory_safeguards": ["锁定完整model5200路径大小SHA/iter/契约；不追逐训练中新文件", "两模式独立进程、同构造/reset种子，物理与actor观察比较；动作独立generator，后续随机流可能因reset分叉", "reset前alive掩码抓终态与足端轨迹/接触，不能累计后续回合位移", "存活不等于会走，结合移动/向箱改善/足端证据；箱旁停下不算失败", "GPU不足/OOM/NaN/契约错/训练异常停止诊断，不停止正式训练；并发回放可能暂时减速", "诊断PASS不等于行走成功；即便0/32也保留完整结果", "每模式报告1/5/10/20秒存活、首次失败分布、roll/pitch/fell/timeout/censored及push前失败", "20秒自然timeout与窗口右删失分开，不把删失当完成成功"], "minimal_tests": ["bash docs/carrybox/wall5_roll05_eval_20261019/check.sh", "bash docs/carrybox/wall5_roll05_eval_20261019/replay.sh"], "blockers": ["checkpoint或source契约不匹配", "GPU余量不足、NaN/OOM或原训练异常", "初态/权重不一致或首回合步数统计不守恒"]}
device_actions: []
real_device_authorized: false
---

采用一位只读专家的边界建议；将其最小测试中的结果报告要求归入safeguards，测试命令固定为两条原样shell入口。生产不修改，失败行为不是诊断验收失败。
