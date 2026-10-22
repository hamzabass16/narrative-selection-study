"""H8 revised (plan: h8r_plan.md, fixed 23 Oct 2026 before these models were run). Data: V-Dem v15 (expert-coded)."""
import json, sys, warnings
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
sys.path.insert(0, '/root/analysis/study1'); import coxlib
warnings.filterwarnings('ignore')
v = pd.read_pickle('/root/data/ext_vdem/vdem.pkl')
keep = ['country_name', 'country_id', 'year', 'v2x_regime', 'v2x_polyarchy', 'v2clkill', 'v2cltort', 'v2csreprss', 'v2exrescon', 'v2x_jucon',
        'v2xlg_legcon', 'v2dlencmps', 'v2exl_legitideolcr_0', 'v2exl_legitideolcr_1', 'v2exl_legitideolcr_4', 'v2exl_legitideol_osp',
        'v2exl_legitlead', 'v2clrelig', 'v2csrlgrep', 'e_gdppc', 'e_pop', 'e_pelifeex', 'e_civil_war', 'e_pt_coup', 'e_regiongeo',
        'v2regidnr', 'v2regendtype']
v = v[keep].copy(); v['year'] = v.year.astype(int)
v['autoc'] = np.where(v.v2x_regime.notna(), (v.v2x_regime <= 1).astype(float), np.where(v.v2x_polyarchy.notna(), (v.v2x_polyarchy < 0.5).astype(float), np.nan))
A = v[v.autoc == 1].copy()
z = lambda s: (s - s.mean()) / s.std()
A['Dom'] = pd.concat([-z(A.v2clkill), -z(A.v2cltort), -z(A.v2csreprss)], axis=1).mean(axis=1)
Cc = pd.concat([z(A.v2exrescon), z(A.v2x_jucon), z(A.v2xlg_legcon), z(A.v2dlencmps)], axis=1)
A['Coop'] = Cc.mean(axis=1).where(Cc.notna().sum(axis=1) >= 3)
A['S'] = z(A.Coop - A.Dom); A['Dz'] = z(A.Dom); A['Cz'] = z(A.Coop)
A['lgdp'] = np.log(A.e_gdppc); A['lpop'] = np.log(A.e_pop); A['decade'] = (A.year // 10) * 10
A['region'] = A.e_regiongeo.astype('Int64').astype(str)
R = dict(n_autoc_years=int(len(A)), countries=int(A.country_id.nunique()), corr_C_D=float(A[['Coop', 'Dom']].corr().iloc[0, 1]))

def ols(df, f, term, cl='country_id'):
    rows = smf.ols(f, df, missing='drop').data.row_labels
    d = df.loc[rows]
    g = pd.factorize(d[cl])[0]
    m = smf.ols(f, d).fit(cov_type='cluster', cov_kwds={'groups': g})  # refit so absent fixed-effect levels are not kept as empty columns
    lo, hi = m.conf_int().loc[term]
    return dict(coef=float(m.params[term]), lo95=float(lo), hi95=float(hi), p=float(m.pvalues[term]), n=int(m.nobs), countries=int(len(set(g))))

# ---------------- Part A: religious legitimation ----------------
a = A[(A.year >= 1900) & (A.year <= 2023)].copy()
for lab, col in [('RL', 'v2exl_legitideolcr_4'), ('NAT', 'v2exl_legitideolcr_0'), ('SOC', 'v2exl_legitideolcr_1')]:
    a[lab] = a[col] * a.v2exl_legitideol_osp / 4
OUTA = {'religious_freedom': z(a.v2clrelig), 'religious_org_repression': -z(a.v2csrlgrep), 'political_killings': -z(a.v2clkill),
        'torture': -z(a.v2cltort), 'CSO_repression': -z(a.v2csreprss), 'exec_respects_constitution': z(a.v2exrescon),
        'judicial_constraints': z(a.v2x_jucon), 'legislative_constraints': z(a.v2xlg_legcon), 'public_goods': z(a.v2dlencmps),
        'personalist_legitimation': z(a.v2exl_legitlead)}
for k, s in OUTA.items(): a[f'y_{k}'] = s
R['A_RL_descr'] = dict(mean=float(a.RL.mean()), share_RL_over_0_5=float((a.RL > 0.5).mean()), n=int(a.RL.notna().sum()),
                       top_countries=a[a.RL > 0.5].groupby('country_name').size().sort_values(ascending=False).head(15).to_dict())
for lab in ['RL', 'NAT', 'SOC']:
    res = {}
    for k in OUTA:
        res[k] = dict(region_fe=ols(a, f'y_{k} ~ {lab} + lgdp + lpop + C(year) + C(region)', lab),
                      country_fe=ols(a, f'y_{k} ~ {lab} + lgdp + lpop + C(year) + C(country_id)', lab))
    R[f'A_{lab}'] = res

# ---------------- Part B1: forward outcomes ----------------
P = v[['country_id', 'year', 'e_gdppc', 'e_pelifeex', 'e_civil_war', 'e_pt_coup']].copy()
P['lgdp'] = np.log(P.e_gdppc)
idx = P.set_index(['country_id', 'year'])
def fwd(col, k):
    s = idx[col]; return s.reindex(pd.MultiIndex.from_arrays([A.country_id, A.year + k])).values
A['g10'] = fwd('lgdp', 10) - A.lgdp; A['g20'] = fwd('lgdp', 20) - A.lgdp; A['gpast10'] = A.lgdp - fwd('lgdp', -10)
A['le20'] = fwd('e_pelifeex', 20) - A.e_pelifeex
cw = np.column_stack([fwd('e_civil_war', k) for k in range(1, 11)]); cp = np.column_stack([fwd('e_pt_coup', k) for k in range(1, 11)])
A['cw_onset10'] = np.where((A.e_civil_war == 0) & (A.year + 10 <= 2006) & (np.isfinite(cw).sum(1) >= 8), (np.nanmax(np.where(np.isfinite(cw), cw, 0), 1) > 0).astype(float), np.nan)
A['coup10'] = np.where((A.year >= 1950) & (A.year + 10 <= 2025) & (np.isfinite(cp).sum(1) >= 8), (np.nanmax(np.where(np.isfinite(cp), cp, 0), 1) > 0).astype(float), np.nan)
b = A[A.year <= 2015].copy()
SPEC = {'g10': 'g10 ~ {x} + lgdp + lpop + gpast10 + C(decade) + C(region)', 'g20': 'g20 ~ {x} + lgdp + lpop + gpast10 + C(decade) + C(region)',
        'le20': 'le20 ~ {x} + e_pelifeex + lgdp + lpop + C(decade) + C(region)', 'cw_onset10': 'cw_onset10 ~ {x} + lgdp + lpop + C(decade) + C(region)',
        'coup10': 'coup10 ~ {x} + lgdp + lpop + C(decade) + C(region)'}
B1 = {}
for y, f in SPEC.items():
    B1[y] = dict(primary=ols(b, f.format(x='S'), 'S'),
                 country_fe=ols(b, f.format(x='S').replace('C(region)', 'C(country_id)'), 'S'),
                 decade_panels=ols(b[b.year % 10 == 0], f.format(x='S'), 'S'),
                 D_only=ols(b, f.format(x='Dz'), 'Dz'), C_only=ols(b, f.format(x='Cz'), 'Cz'),
                 sd_y=float(b[y].std()), mean_y=float(b[y].mean()))
R['B1'] = B1

# ---------------- Part B2/B3: regime level ----------------
rg = v.dropna(subset=['v2regidnr']).copy()
rg = rg.merge(A[['country_id', 'year', 'S']], on=['country_id', 'year'], how='left')
G = rg.groupby('v2regidnr').agg(country_id=('country_id', 'first'), start=('year', 'min'), end=('year', 'max'), years=('year', 'size'),
                                 autoc=('autoc', 'mean'), S=('S', 'mean'), endtype=('v2regendtype', lambda s: s.mode().iloc[0] if s.notna().any() else np.nan),
                                 region=('e_regiongeo', 'first'))
G = G[(G.autoc >= 0.5) & G.S.notna()].copy()
G['region'] = G.region.astype('Int64').astype(str); G['sdec'] = (G.start // 25) * 25; G['ldur'] = np.log(G.years)
VIOL, ORD, EXT = {0, 1, 3, 5, 8}, {4, 9, 10, 11}, {6, 7}
G['ended'] = G.endtype.notna() & (G.endtype != 13)
G['viol'] = np.where(G.endtype.isin(VIOL), 1.0, np.where(G.endtype.isin(ORD), 0.0, np.nan))
G['ext'] = np.where(G.endtype.isin(EXT), 1.0, np.where(G.endtype.isin(ORD), 0.0, np.nan))
G['Sz'] = z(G.S)
R['B2_counts'] = dict(regimes=int(len(G)), ended=int(G.ended.sum()), violent=int((G.viol == 1).sum()), orderly=int((G.viol == 0).sum()), external=int((G.ext == 1).sum()),
                      endtype=G[G.ended].endtype.value_counts().sort_index().to_dict())
def logit(df, f, term, cl='country_id'):
    y = f.split('~')[0].strip()
    d = df.dropna(subset=[y, 'Sz', 'ldur']).copy()
    m = smf.logit(f, d).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(d[cl])[0]}, maxiter=300)
    lo, hi = m.conf_int().loc[term]
    q = d.Sz.quantile([0.25, 0.75]).values
    return dict(OR_per_SD=float(np.exp(m.params[term])), lo95=float(np.exp(lo)), hi95=float(np.exp(hi)), p=float(m.pvalues[term]), n=int(m.nobs),
                share_bottom_quartile_S=float(d[d.Sz <= q[0]][y].mean()), share_top_quartile_S=float(d[d.Sz >= q[1]][y].mean()))
R['B2_internal_violent_end'] = logit(G, 'viol ~ Sz + ldur + C(sdec) + C(region)', 'Sz')
R['B2_external_end'] = logit(G, 'ext ~ Sz + ldur + C(sdec) + C(region)', 'Sz')
# B3 Cox on regime duration
H = G.copy(); H['ev'] = H.ended.astype(int)
dec = pd.get_dummies(H.sdec, prefix='d', drop_first=True).astype(float); reg = pd.get_dummies(H.region, prefix='r', drop_first=True).astype(float)
X = pd.concat([H[['Sz']], dec, reg], axis=1)
r = coxlib.fit(np.zeros(len(H)), H.years.values.astype(float), H.ev.values, X.values, cluster=H.country_id.astype(str).values)
R['B3_regime_duration_cox'] = dict(HR_per_SD=float(np.exp(r['beta'][0])), lo95=float(np.exp(r['beta'][0] - 1.96 * r['se'][0])), hi95=float(np.exp(r['beta'][0] + 1.96 * r['se'][0])),
                                   p=float(2 * stats.norm.sf(abs(r['beta'][0] / r['se'][0]))), n=int(len(H)), events=int(H.ev.sum()))
json.dump(R, open('/root/analysis/h8r/h8r_results.json', 'w'), indent=1, default=str)
print(json.dumps(R, indent=1, default=str)[:20000])
