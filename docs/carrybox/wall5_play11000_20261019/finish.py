from pathlib import Path
from datetime import datetime
import json,sys,re
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2];OUT=ROOT/'outputs/carrybox/wall5_play11000_20261019'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
r=json.loads((DOC/'recording.json').read_text());v=json.loads((DOC/'video_validation.json').read_text());receipts=json.loads((DOC/'receipts.json').read_text())['tests']
assert r['status']==v['status']=='PASS' and all(x['result']=='PASS' for x in receipts)
now=datetime.now().astimezone().isoformat();pid=4038923
status=dict(checked_at=now,training_pid=pid,alive=(Path('/proc')/str(pid)).exists(),modified=False)
(DOC/'formal_status.json').write_text(json.dumps(status,indent=2)+'\n')
episodes='；'.join(f"{('loco','pickup','hold')[e['skill']]} {e['steps']}步（{'timeout' if e['timeout'] else 'tipped' if e['tipped'] else 'fell'}，pitch={e['pitch']:.3f}rad）" for e in r['episodes'])
ending=r['final_censored'];end_text=f"窗口结束仍处于{('loco','pickup','hold')[ending['skill']]}起点回合，已经持续{ending['steps']}步（{ending['steps']*.02:.2f}秒），未完成回合。"
summary=f"实际录制：完成{len(r['episodes'])}个回合，{episodes}。{end_text}这段视频未展示从地面找箱并完整抱起的成功流程。"
with (DOC/'README.md').open('a') as f:
 f.write('\n## 验证与观察结果\n\n'+summary+'\n\nMP4完整解码通过：500帧、25fps、20.00秒、1280×720，文件约'+f"{v['file_bytes']/1024/1024:.2f}"+'MiB。初始、2秒、10秒与最终画面人工检查，机器人和箱子保持可见；[关键帧拼图](../../../outputs/carrybox/wall5_play11000_20261019/contact_sheet.jpg)。详见[录制元数据](recording.json)、[视频检查](video_validation.json)、[测试回执](receipts.json)。\n\n'+now+f'正式PID{pid}存活={status["alive"]}；未停止或重启。当前生产源码仍revision15，本视频使用独立归档revision14。\n')
(OUT/'README.md').write_text('# Wall5 model11000 play\n\n[观看20秒MP4](wall5_rev14_model11000_play_20s.mp4) · [关键帧](contact_sheet.jpg)\n\n'+summary+'\n\n单环境、均值动作、seed42，revision14原环境/满推扰；显示RSI hold表示参考持箱起点。[完整记录](../../../docs/carrybox/wall5_play11000_20261019/README.md)。\n')
note='2026-10-19：[wall5 revision14 model11000的20秒play录像](LINK)：单环境均值动作、原rev14物理/噪声、满推扰/yaw12°；严格模型/环境契约匹配，500帧25fps完整解码通过。开头loco倾倒重置后进入hold参考起点，未展示地面拾箱成功；原正式PID4038923保持运行。'
for relative,link in [('projects/README.md','../docs/carrybox/wall5_play11000_20261019/README.md'),('projects/findbox/README.md','../../docs/carrybox/wall5_play11000_20261019/README.md')]:
 p=ROOT/relative;first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+note.replace('LINK',link)+'\n'+rest)
slug='carrybox-wall5-play11000-20261019';task,_=load_frontmatter(ROOT/'agent/task'/f'{slug}.md')
common=dict(task_id=slug,language='zh-CN',axes=['L'],risk_tier='T1',status='DONE',changed_files=task['allowed_paths'],task_contract_sha256=task_contract_sha256(task),tests=receipts)
for artifact in ('REPORT','HANDOFF'):
 data=dict(common,artifact=artifact)
 if artifact=='HANDOFF':data['resume_command']=None
 body='指定revision14 model11000录像已完成，MP4在outputs/carrybox/wall5_play11000_20261019/wall5_rev14_model11000_play_20s.mp4。严格对照归档环境与权重，无生产修改。'+summary+'\n\n500帧/25fps/20秒完整解码通过，关键帧已视觉检查。实际模型和源码hash在recording.json；只做推理，不更新优化器/AMP或导出覆盖训练工件。现有视频不会被脚本静默覆盖；再次录制应另存新输出。\n\n后台PID4038923仍运行，源码revision15保持，独立录像使用归档rev14。无需恢复任务；短视频不作为成功率证据。\n'
 (ROOT/'agent'/artifact.lower()/f'{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(val,ensure_ascii=False) for k,val in data.items())+'\n---\n\n'+body)
validation=validate_paths(*(ROOT/'agent'/a/f'{slug}.md' for a in ('plan','task','report','handoff')))
(DOC/'artifact_validation.json').write_text(json.dumps(validation,indent=2)+'\n');assert validation['valid'],validation
print(summary);print(json.dumps(validation));print(json.dumps(status))
