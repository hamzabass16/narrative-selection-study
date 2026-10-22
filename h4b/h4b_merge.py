"""Validate H4b coder output, compute agreement on the double-coded 20 percent, list disagreements for adjudication,
and (with --final) write codes/final_codes.csv applying adjudication decisions."""
import json, glob, sys
import numpy as np, pandas as pd
from pathlib import Path
B = Path('/root/analysis/h4b')
KEYS = ['item', 'conquered_tradition', 'conqueror_tradition', 'same_tradition', 'adopted', 'adopted_year', 'conqueror_writing',
        'confidence', 'source1', 'source2', 'notes']
VAL = dict(same_tradition={'Y', 'N', 'U'}, adopted={'Y', 'P', 'N', 'U', 'NA'}, conqueror_writing={'Y', 'N', 'U'}, confidence={'1', '2', '3'})
def load(pas):
    rows = []
    for f in sorted(glob.glob(str(B / f'codes/{pas}/B*.json'))):
        for r in json.load(open(f)):
            r = {k: ('' if r.get(k) is None else str(r.get(k)).strip()) for k in KEYS}; r['batch'] = Path(f).stem; rows.append(r)
    return pd.DataFrame(rows)
p1, p2 = load('pass1'), load('pass2')
items = pd.read_csv(B / 'items.csv')
second = json.load(open(B / 'second_pass_items.json'))
issues = []
for lab, df, exp in [('pass1', p1, set(items.hitem)), ('pass2', p2, set(second))]:
    got = set(df.item) if len(df) else set()
    if exp - got: issues.append(f'{lab} missing {sorted(exp - got)}')
    if len(df) and df.item.duplicated().any(): issues.append(f'{lab} duplicates {df[df.item.duplicated()].item.tolist()}')
    for c, ok in VAL.items():
        if len(df):
            bad = df[~df[c].isin(ok)]
            if len(bad): issues.append(f'{lab} invalid {c}: {bad[["item", c]].values.tolist()}')
    if len(df):
        nos = df[(df.source1 == '') & (df.adopted.isin(['Y', 'P', 'N']))]
        if len(nos): issues.append(f'{lab} no source: {nos.item.tolist()}')
        inc = df[(df.same_tradition.isin(['Y', 'U'])) & (df.adopted != 'NA')]
        if len(inc): issues.append(f'{lab} same_tradition Y/U but adopted not NA: {inc.item.tolist()}')
print('ISSUES:', *issues, sep='\n  ') if issues else print('no validation issues')

def alpha_nominal(a, b):
    """Krippendorff's alpha, nominal, two coders, no missing."""
    vals = sorted(set(a) | set(b)); idx = {v: i for i, v in enumerate(vals)}
    o = np.zeros((len(vals), len(vals)))
    for x, y in zip(a, b): o[idx[x], idx[y]] += 1; o[idx[y], idx[x]] += 1
    n = o.sum(); nc = o.sum(0)
    do = (n - np.trace(o)); de = (n * n - (nc ** 2).sum()) / (n - 1)
    return float(1 - do / de) if de > 0 else float('nan')
def norm_t(s):
    s = s.lower().strip()
    return s.split(':')[0].strip() if s.startswith('other') else s
A = p1.set_index('item').loc[[i for i in second if i in set(p1.item)]]
Bq = p2.set_index('item').reindex(A.index)
agree = {}
both = Bq.adopted.notna()
for c, f in [('same_tradition', str), ('adopted', str), ('conqueror_writing', str), ('conqueror_tradition', norm_t), ('conquered_tradition', norm_t)]:
    a, b = A.loc[both, c].map(f).values, Bq.loc[both, c].map(f).values
    agree[c] = dict(n=int(both.sum()), agree=int((a == b).sum()), alpha=alpha_nominal(list(a), list(b)))
# key derived code: the analysed outcome (excluded / Y / P / N / U)
def outcome(r): return 'excl' if r.same_tradition != 'N' else r.adopted
a, b = A[both].apply(outcome, axis=1).values, Bq[both].apply(outcome, axis=1).values
agree['analysed_outcome'] = dict(n=int(both.sum()), agree=int((a == b).sum()), alpha=alpha_nominal(list(a), list(b)))
print(json.dumps(agree, indent=1))
dis = [i for i in A.index[both] if any(norm_t(A.at[i, c]) != norm_t(Bq.at[i, c]) for c in ['same_tradition', 'adopted', 'conqueror_writing'])
       or outcome(A.loc[i]) != outcome(Bq.loc[i])]
json.dump(dict(agreement=agree, disagreements=dis, issues=issues), open(B / 'agreement.json', 'w'), indent=1)
print('disagreements:', dis)

if '--final' in sys.argv:
    fin = p1.set_index('item').copy(); fin['decided_by'] = 'pass1'
    adj_path = B / 'codes/adjudication.json'
    if adj_path.exists():
        for r in json.load(open(adj_path)):
            i = r['item']
            for c in ['conquered_tradition', 'conqueror_tradition', 'same_tradition', 'adopted', 'adopted_year', 'conqueror_writing', 'confidence']:
                if c in r: fin.at[i, c] = str(r[c])
            fin.at[i, 'decided_by'] = 'adjudicator'; fin.at[i, 'adjudication_note'] = r.get('notes', '')
    fin.reset_index().to_csv(B / 'codes/final_codes.csv', index=False)
    print('final codes written', len(fin))
