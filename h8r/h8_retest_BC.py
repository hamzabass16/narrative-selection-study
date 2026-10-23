"""H8 retest, Parts B and C (approved retest plan, H8). Written before it was run; reuses the frozen construction of
h8r_analysis.py (V-Dem v15; autocracy-years; strategy S = z(Coop - Dom)).
Part B (primary): regime-level strategy averaged only over years at least 10 years before the regime's last year (20 years
as sensitivity); regimes with no such year drop. Ending test as in 14.5 (violent internal end versus orderly), logit with
ldur, start quarter-century and region, errors clustered by country; and with country fixed effects (conditional logit by
country; linear probability model with country fixed effects as a check). External ends as secondary.
Part C: Archigos 4.1 leaders 1875-2015 matched to V-Dem by COW code. Exposure: mean S over the leader's first three
calendar years in office (fewer if the tenure is shorter), autocracy-years only. Outcomes: irregular exit versus regular
exit; removal by foreign force versus regular; bad post-tenure fate (exile, imprisonment, death) versus OK. Logit with
log GDP per head and log population at entry, log tenure, entry decade and region; errors clustered by country.
Part D (Jones and Olken assassination attempts) was optional and is not run: the data were not obtained."""
import json, warnings, numpy as np, pandas as pd, statsmodels.formula.api as smf
from statsmodels.discrete.conditional_models import ConditionalLogit
warnings.filterwarnings('ignore')
v = pd.read_pickle('/root/data/ext_vdem/vdem.pkl')
keep = ['country_name', 'country_id', 'COWcode', 'year', 'v2x_regime', 'v2x_polyarchy', 'v2clkill', 'v2cltort', 'v2csreprss', 'v2exrescon', 'v2x_jucon',
        'v2xlg_legcon', 'v2dlencmps', 'e_gdppc', 'e_pop', 'e_regiongeo', 'v2regidnr', 'v2regendtype']
v = v[keep].copy(); v['year'] = v.year.astype(int)
v['autoc'] = np.where(v.v2x_regime.notna(), (v.v2x_regime <= 1).astype(float), np.where(v.v2x_polyarchy.notna(), (v.v2x_polyarchy < 0.5).astype(float), np.nan))
A = v[v.autoc == 1].copy()
z = lambda s: (s - s.mean()) / s.std()
A['Dom'] = pd.concat([-z(A.v2clkill), -z(A.v2cltort), -z(A.v2csreprss)], axis=1).mean(axis=1)
Cc = pd.concat([z(A.v2exrescon), z(A.v2x_jucon), z(A.v2xlg_legcon), z(A.v2dlencmps)], axis=1)
A['Coop'] = Cc.mean(axis=1).where(Cc.notna().sum(axis=1) >= 3)
A['S'] = z(A.Coop - A.Dom)
R = {}
# ---------- Part B ----------
rg = v.dropna(subset=['v2regidnr']).merge(A[['country_id', 'year', 'S']], on=['country_id', 'year'], how='left')
VIOL, ORD, EXT = {0, 1, 3, 5, 8}, {4, 9, 10, 11}, {6, 7}
def regimes(lag):
    out = []
    for rid, g in rg.groupby('v2regidnr'):
        end = g.year.max(); s = g[g.year <= end - lag].S
        et = g.v2regendtype.dropna(); et = et.mode().iloc[0] if len(et) else np.nan
        out.append(dict(rid=rid, country_id=g.country_id.iloc[0], start=g.year.min(), end=end, years=len(g), autoc=g.autoc.mean(),
                        S=s.mean() if s.notna().any() else np.nan, endtype=et, region=g.e_regiongeo.iloc[0]))
    G = pd.DataFrame(out); G = G[(G.autoc >= 0.5) & G.S.notna()].copy()
    G['region'] = G.region.astype('Int64').astype(str); G['sdec'] = (G.start // 25) * 25; G['ldur'] = np.log(G.years)
    G['viol'] = np.where(G.endtype.isin(VIOL), 1.0, np.where(G.endtype.isin(ORD), 0.0, np.nan))
    G['ext'] = np.where(G.endtype.isin(EXT), 1.0, np.where(G.endtype.isin(ORD), 0.0, np.nan))
    G['Sz'] = z(G.S); return G
def logit(d, y, rhs, term='Sz'):
    d = d.dropna(subset=[y, term, 'ldur']).copy()
    m = smf.logit(f'{y} ~ {term} + {rhs}', d).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(d.country_id)[0]}, maxiter=300)
    lo, hi = m.conf_int().loc[term]; q = d[term].quantile([.25, .75]).values
    return dict(OR=float(np.exp(m.params[term])), lo95=float(np.exp(lo)), hi95=float(np.exp(hi)), p=float(m.pvalues[term]), n=int(m.nobs),
                countries=int(d.country_id.nunique()), share_bottomQ=float(d[d[term] <= q[0]][y].mean()), share_topQ=float(d[d[term] >= q[1]][y].mean()))
def clogit(d, y, term='Sz'):
    d = d.dropna(subset=[y, term, 'ldur']).copy()
    var = d.groupby('country_id')[y].transform(lambda s: s.nunique() > 1); d = d[var]
    m = ConditionalLogit(d[y].values, d[[term, 'ldur']].values, groups=d.country_id.values).fit(disp=0)
    b, se = m.params[0], m.bse[0]
    return dict(OR=float(np.exp(b)), lo95=float(np.exp(b - 1.96 * se)), hi95=float(np.exp(b + 1.96 * se)), p=float(2 * __import__('scipy').stats.norm.sf(abs(b / se))),
                n=int(len(d)), countries=int(d.country_id.nunique()))
def lpm_fe(d, y, term='Sz'):
    d = d.dropna(subset=[y, term, 'ldur']).copy()
    m = smf.ols(f'{y} ~ {term} + ldur + C(sdec) + C(country_id)', d).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.country_id)[0]})
    lo, hi = m.conf_int().loc[term]
    return dict(b=float(m.params[term]), lo95=float(lo), hi95=float(hi), p=float(m.pvalues[term]), n=int(m.nobs))
for lag in [0, 10, 20]:
    G = regimes(lag)
    R[f'B_lag{lag}'] = dict(regimes=int(len(G)), violent=int((G.viol == 1).sum()), orderly=int((G.viol == 0).sum()),
                            viol_logit=logit(G, 'viol', 'ldur + C(sdec) + C(region)'), ext_logit=logit(G, 'ext', 'ldur + C(sdec) + C(region)'),
                            viol_country_clogit=clogit(G, 'viol'), viol_country_lpm=lpm_fe(G, 'viol'))
    print(lag, json.dumps(R[f'B_lag{lag}'], default=float)[:900], flush=True)
# ---------- Part C ----------
ar = pd.read_stata('/root/data/ext2/archigos/Archigos_4.1_stata14.dta')
ar['start'] = pd.to_datetime(ar.startdate, errors='coerce'); ar['end'] = pd.to_datetime(ar.enddate, errors='coerce')
ar = ar[ar.start.dt.year >= 1875].copy()
ar['y0'] = ar.start.dt.year; ar['y1'] = ar.end.dt.year.fillna(2015)
AS = A[['COWcode', 'year', 'S', 'e_gdppc', 'e_pop', 'e_regiongeo', 'country_id']].dropna(subset=['COWcode']).copy(); AS['COWcode'] = AS.COWcode.astype(int)
ix = AS.set_index(['COWcode', 'year'])
rows = []
for r in ar.itertuples():
    yrs = range(int(r.y0), int(min(r.y0 + 2, r.y1)) + 1)
    ss = [ix.S.get((int(r.ccode), y)) for y in yrs]
    ss = [s for s in ss if s is not None and np.isfinite(s)]
    if not ss: continue
    base = ix.loc[(int(r.ccode), int(r.y0))] if (int(r.ccode), int(r.y0)) in ix.index else ix.loc[(int(r.ccode), [y for y in yrs if (int(r.ccode), y) in ix.index][0])]
    if isinstance(base, pd.DataFrame): base = base.iloc[0]
    ten = max((r.end - r.start).days / 365.25, 0.1) if pd.notna(r.end) else np.nan
    rows.append(dict(leader=r.leader, ccode=int(r.ccode), country_id=base.country_id, y0=int(r.y0), S3=np.mean(ss), exit=r.exit, exitcode=r.exitcode,
                     fate=r.posttenurefate, lgdp=np.log(base.e_gdppc) if base.e_gdppc > 0 else np.nan, lpop=np.log(base.e_pop) if base.e_pop > 0 else np.nan,
                     region=str(int(base.e_regiongeo)) if pd.notna(base.e_regiongeo) else 'na', ltenure=np.log(ten) if np.isfinite(ten) else np.nan))
L = pd.DataFrame(rows); L['Sz'] = z(L.S3); L['decade'] = (L.y0 // 10) * 10
L['irregular'] = np.where(L.exit == 'Irregular', 1.0, np.where(L.exit == 'Regular', 0.0, np.nan))
L['foreign'] = np.where(L.exit == 'Foreign', 1.0, np.where(L.exit == 'Regular', 0.0, np.nan))
L['badfate'] = np.where(L.fate.isin(['Exile', 'Imprisonment', 'Death']), 1.0, np.where(L.fate == 'OK', 0.0, np.nan))
R['C_counts'] = dict(leaders=int(len(L)), countries=int(L.ccode.nunique()), exits=L.exit.value_counts().to_dict(), fates=L.fate.value_counts().to_dict())
def logitL(y):
    d = L.dropna(subset=[y, 'Sz', 'lgdp', 'lpop', 'ltenure']).copy()
    m = smf.logit(f'{y} ~ Sz + lgdp + lpop + ltenure + C(decade) + C(region)', d).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(d.ccode)[0]}, maxiter=300)
    lo, hi = m.conf_int().loc['Sz']; q = d.Sz.quantile([.25, .75]).values
    return dict(OR=float(np.exp(m.params['Sz'])), lo95=float(np.exp(lo)), hi95=float(np.exp(hi)), p=float(m.pvalues['Sz']), n=int(m.nobs),
                share_bottomQ=float(d[d.Sz <= q[0]][y].mean()), share_topQ=float(d[d.Sz >= q[1]][y].mean()))
for y in ['irregular', 'foreign', 'badfate']: R[f'C_{y}'] = logitL(y)
b10 = R['B_lag10']['viol_logit']
R['B_verdict_component'] = 'violent-end prediction holds with lagged exposure' if (b10['OR'] < 1 and b10['p'] < 0.05) else 'violent-end prediction not confirmed with lagged exposure'
json.dump(R, open('/root/analysis/h8r/h8_retest_BC_results.json', 'w'), indent=1, default=float)
print(json.dumps({k: R[k] for k in R if k.startswith('C_') or k.endswith('component')}, indent=1, default=float))
