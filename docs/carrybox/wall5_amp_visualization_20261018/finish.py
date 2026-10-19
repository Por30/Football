from pathlib import Path
import json,sys

DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2]
OUT=ROOT/'outputs/carrybox/wall5_amp_20261018'
slug='carrybox-wall5-amp-visualization-20261018'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
receipts=json.loads((DOC/'receipts.json').read_text())['tests'];assert all(t['result']=='PASS' for t in receipts)
v=json.loads((OUT/'verification.json').read_text());r=json.loads((OUT/'index.json').read_text());assert v['status']=='PASS'
body=f'''# 当前wall5 AMP可视化（2026-10-18）

[完整63.08秒MP4](../../../outputs/carrybox/wall5_amp_20261018/wall5_amp_all.mp4) · [交互分段浏览](../../../outputs/carrybox/wall5_amp_20261018/index.html) · [缩略图总览](../../../outputs/carrybox/wall5_amp_20261018/overview.png) · [片段时间表](../../../outputs/carrybox/wall5_amp_20261018/README.md)

当前正式run的agent.yaml、env.yaml与model_0数据契约均确认使用`source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/`。13段为11段行走、1段完整地面拾箱03、1段持箱；3785原生帧，60fps，63.083秒。全部视频为1倍速，另提供13个独立MP4及本地HTML播放器。

- AMP采样：行走40% / 拾箱40% / 持箱20%；当前训练为60维任务AMP。
- RSI初始化：行走80% / 拾箱0% / 持箱20%，与AMP采样权重分别设置。
- 拾箱保留完整129帧，包括抬起阶段；排除的是两个高处拾箱片段。持箱保留原0–20帧，之后重复第20帧至300帧/5秒。
- 来源：源PT逐段SHA-256与`outputs/carrybox/findbox_hold_20261014/recording.json`完全一致，因此复用对应G1原生60fps逐帧画面，更换规范名称、标题及页脚。未运行额外GPU仿真，也未修改源数据或既有录像。
- 展示含义：运动学参考回放，不能作为当前策略表现或物理成功率。箱子位置来自源记录；源数据缺少箱体旋转，箱体朝向借用机器人yaw，参考支撑为示意。本视频不展示wall5的reset修正、障碍或深度。

验证于{v['checked_at']}通过：13个源PT及对应旧视频哈希一致；13段视频完整解码3785帧，合辑完整解码3785帧；每段首/中/末帧与旧源对应画面核对，重编码后画面平均绝对误差最大{v['source_frame_pixel_max_mean_abs_error']:.3f}/255；合辑39个抽检帧与分段逐像素相同。已人工检查新预览与总览标签。

正式训练PID{v['training_pid']}在验证时仍运行；本次没有停止、重启或调整训练。训练身份/源文件hash/每段帧区间见输出index.json，解码验证见verification.json，冻结命令回执见本目录receipts.json。视频中动作数量或时长不代表训练采样比例。

`build.py`为此次CPU导出与验证脚本，已有产物可用`--verify-only`检查；其中实时训练身份检查针对上述PID/run，训练结束后需以保存的身份记录解释该检查，勿把进程退出误解为视频损坏。
'''
(DOC/'README.md').write_text(body)
summary='2026-10-18 21:59 JST：[当前wall5 AMP数据集可视化]({link})：实际run与model_0确认ground_pickup的13段（11行走/1地面拾箱/1持箱）；完整63.08秒MP4、13个分段及HTML浏览页已生成，3785帧/60fps和源hash对应检查通过。复用hash一致的G1录像，仅CPU处理；AMP40/40/20，RSI80/0/20，训练PID3812053保持运行。'
for file,link in [('projects/README.md','../docs/carrybox/wall5_amp_visualization_20261018/README.md'),('projects/findbox/README.md','../../docs/carrybox/wall5_amp_visualization_20261018/README.md')]:
    p=ROOT/file;heading,rest=p.read_text().split('\n',1)
    if link not in rest:rest='\n'+summary.format(link=link)+'\n'+rest
    if file=='projects/README.md':
        rest=rest.replace('| CB-005 | 搬箱子 | FindBox全部动作可视化录制 | 完成 | [当前15段逐PT独立60fps视频](../outputs/carrybox/findbox_hold_20261014/README.md)；4155帧/69.25秒及hash校验通过；旧17段视频保留 |',
            '| CB-005 | 搬箱子 | FindBox动作可视化 | 完成 | [当前wall5的13段/63.08秒/60fps](../outputs/carrybox/wall5_amp_20261018/index.html)，源hash/完整解码通过；[其他变体的15段录像](../outputs/carrybox/findbox_hold_20261014/README.md)和旧17段保留 |')
    else:
        rest=rest.replace('dataset_revision=4；reset只用loco/离地前pickup','dataset_revision=4；当前revision13 RSI为80%loco/0%pickup/20%hold')
    p.write_text(heading+'\n'+rest)
task,_=load_frontmatter(ROOT/f'agent/task/{slug}.md')
changed=['projects/README.md','projects/findbox/README.md']+[f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')]
changed += [str(p.relative_to(ROOT)) for base in (DOC,OUT) for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
changed.append(str((DOC/'artifact_validation.json').relative_to(ROOT)))
common={k:task[k] for k in ('task_id','language','axes','risk_tier')}
common.update(status='DONE',changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=receipts)
for kind in ('report','handoff'):
    meta=dict(common,artifact=kind.upper())
    if kind=='handoff':meta['resume_command']=None
    content=body if kind=='report' else '当前wall5实际13段AMP已可视化。产物位于outputs/carrybox/wall5_amp_20261018/，完整MP4、13个分段、浏览页、源hash/帧索引与验证均齐全。运动学画面复用既有hash相同的录像，箱体朝向/参考支撑为示意。训练PID3812053在2026-10-18 21:59 JST仍运行，未改动训练或数据；无待办。详情见docs/carrybox/wall5_amp_visualization_20261018/README.md。'
    (ROOT/f'agent/{kind}/{slug}.md').write_text('---\n'+''.join(f'{k}: {json.dumps(val,ensure_ascii=False)}\n' for k,val in meta.items())+'---\n\n'+content+'\n')
result=validate_paths(*(ROOT/f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')))
(DOC/'artifact_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');assert result['valid'],result
print(json.dumps(result,ensure_ascii=False))
