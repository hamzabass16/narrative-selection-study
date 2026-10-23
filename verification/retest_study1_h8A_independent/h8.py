"""Step 3: H8 Part A (premodern constraint) re-derivation.

Usage: python -I h8.py
"""
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, '/root/analysis/verify5')
from build import load_polities  # noqa: E402
from mycox import cox_fit  # noqa: E402

PT = '/root/data/seshat_polaris/SeshatDatasetAnalysis/test_scripts/power_transitions.xlsx'
IND = ['overturn', 'predecessor_assassination', 'military_revolt', 'popular_uprising']
Z = 1.959964


def era_of(year):
    year = np.asarray(year, float)
    return np.where(year < -500, 0, np.where(year < 1500, 1, 2))


def exposure_sample(xcol):
    d = load_polities()
    s = d[d[xcol].notna() & d.event.notna()].copy()
    s['Xz'] = (s[xcol] - s[xcol].mean()) / s[xcol].std(ddof=1)
    s['dur'] = np.maximum(s.end_year - s.start_year, 1)
    s['era'] = era_of(s.start_year)
    return s


def cox_summary(s, event_col, ties='breslow'):
    r = cox_fit(s.dur.values, s[event_col].values.astype(int), s[['Xz']].values,
                strata=s.era.values, cluster=s.nga_name.values, ties=ties)
    b, se = r['beta'][0], r['se_robust'][0]
    return dict(HR=float(np.exp(b)), lo=float(np.exp(b - Z * se)),
                hi=float(np.exp(b + Z * se)), p=float(r['p_robust'][0]),
                events=r['events'], n=r['n'])


def cox_statsmodels(s, event_col, ties='breslow'):
    """Cross-check with statsmodels PHReg (robust covariance by groups)."""
    from statsmodels.duration.hazard_regression import PHReg
    m = PHReg(s.dur.values, s[['Xz']].values, status=s[event_col].values.astype(int),
              strata=s.era.values, ties=ties)
    r = m.fit(groups=s.nga_name.values)
    b, se = r.params[0], r.bse[0]
    return dict(HR=float(np.exp(b)), p=float(r.pvalues[0]), se=float(se))


def logit_cluster(y, X, groups):
    X = sm.add_constant(X)
    m = sm.Logit(y, X)
    r = m.fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(groups)[0]})
    b, se = r.params['Xz'], r.bse['Xz']
    return dict(OR=float(np.exp(b)), lo=float(np.exp(b - Z * se)),
                hi=float(np.exp(b + Z * se)), p=float(r.pvalues['Xz']), n=int(r.nobs))


def part_a(xcol):
    s = exposure_sample(xcol)
    out = dict(exposure=xcol, n=len(s), events=int(s.event.sum()),
               internal=int(s.internal.sum()), conquest=int(s.conquest.sum()),
               ngas=int(s.nga_name.nunique()))
    out['cox_all'] = cox_summary(s, 'event')
    out['cox_internal'] = cox_summary(s, 'internal')
    out['cox_all_efron'] = cox_summary(s, 'event', 'efron')
    out['cox_internal_efron'] = cox_summary(s, 'internal', 'efron')
    out['sm_cox_all'] = cox_statsmodels(s, 'event')
    out['sm_cox_internal'] = cox_statsmodels(s, 'internal')
    # logit internal collapse vs continuity
    lg = s[s.q2clean.isin(['T1a', 'T1b', 'T1c', 'T0'])].copy()
    lg['y'] = lg.q2clean.isin(['T1a', 'T1b', 'T1c']).astype(int)
    X = pd.DataFrame({'Xz': lg.Xz})
    X = X.join(pd.get_dummies(lg.era, prefix='era', drop_first=True, dtype=float))
    out['logit_internal_vs_T0'] = logit_cluster(lg.y, X, lg.nga_name.values)
    return out, s


def transitions(xcol, s):
    pt = pd.read_excel(PT, sheet_name='Raw')
    pt = pt[pt.PolityName.isin(s.name)].copy()
    vals = pt[IND].astype(float)
    tol = 1e-9
    any_hi = (vals >= 0.9 - tol).any(axis=1)
    all_lo = (vals <= 0.1 + tol).all(axis=1) & vals.notna().all(axis=1)
    pt['irregular'] = np.where(any_hi, 1.0, np.where(all_lo, 0.0, np.nan))
    pt = pt[pt.irregular.notna()].copy()
    pt = pt.merge(s[['name', 'Xz']], left_on='PolityName', right_on='name', how='left')
    pt['era'] = era_of(pt.Year)
    X = pd.DataFrame({'Xz': pt.Xz.values})
    X = X.join(pd.get_dummies(pd.Series(pt.era.values), prefix='era', drop_first=True, dtype=float))
    res = logit_cluster(pt.irregular.values, X, pt.PolityName.values)
    res['n_polities'] = int(pt.PolityName.nunique())
    res['n_irregular'] = int(pt.irregular.sum())
    res['era_counts'] = pt.era.value_counts().sort_index().to_dict()
    return res


if __name__ == '__main__':
    for xcol in ['CONSTR', 'rulers_eq_commoners']:
        out, s = part_a(xcol)
        print(out)
        if xcol == 'rulers_eq_commoners':
            print('transitions', transitions(xcol, s))
