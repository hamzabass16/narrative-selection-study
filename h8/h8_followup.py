"""H8 follow-up (plan: h8_followup_plan.md, fixed 23 Oct 2026). Is ruler removal / internal collapse costly to the society?"""
import json, sys, warnings
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
sys.path.insert(0, '/root/analysis/study1'); import coxlib
warnings.filterwarnings('ignore')
A = '/root/analysis/'
pol = pd.read_csv(A + 'frame/polities_frame.csv', index_col=0)
cov = pd.read_csv(A + 'study1/covariates.csv', index_col=0)
fc = pd.read_csv(A + 'frame/final_codes.csv').set_index('polity_id')
db = json.load(open(A + 'seshat/seshat_current_2026-10-17.json'))
R = {}

# ---------- polity-level measures ----------
CC9 = ['PolPop', 'PolTerr', 'CapPop', 'Hierarchy', 'Government', 'Infrastructure', 'Writing', 'Texts', 'Money']
Z = (cov[CC9] - cov[CC9].mean()) / cov[CC9].std()
pol['SC_mean'] = Z.mean(axis=1).where(cov[CC9].notna().sum(axis=1) >= 5)
pol['PolPop'] = cov.PolPop; pol['PolTerr'] = cov.PolTerr; pol['MER'] = cov.MER
pol['MERb'] = (pol.MER >= 0.5).astype(float).where(pol.MER.notna())
pol['Q2'] = fc.Q2
def etype(q):
    if q in ('T1a', 'T1b', 'T1c'): return 'internal'
    if q == 'T2': return 'conquest'
    if q == 'T0': return 'continuity'
    if q in ('T3', 'T4', 'T5', 'T6'): return 'other'
    return None
pol['etype'] = pol.Q2.map(etype)
pol.loc[pol.censored_present == True, 'etype'] = None
era = lambda y: 'pre500BCE' if y < -500 else ('500BCE_1500CE' if y <= 1500 else 'post1500CE')

# ---------- crises ----------
cc = pd.DataFrame(db['crisisdb/crisis-consequences']['rows'], columns=db['crisisdb/crisis-consequences']['cols'])
CONS = ['decline', 'collapse', 'extermination', 'civil_war', 'fragmentation', 'conquest', 'epidemic', 'downward_mobility',
        'century_plus', 'capital', 'constitution', 'public_goods']
B01 = lambda s: s.map({'P': 1.0, 'IP': 1.0, 'A': 0.0, 'IA': 0.0})
for c in CONS + ['depose', 'assassination']: cc[c] = B01(cc[c])
cc['removed'] = cc[['depose', 'assassination']].max(axis=1)
cc.loc[cc[['depose', 'assassination']].isna().all(axis=1), 'removed'] = np.nan
cc['y0'] = pd.to_numeric(cc.year_from, errors='coerce'); cc['y1'] = pd.to_numeric(cc.year_to, errors='coerce').fillna(cc.y0)
cc = cc[cc.y0.notna()].copy()
cc['era'] = cc.y0.map(era)
cc['nga'] = cc.polity.map(pol.home_nga)
for c in ['PolPop', 'MERb', 'end_year', 'etype', 'censored_present', 'start_year']: cc[c] = cc.polity.map(pol[c])
R['n_crises'] = int(len(cc)); R['n_crisis_polities'] = int(cc.polity.nunique())
R['removed_counts'] = cc.removed.value_counts(dropna=False).to_dict()

def logit(df, y, x, cl, extra=''):
    d = df.dropna(subset=[y] + x.split(' + ') + [cl]).copy()
    if d[y].nunique() < 2 or d[y].sum() < 3: return dict(n=int(len(d)), events=int(d[y].sum()) if len(d) else 0, note='too few events')
    f = f'{y} ~ {x} + C(era){extra}'
    try:
        m = smf.logit(f, d).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(d[cl])[0]}, maxiter=200)
    except Exception as e:
        return dict(n=int(len(d)), note=f'failed: {e.__class__.__name__}')
    term = x.split(' + ')[0]; lo, hi = m.conf_int().loc[term]
    return dict(OR=float(np.exp(m.params[term])), lo95=float(np.exp(lo)), hi95=float(np.exp(hi)), p=float(m.pvalues[term]), n=int(m.nobs),
                share_x1=float(d[d[term] == 1][y].mean()), share_x0=float(d[d[term] == 0][y].mean()), n_x1=int((d[term] == 1).sum()), n_x0=int((d[term] == 0).sum()))
def holm(ps):
    idx = [k for k, p in ps.items() if p is not None and np.isfinite(p)]; order = sorted(idx, key=lambda k: ps[k]); m = len(order); out = {}; run = 0
    for i, k in enumerate(order): run = max(run, min(1, (m - i) * ps[k])); out[k] = run
    return out

# ---------- A: what comes with removal ----------
for xv in ['removed', 'depose', 'assassination']:
    res = {c: logit(cc, c, xv, 'polity') for c in CONS}
    h = holm({c: r.get('p') for c, r in res.items()})
    for c in res:
        if c in h: res[c]['p_holm'] = h[c]
    R[f'A_{xv}'] = res

# ---------- B: fate of the polity after the crisis ----------
b = cc[cc.etype.notna() | (cc.censored_present == True)].copy()
b['t'] = (b.end_year - b.y1).clip(lower=0.5)
b['ev'] = b.etype.isin(['internal', 'conquest', 'other']).astype(int)
b['ev100'] = (b.ev.astype(bool) & (b.t <= 100)).astype(float)
b['int100'] = ((b.etype == 'internal') & (b.t <= 100)).astype(float)
for c in ['pre500BCE', 'post1500CE']: b[f'e_{c}'] = (b.era == c).astype(float)
def cox(df, xs, cl='polity', time='t', ev='ev'):
    d = df.dropna(subset=xs + [time, ev]).copy()
    r = coxlib.fit(np.zeros(len(d)), d[time].values, d[ev].values.astype(int), d[xs].values.astype(float), cluster=d[cl].astype(str).values)
    j = 0; b_, se = r['beta'][j], r['se'][j]
    return dict(HR=float(np.exp(b_)), lo95=float(np.exp(b_ - 1.96 * se)), hi95=float(np.exp(b_ + 1.96 * se)), p=float(2 * stats.norm.sf(abs(b_ / se))),
                n=int(len(d)), events=int(d[ev].sum()), terms=xs, all_HR={x: float(np.exp(v)) for x, v in zip(xs, r['beta'])})
ERA_X = ['e_pre500BCE', 'e_post1500CE']
R['B_cox_removed'] = cox(b, ['removed', 'PolPop'] + ERA_X)
R['B_cox_removed_plus_violence'] = cox(b, ['removed', 'PolPop', 'civil_war', 'extermination'] + ERA_X)
R['B_cox_depose'] = cox(b, ['depose', 'PolPop'] + ERA_X)
R['B_cox_assassination'] = cox(b, ['assassination', 'PolPop'] + ERA_X)
R['B_end_within100'] = logit(b, 'ev100', 'removed + PolPop', 'polity')
R['B_internal_within100'] = logit(b, 'int100', 'removed + PolPop', 'polity')
R['B_median_years_to_end'] = dict(removed=float(b[b.removed == 1].t.median()), not_removed=float(b[b.removed == 0].t.median()))
# E (part 1): interaction with moral enforcement of rulers
b['rem_x_MER'] = b.removed * b.MERb
R['E_cox_removed_x_MER'] = cox(b, ['rem_x_MER', 'removed', 'MERb', 'PolPop'] + ERA_X)
R['E_cox_removed_in_MER1'] = cox(b[b.MERb == 1], ['removed', 'PolPop'] + ERA_X)
R['E_cox_removed_in_MER0'] = cox(b[b.MERb == 0], ['removed', 'PolPop'] + ERA_X) if (b[b.MERb == 0].ev.sum() >= 3) else 'too few events'

# ---------- C: does crisis follow crisis ----------
def next_crisis(r):
    if pd.isna(r.nga): return np.nan
    o = cc[(cc.nga == r.nga) & (cc.y0 > r.y1) & (cc.y0 <= r.y1 + 100)]
    return float(len(o) > 0)
cc['next100'] = cc.apply(next_crisis, axis=1)
R['C_next_crisis_100y'] = logit(cc, 'next100', 'removed', 'nga')
R['C_next_crisis_100y_assassination'] = logit(cc, 'next100', 'assassination', 'nga')

# ---------- D: cost of internal collapse to the society in the region ----------
g = pol[pol.home_nga.notna()].copy()
rows = []
for pid, r in g[g.etype.notna()].iterrows():
    same = g[(g.home_nga == r.home_nga) & (g.index != pid)]
    cand = same[(same.start_year >= r.end_year - 50) & (same.start_year <= r.end_year + 300)]
    if not len(cand): continue
    q = cand.iloc[(cand.start_year - r.end_year).abs().argsort()].iloc[0]
    later = same[(same.start_year >= r.end_year - 50)].sort_values('start_year')
    rec = later[later.SC_mean >= r.SC_mean] if pd.notna(r.SC_mean) else later.iloc[0:0]
    if pd.notna(r.SC_mean) and len(rec):
        rec_t, rec_ev = max(0.5, rec.start_year.iloc[0] - r.end_year), 1
    elif pd.notna(r.SC_mean):
        rec_t, rec_ev = max(0.5, same.end_year.max() - r.end_year), 0
    else:
        rec_t, rec_ev = np.nan, np.nan
    rows.append(dict(polity=pid, succ=q.name, nga=r.home_nga, etype=r.etype, era=era(r.end_year), MERb=r.MERb,
                     dSC=q.SC_mean - r.SC_mean, dPop=q.PolPop - r.PolPop, dTerr=q.PolTerr - r.PolTerr, gap=q.start_year - r.end_year,
                     rec_t=rec_t, rec_ev=rec_ev, SC_pred=r.SC_mean))
D = pd.DataFrame(rows)
D.to_csv(A + 'h8/h8_followup_transitions.csv', index=False)
R['D_counts'] = D.etype.value_counts().to_dict()
R['D_means'] = D.groupby('etype')[['dSC', 'dPop', 'dTerr', 'gap']].mean().round(3).to_dict()
R['D_n_nonmissing'] = D.groupby('etype')[['dSC', 'dPop', 'dTerr']].count().to_dict()
Dm = D[D.etype.isin(['internal', 'conquest', 'continuity'])].copy()
for y in ['dSC', 'dPop', 'dTerr', 'gap']:
    d = Dm.dropna(subset=[y]).copy()
    out = {}
    for lab, f, kw in [('clustered', f"{y} ~ C(etype, Treatment('continuity')) + C(era)", dict(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.nga)[0]})),
                       ('nga_fe', f"{y} ~ C(etype, Treatment('continuity')) + C(era) + C(nga)", dict(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.nga)[0]}))]:
        m = smf.ols(f, d).fit(**kw)
        for t in ['internal', 'conquest']:
            k = f"C(etype, Treatment('continuity'))[T.{t}]"
            if k in m.params: out[f'{lab}_{t}'] = dict(coef=float(m.params[k]), lo95=float(m.conf_int().loc[k, 0]), hi95=float(m.conf_int().loc[k, 1]), p=float(m.pvalues[k]))
        out[f'{lab}_n'] = int(m.nobs)
    R[f'D_{y}'] = out
Dr = Dm.dropna(subset=['rec_t', 'rec_ev']).copy()
Dr['internal'] = (Dr.etype == 'internal').astype(float); Dr['conquest'] = (Dr.etype == 'conquest').astype(float)
for c in ['pre500BCE', 'post1500CE']: Dr[f'e_{c}'] = (Dr.era == c).astype(float)
R['D_recovery_cox_internal'] = cox(Dr, ['internal', 'conquest', 'SC_pred'] + ERA_X, cl='nga', time='rec_t', ev='rec_ev')
R['D_recovery_cox_conquest'] = cox(Dr, ['conquest', 'internal', 'SC_pred'] + ERA_X, cl='nga', time='rec_t', ev='rec_ev')
R['D_recovery_median_years'] = Dr[Dr.rec_ev == 1].groupby('etype').rec_t.median().to_dict()
R['D_recovered_share'] = Dr.groupby('etype').rec_ev.mean().round(3).to_dict()
# E (part 2): does moral sanction cushion the cost of internal collapse?
de = Dm.dropna(subset=['dSC', 'MERb']).copy(); de['internal'] = (de.etype == 'internal').astype(float); de['conquest'] = (de.etype == 'conquest').astype(float)
m = smf.ols('dSC ~ internal*MERb + conquest + C(era)', de).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(de.nga)[0]})
R['E_dSC_internal_x_MER'] = dict(coef=float(m.params['internal:MERb']), lo95=float(m.conf_int().loc['internal:MERb', 0]), hi95=float(m.conf_int().loc['internal:MERb', 1]),
                                 p=float(m.pvalues['internal:MERb']), internal_main=float(m.params['internal']), n=int(m.nobs),
                                 cells=de.groupby(['etype', 'MERb']).dSC.agg(['size', 'mean']).round(3).reset_index().to_dict('records'))
json.dump(R, open(A + 'h8/h8_followup_results.json', 'w'), indent=1, default=str)
print(json.dumps(R, indent=1, default=str))
