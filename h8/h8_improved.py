"""Study 1 analysis (exploratory under Deviations D1-D4 and D7-D12). Written in full before its first run on 17 Oct 2026.
Outputs: results.json and printed tables."""
import json, sys, itertools, warnings
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, '/root/analysis/study1'); sys.path.insert(0, '/root/analysis/cci')
import coxlib
from tradition_map import tradition
warnings.filterwarnings('ignore')
rng = np.random.default_rng(20261017)
OUT = {}
FAILED = []

# ---------- data ----------
pol = pd.read_csv('/root/analysis/frame/polities_frame.csv', index_col=0)
cov = pd.read_csv('/root/analysis/study1/covariates.csv', index_col=0)
fc = pd.read_csv('/root/analysis/frame/final_codes.csv').set_index('polity_id')
cci = pd.read_csv('/root/analysis/cci/cci_traditions.csv', index_col=0)
d = pol[pol.in_frame].join(cov, rsuffix='_c')
d = d.join(fc[['Q2', 'Q3', 'end_year']].rename(columns={'end_year': 'coder_end'}))
d.loc[d.censored_present, 'Q2'] = 'CENS'
d['dur'] = (d.end_year - d.start_year).astype(float)
d['dur_coder'] = (pd.to_numeric(d.coder_end, errors='coerce').fillna(d.end_year) - d.start_year).clip(lower=1).astype(float)
INTERNAL = {'T1a', 'T1b', 'T1c'}; CONQ = {'T2'}; OTHER = {'T3', 'T4', 'T5'}
def any_event(r):
    if r.Q2 in INTERNAL | CONQ | OTHER: return 1
    if r.Q2 == 'T9': return 1 if r.Q3 == 'Y' else (0 if r.Q3 == 'N' else np.nan)
    return 0
d['ev_any'] = d.apply(any_event, axis=1)
d['cause'] = d.Q2.map(lambda q: 1 if q in INTERNAL else (2 if q in CONQ else (3 if q in OTHER else (9 if q == 'T9' else 0))))
d['era'] = pd.cut(d.start_year, [-1e5, -500, 1500, 3000], labels=['pre500BCE', '500BCE_1500CE', 'post1500CE'])

def cci_for(s, col='CCI'):
    if not isinstance(s, str) or not s: return np.nan
    v = [cci.at[t, col] for t in s.split(';') if t in cci.index]
    return float(np.mean(v)) if v else np.nan
for lab, col in [('primary', 'trad_primary'), ('official', 'trad_official'), ('widespread', 'trad_widespread1')]:
    d[f'CCIraw_{lab}'] = d[col].map(cci_for)
    d[f'CCInetraw_{lab}'] = d[col].map(lambda s: cci_for(s, 'CCI_net'))
d['tradkey'] = d.trad_primary.fillna('')

CC9 = ['PolPop', 'PolTerr', 'CapPop', 'Hierarchy', 'Government', 'Infrastructure', 'Writing', 'Texts', 'Money']
CTRL = ['MilTech', 'iron', 'cavalry', 'PolPop', 'SC_PC1', 'abslat', 'script']

# ---------- multiple imputation (chained equations, Bayesian ridge, posterior draws) ----------
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
M = 20
def nelson_aalen(time, event):
    order = np.argsort(time); H = np.zeros(len(time)); cum = 0.0
    ts = np.unique(time)
    haz = {t: ((time == t) & (event == 1)).sum() / (time >= t).sum() for t in ts}
    cumh = np.cumsum([haz[t] for t in ts]); m = dict(zip(ts, cumh))
    return np.array([m[t] for t in time])
impcols = CC9 + ['MilTech', 'iron', 'cavalry', 'abslat', 'script', 'MSP', 'MER', 'ImpInst']
base = d[impcols].astype(float).copy()
ev0 = d.ev_any.fillna(0).values
aux = pd.DataFrame({'NA_hazard': nelson_aalen(d.dur.values, ev0), 'ev': ev0, 'start': d.start_year.values,
                    'int': (d.cause == 1).astype(float).values}, index=d.index)
macro = pd.get_dummies(d.macro_region.astype(int), prefix='mr', drop_first=True).astype(float)
Z = pd.concat([base, aux, macro], axis=1)
imps = []
for m in range(M):
    it = IterativeImputer(max_iter=15, sample_posterior=True, random_state=1000 + m, skip_complete=True)
    A = pd.DataFrame(it.fit_transform(Z.values), index=Z.index, columns=Z.columns)
    for c in ['iron', 'cavalry', 'script', 'MSP', 'MER', 'Writing', 'Texts', 'Government', 'Infrastructure', 'Money', 'ImpInst']:
        A[c] = A[c].clip(0, 1)
    S = (A[CC9] - A[CC9].mean()) / A[CC9].std()
    u, s, vt = np.linalg.svd(S.values, full_matrices=False)
    pc1 = S.values @ vt[0]
    if np.corrcoef(pc1, A['PolPop'])[0, 1] < 0: pc1 = -pc1
    A['SC_PC1'] = (pc1 - pc1.mean()) / pc1.std()
    A['pc1_var'] = s[0] ** 2 / (s ** 2).sum()
    imps.append(A)
OUT['pc1_variance_explained_mean'] = float(np.mean([A.pc1_var.iloc[0] for A in imps]))
complete = d[CTRL[:4] + ['abslat', 'script']].notna().all(axis=1) & d[CC9].notna().all(axis=1)

def rubin(betas, ses):
    betas, ses = np.array(betas), np.array(ses)
    qbar = betas.mean(0); W = (ses ** 2).mean(0); B = betas.var(0, ddof=1); Tv = W + (1 + 1 / len(betas)) * B
    r = (1 + 1 / len(betas)) * B / np.where(W > 0, W, np.nan)
    df = (len(betas) - 1) * (1 + 1 / np.where(r > 0, r, np.nan)) ** 2
    return qbar, np.sqrt(Tv), df

def design(sub, A, xvars, cci_col):
    X = pd.DataFrame(index=sub.index)
    X['CCI'] = sub[cci_col]
    for v in xvars:
        X[v] = A.loc[sub.index, v] if v in A.columns else sub[v]
    return X

def zscore_cci(sub, col):
    return (sub[col] - sub[col].mean()) / sub[col].std()

def run_model(sub, xvars, cci_col='CCI', time='dur', model='cox', cause=None, strata=None, imputed=True, cluster='tradkey', extra=None):
    """Returns pooled log HR, SE, df for CCI (and other terms) across imputations."""
    betas, ses = [], []
    Aset = imps if (imputed and xvars) else [None]
    for A in Aset:
        X = pd.DataFrame(index=sub.index); X['CCI'] = sub[cci_col]
        for v in xvars:
            X[v] = (A.loc[sub.index, v] if (A is not None and v in A.columns) else sub[v])
        if extra is not None:
            for k, f in extra.items(): X[k] = f(X)
        ok = X.notna().all(axis=1)
        s2 = sub[ok]; Xv = X[ok].values
        cl = s2[cluster].values
        st = None if strata is None else s2[strata].values
        if model == 'cox':
            ev = s2['ev_any'].values if cause is None else (s2['cause'] == cause).astype(int).values
            r = coxlib.fit(np.zeros(len(s2)), s2[time].values, ev, Xv, strata=st, cluster=cl)
        else:  # Fine-Gray for cause
            status = s2['cause'].replace({9: 0}).values if model == 'fg' else None
            s_, e_, dd, Xe, w, cle = coxlib.finegray_expand(s2[time].values, status, cause, Xv, cl)
            r = coxlib.fit(s_, e_, dd, Xe, w=w, cluster=cle)
        if np.isfinite(r['beta']).all():
            betas.append(r['beta']); ses.append(r['se'])
        else:
            FAILED.append(1)
    if not betas:
        nanp = np.full(Xv.shape[1], np.nan); return dict(names=list(X.columns), beta=nanp, se=nanp, df=nanp, n=int(ok.sum()), events=r['events'], clusters=r['clusters'], failed=len(Aset))
    q, se, df = rubin(betas, ses) if len(betas) > 1 else (betas[0], ses[0], np.full(len(betas[0]), np.inf))
    names = list(X.columns)
    return dict(names=names, beta=q, se=se, df=df, n=int(ok.sum()), events=r['events'], clusters=r['clusters'], failed=len(Aset) - len(betas))

def summarize(res, term='CCI', bounds=(np.log(0.90), np.log(1.11))):
    j = res['names'].index(term); b, se = res['beta'][j], res['se'][j]
    df = res['df'][j] if np.isfinite(res['df'][j]) else 1e6
    tq = stats.t.ppf(0.975, df); tq90 = stats.t.ppf(0.95, df)
    p = 2 * stats.t.sf(abs(b / se), df)
    lo90, hi90 = b - tq90 * se, b + tq90 * se
    equiv = (lo90 > bounds[0]) and (hi90 < bounds[1])
    return dict(term=term, HR=float(np.exp(b)), lo95=float(np.exp(b - tq * se)), hi95=float(np.exp(b + tq * se)),
                lo90=float(np.exp(lo90)), hi90=float(np.exp(hi90)), p=float(p), equivalent=bool(equiv),
                n=res['n'], events=float(res['events']), clusters=res['clusters'], failed_imputations=int(res.get('failed', 0)))

def permutation_p(sub, xvars, cci_col_raw='CCIraw_primary', nperm=2000, cause=None, model='cox', mimp=5):
    """Permute tradition-level CCI across traditions; statistic = mean log HR over the first mimp imputations."""
    trads = sorted(cci.index)
    def stat(cmap):
        s = sub.copy(); s['CCIp'] = s.trad_primary.map(lambda t: np.mean([cmap[x] for x in t.split(';')]))
        s['CCIp'] = zscore_cci(s, 'CCIp')
        global imps
        saved = imps; imps = saved[:mimp]
        try:
            r = run_model(s, xvars, 'CCIp', cause=cause, model=model)
        finally:
            imps = saved
        return r['beta'][0]
    obs = stat({t: cci.at[t, 'CCI'] for t in trads})
    vals = cci.loc[trads, 'CCI'].values; null = []
    for k in range(nperm):
        perm = rng.permutation(vals); null.append(stat(dict(zip(trads, perm))))
    null = np.array(null)
    return float(obs), float((np.sum(np.abs(null) >= abs(obs)) + 1) / (nperm + 1))


# ======== H8 improved (Addendum 14.4, fixed 22 Oct 2026) ========
import statsmodels.formula.api as smf
R = {}
h8 = d[d.MER.notna() & d.ev_any.notna()].copy()
h8['MERb'] = (h8.MER >= 0.5).astype(float)
h8['nga'] = pol.loc[h8.index, 'home_nga']
eras = pd.get_dummies(h8.era, drop_first=True).astype(float); h8 = h8.join(eras)
ERA = list(eras.columns)
def pooled(sub, xv, strata=None, cluster='region'):
    betas, ses = [], []
    for A in imps:
        X = pd.DataFrame({'MERb': sub.MERb}, index=sub.index)
        for v in xv: X[v] = A.loc[sub.index, v] if v in A.columns else sub[v]
        st = None if strata is None else sub[strata].values
        r = coxlib.fit(np.zeros(len(sub)), sub.dur.values, (sub.cause == 1).astype(int).values, X.values, strata=st, cluster=sub[cluster].astype(str).values)
        if np.isfinite(r['beta']).all(): betas.append(r['beta']); ses.append(r['se'])
    q, se, df = rubin(betas, ses)
    return summarize(dict(names=list(X.columns), beta=q, se=se, df=df, n=len(sub), events=float((sub.cause == 1).sum()), clusters=sub[cluster].nunique(), failed=len(imps) - len(betas)), 'MERb')
COV = ['SC_PC1', 'PolPop'] + ERA
g = h8[h8.nga.notna()]
R['H8-1_within_NGA'] = pooled(g, COV, strata='nga')
R['H8-1_within_NGA_unadjusted'] = pooled(g, [], strata='nga')
lit = h8[h8.script >= 0.5]
R['H8-2_literate_states'] = pooled(lit, COV)
lit2 = lit[lit.nga.notna()]
R['H8-2_literate_within_NGA'] = pooled(lit2, COV, strata='nga')
R['counts'] = dict(n_all=len(h8), n_nga=len(g), nga=int(g.nga.nunique()), internal_nga=int((g.cause == 1).sum()),
                   n_literate=len(lit), internal_literate=int((lit.cause == 1).sum()),
                   MER_absent_nga=int((g.MERb == 0).sum()), MER_absent_literate=int((lit.MERb == 0).sum()),
                   MER_by_era=h8.groupby('era').MERb.mean().round(3).to_dict())
# H8-3: all CrisisDB crises
db = json.load(open('/root/analysis/seshat/seshat_current_2026-10-17.json'))
cc = pd.DataFrame(db['crisisdb/crisis-consequences']['rows'], columns=db['crisisdb/crisis-consequences']['cols'])
P = lambda s: s.map({'P': 1, 'IP': 1, 'A': 0, 'IA': 0})
for c in ['civil_war', 'extermination', 'collapse', 'depose', 'assassination']: cc[c] = P(cc[c])
cc['severity'] = cc[['civil_war', 'extermination', 'collapse']].sum(axis=1, min_count=2)
cc['removed'] = cc[['depose', 'assassination']].max(axis=1)
cc['MER'] = cc.polity.map(cov.MER); cc['MERb'] = (cc.MER >= 0.5).astype(float).where(cc.MER.notna())
cc['PolPop'] = cc.polity.map(imps[0].PolPop) if False else cc.polity.map(cov.PolPop)
cc['year'] = pd.to_numeric(cc.year_from, errors='coerce').fillna(cc.polity.map(pol.start_year))
cc['era'] = pd.cut(cc.year, [-1e5, -500, 1500, 3000], labels=['pre500BCE', '500BCE_1500CE', 'post1500CE'])
for y in ['severity', 'removed']:
    dd = cc.dropna(subset=[y, 'MERb', 'era']).copy(); dd['era'] = dd.era.astype(str)
    fam = 'ols' if y == 'severity' else 'logit'
    f = f'{y} ~ MERb + C(era)'
    m = (smf.ols(f, dd) if fam == 'ols' else smf.logit(f, dd)).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.polity)[0]}, disp=0) if fam == 'logit' else smf.ols(f, dd).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.polity)[0]})
    lo, hi = m.conf_int().loc['MERb']
    R[f'H8-3_{y}'] = dict(coef=float(m.params['MERb']), lo95=float(lo), hi95=float(hi), p=float(m.pvalues['MERb']), n=int(m.nobs),
                          polities=int(dd.polity.nunique()), mean_MER1=float(dd[dd.MERb == 1][y].mean()), mean_MER0=float(dd[dd.MERb == 0][y].mean()),
                          n_MER0=int((dd.MERb == 0).sum()), model=fam)
json.dump(R, open('/root/analysis/h8/h8_improved_results.json', 'w'), indent=1, default=str)
for k, v in R.items(): print(k, json.dumps(v, default=str)[:400])
