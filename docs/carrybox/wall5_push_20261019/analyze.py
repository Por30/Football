"""Read-only full-run push-course audit; retained termination labels are not event fractions."""
from pathlib import Path
from datetime import datetime
import hashlib,json,re,statistics as st
import torch
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2];BASE=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5'
LOGS={'rev13':BASE/'launch_wall5_v13_perf_fresh_20261018_131037.log',
      'rev14':BASE/'launch_wall5_v14_asymmetric_fresh_20261019_003706.log'}
KEYS=['Mean episode length','Mean box_position loss','AMP/style_reward','Reward/task_weighted_per_step','Reward/amp_per_step',
      'Episode_Termination/time_out','Episode_Termination/tipped','Episode_Termination/fell','Iteration time']
KEYS += ['Skill/'+s+'_'+k for s in ('loco','hold') for k in ('episodes','mean_steps','successes')]

def main():
    torch.set_num_threads(1);result={'checked_at':datetime.now().astimezone().isoformat(),'runs':{}}
    all_rows={}
    for name,path in LOGS.items():
        raw=path.read_bytes();text=re.sub(r'\x1b\[[0-9;]*m','',raw.decode(errors='replace'))
        pieces=re.split(r'Learning iteration\s+(\d+)/\d+',text);rows=[]
        for i in range(1,len(pieces),2):
            if 'Iteration time:' not in pieces[i+1]:continue
            row={'iteration':int(pieces[i])}
            for line in pieces[i+1].splitlines():
                m=re.fullmatch(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)(?:s)?\s*',line)
                if m and m[1].strip() in KEYS:row[m[1].strip()]=float(m[2])
            assert all(k in row for k in KEYS),row
            row['push_scale']=min(1.,max(0.,(row['iteration']-1000)/4000));rows.append(row)
        assert rows[0]['iteration']==0 and len(rows)==rows[-1]['iteration']+1
        all_rows[name]=rows;windows=[]
        ranges=[(0,13),(0,249),(750,999),(1000,1249),(1750,1999),(2250,2499),(2750,2999),(3250,3499),(4750,4999),(6750,6999),(10000,10249),(len(rows)-250,len(rows)-1)]
        for lo,hi in ranges:
            if hi>=len(rows) or lo<0:continue
            selection=rows[lo:hi+1];entry={'first':lo,'last':hi,'means':{k:st.mean(r[k] for r in selection) for k in KEYS+['push_scale']}}
            a=rows[max(0,lo-1)];b=rows[hi];entry['skill_window_estimates']={}
            for skill in ('loco','hold'):
                prefix='Skill/'+skill+'_';n=b[prefix+'episodes']-a[prefix+'episodes']
                entry['skill_window_estimates'][skill]={'episodes_approx':n,'mean_steps_approx':
                    (b[prefix+'episodes']*b[prefix+'mean_steps']-a[prefix+'episodes']*a[prefix+'mean_steps'])/n if n else None,
                    'success_delta_approx':b[prefix+'successes']-a[prefix+'successes']}
            windows.append(entry)
        result['runs'][name]={'log':str(path),'log_snapshot_sha256':hashlib.sha256(raw).hexdigest(),'last_iteration':rows[-1]['iteration'],'windows':windows}
    ckpt=BASE/'2026-10-18_13-10-42_wall5_v13_perf_fresh_20261018_131037/model_10600.pt'
    c=torch.load(ckpt,map_location='cpu',weights_only=False)
    assert c['environment_contract']['migration_revision']==13 and c['amp']['dataset']['clip_count']==13
    assert c['environment_contract']['reset_probs']==[.8,0.,.2] and c['iter']==10600
    assert all(torch.isfinite(v).all() for v in c['model_state_dict'].values())
    result['checkpoint']={'path':str(ckpt),'sha256':hashlib.sha256(ckpt.read_bytes()).hexdigest(),'iteration':c['iter'],
        'environment_contract':c['environment_contract'],'action_std':c['model_state_dict']['log_std'].exp().tolist()}
    result['caveats']=['Training curves show correlation, not isolated causation','Mean episode length is recent completed episodes, not skill-matched survival',
        'Skill differences use rounded/rollout-averaged cumulative logs; approximate only','Termination labels are retained last labels over environments, not new-episode fractions']
    (DOC/'training_rows.json').write_text(json.dumps(all_rows)+'\n');(DOC/'training_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for name,rows in all_rows.items():
        chunks=[rows[i:i+100] for i in range(0,len(rows),100)];x=[st.mean(r['iteration'] for r in a) for a in chunks]
        for ax,key in zip(axes.flat,['Mean episode length','Skill/loco_mean_steps','Mean box_position loss','AMP/style_reward']):
            ax.plot(x,[st.mean(r[key] for r in a) for a in chunks],label=name);ax.set_title(key)
    for ax in axes.flat:
        ax.axvline(1000,color='grey',ls=':');ax.axvline(5000,color='grey',ls=':');ax.grid(alpha=.2);ax.legend();ax.set_xlabel('Training iteration')
    fig.suptitle('100-iteration means; loco mean is cumulative; dotted: push ramp start/end')
    fig.tight_layout();fig.savefig(DOC/'training_curves.png',dpi=150)
    for name,r in result['runs'].items():
        print(name,'last',r['last_iteration'])
        for w in r['windows']:
            m=w['means'];print(w['first'],w['last'],'length',round(m['Mean episode length'],2),'loco',round(w['skill_window_estimates']['loco']['mean_steps_approx'] or 0,2),'hold',round(w['skill_window_estimates']['hold']['mean_steps_approx'] or 0,2),'timeout_label',round(m['Episode_Termination/time_out'],3),'style',round(m['AMP/style_reward'],3))
if __name__=='__main__':main()
