"""Build the Study 1 coding frame from the current Seshat release (export of 17 Oct 2026).
Frame = polities that enter at least one Study 1 model:
  (a) a narrative tradition with a public-domain canon (widespread religion of order 1, else official religion), or
  (b) a known value of moralizing enforcement of rulers (H8), or
  (c) a known value of moralizing supernatural punishment and reward (H5).
Polities whose end year is 2000 or later are right-censored and not coded."""
import json, sys, pandas as pd, numpy as np
sys.path.insert(0, '/root/analysis/cci')
from tradition_map import tradition
db = json.load(open('/root/analysis/seshat/seshat_current_2026-10-17.json'))
T = lambda k: pd.DataFrame(db[k]['rows'], columns=db[k]['cols'])
pol = T('core/polities').set_index('id')
nga = T('core/ngas').set_index('id'); reg = T('core/regions').set_index('id')
rel = T('core/religions').set_index('id').religion_name
known = {'present', 'absent', 'inferred present', 'inferred absent', 'A~P'}

def trad_sets(df, col):
    df = df.copy(); df['trad'] = df[col].map(rel).map(tradition)
    return df.groupby('polity').trad.apply(lambda s: sorted(set(x for x in s if isinstance(x, str))))
w = T('rt/widespread-religions'); w1 = trad_sets(w[w.order.astype(str) == '1'], 'widespread_religion')
of = trad_sets(T('rt/official-religions'), 'coded_value')
prim = {}
for p in pol.index:
    a = w1.get(p, []); b = of.get(p, [])
    prim[p] = a if a else b
pol['trad_primary'] = pd.Series({p: ';'.join(v) for p, v in prim.items()})
pol['trad_widespread1'] = pd.Series({p: ';'.join(w1.get(p, [])) for p in pol.index})
pol['trad_official'] = pd.Series({p: ';'.join(of.get(p, [])) for p in pol.index})
def val(table):
    r = T(table); r = r[r.coded_value.isin(known)]
    return r.groupby('polity').coded_value.apply(lambda s: ';'.join(sorted(set(s))))
pol['mer'] = val('rt/moralizing-enforcement-of-rulers')
pol['mspr'] = val('rt/moralizing-supernatural-punishment-and-reward')
pol['in_frame'] = (pol.trad_primary.fillna('') != '') | pol.mer.notna() | pol.mspr.notna()
pol['censored_present'] = pol.end_year >= 2000
pol['nga_name'] = pol.home_nga.map(nga.name); pol['region_name'] = pol.home_seshat_region.map(reg.name)

# capitals
cap = T('general/polity-capitals'); capn = cap.groupby('polity').capital.apply(lambda s: '; '.join(dict.fromkeys(str(x) for x in s if isinstance(x, str)))[:120])
pol['capitals'] = capn
# successor candidates
pre = T('general/polity-preceding-entities'); suc = T('general/polity-succeeding-entities'); npr = T('core/nga-polity-relations')
cand = {p: [] for p in pol.index}
for _, r in pre.dropna(subset=['other_polity']).iterrows():
    o = int(r.other_polity); s = r.polity
    if o in cand and s in pol.index: cand[o].append((s, 'S names P as its predecessor'))
for _, r in npr.dropna(subset=['polity_party']).iterrows():
    pass
npr2 = npr.dropna(subset=['polity_party', 'nga_party']).copy(); npr2['polity_party'] = npr2.polity_party.astype(int)
for g, df in npr2.groupby('nga_party'):
    ps = [p for p in df.polity_party.unique() if p in pol.index]
    for p in ps:
        e = pol.at[p, 'end_year']; s0 = pol.at[p, 'start_year']
        nxt = [q for q in ps if q != p and pol.at[q, 'start_year'] > s0 and abs(pol.at[q, 'start_year'] - e) <= 50]
        nxt = sorted(nxt, key=lambda q: abs(pol.at[q, 'start_year'] - e))[:3]
        for q in nxt: cand[p].append((q, f'next in NGA sequence ({nga.name.get(g, g)})'))
for p in pol.index:
    rg = pol.at[p, 'home_seshat_region']; e = pol.at[p, 'end_year']; s0 = pol.at[p, 'start_year']
    if pd.isna(rg): continue
    same = pol[(pol.home_seshat_region == rg) & (pol.index != p) & (pol.start_year > s0) & ((pol.start_year - e).abs() <= 30)]
    same = same.assign(d=(same.start_year - e).abs()).sort_values('d').head(4)
    for q in same.index: cand[p].append((q, 'starts within 30 years of P end in same Seshat region'))
sucname = suc.groupby('polity').succeeding_entity.apply(lambda s: '; '.join(dict.fromkeys(str(x) for x in s if isinstance(x, str) and x.lower() not in ('unknown', 'none', 'nan'))))
def fmt(p):
    seen = {}; 
    for q, why in cand[p]:
        seen.setdefault(q, []).append(why)
    return ' || '.join(f"{pol.at[q,'long_name']} ({pol.at[q,'start_year']} to {pol.at[q,'end_year']}): {', '.join(dict.fromkeys(w))}" for q, w in seen.items())
pol['cand_successors'] = [fmt(p) for p in pol.index]
pol['succeeding_entity_text'] = sucname
pol.to_csv('/root/analysis/frame/polities_frame.csv')
f = pol[pol.in_frame & ~pol.censored_present]
print('polities', len(pol), 'in_frame', pol.in_frame.sum(), 'to code', len(f), 'censored_present in frame', (pol.in_frame & pol.censored_present).sum())
print('with any candidate', (f.cand_successors != '').sum(), 'with succeeding text', f.succeeding_entity_text.notna().sum())
print('era', pd.cut(f.end_year, [-1e5, -500, 1500, 2000]).value_counts().sort_index().to_dict())
