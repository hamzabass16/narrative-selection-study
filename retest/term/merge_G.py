"""Merge the 29 new termination codes (batches G01, G02) with the blind double codes (G_dbl).
Rule (same as the original Study 1 coding): the batch code is primary. For a double-coded item whose Q2 differs, a third
blind coder (out/G_adj.json) decides by majority of the three Q2 codes; Q3 and end_year are taken from a coder whose Q2
matches the final Q2 (the primary coder first). With no majority, Q2 = T9 and Q3 = U (event status unknown).
Writes final_codes_G.csv (polity_id, Q2, Q3, end_year) and agreement_G.json."""
import json, collections, os, pandas as pd
T = '/root/analysis/retest/term/'
items = pd.read_csv(T + 'items_G.csv')[['id', 'item', 'long_name']]
prim = {}
for b in ['G01', 'G02']:
    for r in json.load(open(T + f'out/{b}.json')): prim[r['item']] = r
assert set(prim) == set(items.item), sorted(set(items.item) ^ set(prim))
dbl = {r['item']: r for r in json.load(open(T + 'out/G_dbl.json'))}
adj = {r['item']: r for r in json.load(open(T + 'out/G_adj.json'))} if os.path.exists(T + 'out/G_adj.json') else {}
# Follow-up (added 23 October 2026 after the first Study 1 run, before its results were read): 8 weakly sourced items were
# coded again from scratch by a blind coder (out/G_fu.json). The follow-up code counts as a second code: where its Q2 differs
# from the primary code, a third blind coder (out/G_adj.json) decides by majority, as for the double-coded items.
fu = {r['item']: r for r in json.load(open(T + 'out/G_fu.json'))} if os.path.exists(T + 'out/G_fu.json') else {}
cmp = []
for k, d in dbl.items():
    p = prim[k]
    cmp.append(dict(item=k, Q1=(p['Q1'], d['Q1']), Q2=(p['Q2'], d['Q2']), Q3=(p['Q3'], d['Q3']), end=(p['end_year'], d['end_year'])))
need_adj = [c['item'] for c in cmp if c['Q2'][0] != c['Q2'][1]]
need_fu = [k for k, d in fu.items() if prim[k]['Q2'] != d['Q2']]
missing = [k for k in need_adj + need_fu if k not in adj]
out = []
for r in items.itertuples():
    p = prim[r.item]; q2, q3, ey = p['Q2'], p['Q3'], p['end_year']
    if r.item in need_adj and r.item in adj:
        codes = [p, dbl[r.item], adj[r.item]]
        top, n = collections.Counter(c['Q2'] for c in codes).most_common(1)[0]
        if n >= 2:
            src = next(c for c in codes if c['Q2'] == top); q2, q3, ey = top, src['Q3'], src['end_year']
        else:
            q2, q3 = 'T9', 'U'
    if r.item in need_fu and r.item in adj:
        codes = [p, fu[r.item], adj[r.item]]
        top, n = collections.Counter(c['Q2'] for c in codes).most_common(1)[0]
        if n >= 2:
            src = next(c for c in codes if c['Q2'] == top); q2, q3, ey = top, src['Q3'], src['end_year']
        else:
            q2, q3 = 'T9', 'U'
    out.append(dict(polity_id=int(r.id), item=r.item, name=r.long_name, Q2=q2, Q3=q3, end_year=ey))
O = pd.DataFrame(out)
agree = dict(double_coded=len(cmp), Q1_agree=sum(c['Q1'][0] == c['Q1'][1] for c in cmp), Q2_agree=sum(c['Q2'][0] == c['Q2'][1] for c in cmp),
             Q3_agree=sum(c['Q3'][0] == c['Q3'][1] for c in cmp), end_within_25y=sum(abs(float(c['end'][0]) - float(c['end'][1])) <= 25 for c in cmp),
             need_adjudication=need_adj, followup_items=sorted(fu), followup_Q2_agree=sum(prim[k]['Q2'] == d['Q2'] for k, d in fu.items()),
             followup_need_adjudication=need_fu, adjudication_missing=missing, pairs=cmp, final_Q2_counts=O.Q2.value_counts().to_dict())
json.dump(agree, open(T + 'agreement_G.json', 'w'), indent=1, default=str)
if missing:
    print('ADJUDICATION NEEDED for', missing); raise SystemExit(1)
O.to_csv(T + 'final_codes_G.csv', index=False)
print(json.dumps({k: v for k, v in agree.items() if k != 'pairs'}, indent=1, default=str))
