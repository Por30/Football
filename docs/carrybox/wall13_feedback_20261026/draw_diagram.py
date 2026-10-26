"""Generate a readable vector/PNG architecture figure directly from shapes/text."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.path import Path as Curve
from matplotlib.font_manager import FontProperties

OUT=Path(__file__).resolve().parent
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
fig,ax=plt.subplots(figsize=(16,10.5),dpi=140)
ax.set_xlim(0,1600);ax.set_ylim(0,1050);ax.axis('off')
blue,orange='#28699D','#B87922'


def text(x,y,value,size=16,color='#183D58',**kw):
    ax.text(x,y,value,ha='center',va='center',fontsize=size,fontproperties=FONT,color=color,**kw)


def box(x,y,w,h,label,training=False,strong=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=15',
        linewidth=2.1 if strong else 1.6,edgecolor=orange if training else blue,
        facecolor='#FFF0DB' if training else '#CCE9FC' if strong else '#EAF4FC'))
    text(x+w/2,y+h/2,label,16,'#714715' if training else '#183D58')


def arrow(a,b,training=False,dashed=False,points=None):
    kw=dict(arrowstyle='-|>',mutation_scale=17,linewidth=1.8,
        color=orange if training else blue,linestyle=(0,(4,3)) if dashed else '-')
    if points:
        ax.add_patch(FancyArrowPatch(path=Curve(points,[Curve.MOVETO]+[Curve.LINETO]*(len(points)-1)),**kw))
    else:ax.add_patch(FancyArrowPatch(a,b,**kw))


text(800,1005,'Wall13｜预测箱子位姿融入 128 维深度特征',24)
text(800,959,'revision 2 · 蓝色模块在训练和部署中都参与动作计算',16,'#526879')
box(50,700,200,130,'深度历史\n4 × 27 × 48\n单位：米')
box(310,700,150,130,'共享 CNN')
box(520,700,200,130,'原始视觉特征 z\n128 维')
box(800,690,240,150,'拼接 [z, p]：137 维\nLinear 137 → 128\nELU → 融合特征128',strong=True)
box(1180,700,300,130,'Actor：输入 686 维\n558 本体 + 128 视觉\n512 → 256 → 256')
box(1180,855,300,75,'本体历史：93 × 6 = 558')
box(1180,450,300,130,'29 维关节动作')
box(520,450,200,130,'箱子回归头\n128 → 128 → 9')
box(800,450,240,130,'预测位姿 p：9 维\n相机系 xyz：3 维\n原始旋转 6D：6 维')
for a,b in [((250,765),(310,765)),((460,765),(520,765)),((720,765),(800,765)),
            ((1040,765),(1180,765)),((1330,855),(1330,830)),((1330,700),(1330,580)),
            ((620,700),(620,580)),((720,515),(800,515)),((920,580),(920,690))]:
    arrow(a,b)
text(1110,790,'128 维',13)
text(975,634,'预测反馈',14)

ax.add_patch(FancyBboxPatch((25,105),1015,245,boxstyle='round,pad=0,rounding_size=18',
    linewidth=1.1,edgecolor='#D5B083',facecolor='#FFFAF2',zorder=-1))
text(532,315,'仅训练：真值参与监督，不输入 Actor',16,'#8F5F22',
     bbox=dict(facecolor='#FFFAF2',edgecolor='none',pad=3))
box(50,145,330,115,'仿真真值：12 维\n位置3 + 旋转6 + 实际尺寸3',training=True)
box(520,145,330,115,'位置 MSE + 对称旋转 MSE\n辅助系数 = 1.0',training=True)
arrow((380,202),(520,202),training=True)
arrow((920,450),(850,202),training=True,
    points=[(920,450),(920,202),(850,202)])
text(989,383,'配对当前帧',12,'#98641E')
arrow((620,260),(620,450),training=True,dashed=True)
text(556,390,'辅助梯度',12,'#98641E')
arrow((520,215),(385,700),training=True,dashed=True,
    points=[(520,215),(420,215),(420,625),(385,625),(385,700)])
text(1300,306,'部署保留回归头与融合层\n输入仍只有深度和本体信息',16)
text(800,66,'PPO 梯度：Actor → 融合层 → 回归头 / CNN；预测不 detach',15,'#526879')
text(800,28,'Critic 123 维、AMP 600 维仅训练使用；原任务、数据和 24 步训练配方保持',14,'#526879')
fig.subplots_adjust(left=.015,right=.985,bottom=.01,top=.99)
fig.savefig(OUT/'architecture.png',dpi=140,facecolor='white')
fig.savefig(OUT/'architecture.svg',facecolor='white')
plt.close(fig)
