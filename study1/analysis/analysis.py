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
M = 50
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

# ---------- H1 / H2 sample ----------
h = d[d.CCIraw_primary.notna() & d.ev_any.notna()].copy()
h['CCI'] = zscore_cci(h, 'CCIraw_primary')
OUT['sample'] = dict(n=len(h), events_any=int(h.ev_any.sum()), internal=int((h.cause == 1).sum()), conquest=int((h.cause == 2).sum()),
                     other=int((h.cause == 3).sum()), T9=int((h.cause == 9).sum()), traditions=int(h.tradkey.nunique()),
                     cci_sd_raw=float(h.CCIraw_primary.std()), median_duration=float(h.dur.median()))
print('SAMPLE', OUT['sample'])

res = {}
res['H1'] = summarize(run_model(h, []))
res['H1']['perm_logHR'], res['H1']['perm_p'] = permutation_p(h, [], nperm=5000)
res['H2'] = summarize(run_model(h, CTRL))
res['H2']['perm_logHR'], res['H2']['perm_p'] = permutation_p(h, CTRL, nperm=1000)
# H2 other covariate terms
r2 = run_model(h, CTRL); res['H2_terms'] = [summarize(r2, t) for t in r2['names']]
# H4a: cause-specific and Fine-Gray, internal (1) and conquest (2), adjusted as H2
for cz, lab in [(1, 'internal'), (2, 'conquest')]:
    res[f'H4a_cs_{lab}'] = summarize(run_model(h, CTRL, cause=cz))
    res[f'H4a_fg_{lab}'] = summarize(run_model(h, CTRL, model='fg', cause=cz))
res['H4a_fg_internal']['perm_logHR'], res['H4a_fg_internal']['perm_p'] = permutation_p(h, CTRL, nperm=500, cause=1, model='fg', mimp=2)
# H5: add moralizing supernatural punishment
res['H5'] = summarize(run_model(h, CTRL + ['MSP']))
r5 = run_model(h, CTRL + ['MSP']); res['H5_MSP'] = summarize(r5, 'MSP')
res['H5_med_ImpInst'] = summarize(run_model(h, CTRL + ['MSP', 'ImpInst']))
# H7: era interaction (unadjusted and adjusted)
for lab, xv in [('unadj', []), ('adj', CTRL)]:
    era_d = pd.get_dummies(h.era, drop_first=True).astype(float)
    hh = h.join(era_d)
    extra = {f'CCIx{c}': (lambda X, c=c: X['CCI'] * hh.loc[X.index, c]) for c in era_d.columns}
    xv2 = xv + list(era_d.columns)
    r7 = run_model(hh, xv2, extra=extra)
    ks = [r7['names'].index(k) for k in extra]
    # Wald test of the interaction terms using pooled variances (diagonal approximation)
    W = sum((r7['beta'][k] / r7['se'][k]) ** 2 for k in ks)
    res[f'H7_{lab}'] = dict(wald_chi2=float(W), df=len(ks), p=float(stats.chi2.sf(W, len(ks))),
                            era_HR={'pre500BCE': float(np.exp(r7['beta'][0]))} |
                                   {c: float(np.exp(r7['beta'][0] + r7['beta'][r7['names'].index(f'CCIx{c}')])) for c in era_d.columns},
                            n_by_era=h.era.value_counts().to_dict(), events_by_era=h.groupby('era').ev_any.sum().to_dict())
# Proportional hazards check (H1)
r = coxlib.fit(np.zeros(len(h)), h.dur.values, h.ev_any.values, h[['CCI']].values)
sc = coxlib.schoenfeld_test(np.zeros(len(h)), h.dur.values, h.ev_any.values, h[['CCI']].values, r['beta'])
res['PH_test_H1'] = dict(rho=float(sc[0].correlation), p=float(sc[0].pvalue))

# Holm-Bonferroni across the confirmatory tests that could be run (H1, H2, H4a, H5, H7)
fam = {'H1': res['H1']['perm_p'], 'H2': res['H2']['perm_p'], 'H4a': res['H4a_fg_internal']['perm_p'], 'H5': res['H5']['p'], 'H7': res['H7_adj']['p']}
order = sorted(fam, key=fam.get); m = len(fam); holm = {}; running = 0
for i, k in enumerate(order):
    running = max(running, min(1, (m - i) * fam[k])); holm[k] = running
res['holm'] = holm

# ---------- sensitivity analyses for H1/H2 ----------
sens = {}
sens['H2_complete_case'] = summarize(run_model(h[complete.loc[h.index]], CTRL, imputed=True))  # rows with complete covariates
for lab in ['official', 'widespread']:
    hs = d[d[f'CCIraw_{lab}'].notna() & d.ev_any.notna()].copy(); hs['CCI'] = zscore_cci(hs, f'CCIraw_{lab}')
    hs['tradkey'] = hs[{'official': 'trad_official', 'widespread': 'trad_widespread1'}[lab]].fillna('')
    sens[f'H1_assign_{lab}'] = summarize(run_model(hs, []))
    sens[f'H2_assign_{lab}'] = summarize(run_model(hs, CTRL))
hn = h.copy(); hn['CCI'] = zscore_cci(hn, 'CCInetraw_primary')
sens['H1_CCI_net'] = summarize(run_model(hn, [])); sens['H2_CCI_net'] = summarize(run_model(hn, CTRL))
sens['H1_coder_dates'] = summarize(run_model(h, [], time='dur_coder')); sens['H2_coder_dates'] = summarize(run_model(h, CTRL, time='dur_coder'))
sens['H2_macro_strata'] = summarize(run_model(h, CTRL, strata='macro_region'))
hx = h[h.cause != 9]; sens['H2_excl_T9'] = summarize(run_model(hx, CTRL))
hr_ = h.copy(); sens['H2_cluster_region'] = summarize(run_model(hr_, CTRL, cluster='region'))
pilot = set(l.split('|')[5] for l in open('/root/analysis/out/pilot_sample_raw.txt') if l.strip())
hp = h[~h['name'].isin(pilot)]; sens['H2_excl_pilot_polities'] = summarize(run_model(hp, CTRL))
jk = {}
for t in sorted(cci.index):
    hj = h[~h.trad_primary.fillna('').str.split(';').map(lambda L: t in L)]
    if len(hj) < len(h):
        hj = hj.copy(); hj['CCI'] = zscore_cci(hj, 'CCIraw_primary'); jk[t] = summarize(run_model(hj, CTRL))['HR']
sens['H2_leave_one_tradition_out_HR'] = jk
res['sensitivity'] = sens

# ---------- specification curve (Section 6.11) ----------
spec = []
for ctrl_lab, xv in [('none', []), ('H2', CTRL), ('H2+MSP', CTRL + ['MSP'])]:
    for assign in ['primary', 'official', 'widespread']:
        for idx in ['CCI', 'CCI_net']:
            for strata in [None, 'macro_region']:
                for tvar in ['dur', 'dur_coder']:
                    rawc = f"{'CCIraw' if idx == 'CCI' else 'CCInetraw'}_{assign}"
                    hs = d[d[rawc].notna() & d.ev_any.notna()].copy(); hs['CCI'] = zscore_cci(hs, rawc)
                    hs['tradkey'] = hs[{'primary': 'trad_primary', 'official': 'trad_official', 'widespread': 'trad_widespread1'}[assign]].fillna('')
                    saved = imps
                    imps_local = saved[:10]
                    globals()['imps'] = imps_local
                    try:
                        s_ = summarize(run_model(hs, xv, strata=strata, time=tvar))
                    finally:
                        globals()['imps'] = saved
                    spec.append(dict(controls=ctrl_lab, assign=assign, index=idx, strata=str(strata), time=tvar, HR=s_['HR'], p=s_['p'], n=s_['n']))
spec = pd.DataFrame(spec); spec.to_csv('/root/analysis/study1/spec_curve.csv', index=False)
res['spec_curve'] = dict(n_specs=len(spec), share_HR_below_1=float((spec.HR < 1).mean()), share_p_below_05_and_HR_below_1=float(((spec.HR < 1) & (spec.p < .05)).mean()),
                         share_p_below_05_and_HR_above_1=float(((spec.HR > 1) & (spec.p < .05)).mean()), median_HR=float(spec.HR.median()))

# ---------- H8: moralizing enforcement of rulers (exploratory) ----------
h8 = d[d.MER.notna() & d.ev_any.notna()].copy()
h8['MERb'] = (h8.MER >= 0.5).astype(float)
h8['tradkey'] = h8.region.astype(str)  # cluster on Seshat region
def run8(xv, cause, model):
    out = []
    for A in imps[:20]:
        X = pd.DataFrame({'MERb': h8.MERb}, index=h8.index)
        for v in xv: X[v] = A.loc[h8.index, v]
        if model == 'fg':
            s_, e_, dd, Xe, w, cle = coxlib.finegray_expand(h8.dur.values, h8.cause.replace({9: 0}).values, cause, X.values, h8.tradkey.values)
            r = coxlib.fit(s_, e_, dd, Xe, w=w, cluster=cle)
        else:
            r = coxlib.fit(np.zeros(len(h8)), h8.dur.values, (h8.cause == cause).astype(int).values, X.values, cluster=h8.tradkey.values)
        out.append((r['beta'], r['se']))
        if not xv: break
    q, se, df = rubin([o[0] for o in out], [o[1] for o in out]) if len(out) > 1 else (out[0][0], out[0][1], np.full(len(out[0][0]), np.inf))
    return summarize(dict(names=['MERb'] + xv, beta=q, se=se, df=df, n=len(h8), events=float((h8.cause == cause).sum()), clusters=h8.tradkey.nunique()), 'MERb')
res['H8'] = dict(n=len(h8), MER_present=int(h8.MERb.sum()), MER_absent=int((1 - h8.MERb).sum()),
                 internal_events=int((h8.cause == 1).sum()), conquest_events=int((h8.cause == 2).sum()),
                 fg_internal_unadj=run8([], 1, 'fg'), fg_internal_adj=run8(CTRL, 1, 'fg'),
                 fg_conquest_unadj=run8([], 2, 'fg'), cs_internal_unadj=run8([], 1, 'cs'))
sev = d[d.crisis_end_severity.notna() & d.MER.notna()]
a_, b_ = sev[sev.MER >= .5].crisis_end_severity, sev[sev.MER < .5].crisis_end_severity
res['H8b'] = dict(n_present=len(a_), n_absent=len(b_), mean_present=float(a_.mean()) if len(a_) else None, mean_absent=float(b_.mean()) if len(b_) else None,
                  mannwhitney_p=float(stats.mannwhitneyu(a_, b_).pvalue) if len(a_) and len(b_) else None)
OUT['results'] = res
OUT['failed_fits_total'] = len(FAILED)
json.dump(OUT, open('/root/analysis/study1/results.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
for k, v in res.items():
    print(k, json.dumps(v, default=str)[:600])
