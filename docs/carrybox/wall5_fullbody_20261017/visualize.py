"""Draw actual authored collision convex hulls; no simulator or CDN dependencies."""
import base64
import json
import numpy as np

BLUE=(0.25,0.48,0.69)
ORANGE=(0.98,0.56,0.18)
GREEN=(0.22,0.68,0.49)


def create_visualizations(before,after,added,replaced,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.patches import Patch

    def color(name): return ORANGE if name in added else GREEN if name in replaced else BLUE
    all_points=np.concatenate([x['vertices'] for x in after])
    low,high=all_points.min(0),all_points.max(0)
    center=(low+high)/2
    half=max(high-low)*.56
    fig=plt.figure(figsize=(15,9),facecolor='#f8fafc')
    layouts=[(before,18,-55,'Previous: 28 links / 30 shapes'),
             (after,18,-55,'Full body: 35 links / 35 convex hulls'),
             (after,0,0,'Front (+X)'),(after,0,-90,'Side (-Y)')]
    for i,(rows,elev,azim,title) in enumerate(layouts):
        ax=fig.add_subplot(1,4,i+1,projection='3d',computed_zorder=False)
        ax.set_facecolor('#f8fafc')
        for row in rows:
            points=row['vertices']; faces=row['faces']
            mesh=Poly3DCollection(points[faces],facecolors=[color(row['link']) if i else BLUE],
                                 edgecolors=None,alpha=1,shade=True,
                                 lightsource=matplotlib.colors.LightSource(azdeg=120,altdeg=45))
            ax.add_collection3d(mesh)
        ax.set_xlim(center[0]-.42,center[0]+.42)
        ax.set_ylim(center[1]-.42,center[1]+.42)
        ax.set_zlim(low[2]-.04,high[2]+.05)
        ax.set_box_aspect((.84,.84,high[2]-low[2]+.09))
        ax.view_init(elev=elev,azim=azim);ax.set_proj_type('ortho');ax.set_axis_off()
        ax.set_title(title,fontsize=11,pad=4)
    fig.suptitle('G1 / CarryBox wall5 — full-body external collision geometry',fontsize=18,y=.94)
    fig.legend(handles=[Patch(color=BLUE,label='Preserved: 22 hulls'),Patch(color=ORANGE,label='Added: 7 hulls'),
                        Patch(color=GREEN,label='Replaced: shoulders + lower legs (6 hulls)')],
               loc='lower center',bbox_to_anchor=(.5,.11),ncol=3,frameon=False,fontsize=11)
    fig.text(.5,.06,'Authored convex-hull preview • USD reference pose • self-collision OFF\n'
             'Collision surfaces fill concavities; PhysX cooking can simplify the hulls.',ha='center',fontsize=10,color='#475569')
    fig.subplots_adjust(left=.01,right=.99,bottom=.15,top=.88,wspace=-.15)
    fig.savefig(out/'collision_structure.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)

    # Static binary vertex buffers make the HTML independent of local files/CDNs.
    buffers=[]
    for mode,rows in [('before',before),('after',after)]:
        records=[]
        for row in rows:
            pts=(row['vertices']-center)/half
            triangles=pts[row['faces']]
            normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
            normals/=np.linalg.norm(normals,axis=1)[:,None]
            c=color(row['link']) if mode=='after' else BLUE
            packed=np.concatenate((triangles.reshape(-1,3),np.repeat(normals,3,axis=0),
                                   np.tile(c,(len(triangles)*3,1))),axis=1).astype('<f4')
            records.append(dict(name=row['link'],count=len(packed),data=base64.b64encode(packed.tobytes()).decode()))
        buffers.append(records)
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>G1 wall5 全身碰撞体</title><style>
body{margin:0;background:#edf2f7;color:#172b46;font:15px system-ui}header{padding:18px 24px;background:white}
h1{margin:0 0 8px;font-size:24px}p{margin:6px 0;color:#516176}button{margin:6px;padding:9px 14px;border:1px solid #bac9dc;border-radius:8px;background:white;cursor:pointer}
main{display:flex;height:calc(100vh - 185px);min-height:480px}canvas{width:calc(100% - 260px);height:100%;touch-action:none}aside{overflow:auto;width:240px;padding:10px;background:#fff}label{display:block;font-size:12px;margin:6px 0}.orange{color:#d77816}.green{color:#208955}footer{padding:8px 24px;font-size:12px}
</style><header><h1>G1 · wall5 全身碰撞体</h1><p>蓝：原有22处　<span class="orange">橙：新增7处</span>　<span class="green">绿：替换6处肩部／小腿</span></p>
<button id="mode">当前：修改后（35个凸包）</button><button id="front">正面</button><button id="side">侧面</button><button id="iso">三维</button><button id="all">显示全部</button><span>拖动旋转 · 滚轮缩放 · 右侧可单独隐藏连杆</span></header>
<main><canvas id="c"></canvas><aside id="links"></aside></main><footer>从最终USD碰撞定义提取的凸包预览，采用资产参考姿态。非外观模型。PhysX cooking可能简化顶点；物理自碰撞关闭。空传感器／掌部坐标系不生成虚构体积。</footer>
<script>
const DATA=__BUFFERS__;
const canvas=document.getElementById('c'),gl=canvas.getContext('webgl',{antialias:true});
if(!gl)throw new Error('浏览器未提供WebGL');
function shader(type,src){let s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
let program=gl.createProgram();
gl.attachShader(program,shader(gl.VERTEX_SHADER,`attribute vec3 p,n,c;uniform mat3 R;uniform vec2 aspect;uniform float zoom;varying vec3 color;void main(){vec3 q=R*p;vec3 nn=R*n;float light=0.45+0.55*abs(dot(normalize(nn),normalize(vec3(-0.5,0.6,1.0))));color=c*light;gl_Position=vec4(q.x*aspect.x*zoom,q.y*aspect.y*zoom,-q.z*0.3,1.0);}`));
gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`precision mediump float;varying vec3 color;void main(){gl_FragColor=vec4(color,1.0);}`));gl.linkProgram(program);gl.useProgram(program);
const R=gl.getUniformLocation(program,'R'),aspect=gl.getUniformLocation(program,'aspect'),Z=gl.getUniformLocation(program,'zoom');
const attrs=['p','n','c'].map(x=>gl.getAttribLocation(program,x));attrs.forEach(x=>gl.enableVertexAttribArray(x));
const meshes=DATA.map(rows=>rows.map(o=>{let bytes=Uint8Array.from(atob(o.data),x=>x.charCodeAt(0));let b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,bytes,gl.STATIC_DRAW);return {name:o.name,count:o.count,buffer:b,visible:true};}));
let mode=1,yaw=-0.65,el=0.2,zoom=1;
function list(){let box=document.getElementById('links');box.innerHTML='';meshes[mode].forEach(o=>{let l=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=o.visible;ch.onchange=()=>{o.visible=ch.checked;draw()};l.append(ch,document.createTextNode(o.name));box.append(l);});}
function draw(){let ratio=devicePixelRatio||1;canvas.width=canvas.clientWidth*ratio;canvas.height=canvas.clientHeight*ratio;gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.929,.949,.969,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);
let a=Math.cos(yaw),b=Math.sin(yaw),ce=Math.cos(el),se=Math.sin(el);
// World Z remains vertical; camera points toward the robot from horizontal bearing yaw.
gl.uniformMatrix3fv(R,false,new Float32Array([-b,-a*se,a*ce,a,-b*se,b*ce,0,ce,se]));
let ar=canvas.width/canvas.height;gl.uniform2f(aspect,1/Math.max(ar,1),Math.min(ar,1));gl.uniform1f(Z,zoom);
meshes[mode].forEach(o=>{if(!o.visible)return;gl.bindBuffer(gl.ARRAY_BUFFER,o.buffer);attrs.forEach((a,i)=>gl.vertexAttribPointer(a,3,gl.FLOAT,false,36,i*12));gl.drawArrays(gl.TRIANGLES,0,o.count);});}
document.getElementById('mode').onclick=()=>{mode=1-mode;document.getElementById('mode').textContent=mode?'当前：修改后（35个凸包）':'当前：修改前（30个形状）';list();draw()};
document.getElementById('front').onclick=()=>{yaw=0;el=0;draw()};document.getElementById('side').onclick=()=>{yaw=-Math.PI/2;el=0;draw()};document.getElementById('iso').onclick=()=>{yaw=-.65;el=.2;draw()};document.getElementById('all').onclick=()=>{meshes[mode].forEach(o=>o.visible=true);list();draw()};
let drag=null;canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointerup=()=>drag=null;canvas.onpointermove=e=>{if(!drag)return;yaw+=(e.clientX-drag[0])*.007;el=Math.max(-1.4,Math.min(1.4,el+(e.clientY-drag[1])*.007));drag=[e.clientX,e.clientY];draw()};canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.3,Math.min(4,zoom*Math.exp(-e.deltaY*.001)));draw()},{passive:false});window.onresize=draw;list();draw();
</script></html>'''
    (out/'collision_structure.html').write_text(html.replace('__BUFFERS__',json.dumps(buffers,separators=(',',':'))))
