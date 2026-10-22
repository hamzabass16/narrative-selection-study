"""H9a pipeline (Addendum 14.3). Rules fixed here on 23 Oct 2026 before candidates.csv was read.
Stage 'sample': choose one society per top-level family from candidates.csv:
  - keep candidates whose society is not a PSF society (checked by the candidate agent) and whose approx_words >= 30000;
  - within a family, choose one candidate at random (random.Random('20261022-<family_glottocode>'));
  - if more than 30 families remain, choose 30 by region: regions are Africa, Asia, Oceania, Americas, Europe-NEurasia
    (as recorded in the candidates' region field, mapped below); take up to 6 per region in random order (seed 20261022),
    then fill remaining slots at random from the leftover families; writes sample.csv and sample_rule.json.
Stage 'batches': after texts are retrieved and passages extracted (extract_passages.py -> passages.json), write one coding
  batch per society (codes/batches/<society>.json) and a 20 percent double-coding sample (random, seed 20261022), split into
  batches of at most 80 items (codes/batches/dbl_<k>.json).
Stage 'analyse': merge codes, compute agreement on the double-coded items, and for each behaviour the share of
  valence-coded instances judged bad (NEG / (POS + NEG)) with a 95 percent Wilson interval; H9a is falsified for a behaviour
  if that share exceeds 5 percent. Primary codes = first coder; sensitivity: double-coded items replaced by the second coder."""
import sys, json, random, csv, math, collections, re
from pathlib import Path
import pandas as pd
B = Path('/root/analysis/h9a')
DOM = ['Family', 'Group', 'Reciprocity', 'Heroism', 'Deference', 'Fairness', 'Property']
def region_bucket(r):
    r = str(r).lower()
    if any(k in r for k in ['africa', 'sahara', 'madagascar']): return 'Africa'
    if any(k in r for k in ['oceania', 'australia', 'new guinea', 'melanesia', 'polynesia', 'micronesia', 'pacific', 'torres']): return 'Oceania'
    if any(k in r for k in ['america', 'arctic', 'amazon', 'andes', 'caribbean', 'mexico', 'canada', 'alaska', 'greenland']): return 'Americas'
    if any(k in r for k in ['europe', 'siberia', 'eurasia', 'caucasus', 'scandinavia', 'lapland', 'russia']): return 'Europe-NEurasia'
    return 'Asia'
def sample():
    c = pd.read_csv(B / 'candidates.csv', dtype=str).fillna('')
    c['w'] = pd.to_numeric(c.approx_words.str.replace(',', '').str.extract(r'(\d+)')[0], errors='coerce')
    c = c[(c.w >= 30000) & (c.fulltext_url != '')].copy()
    c['fam'] = c.family_glottocode.where(c.family_glottocode != '', c.family)
    pick = []
    for fam, g in c.groupby('fam', sort=True):
        rng = random.Random(f'20261022-{fam}'); pick.append(g.iloc[rng.randrange(len(g))])
    s = pd.DataFrame(pick); s['bucket'] = s.region.map(region_bucket)
    if len(s) > 30:
        rng = random.Random(20261022); chosen = []; left = []
        for bk in ['Africa', 'Asia', 'Oceania', 'Americas', 'Europe-NEurasia']:
            ids = list(s[s.bucket == bk].index); rng.shuffle(ids); chosen += ids[:6]; left += ids[6:]
        rng.shuffle(left); chosen += left[:30 - len(chosen)]
        s = s.loc[chosen]
    s['society_key'] = s.society.map(lambda x: re.sub(r'[^A-Za-z0-9]+', '_', x).strip('_'))
    s.to_csv(B / 'sample.csv', index=False)
    json.dump(dict(rule=__doc__.split("Stage 'batches'")[0], n_candidates=int(len(c)), n_families=int(c.fam.nunique()), n_sample=int(len(s)),
                   by_bucket=s.bucket.value_counts().to_dict()), open(B / 'sample_rule.json', 'w'), indent=1)
    print(s[['society', 'family', 'bucket', 'title', 'year']].to_string())
def batches():
    items = json.load(open(B / 'passages.json'))
    out = B / 'codes/batches'; out.mkdir(parents=True, exist_ok=True)
    by = collections.defaultdict(list)
    for it in items: by[it['society']].append({k: it[k] for k in ['pid', 'society', 'domain', 'text']})
    for soc, lst in by.items(): json.dump(lst, open(out / f'{soc}.json', 'w'), indent=0)
    rng = random.Random(20261022); ids = [it['pid'] for it in items]; dbl = sorted(rng.sample(ids, round(0.2 * len(ids))))
    dset = set(dbl); dl = [{k: it[k] for k in ['pid', 'society', 'domain', 'text']} for it in items if it['pid'] in dset]
    rng.shuffle(dl)
    for k in range(0, len(dl), 80): json.dump(dl[k:k + 80], open(out / f'dbl_{k // 80 + 1:02d}.json', 'w'), indent=0)
    json.dump(dbl, open(B / 'double_coded_pids.json', 'w'))
    print({s: len(v) for s, v in by.items()}, 'double:', len(dl), 'batches:', math.ceil(len(dl) / 80))
def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'),) * 3
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)
def analyse():
    items = {it['pid']: it for it in json.load(open(B / 'passages.json'))}
    def load(pat):
        rows = {}
        for f in sorted((B / 'codes').glob(pat)):
            for r in json.load(open(f)): rows[r['pid']] = r
        return rows
    c1, c2 = load('pass1/*.json'), load('pass2/*.json')
    R = dict(items=len(items), coded1=len(c1), coded2=len(c2), missing1=sorted(set(items) - set(c1))[:50])
    both = [p for p in c2 if p in c1]
    def alpha(a, b):
        vals = sorted(set(a) | set(b)); ix = {v: i for i, v in enumerate(vals)}; import numpy as np
        o = np.zeros((len(vals), len(vals)))
        for x, y in zip(a, b): o[ix[x], ix[y]] += 1; o[ix[y], ix[x]] += 1
        n = o.sum(); nc = o.sum(0); de = (n * n - (nc ** 2).sum()) / (n - 1)
        return float(1 - (n - o.trace()) / de) if de > 0 else float('nan')
    rel1 = [c1[p]['relevant'] for p in both]; rel2 = [c2[p]['relevant'] for p in both]
    v1 = [c1[p]['valence'] for p in both]; v2 = [c2[p]['valence'] for p in both]
    R['agreement'] = dict(n=len(both), relevant_agree=sum(a == b for a, b in zip(rel1, rel2)), relevant_alpha=alpha(rel1, rel2),
                          valence_agree=sum(a == b for a, b in zip(v1, v2)), valence_alpha=alpha(v1, v2),
                          neg_by_coder1=sum(x == 'NEG' for x in v1), neg_by_coder2=sum(x == 'NEG' for x in v2))
    for lab, codes in [('primary', c1), ('second_coder_where_double', {**c1, **{p: c2[p] for p in both}})]:
        res = {}
        for d in DOM:
            rows = [(p, codes[p]) for p in codes if items.get(p, {}).get('domain') == d]
            pos = sum(r['valence'] == 'POS' for _, r in rows); neg = sum(r['valence'] == 'NEG' for _, r in rows)
            none = sum(r['valence'] == 'NONE' for _, r in rows); irr = sum(r['relevant'] == 'N' for _, r in rows)
            p, lo, hi = wilson(neg, pos + neg)
            socs_neg = sorted({items[p_]['society'] for p_, r in rows if r['valence'] == 'NEG'})
            socs_pos = sorted({items[p_]['society'] for p_, r in rows if r['valence'] == 'POS'})
            res[d] = dict(items=len(rows), irrelevant=irr, none=none, pos=pos, neg=neg, share_neg=p, lo95=lo, hi95=hi,
                          falsified=bool(p > 0.05) if pos + neg else None, upper_bound_below_5pct=bool(hi < 0.05) if pos + neg else None,
                          societies_with_pos=len(socs_pos), societies_with_neg=len(socs_neg), neg_societies=socs_neg)
        R[lab] = res
    R['neg_examples'] = [dict(pid=p, society=items[p]['society'], domain=items[p]['domain'], behaviour=r.get('behaviour'), quote=r.get('quote'))
                         for p, r in c1.items() if r['valence'] == 'NEG'][:80]
    json.dump(R, open(B / 'h9a_results.json', 'w'), indent=1)
    print(json.dumps({k: R[k] for k in ['items', 'coded1', 'coded2', 'agreement']}, indent=1))
    for d, r in R['primary'].items(): print(d, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != 'neg_societies'})
if __name__ == '__main__':
    {'sample': sample, 'batches': batches, 'analyse': analyse}[sys.argv[1]]()
