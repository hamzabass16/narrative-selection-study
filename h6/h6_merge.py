"""H6 extraction merge (written 23 October 2026 while the extractors were running, before any extraction was read).
Stage 'compare': for each study, compute Hedges' g (with h6_meta.g_from) for every accessible record of extractor A and
of extractor B, in the stratum given by candidates.csv. A study AGREES when both extractors have the same number of usable
records and, after sorting each list by (n_t + n_c, g), every pair matches with |g_A - g_B| <= 0.05 and the same total n
within 2. Otherwise it is DISPUTED. Studies where both mark the full text inaccessible agree as inaccessible. Writes
compare.json and the list of disputed studies (adjudicate_list.json) for a third, blind adjudicator, plus a 20 percent
random sample of agreeing studies (seed 20261023) for the separate verifier (verify_list.json).
Stage 'final': extraction_final.json = extractor A's records for agreeing studies, with the verifier's corrections applied
where it found an error (verified.json), and the adjudicator's records for disputed studies (adjudicated.json).
Every record gets 'stratum' from candidates.csv and 'study_id' as in the list."""
import sys, json, glob, random, numpy as np, pandas as pd
H = '/root/analysis/h6/'
sys.path.insert(0, H); from h6_meta import g_from
cand = pd.read_csv(H + 'candidates.csv').set_index('id')
def load(pattern):
    out = []
    for f in sorted(glob.glob(H + pattern)): out += json.load(open(f))
    return out
def usable(recs):
    rows = []
    for r in recs:
        if not r.get('accessible', True): continue
        g = g_from(r.get('stat_type'), r.get('values') or {}, r.get('higher_is_more_prosocial', True))
        if g is None: continue
        v = r.get('values') or {}
        rows.append((float(v.get('n_t', 0)) + float(v.get('n_c', 0)), g[0], r))
    return sorted(rows, key=lambda x: (x[0], x[1]))
stage = sys.argv[1]
A = load('extraction_A_*.json'); Bx = load('extraction_B_*.json')
byA, byB = {}, {}
for r in A: byA.setdefault(r['study_id'], []).append(r)
for r in Bx: byB.setdefault(r['study_id'], []).append(r)
studies = sorted(set(byA) | set(byB))
if stage == 'compare':
    comp = {}
    for s in studies:
        a, b = byA.get(s, []), byB.get(s, [])
        ua, ub = usable(a), usable(b)
        if not ua and not ub:
            comp[s] = dict(status='AGREE_inaccessible' if a and b else 'DISPUTED', nA=len(a), nB=len(b)); continue
        ok = len(ua) == len(ub) and all(abs(x[1] - y[1]) <= 0.05 and abs(x[0] - y[0]) <= 2 for x, y in zip(ua, ub))
        comp[s] = dict(status='AGREE' if ok else 'DISPUTED', usableA=len(ua), usableB=len(ub),
                       gA=[round(x[1], 3) for x in ua], gB=[round(x[1], 3) for x in ub])
    dis = [s for s, c in comp.items() if c['status'] == 'DISPUTED']
    agree = sorted(s for s, c in comp.items() if c['status'] == 'AGREE')
    rng = random.Random(20261023); ver = sorted(rng.sample(agree, max(1, round(0.2 * len(agree))))) if agree else []
    json.dump(comp, open(H + 'compare.json', 'w'), indent=1); json.dump(dis, open(H + 'adjudicate_list.json', 'w')); json.dump(ver, open(H + 'verify_list.json', 'w'))
    print(json.dumps(dict(studies=len(studies), agree=len(agree), agree_inaccessible=sum(c['status'] == 'AGREE_inaccessible' for c in comp.values()),
                          disputed=dis, verify=ver), indent=1))
elif stage == 'final':
    comp = json.load(open(H + 'compare.json'))
    adj = {}
    for r in (json.load(open(H + 'adjudicated.json')) if glob.glob(H + 'adjudicated.json') else []): adj.setdefault(r['study_id'], []).append(r)
    ver = {}
    for r in (json.load(open(H + 'verified.json')) if glob.glob(H + 'verified.json') else []): ver.setdefault(r['study_id'], []).append(r)
    final = []; missing = []
    for s in studies:
        st = comp[s]['status']
        if st == 'DISPUTED':
            if s not in adj: missing.append(s); continue
            recs = adj[s]
        else:
            recs = ver.get(s) or byA.get(s, [])
        for r in recs:
            r = dict(r); r['study_id'] = s; r['stratum'] = cand.at[s, 'stratum'] if s in cand.index else r.get('stratum'); final.append(r)
    if missing: print('ADJUDICATION MISSING for', missing); raise SystemExit(1)
    json.dump(final, open(H + 'extraction_final.json', 'w'), indent=1)
    print('final records', len(final), 'studies', len({r['study_id'] for r in final}))
