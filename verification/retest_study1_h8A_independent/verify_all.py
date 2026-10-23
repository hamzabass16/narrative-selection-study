"""Step 4: run every check and write verification_B.json.

Usage: python -I -W ignore verify_all.py
Tolerances: counts exact; HR/OR within 0.03; p-values on the same side of 0.05.
"""
import json
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, '/root/analysis/verify5')
from build import load_polities  # noqa: E402
import h1  # noqa: E402
import h8  # noqa: E402
from statsmodels.duration.hazard_regression import PHReg  # noqa: E402

OUT = '/root/analysis/verify5/verification_B.json'
results = []


def add(claim, item, claimed, mine, kind, note=''):
    if kind == 'count':
        ok = int(claimed) == int(mine)
    elif kind == 'ratio':
        ok = abs(float(claimed) - float(mine)) <= 0.03
    elif kind == 'p':
        ok = (float(claimed) < 0.05) == (float(mine) < 0.05)
    else:
        raise ValueError(kind)
    results.append(dict(claim=claim, item=item, claimed=claimed,
                        yours=round(float(mine), 4) if kind != 'count' else int(mine),
                        verdict='REPRODUCED' if ok else 'DIFFERS', note=note))


# ---- Claim 1: H1 sample ----
d = load_polities()
s1 = d[d.EPI.notna() & d.event.notna()]
add(1, 'polities', 221, len(s1), 'count')
add(1, 'events', 117, s1.event.sum(), 'count')
add(1, 'internal collapse', 42, s1.internal.sum(), 'count')
add(1, 'conquest', 70, s1.conquest.sum(), 'count')
add(1, 'NGAs', 34, s1.nga_name.nunique(), 'count')

# ---- Claim 2: discrete-time hazard with NGA dummies ----
# primary spec: frame end_year, agecat = 0-based piece index capped at 3,
# era bins right-closed (pd.cut default)
o, pp = h1.run_variant('end_year', 0, True, verbose=False)
best = o['best']
irls_note = ('default IRLS converges to a false optimum (llf %.2f, HR blows up); '
             'zero-start IRLS / Newton / BFGS agree at llf %.3f'
             % (o['irls']['llf'], best['llf']))
add(2, 'polity-centuries', 526, o['n_rows'], 'count')
add(2, 'NGAs', 30, o['n_nga'], 'count')
add(2, 'HR', 1.029, best['HR'], 'ratio', irls_note)
add(2, 'CI low', 0.722, best['lo'], 'ratio')
add(2, 'CI high', 1.466, best['hi'], 'ratio')

# sensitivity of claim 2 to the ambiguous coding choices
sens = {}
for endcol in ['end_year', 'code_end_year']:
    for base in [0, 1]:
        for right in [False, True]:
            ov, _ = h1.run_variant(endcol, base, right, verbose=False)
            sens['%s|agecat_base=%d|right_closed=%s' % (endcol, base, right)] = dict(
                HR=round(ov['best']['HR'], 4), lo=round(ov['best']['lo'], 4),
                hi=round(ov['best']['hi'], 4), n_rows=ov['n_rows'],
                HR_noNGA_dropped_sample=round(ov['nonga']['HR'], 4))

# ---- Claim 3: same model without NGA dummies ----
# (a) on the full sample (no-event NGAs kept): 555 pieces, 34 NGAs
s = h1.h1_sample('end_year')
pfull = h1.split_centuries(s, 0)
pfull['era'] = h1.era_bins(pfull, True)
_, _, _, bfull = h1.fit_glm(pfull, with_nga=False)
rf = h1.summarize(bfull)
note3 = ('matches only when the NGAs with no events are kept (%d polity-centuries, %d NGAs). '
         'On the 526-piece / 30-NGA sample of claim 2 the no-dummy HR is %.3f (%.3f to %.3f, p %.3f).'
         % (len(pfull), pfull.nga.nunique(), o['nonga']['HR'], o['nonga']['lo'],
            o['nonga']['hi'], o['nonga']['p']))
add(3, 'HR', 1.184, rf['HR'], 'ratio', note3)
add(3, 'CI low', 0.902, rf['lo'], 'ratio')
add(3, 'CI high', 1.556, rf['hi'], 'ratio')

# ---- Claim 4: Cox stratified by NGA ----
c4 = h1.cox_nga('end_year', 'breslow')
c4e = h1.cox_nga('end_year', 'efron')
m = PHReg(s.dur.values, s[['EPIz']].values, status=s.event.values.astype(int),
          strata=s.nga_name.values, ties='breslow')
rsm = m.fit(groups=s.nga_name.values)
note4 = ('own Cox; Breslow and Efron identical (HR %.4f, no tied event times within NGA); '
         'statsmodels PHReg point estimate HR %.4f (its grouped robust SE returns NaN here; '
         'own robust SE matches PHReg exactly where PHReg returns one, e.g. claim 6 all-endings); '
         'own robust p %.4f; using the codes-file end_year instead gives HR %.3f'
         % (c4e['HR'], np.exp(rsm.params[0]), c4['p'],
            h1.cox_nga('code_end_year', 'breslow')['HR']))
add(4, 'HR', 1.25, c4['HR'], 'ratio', note4)
add(4, 'CI low', 0.95, c4['lo'], 'ratio')
add(4, 'CI high', 1.64, c4['hi'], 'ratio')

# ---- Claims 5-7: H8 Part A ----
a5, _ = h8.part_a('CONSTR')
add(5, 'polities', 87, a5['n'], 'count')
add(5, 'events', 47, a5['events'], 'count')
add(5, 'internal collapse', 19, a5['internal'], 'count')
add(5, 'conquest', 26, a5['conquest'], 'count')
add(5, 'Cox all endings HR', 1.11, a5['cox_all']['HR'], 'ratio')
add(5, 'Cox all endings p', 0.47, a5['cox_all']['p'], 'p')
add(5, 'Cox internal HR', 0.93, a5['cox_internal']['HR'], 'ratio')
add(5, 'Cox internal p', 0.78, a5['cox_internal']['p'], 'p')

a6, s6 = h8.part_a('rulers_eq_commoners')
add(6, 'polities', 215, a6['n'], 'count')
add(6, 'events', 116, a6['events'], 'count')
add(6, 'internal collapse', 42, a6['internal'], 'count')
add(6, 'Cox internal HR', 0.71, a6['cox_internal']['HR'], 'ratio')
add(6, 'Cox internal p', 0.12, a6['cox_internal']['p'], 'p')
add(6, 'logit OR', 0.63, a6['logit_internal_vs_T0']['OR'], 'ratio')
add(6, 'logit p', 0.08, a6['logit_internal_vs_T0']['p'], 'p')
add(6, 'logit n', 140, a6['logit_internal_vs_T0']['n'], 'count')

t7 = h8.transitions('rulers_eq_commoners', s6)
add(7, 'OR', 1.24, t7['OR'], 'ratio')
add(7, 'CI low', 1.03, t7['lo'], 'ratio')
add(7, 'CI high', 1.50, t7['hi'], 'ratio')
add(7, 'p', 0.026, t7['p'], 'p')
add(7, 'transitions', 977, t7['n'], 'count')
add(7, 'polities', 100, t7['n_polities'], 'count')

extra = dict(
    claim2_sensitivity=sens,
    claim5_detail=a5, claim6_detail=a6, claim7_detail=t7,
    spec_choices=dict(
        duration='frame end_year - start_year, min 1 (code end_year tested as alternative)',
        agecat='0-based piece index capped at 3 (categories 0,1,2,3)',
        era_bins='pd.cut right-closed on piece midpoint; no bin lacked events so no merging',
        glm_se='statsmodels GLM cov_type=cluster (default small-sample correction), normal CI',
        cox='own Newton-Raphson Cox, robust SE = lifelines/R-style clustered dfbeta sandwich, no correction',
        logit='statsmodels Logit cov_type=cluster by NGA / PolityName',
    ))


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return o


with open(OUT, 'w') as fh:
    json.dump(clean(dict(claims=results, extra=extra)), fh, indent=2)

for r in results:
    print(r['claim'], r['item'], r['claimed'], r['yours'], r['verdict'], r['note'][:90])
