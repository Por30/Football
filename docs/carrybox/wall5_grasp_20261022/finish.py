"""Publish the measured revision23 implementation and fresh formal-start receipt."""
from pathlib import Path
import json,re,sys,statistics
D=Path(__file__).resolve().parent;R=D.parents[2];slug='carrybox-wall5-grasp-20261022'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
s=json.loads((D/'snapshot.json').read_text());m=json.loads((D/'smoke.json').read_text());stop=json.loads((D/'stopped_run.json').read_text())
receipts=json.loads((D/'receipts.json').read_text())['tests'];assert s['status']==m['status']=='PASS' and all(x['result']=='PASS' for x in receipts)
count=int(re.search(r'Ran (\d+) tests',(D/'cpu.log').read_text())[1])
audit=json.loads((D/'geometry_audit.json').read_text());rows=audit['rows'];summary=[]
for name in sorted({x['clip'] for x in rows}):
    values=[x for x in rows if x['clip']==name];contact=[x for x in values if abs(x['frame']-x['contact_index'])<=5]
    close=[x for x in values if max(x['palm_to_surface'])<.08]
    summary.append(dict(clip=name,frames=len(values),contact_index=values[0]['contact_index'],
        metadata_contact_window_xy_m=[min(x['root_box_xy'] for x in contact),max(x['root_box_xy'] for x in contact)],
        fk_error_max_m=max(x['source_palm_fk_max_error'] for x in values),
        first_both_palms_within_8cm_frame=min(x['frame'] for x in close),
        close_palms_xy_m=[min(x['root_box_xy'] for x in close),max(x['root_box_xy'] for x in close)],
        close_palms_surface_m=[min(min(x['palm_to_surface']) for x in close),max(max(x['palm_to_surface']) for x in close)]))
(D/'calibration_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
body=f'''# Wall5 抓取奖励、完整三段AMP与自碰撞（revision23）

{s['checked_at']}：实现、{count}项CPU检查、20环境2轮更新＋保存恢复1轮/导出，以及4096环境正式启动验收通过。旧PID{stop['pid']}已停，新PID{s['pid']}从零训练，检查至第{s['progress_to']}轮；近10轮平均{s['mean_iteration_seconds']:.3f}s，最慢{s['max_iteration_seconds']:.3f}s。尚未证明地面拾箱收敛。

## 数据与几何核对

AMP恢复现有`assets/motions/findbox/amp_manifest.json`（dataset_revision3）完整15段、4155帧：11段行走、3段拾箱、1段持箱。pick_up_01/02/03分别192/178/129帧，共499帧，原文件、hash和filename_mapping不变；完整片段不裁剪、不平移、不拼接。60Hz源数据按50Hz插值形成10帧×60维AMP窗口。行走/拾箱/持箱组权重40/40/20保持，每段拾箱占总采样约13.33%。首/末完整窗口、hash、长度、分组权重检查通过。

G1真实PhysX正运动学逐帧读回全部499帧，两掌原点与数据最大偏差小于2.1微米。源contact_index附近，三段骨盆到箱子水平距离分别约0.547–0.558、0.492–0.526、0.487–0.489m；实际两掌都进入箱面8cm以内的帧，其水平距离覆盖0.368–0.558m（含抬起后的持箱段）。近地拾箱段开始靠近箱面时约0.486m。因此站位目标取0.52m并保留宽容区间，不再鼓励骨盆无限贴近箱心。掌原点、橡胶手COM与箱面是不同位置；新奖励明确使用左右palm link原点到旋转箱面距离，接触仍来自rubber_hand对Box的过滤力。

前两段原始箱心初始高度约0.365/0.215m，第3段约0.128m（这组高度包含原有base_height+0.05参考补偿，实际地面校正后的值见geometry_audit.json）。前两段是高处拾取的AMP样本，不能直接作为地面RSI。故`reference_motion_dataset`仍指向独立ground_pickup profile，pickup只采03的0–31帧；RSI保持75%loco/5%pickup/20%hold，hold从持箱参考开始。源contact_index并不等于物理手箱接触真值，例如03的两掌进入8cm范围在第57帧，晚于metadata的42帧；奖励不读取这个索引。

## 抓取奖励变化

以下是未乘policy dt与任务混合系数的值；RewardManager每控制步乘0.02s，任务/AMP配方保持原值。

| 项目 | 原revision22 | revision23 |
|---|---|---|
| 3D近箱门控 | 约0.784m，站立时水平约0.44m | 0.90m；伸手奖励在0.90–0.98m平滑衰减 |
| walk近箱收益 | 进入近箱区固定1.5 | 去掉满值；远处朝向项须有正向接近速度，原地朝向不取分；接近奖励在水平0.80→0.60m衰减为0 |
| 站位 | 越近也不受站位约束 | 目标0.52m、宽度0.12m，最多0.2；未抬起时水平<0.40m逐渐扣分，最多−0.5 |
| 手部接近 | 先平均双手位置再算距箱心 | 分别算左右掌到旋转箱面的距离，4cm容差、18cm指数尺度，异侧夹持更高，最高1.5 |
| 接触 | 平均手力及手中点门控 | 仅Box过滤力，>1N开始、5N饱和；单/双手接触均值最高0.5，双手异侧接触另最高1.5 |
| 抬升 | 未接触也有箱心高度基础奖励 | 双手异侧接触才给抬升分；旋转后箱底净空从1cm到25cm线性增加，最高2.5 |
| 稳定抓取 | 下蹲与双手中点接近可获奖励 | 要有双手异侧实际接触，沿用0.2权重与速度/加速度平滑 |
| 拾取动作平滑惩罚 | 下蹲伸手阶段即可触发 | slow_pickup、arm_speed_pickup、arm_acc_pickup仅双手已接触后启用，原权重保持 |

反例检查覆盖双手很远但中点对箱、单手远离、同侧双手、单手/无手碰撞顶起箱子、过量握力、箱体yaw90°与倾斜。受控姿态的walk+carryup总奖励满足站立 < 伸手 < 双手贴近 < 单手接触 < 双手接触 < 接触抬起。严格任务成功仍用原条件：真实双手Box接触、箱底离地至少12cm、箱体直立、低速并持续0.5s；没有把持箱RSI或箱子弹起算地面成功。

新增`Grasp/loco_reach`、`bilateral`、`lift`、`crowding`、`both_contact_fraction`和`palm_surface_distance_m`日志，读取奖励对应的reset前状态；后续观察是否真正由伸手进入接触/抬升，不能只看总奖励或episode length。

## G1自碰撞

wall5的articulation self collision已打开，既有全身35个碰撞形状、质量、惯量、PD和外部碰撞保持。仅在wall5场景作者阶段排除3对已实测结构凸包重叠：waist_yaw_link↔torso_link、左右knee_link↔同侧ankle_roll_link；它们跨越同一腰/踝关节装配，不是过滤整条肢体。共享USD、football及wall3/4不改。

直接打开开关而不处理这些结构凸包，会在默认/拾箱/持箱姿态产生约20–71kN自接触峰值。过滤后默认悬空静姿态约10.4N（左手与髋部真实轻微接触）；20环境每类RSI各8次、每次4个物理步的初始化抽查中，env0读取的自接触峰值为0，全部环境状态有限。刻意交叉手臂时仍读到非相邻肘/手臂↔躯干真实接触（约20.5kN最大峰值，这是故意穿插诊断，非正式reset），证实开关不是名义开启。相邻关节仍由PhysX默认规则处理，机器人和箱子之间没有新增过滤。

这不是“所有完整AMP参考都动态可执行”的证明；此前03后段的膝箱穿插风险仍存在，故没有扩大RSI帧范围。高处拾箱样本与地面任务也有分布差异，需通过后续正式回放评估效果。

## 验证与正式训练

{count}项CPU测试通过。20环境短测核对深度米制、critic123及终止前状态、reset75/5/20、自碰撞物理读回、真实掌箱距离、完整15段AMP、PPO/判别器/actor/critic/CNN/pose_head更新与数值有限；保存严格恢复再更新通过。部署JIT重新加载输出与actor一致，critic与pose head不进入导出；ONNX已生成，未单独执行ONNX Runtime。第一次短测因诊断工具调用PhysX contact-view重载类型不匹配而失败，修复为已验证的字符串pattern后通过。随后在正式启动接受前发现原远处朝向分会奖励原地站立，把该项与正向接近速度绑定，补充远处静止/近箱准备收益排序检查。首个未完成迭代的启动PID1587359已停止并保留记录，重新全量验收后才启动本次正式run；由于其仍在场景初始化中，SIGINT/TERM未退出，身份核对后SIGKILL结束。所有失败/中止回执保留，没有删除或放宽断言。

checkpoint仍schema2，环境revision23记录抓取参数、完整AMP manifest、自碰撞及过滤对。旧revision22严格恢复被拒绝，新正式run无resume/warm-start。actor深度＋本体、独立critic123、辅助coef1全配对帧、roll0.5、20s、PPO及AMP60维Normalizer均保持。

旧训练最后日志{stop['last_log_iteration']}轮，保存至`{stop['last_saved_checkpoint']}`，历史产物保留。
新训练：4096环境、seed42、40000轮，PID{s['pid']}。首checkpoint核对环境契约、完整15段AMP、fresh优化器step20和Normalizer计数61440；正式近10轮均低于6s。实现与启动通过不等同于学会搬箱。

run：`{s['run']}`

```bash
tail -f {s['log']}
```

证据：[原始三段数据核对](dataset_audit_raw.json)、[499帧FK与自碰撞](geometry_audit.json)、[未过滤自碰撞对照](geometry_audit_unfiltered.json)、[CPU日志](cpu.log)、[短测](smoke.json)、[启动状态](snapshot.json)、[停止记录](stopped_run.json)、[测试回执](receipts.json)。
'''
(D/'README.md').write_text(body)
entry=f'2026-10-22：[wall5抓取优化revision23]({{link}})：恢复完整三段pickup的15段AMP，RSI75/5/20仍用地面03前缀；站位0.52m、近箱3D0.90m，逐手箱面距离＋双手接触/抬升奖励，取消近箱walk满值；开启G1自碰撞并仅过滤3对结构重叠。{count}项CPU、20环境更新恢复导出通过。旧PID{stop["pid"]}已停，新PID{s["pid"]}、4096 fresh，检查至{s["progress_to"]}轮，近10轮平均{s["mean_iteration_seconds"]:.3f}s。正式训练进行中，未证明拾箱收敛。'
for name,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
    p=R/name;title,rest=p.read_text().split('\n',1);link=prefix+'docs/carrybox/wall5_grasp_20261022/README.md'
    if link not in rest:p.write_text(title+'\n\n'+entry.format(link=link)+'\n'+rest)
p=R/'projects/findbox/README.md';text=p.read_text();text=text.replace('| `source/perceptual_ball/perceptual_ball/assets/motions/findbox/` | 基线及wall3/wall4的15段规范AMP/RSI数据：行走11、拾起3、抱箱1；dataset_revision=3 |','| `source/perceptual_ball/perceptual_ball/assets/motions/findbox/` | 基线/wall3/wall4及wall5 revision23的15段完整AMP：行走11、拾起3、抱箱1；dataset_revision=3，wall5 RSI另用ground_pickup |');text=text.replace('| `source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/` | wall5专用13段：行走11、地面拾起1、抱箱1；dataset_revision=4；当前正式RSI为75%loco/5%pickup/20%hold（2026-10-21从零启动） |','| `source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/` | wall5专用地面RSI：行走11、地面拾起1、抱箱1；dataset_revision=4；75%loco/5%pickup03前缀/20%hold，revision23的AMP已切回上级完整15段 |');p.write_text(text)
task,_=load_frontmatter(R/f'agent/task/{slug}.md')
changed=set(json.loads((D/'before.json').read_text())['source_before'])|{'tests/test_carrybox_grasp.py','projects/README.md','projects/findbox/README.md'}
changed.update(str(p.relative_to(R)) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
changed.update(str(p.relative_to(R)) for p in Path(s['run']).rglob('*') if p.is_file());changed.add(str(Path(s['log']).relative_to(R)))
changed.add(str((D/'artifact_validation.json').relative_to(R)));changed.update(f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff'))
for kind in ('report','handoff'):
    front=dict(task_id=slug,language='zh-CN',axes=['E','L'],risk_tier='T2',artifact=kind.upper(),status='DONE',changed_files=sorted(changed),tests=receipts,task_contract_sha256=task_contract_sha256(task),resume_command=None)
    text=body if kind=='report' else f'''revision23已实现并正式fresh启动，PID{s['pid']}仅为{s['checked_at']}快照，后续核对launch.json、/proc与实际日志，不重复启动。\n\n完整三段pickup AMP来自现有上级findbox15段，hash不变；RSI继续ground_pickup/03前缀，75/5/20。站位0.52m/3D门控0.90m，逐掌到旋转箱面奖励，双手Box接触才能获得抬升奖励；平滑惩罚延后到双手接触，新增Grasp/loco_*日志。self collision已开启，三对腰/踝结构重叠过滤见contract，其余非相邻真实碰撞保留。\n\n{count}项CPU、20env2+1更新/恢复/导出及4096启动验收通过，近10轮平均{s['mean_iteration_seconds']:.3f}s。正式目录{s['run']}，日志命令 `tail -f {s['log']}`。旧模型严格restore不兼容，原checkpoint保留。actor、critic123、aux1、米制深度、roll0.5、20秒及PPO/AMP算法保持。\n\n尚未证明地面拾箱收敛；高处拾箱AMP与地面初始化用途不同，完整AMP并不保证后段参考在全身碰撞下都可动态执行。后续重点查loco双手接触/抬升与独立回放，不把hold参考成功作地面拾箱。详情docs/carrybox/wall5_grasp_20261022/README.md。没有待恢复工作。\n'''
    (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in front.items())+'\n---\n\n'+text)
result=validate_paths(*(R/f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')))
(D/'artifact_validation.json').write_text(json.dumps(result,indent=2)+'\n');assert result['valid'],result
print(json.dumps(result));print('FINISHED',s['pid'],s['progress_to'],s['mean_iteration_seconds'])
