"""H4b analysis (Addendum 14.2, plan fixed 22 Oct 2026). Written before the adjudicated adoption codes were read.
Input: /root/analysis/h4b/codes/final_codes.csv (one row per item after adjudication).
Rules fixed here, before the codes were read:
- conquered tradition = the coder's (adjudicated) conquered_tradition if it is one of the 15 scored traditions; episodes whose
  corrected tradition is unscored or U are dropped. Sensitivity: the database tradition (trad_primary).
- episodes with same_tradition Y or U are excluded; adopted U is excluded; P excluded (primary) or counted as 1 (sensitivity).
- conqueror_writing U is dropped in the primary model; sensitivity omits that covariate.
- inference: tradition-level permutation (CCI values shuffled across the 15 traditions, 2000 draws) is primary;
  cluster-robust logit (clusters = conquered tradition) is secondary. With fewer than 10 events or non-events the model is
  not fitted and only counts and the exact permutation test of the tradition-level association are reported.
"""
import json, sys, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
warnings.filterwarnings('ignore')
src = open('/root/analysis/h8/h8_improved.py').read().split('# ======== H8 improved')[0]
exec(src)  # builds d (Study 1 frame), imps (20 imputations), cci, rubin()
rng = np.random.default_rng(20261022)
TR = list(cci.index)
items = pd.read_csv('/root/analysis/h4b/items.csv')
codes = pd.read_csv('/root/analysis/h4b/codes/final_codes.csv', dtype=str).fillna('')
x = items.merge(codes, left_on='hitem', right_on='item', how='left')
def norm_trad(s):
    s = (s or '').strip()
    for t in TR:
        if s.lower() == t.lower(): return t
    return None
x['trad_c'] = x.conquered_tradition.map(norm_trad)
x['trad_q'] = x.conqueror_tradition.map(norm_trad)
R = dict(n_items=len(x), coded=int((x.adopted != '').sum()))
R['same_tradition'] = x.same_tradition.value_counts().to_dict()
R['adopted_all'] = x.adopted.value_counts().to_dict()
R['tradition_corrected'] = int((x.trad_c.notna() & (x.trad_c != x.trad_primary)).sum())

def build(df, tradcol, partial_as_yes=False):
    s = df[(df.same_tradition == 'N') & df.adopted.isin(['Y', 'N'] + (['P'] if partial_as_yes else []))].copy()
    s = s[s[tradcol].isin(TR)]
    s['y'] = s.adopted.map({'Y': 1, 'P': 1, 'N': 0}).astype(float)
    s['cci_raw'] = s[tradcol].map(cci.CCI)
    s['qwrite'] = s.conqueror_writing.map({'Y': 1.0, 'N': 0.0})
    s['tradk'] = s[tradcol]
    return s

def fit(s, use_qwrite=True, cci_map=None, imps_use=None):
    s = s.copy()
    if cci_map is not None: s['cci_raw'] = s.tradk.map(cci_map)
    s['CCIz'] = (s.cci_raw - s.cci_raw.mean()) / s.cci_raw.std()
    cols = ['CCIz', 'SC_PC1', 'script'] + (['qwrite'] if use_qwrite else [])
    if use_qwrite: s = s[s.qwrite.notna()]
    betas, ses = [], []
    for A in (imps_use or imps):
        X = pd.DataFrame({'CCIz': s.CCIz, 'SC_PC1': A.loc[s.id, 'SC_PC1'].values, 'script': A.loc[s.id, 'script'].values}, index=s.index)
        if use_qwrite: X['qwrite'] = s.qwrite
        X = sm.add_constant(X[cols])
        try:
            m = sm.Logit(s.y, X).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(s.tradk)[0]}, maxiter=200)
            if np.isfinite(m.params).all() and np.isfinite(m.bse).all() and abs(m.params['CCIz']) < 15:
                betas.append(m.params.values); ses.append(m.bse.values)
        except Exception:
            pass
    if len(betas) < 2: return None, s
    q, se, df_ = rubin(betas, ses)
    j = list(X.columns).index('CCIz'); dfj = df_[j] if np.isfinite(df_[j]) else 1e6
    tq = stats.t.ppf(0.975, dfj); tq90 = stats.t.ppf(0.95, dfj)
    return dict(OR=float(np.exp(q[j])), lo95=float(np.exp(q[j] - tq * se[j])), hi95=float(np.exp(q[j] + tq * se[j])),
                lo90=float(np.exp(q[j] - tq90 * se[j])), hi90=float(np.exp(q[j] + tq90 * se[j])),
                p_cluster=float(2 * stats.t.sf(abs(q[j] / se[j]), dfj)), beta=float(q[j]), n=int(len(s)), events=int(s.y.sum()),
                traditions=int(s.tradk.nunique()), imputations_ok=len(betas),
                equivalent_null=bool(np.exp(q[j] - tq90 * se[j]) > 0.80 and np.exp(q[j] + tq90 * se[j]) < 1.25)), s

def perm(s, use_qwrite=True, nperm=2000):
    obs, _ = fit(s, use_qwrite, imps_use=imps[:5])
    if obs is None: return None
    vals = cci.loc[TR, 'CCI'].values; null = []
    for k in range(nperm):
        r, _ = fit(s, use_qwrite, cci_map=dict(zip(TR, rng.permutation(vals))), imps_use=imps[:5])
        if r is not None: null.append(r['beta'])
    null = np.array(null)
    return dict(beta_obs=obs['beta'], p_perm=float((np.sum(np.abs(null) >= abs(obs['beta'])) + 1) / (len(null) + 1)), draws=len(null))

def describe(s, nperm=2000):
    t = s.groupby('tradk').agg(n=('y', 'size'), adopted=('y', 'sum'), cci=('cci_raw', 'first')).sort_values('cci')
    rho, p = stats.spearmanr(t.cci, t.adopted / t.n) if len(t) > 2 else (np.nan, np.nan)
    # tradition-level permutation test (the header's 'exact permutation test'): statistic = correlation between each
    # episode's adoption (0/1) and its tradition's CCI; CCI values shuffled across the 15 traditions
    vals = cci.loc[TR, 'CCI'].values
    obs = np.corrcoef(s.y, s.tradk.map(cci.CCI))[0, 1] if s.y.nunique() > 1 else np.nan
    null = []
    for k in range(nperm):
        m = dict(zip(TR, rng.permutation(vals))); x = s.tradk.map(m)
        if x.nunique() > 1: null.append(np.corrcoef(s.y, x)[0, 1])
    null = np.array(null)
    pp = float((np.sum(np.abs(null) >= abs(obs)) + 1) / (len(null) + 1)) if np.isfinite(obs) else np.nan
    return dict(by_tradition=t.reset_index().to_dict('records'), spearman_rho_trad=float(rho), spearman_p_trad=float(p),
                r_episode=float(obs), p_perm_trad=pp, n=int(len(s)), events=int(s.y.sum()))

for lab, tc, pay, uq in [('primary', 'trad_c', False, True), ('partial_as_yes', 'trad_c', True, True),
                         ('database_tradition', 'trad_primary', False, True), ('no_conqueror_writing', 'trad_c', False, False)]:
    s = build(x, tc, pay)
    R[lab] = dict(describe=describe(s))
    ok = s.y.sum() >= 10 and (len(s) - s.y.sum()) >= 10
    if ok:
        r, _ = fit(s, uq); R[lab]['model'] = r
        if lab in ('primary', 'partial_as_yes'): R[lab]['permutation'] = perm(s, uq)
    else:
        R[lab]['model'] = 'not fitted: fewer than 10 events or non-events'
# Secondary: CCI difference where both traditions are scored
s = build(x, 'trad_c'); s = s[s.trad_q.isin(TR)].copy()
s['diff'] = s.cci_raw - s.trad_q.map(cci.CCI)
R['secondary_difference'] = dict(n=int(len(s)), events=int(s.y.sum()))
if len(s) >= 15 and s.y.sum() >= 5 and (len(s) - s.y.sum()) >= 5:
    s['dz'] = (s['diff'] - s['diff'].mean()) / s['diff'].std()
    m = sm.Logit(s.y, sm.add_constant(s[['dz']])).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(s.tradk)[0]})
    R['secondary_difference'].update(OR=float(np.exp(m.params['dz'])), lo95=float(np.exp(m.conf_int().loc['dz', 0])),
                                     hi95=float(np.exp(m.conf_int().loc['dz', 1])), p=float(m.pvalues['dz']))
    R['secondary_difference']['pairs'] = s.groupby(['tradk', 'trad_q']).y.agg(['size', 'sum']).reset_index().to_dict('records')
json.dump(R, open('/root/analysis/h4b/h4b_results.json', 'w'), indent=1, default=str)
print(json.dumps(R, indent=1, default=str)[:6000])
