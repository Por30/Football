"""Package already checked local evidence into reviewer-facing tables."""
from pathlib import Path
import hashlib, json, math, xml.etree.ElementTree as ET

D = Path(__file__).resolve().parent
R = D.parents[2]
s = json.loads((D/'sources.json').read_text())
d = json.loads((D/'data.json').read_text())
identities = json.loads((D/'source_identity.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in identities.items())
urdf = Path('/home/cao/PhysHSI/legged_gym/resources/robots/g1/urdf/g1_29dof.urdf')
root = ET.parse(urdf).getroot()
cfg = s['source_default']['env']
out = ['# 逐项证据附录', '', '与[完整对照](README.md)配套。配置作者值和实际spawn覆写分开；本轮没有物理仿真。', '',
       '## 29个关节：原URDF限位与两边名义控制参数', '',
       '以下顺序为URDF定义顺序，非运行时张量顺序。动作/专家数据必须按名字映射，不能依赖这个表的行号。Kp/Kd为两边当前相同的名义值；PhysHSI另外施加每reset随机因子。', '',
       '| 关节 | 默认角rad | Kp | Kd | 下限rad | 上限rad | effort Nm | velocity rad/s |',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
for joint in root.findall('joint'):
    if joint.attrib['type'] not in ('revolute', 'continuous'):
        continue
    name = joint.attrib['name']
    lim = joint.find('limit').attrib
    kp = next(v for k,v in cfg['control']['stiffness'].items() if k in name)
    kd = next(v for k,v in cfg['control']['damping'].items() if k in name)
    vals = [name,cfg['init_state']['default_joint_angles'][name],kp,kd,lim.get('lower'),lim.get('upper'),lim['effort'],lim['velocity']]
    out.append('| ' + ' | '.join(str(x) for x in vals) + ' |')
out += ['', '## 所有link：质量、原始碰撞几何与坐标', '',
        '“无collision”不代表没有visual mesh或不能在深度中遮挡。USD继承原collision；mesh为convexHull，肩部四个cylinder在当前spawn后转换成capsule。几何原点是link局部坐标。', '',
        '| link | URDF质量kg | USD质量kg | 原URDF collision | 局部origin xyz / rpy |',
        '|---|---:|---:|---|---|']
for link in root.findall('link'):
    name = link.attrib['name']
    mass = link.find('inertial/mass')
    mass = None if mass is None else float(mass.attrib['value'])
    usd = s['usd']['bodies'].get(name,{}).get('mass')
    geometries, origins = [], []
    for c in link.findall('collision'):
        geom = list(c.find('geometry'))[0]
        geometries.append(geom.tag + ' ' + ' '.join(f'{k}={v}' for k,v in geom.attrib.items()))
        origin = c.find('origin')
        origins.append('0 0 0 / 0 0 0' if origin is None else origin.get('xyz','0 0 0')+' / '+origin.get('rpy','0 0 0'))
    out.append('| ' + ' | '.join((name,str(mass),str(usd),'<br>'.join(geometries) or '无collision','<br>'.join(origins) or '—')) + ' |')
out += ['', f'URDF合计{s["usd"]["urdf_mass_sum"]:.8f} kg；USD合计{s["usd"]["usd_mass_sum"]:.8f} kg。未把质量一致推断成所有惯量/接触响应等价。', '',
        '## 全部专家文件与当前映射', '',
        'hash是完整文件SHA256；同hash意味着字节一致，不仅是同名或同帧数。源概率按19段总weight45；wall5按组40/40/20重新加权。', '',
        '| PhysHSI文件（相对dataset_carrybox） | 帧数 | 源weight | 当前文件 | 文件SHA256 |',
        '|---|---:|---:|---|---|']
for clip in d['source_clips']:
    match = next((x['file'] for x in d['current_clips'] if x['identical_source'] == clip['file']), None)
    if clip['file'].endswith('/carryWith/carrywith1.pt'):
        match = '改造为hold/hold_box_01.pt，非同文件'
    name = clip['file'].split('/dataset_carrybox/')[1]
    out.append(f'| `{name}` | {clip["frames"]} | {clip["weight"]:g} | {match or "未纳入"} | `{clip["sha256"]}` |')
hold = next(x for x in d['current_clips'] if x['file'].startswith('hold/'))
out += ['', f'当前hold文件：`{hold["file"]}`，{hold["frames"]}帧，SHA256=`{hold["sha256"]}`。前21帧后重复frame20；并不是完整carryWith轨迹。', '',
        '## 独立FK检查：每段最多32个均匀帧', '',
        '五端点顺序：left_palm、right_palm、left_ankle_pitch、right_ankle_pitch、mid360。用原URDF、数据q和root quaternion独立计算，比较数据前五行link_position。单位mm。', '',
        '| 当前文件 | 检查帧数 | 左掌最大误差 | 右掌最大误差 | 左踝最大误差 | 右踝最大误差 | mid360最大误差 |',
        '|---|---:|---:|---:|---:|---:|---:|']
for name, k in d['kinematics'].items():
    out.append('| ' + ' | '.join([name,str(k['frames'])]+[f'{v*1000:.6g}' for v in k['endpoint_max_error_m']]) + ' |')
out += ['', '源base_height和按双踝相对z重建的专家高度在这些样本上基本一致，详见data.json的差值；这不是动态仿真的根部/足底高度检查。', '',
        '## 每一个有效reward term与最终注册函数', '',
        '下表来自正式wall5 env.yaml；None不算有效项。函数内部更深的门控在主报告第11节。', '',
        '| term | weight | func | params |', '|---|---:|---|---|']
for name,v in s['wall5']['env']['rewards'].items():
    if isinstance(v, dict):
        out.append(f'| {name} | {v["weight"]} | `{v["func"]}` | `{json.dumps(v["params"],ensure_ascii=False)}` |')
out += ['', 'PhysHSI有效scales（所有非零项）：', '', '| term | weight |', '|---|---:|']
for name,value in cfg['rewards']['scales'].items():
    out.append(f'| {name} | {value} |')
out += ['', '## 源码/资产身份与符号入口', '',
        '完整展开参数保存在sources.json，所有相关函数起始行保存在source_symbols。以下hash锁定本轮审阅身份；当前工作区不是干净checkout，不能只用git HEAD替代文件身份。', '',
        '| 文件 | SHA256 |', '|---|---|']
for path, digest in identities.items():
    out.append(f'| [{path}]({path}) | `{digest}` |')
out += ['', '## 机器可读原始参数', '',
        '[effective_parameters.tsv](effective_parameters.tsv)按source_default / source_resume / wall5逐字段展平全部已存配置。各框架字段名不同，这个文件用于找漏项，不以同名字段自动判定语义等价。', '']
(D/'appendix.md').write_text('\n'.join(out))

def flatten(value, prefix=''):
    if isinstance(value,dict):
        for key,v in value.items():
            yield from flatten(v, f'{prefix}.{key}' if prefix else key)
    else:
        yield prefix, json.dumps(value,ensure_ascii=False)
rows = ['implementation\tpath\tvalue']
for key in ('source_default','source_resume','wall5'):
    rows.extend(f'{key}\t{path}\t{value}' for path,value in flatten(s[key]))
(D/'effective_parameters.tsv').write_text('\n'.join(rows)+'\n')
print('Packaged appendix:',len(out),'lines;',len(rows)-1,'effective parameter leaves')
