import json, glob, sys, pandas as pd
rows=[]; bad=[]
pas=sys.argv[1]
for f in sorted(glob.glob(f'codes/{pas}/B*.json')):
    try:
        d=json.load(open(f))
    except Exception as e:
        bad.append((f,str(e))); continue
    for r in d: r['batch']=f.split('/')[-1][:3]; rows.append(r)
df=pd.DataFrame(rows)
print(pas, 'files', len(glob.glob(f'codes/{pas}/B*.json')), 'rows', len(df), 'bad', bad)
if len(df):
    Q2ok={'T0','T1a','T1b','T1c','T2','T3','T4','T5','T6','T9'}
    viol=[]
    for _,r in df.iterrows():
        q1,q2,q3=r.Q1,r.Q2,r.Q3
        if q2 not in Q2ok: viol.append((r['item'],'Q2 '+str(q2)))
        if q1=='S3' and q2!='T0': viol.append((r['item'],'S3 not T0'))
        if q1=='S4' and q2 not in ('T0','T4','T9'): viol.append((r['item'],'S4 code'))
        if q1=='S9' and q2!='T9': viol.append((r['item'],'S9 not T9'))
        if q2 in ('T0','T6') and q3!='N' and not (q1=='S4' and q3=='U'): viol.append((r['item'],f'{q2} Q3={q3}'))
        if q2 in ('T1a','T1b','T1c','T2','T5') and q3!='Y': viol.append((r['item'],f'{q2} Q3={q3}'))
    print('rule violations', len(viol), viol[:20])
    print(df.Q2.value_counts().to_dict()); print(df.Q1.value_counts().to_dict()); print(df.Q5.astype(str).value_counts().to_dict())
    print('dup items', df.item.duplicated().sum())
    df.to_csv(f'codes/{pas}_all.csv', index=False)
