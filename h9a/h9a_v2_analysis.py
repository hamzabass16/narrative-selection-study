"""H9a version 2 analysis (approved retest plan). Written before any version-2 code was read.
Stage 'negbatch': after pass 1, every passage coded NEG by the first coder is sent to two further independent coders
(the second-coder code from the 20 percent sample counts as one of them where it exists).
Stage 'analyse':
- Agreement on the random 20 percent double-coded sample (relevance, valence; Krippendorff alpha, nominal).
- Final valence: first coder's code, except for passages the first coder coded NEG, whose final code is the majority of
  the three codes (a passage with no majority is 'disputed' and counted as NEG in the primary analysis).
- For each behaviour: share judged bad = NEG / (POS + NEG). Primary estimate: family-weighted (each language family has
  total weight 1, split equally among its societies), with a 95 percent family-cluster bootstrap interval (2,000 draws).
  Also unweighted counts with Wilson intervals, and whether n >= 73.
- H9a falsified for a behaviour if the family-weighted share exceeds 5 percent.
- Negative share by target (KIN, GROUP, STRANGER, ENEMY, UNCLEAR)."""
import sys, json, glob, math, random, collections
import numpy as np, pandas as pd, krippendorff
B = '/root/analysis/h9a/'
DOM = ['Family', 'Group', 'Reciprocity', 'Heroism', 'Deference', 'Fairness', 'Property']
def load(pattern):
    out = {}
    for f in sorted(glob.glob(pattern)):
        for r in json.load(open(f)): out[r['pid']] = r
    return out
def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'),) * 2
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))
items = {it['pid']: it for it in json.load(open(B + 'passages_v2.json'))}
if sys.argv[1] == 'negbatch':
    p1 = load(B + 'codes_v2/pass1/*.json'); p2 = load(B + 'codes_v2/pass2/D*.json')
    neg = [pid for pid, r in p1.items() if r.get('valence') == 'NEG']
    need2 = [pid for pid in neg if pid not in p2]
    slim = lambda pid: {k: items[pid][k] for k in ['pid', 'society', 'domain', 'text']}
    rng = random.Random(20261025)
    a = [slim(p) for p in need2]; rng.shuffle(a)
    b = [slim(p) for p in neg]; rng.shuffle(b)
    json.dump(a, open(B + 'codes_v2/batches/N2.json', 'w'), indent=0)  # second code where the 20% sample gave none
    json.dump(b, open(B + 'codes_v2/batches/N3.json', 'w'), indent=0)  # third code for every NEG passage
    print('NEG by first coder', len(neg), 'need second code', len(need2)); sys.exit()
p1 = load(B + 'codes_v2/pass1/*.json'); p2 = load(B + 'codes_v2/pass2/D*.json')
n2 = load(B + 'codes_v2/pass2/N2*.json'); n3 = load(B + 'codes_v2/pass2/N3*.json')
assert set(p1) == set(items), (len(p1), len(items))
OUT = {'passages': len(items)}
dbl = json.load(open(B + 'codes_v2/double_coded_pids.json'))
both = [p for p in dbl if p in p2]
def al(a, b):
    lab = {v: i for i, v in enumerate(sorted(set(a) | set(b)))}
    return float(krippendorff.alpha(reliability_data=np.vstack([[lab[x] for x in a], [lab[x] for x in b]]).astype(float), level_of_measurement='nominal'))
rel_a = [p1[p]['relevant'] for p in both]; rel_b = [p2[p]['relevant'] for p in both]
val_a = [p1[p]['valence'] for p in both]; val_b = [p2[p]['valence'] for p in both]
br = [p for p in both if p1[p]['relevant'] == 'Y' and p2[p]['relevant'] == 'Y']
OUT['agreement'] = dict(n=len(both), relevance_agree=sum(a == b for a, b in zip(rel_a, rel_b)), relevance_alpha=al(rel_a, rel_b),
                        valence_agree=sum(a == b for a, b in zip(val_a, val_b)), valence_alpha=al(val_a, val_b),
                        both_relevant=len(br), valence_alpha_both_relevant=al([p1[p]['valence'] for p in br], [p2[p]['valence'] for p in br]),
                        neg_first=sum(v == 'NEG' for v in val_a), neg_second=sum(v == 'NEG' for v in val_b))
final = {}; neg_audit = []
for pid, r in p1.items():
    v = r['valence'] if r['relevant'] == 'Y' else 'NA'
    if v == 'NEG':
        c2 = (p2.get(pid) or n2.get(pid) or {}); c3 = n3.get(pid) or {}
        codes = [v, c2.get('valence') if c2.get('relevant') == 'Y' else 'NA', c3.get('valence') if c3.get('relevant') == 'Y' else 'NA']
        cnt = collections.Counter(codes); top, k = cnt.most_common(1)[0]
        fv = top if k >= 2 else 'DISPUTED'
        neg_audit.append(dict(pid=pid, society=items[pid]['society'], domain=items[pid]['domain'], codes=codes, final=fv, quote=r.get('quote', ''), target=r.get('target')))
        v = 'NEG' if fv in ('NEG', 'DISPUTED') else fv
    final[pid] = dict(valence=v, target=r.get('target', 'NA'), society=items[pid]['society'], domain=items[pid]['domain'], first=r['valence'] if r['relevant'] == 'Y' else 'NA')
F = pd.DataFrame.from_dict(final, orient='index')
cand = pd.concat([pd.read_csv(B + 'candidates.csv'), pd.read_csv(B + 'candidates_extra.csv')])
import re
cand['society_key'] = cand.society.map(lambda x: re.sub(r'[^A-Za-z0-9]+', '_', x).strip('_'))
fam = cand.drop_duplicates('society_key').set_index('society_key').family
F['family'] = F.society.map(fam)
assert F.family.notna().all(), F[F.family.isna()].society.unique()
nsoc = F.groupby('family').society.nunique(); F['w'] = F.family.map(lambda f: 1.0 / nsoc[f])
OUT['societies'] = int(F.society.nunique()); OUT['families'] = int(F.family.nunique())
OUT['relevant'] = int((F.valence != 'NA').sum()); OUT['valenced'] = int(F.valence.isin(['POS', 'NEG']).sum())
OUT['neg_review'] = dict(first_coder_neg=len(neg_audit), confirmed=sum(a['final'] == 'NEG' for a in neg_audit), disputed=sum(a['final'] == 'DISPUTED' for a in neg_audit),
                         overturned=sum(a['final'] not in ('NEG', 'DISPUTED') for a in neg_audit))
rng = np.random.default_rng(20261025)
fams = sorted(F.family.unique())
res = {}
for d in DOM:
    s = F[(F.domain == d) & F.valence.isin(['POS', 'NEG'])]
    k, n = int((s.valence == 'NEG').sum()), int(len(s))
    lo, hi = wilson(k, n)
    wn = (s.w * (s.valence == 'NEG')).sum(); wd = s.w.sum(); ws = float(wn / wd) if wd > 0 else float('nan')
    bs = []
    byf = {f: g for f, g in s.groupby('family')}
    for _ in range(2000):
        pick = rng.choice(fams, len(fams))
        num = sum((byf[f].w * (byf[f].valence == 'NEG')).sum() for f in pick if f in byf); den = sum(byf[f].w.sum() for f in pick if f in byf)
        if den > 0: bs.append(num / den)
    res[d] = dict(pos=n - k, neg=k, n=n, share=k / n if n else float('nan'), wilson_lo=lo, wilson_hi=hi, weighted_share=ws,
                  boot_lo=float(np.percentile(bs, 2.5)) if bs else float('nan'), boot_hi=float(np.percentile(bs, 97.5)) if bs else float('nan'),
                  societies_with_evaluation=int(s.society.nunique()), n_ge_73=bool(n >= 73), falsified=bool(ws > 0.05))
OUT['by_behaviour'] = res
T = F[F.valence.isin(['POS', 'NEG'])]
OUT['by_target'] = {t: dict(pos=int((g.valence == 'POS').sum()), neg=int((g.valence == 'NEG').sum())) for t, g in T.groupby('target')}
OUT['first_coder_only_counts'] = {d: dict(pos=int(((F.domain == d) & (F['first'] == 'POS')).sum()), neg=int(((F.domain == d) & (F['first'] == 'NEG')).sum())) for d in DOM}
OUT['verdict'] = 'falsified for: ' + ', '.join(d for d in DOM if res[d]['falsified']) if any(res[d]['falsified'] for d in DOM) else 'not falsified for any behaviour'
OUT['upper_bound_below_5pct'] = [d for d in DOM if res[d]['wilson_hi'] < 0.05]
json.dump(OUT, open(B + 'h9a_v2_results.json', 'w'), indent=1, default=float); json.dump(neg_audit, open(B + 'h9a_v2_neg_audit.json', 'w'), indent=1)
print(json.dumps(OUT, indent=1, default=float))
