"""Study 2 (Addendum 14.1, fixed 22 Oct 2026): folklore CCI from Berezkin motif descriptions scored by MAC-D."""
import sys, json, numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy import stats
sys.path.insert(0, '/root/analysis/cci'); import macd
M = '/root/data/mx_folklore/'
rd = lambda f, **k: pd.read_stata(M + f, convert_categoricals=False, **k)
mm = rd('Motif_Master.dta')
flags = []
for _, r in mm.iterrows():
    n, c = macd.score(f"{r.title_english}. {r.desc_eng}")
    row = {'motif_id': r.motif_id, 'tokens': n}
    for d in macd.DOMAINS:
        row[f'v_{d}'] = int(c.get(f'Virtue{d}', 0) > 0); row[f'x_{d}'] = int(c.get(f'Vice{d}', 0) > 0)
    flags.append(row)
F = pd.DataFrame(flags).set_index('motif_id'); F.to_csv('/root/analysis/study2/motif_macd_flags.csv')
OUT = {'motifs': len(F), 'share_motifs_any_virtue': float((F.filter(like='v_').sum(axis=1) > 0).mean()),
       'domain_share_motifs': {d: float(F[f'v_{d}'].mean()) for d in macd.DOMAINS}}
def unit_scores(inc):
    cols = [c for c in inc.columns if c in F.index]
    X = inc[cols].astype(float).fillna(0).values; tot = X.sum(axis=1)
    S = pd.DataFrame(index=inc.index)
    for d in macd.DOMAINS:
        S[f's_{d}'] = (X @ F.loc[cols, f'v_{d}'].values) / np.where(tot > 0, tot, np.nan)
        S[f'n_{d}'] = (X @ (F.loc[cols, f'v_{d}'].values - F.loc[cols, f'x_{d}'].values)) / np.where(tot > 0, tot, np.nan)
    S['n_motifs_scored'] = (X > 0).sum(axis=1)
    return S
def cci(S, keep):
    S = S[keep].copy(); z = lambda s: (s - s.mean()) / s.std(ddof=1)
    S['CCI'] = np.mean([z(S[f's_{d}']) for d in macd.DOMAINS], axis=0)
    S['CCI_net'] = np.mean([z(S[f'n_{d}']) for d in macd.DOMAINS], axis=0)
    for c in ['CCI', 'CCI_net']: S[c] = z(S[c])
    return S
def res(m, term, ysd=None, xsd=1.0):
    b, se, p = m.params[term], m.bse[term], m.pvalues[term]
    lo, hi = m.conf_int().loc[term]; lo90, hi90 = m.conf_int(alpha=0.10).loc[term]
    out = dict(b=float(b), se=float(se), p=float(p), lo95=float(lo), hi95=float(hi), n=int(m.nobs))
    if ysd:  # standardized effect: SD of outcome per SD of predictor
        out.update(std_b=float(b * xsd / ysd), std_lo90=float(lo90 * xsd / ysd), std_hi90=float(hi90 * xsd / ysd))
        out['equivalent_within_0.10'] = bool(out['std_lo90'] > -0.10 and out['std_hi90'] < 0.10)
    return out
R = {}
# ---- S2-1 countries ----
cty = rd('Motifs_Countries.dta'); idc = 'cntry' if 'cntry' in cty.columns else cty.columns[0]
cty = cty.set_index(idc)
Sc = unit_scores(cty); creg = rd('Country_Regressions_Ready.dta', columns=['cntry', 'lntrust_wvsavg', 'trust_gps', 'lnyear_firstpub', 'lnnmbr_title', 'motifs_total', 'asia', 'africa', 'americas', 'europe', 'tricksters_punish']).set_index('cntry')
cd = creg.join(Sc, how='inner'); cd = cci(cd, cd.motifs_total >= 5)
R['countries_n'] = int(len(cd))
for y in ['lntrust_wvsavg', 'trust_gps']:
    for lab, rhs in [('cont0', 'lnyear_firstpub + lnnmbr_title'), ('cont1', 'lnyear_firstpub + lnnmbr_title + asia + africa + americas + europe')]:
        for x in ['CCI', 'CCI_net', 'tricksters_punish']:
            dd = cd.dropna(subset=[y, x, 'lnyear_firstpub', 'lnnmbr_title'])
            m = smf.ols(f'{y} ~ {x} + {rhs}', dd).fit(cov_type='HC1')
            R[f'S2-1_{y}_{lab}_{x}'] = res(m, x, dd[y].std(), dd[x].std())
# ---- S2-2 ESS second generation ----
ess = rd('European_Social_Surveys_Regressions_Ready.dta')
ess['lntrust_ess'] = np.log1p(ess.ppltrst); ess['age'] = ess.agea.where(ess.agea <= 100); ess['gender'] = ess.gndr
ess['rel'] = ess.rlgdnm; ess.loc[ess.rlgblg == 2, 'rel'] = 0; ess.loc[ess.rlgblg.isna(), 'rel'] = np.nan
ess['cntry_round'] = ess.cntry_ess.astype(str) + ess.essround.astype(int).astype(str)
ess['age10'] = pd.qcut(ess.age, 10, labels=False, duplicates='drop')
ess = ess.join(cd[['CCI', 'CCI_net']], on='cntry')
base = ess[ess.rel.notna() & ess.health.notna() & ess.age.notna() & ess.gender.notna() & (ess.age > 17)]
for x in ['CCI', 'CCI_net', 'tricksters_punish']:
    for lab, rhs in [('cont0', 'lnyear_firstpub + lnnmbr_title'), ('cont1', 'lnyear_firstpub + lnnmbr_title + gender + C(rel) + C(health) + C(age10)')]:
        dd = base.dropna(subset=['lntrust_ess', x, 'lnyear_firstpub', 'lnnmbr_title'])
        m = smf.ols(f'lntrust_ess ~ {x} + {rhs} + C(cntry_round)', dd).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.cntry)[0]})
        R[f'S2-2_{lab}_{x}'] = res(m, x, dd.lntrust_ess.std(), dd[x].std()); R[f'S2-2_{lab}_{x}']['origin_countries'] = int(dd.cntry.nunique())
# ---- S2-3 Ethnographic Atlas ----
eam = rd('Motifs_EA_groups.dta').set_index('atlas')
Se = unit_scores(eam)
ear = rd('Ethnographic_Atlas_Regressions_Ready.dta', columns=['atlas', 'v33', 'v34', 'v98', 'continent_EA', 'lnyear_firstpub', 'lnnmbr_title', 'motifs_total', 'tricksters_punish']).set_index('atlas')
ed = ear.join(Se, how='inner'); ed = cci(ed, ed.motifs_total > 4)
R['EA_n'] = int(len(ed))
for x in ['CCI', 'CCI_net']:
    for lab, rhs in [('base', ''), ('highgods', ' + C(v34)')]:
        dd = ed.dropna(subset=['v33', x, 'lnyear_firstpub', 'lnnmbr_title', 'v98', 'continent_EA'] + (['v34'] if lab == 'highgods' else []))
        m = smf.ols(f'v33 ~ {x} + lnyear_firstpub + lnnmbr_title + C(continent_EA){rhs}', dd).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.v98)[0]})
        R[f'S2-3_{lab}_{x}'] = res(m, x, dd.v33.std(), dd[x].std()); R[f'S2-3_{lab}_{x}']['families'] = int(dd.v98.nunique())
OUT['results'] = R
json.dump(OUT, open('/root/analysis/study2/study2_results.json', 'w'), indent=1)
for k, v in R.items(): print(k, v if not isinstance(v, dict) else {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()})
