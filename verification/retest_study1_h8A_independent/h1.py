"""Step 2: Study 1 H1 discrete-time hazard (cloglog GLM) and NGA-stratified Cox.

Usage: python -I h1.py
Prints results for each variant of the ambiguous choices (end_year source,
agecat indexing, era-bin closure) so the closest match can be identified.
"""
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, '/root/analysis/verify5')
from build import load_polities  # noqa: E402
from mycox import cox_fit  # noqa: E402

EDGES = [-100000, -1000, 0, 1000, 1500, 3000]


def h1_sample(endcol):
    d = load_polities()
    s = d[d.EPI.notna() & d.event.notna()].copy()
    s['EPIz'] = (s.EPI - s.EPI.mean()) / s.EPI.std(ddof=1)
    s['end_use'] = s[endcol]
    s['dur'] = np.maximum(s.end_use - s.start_year, 1)
    return s


def split_centuries(s, agecat_base):
    rows = []
    for _, r in s.iterrows():
        length = r.dur
        npieces = int(np.ceil(length / 100.0))
        for i in range(npieces):
            p_start = r.start_year + 100 * i
            p_len = min(100, length - 100 * i)
            last = (i == npieces - 1)
            rows.append({
                'id': r.id, 'nga': r.nga_name, 'EPIz': r.EPIz,
                'L': p_len / 100.0,
                'mid': p_start + p_len / 2.0,
                'agecat': min(i + agecat_base, 3),
                'y': int(r.event == 1 and last),
            })
    return pd.DataFrame(rows)


def era_bins(pp, right):
    b = pd.cut(pp.mid, EDGES, right=right, labels=False)
    b = b.astype(int)
    nb = len(EDGES) - 1
    # merge bins with no events into the next bin (or previous at the end)
    labels = list(range(nb))
    mapping = {k: k for k in labels}
    changed = True
    while changed:
        changed = False
        cur = b.map(mapping)
        present = sorted(cur.unique())
        ev = pp.y.groupby(cur).sum()
        for k in present:
            if ev.get(k, 0) == 0:
                later = [j for j in present if j > k]
                earlier = [j for j in present if j < k]
                target = later[0] if later else (earlier[-1] if earlier else k)
                if target != k:
                    for kk, vv in mapping.items():
                        if vv == k:
                            mapping[kk] = target
                    changed = True
                    break
    return b.map(mapping)


def fit_glm(pp, with_nga=True):
    X = pd.DataFrame({'EPIz': pp.EPIz})
    X = X.join(pd.get_dummies(pp.agecat, prefix='age', drop_first=True, dtype=float))
    X = X.join(pd.get_dummies(pp.era, prefix='era', drop_first=True, dtype=float))
    if with_nga:
        X = X.join(pd.get_dummies(pp.nga, prefix='nga', drop_first=True, dtype=float))
    X = sm.add_constant(X)
    groups = pd.factorize(pp.nga)[0]
    fam = sm.families.Binomial(link=sm.families.links.CLogLog())
    mod = sm.GLM(pp.y, X, family=fam, offset=np.log(pp.L))
    ck = {'groups': groups}
    # 1) default IRLS (may diverge / stop at a false optimum)
    r_irls = mod.fit(cov_type='cluster', cov_kwds=ck)
    # 2) IRLS started from zeros
    zero = np.zeros(X.shape[1])
    r_zero = mod.fit(start_params=zero, tol=1e-12, maxiter=1000,
                     cov_type='cluster', cov_kwds=ck)
    # 3) Newton from the zero-start IRLS solution (second optimizer)
    r_newton = mod.fit(method='newton', start_params=r_zero.params.values,
                       maxiter=500, cov_type='cluster', cov_kwds=ck)
    # 4) BFGS from zeros (independent optimizer)
    r_bfgs = mod.fit(method='bfgs', start_params=zero, maxiter=20000,
                     cov_type='cluster', cov_kwds=ck)
    fits = [r_irls, r_zero, r_newton, r_bfgs]
    best = max(fits, key=lambda r: r.llf)
    return r_irls, r_newton, r_bfgs, best


def summarize(r, name='EPIz'):
    b = r.params[name]
    se = r.bse[name]
    return dict(HR=float(np.exp(b)), lo=float(np.exp(b - 1.959964 * se)),
                hi=float(np.exp(b + 1.959964 * se)), p=float(r.pvalues[name]),
                llf=float(r.llf))


def run_variant(endcol, agecat_base, right, verbose=True):
    s = h1_sample(endcol)
    pp = split_centuries(s, agecat_base)
    ev_by_nga = pp.groupby('nga').y.sum()
    keep = ev_by_nga[ev_by_nga > 0].index
    pp = pp[pp.nga.isin(keep)].reset_index(drop=True)
    pp['era'] = era_bins(pp, right)
    r_irls, r_newton, r_tight, best = fit_glm(pp, with_nga=True)
    _, _, _, best_nonga = fit_glm(pp, with_nga=False)
    out = dict(endcol=endcol, agecat_base=agecat_base, right=right,
               n_rows=len(pp), n_nga=pp.nga.nunique(), n_pol=pp.id.nunique(),
               events=int(pp.y.sum()),
               era_bins=sorted(pp.era.unique().tolist()),
               irls=summarize(r_irls), newton=summarize(r_newton),
               bfgs=summarize(r_tight), best=summarize(best),
               nonga=summarize(best_nonga))
    if verbose:
        print(out)
    return out, pp


def cox_nga(endcol, ties):
    s = h1_sample(endcol)
    res = cox_fit(s.dur.values, s.event.values.astype(int), s[['EPIz']].values,
                  strata=s.nga_name.values, cluster=s.nga_name.values, ties=ties)
    b, se = res['beta'][0], res['se_robust'][0]
    return dict(endcol=endcol, ties=ties, HR=float(np.exp(b)),
                lo=float(np.exp(b - 1.959964 * se)), hi=float(np.exp(b + 1.959964 * se)),
                p=float(res['p_robust'][0]), n=len(s), events=int(s.event.sum()))


if __name__ == '__main__':
    for endcol in ['end_year', 'code_end_year']:
        for base in [0, 1]:
            for right in [False, True]:
                run_variant(endcol, base, right)
    for endcol in ['end_year', 'code_end_year']:
        for ties in ['breslow', 'efron']:
            print(cox_nga(endcol, ties))
