"""Study 2 rerun with endorsement codes (approved retest plan, Sections 3.2 and 5, Study 2). Written before any outcome was linked.
Exposure: unit mean of the motif score (cooperative acts rewarded + defections punished - defections rewarded - cooperative
acts punished), over the unit's coded motifs, incidence-weighted as in the first run; pilot motifs (5 percent) excluded.
ENDORSE = z-score of that mean across the units of each dataset; units with fewer than 5 motifs excluded (as in 14.1).
Variants: ENDORSE_noenemy (acts against enemies excluded); ENDORSE_rel (bravery and fairness acts removed, the two behaviours
below alpha 0.80 in double coding; sensitivity fixed before outcomes were linked).
Primary tests (Study 2 family, Holm): S2-1 ln WVS trust with continent dummies; S2-2 ESS second generation with the
authors' individual controls. Supported if both coefficients are positive with Holm p < 0.05. Falsified if both 90 percent
intervals of the standardized effect lie inside the trickster benchmarks (+-0.34 SD across countries, +-0.03 SD among
immigrants). Otherwise inconclusive. S2-3 political scale and the language-survival outcome are secondary/exploratory."""
import json, re, numpy as np, pandas as pd, statsmodels.formula.api as smf
from statsmodels.miscmodels.ordinal_model import OrderedModel
M = '/root/data/mx_folklore/'; S2 = '/root/analysis/s2r/'
rd = lambda f, **k: pd.read_stata(M + f, convert_categoricals=False, **k)
P = pd.read_csv(S2 + 'codes/motif_codes_primary.csv').set_index('motif_id')
P = P[~P.pilot]
P['score_rel'] = P.score - P.s_bravery - P.s_fairness
OUT = {'motifs_scored': int(len(P)), 'share_motifs_with_act': float((P.n_acts > 0).mean()),
       'mean_motif_score': float(P.score.mean()), 'share_pro': float((P.score > 0).mean()), 'share_anti': float((P.score < 0).mean())}
def unit_scores(inc):
    cols = [c for c in inc.columns if c in P.index]
    X = inc[cols].astype(float).fillna(0).values; tot = X.sum(axis=1); den = np.where(tot > 0, tot, np.nan)
    S = pd.DataFrame(index=inc.index)
    for v in ['score', 'score_noenemy', 'score_rel']: S['m_' + v] = (X @ P.loc[cols, v].values) / den
    for b in ['family', 'group', 'reciprocity', 'bravery', 'deference', 'fairness', 'property']: S['m_' + b] = (X @ P.loc[cols, 's_' + b].values) / den
    S['n_coded'] = (X > 0).sum(axis=1)
    return S
z = lambda s: (s - s.mean()) / s.std(ddof=1)
def prep(S, keep):
    S = S[keep].copy()
    S['ENDORSE'] = z(S.m_score); S['ENDORSE_noenemy'] = z(S.m_score_noenemy); S['ENDORSE_rel'] = z(S.m_score_rel)
    return S
def res(m, term, ysd, xsd):
    b, se, p = m.params[term], m.bse[term], m.pvalues[term]
    lo, hi = m.conf_int().loc[term]; lo90, hi90 = m.conf_int(alpha=0.10).loc[term]
    return dict(b=float(b), se=float(se), p=float(p), lo95=float(lo), hi95=float(hi), n=int(m.nobs),
                std_b=float(b * xsd / ysd), std_lo90=float(lo90 * xsd / ysd), std_hi90=float(hi90 * xsd / ysd))
R = {}
X3 = ['ENDORSE', 'ENDORSE_noenemy', 'ENDORSE_rel', 'tricksters_punish']
cty = rd('Motifs_Countries.dta').set_index('cntry')
creg = rd('Country_Regressions_Ready.dta', columns=['cntry', 'lntrust_wvsavg', 'trust_gps', 'lnyear_firstpub', 'lnnmbr_title', 'motifs_total', 'asia', 'africa', 'americas', 'europe', 'tricksters_punish']).set_index('cntry')
cd = prep(creg.join(unit_scores(cty), how='inner'), lambda d: d.motifs_total >= 5)
R['countries_n'] = int(len(cd)); R['corr_ENDORSE_trickster_countries'] = float(cd[['ENDORSE', 'tricksters_punish']].corr().iloc[0, 1])
for y in ['lntrust_wvsavg', 'trust_gps']:
    for lab, rhs in [('cont0', 'lnyear_firstpub + lnnmbr_title'), ('cont1', 'lnyear_firstpub + lnnmbr_title + asia + africa + americas + europe')]:
        for x in X3:
            dd = cd.dropna(subset=[y, x, 'lnyear_firstpub', 'lnnmbr_title'])
            m = smf.ols(f'{y} ~ {x} + {rhs}', dd).fit(cov_type='HC1')
            R[f'S2-1_{y}_{lab}_{x}'] = res(m, x, dd[y].std(), dd[x].std())
ess = rd('European_Social_Surveys_Regressions_Ready.dta')
ess['lntrust_ess'] = np.log1p(ess.ppltrst); ess['age'] = ess.agea.where(ess.agea <= 100); ess['gender'] = ess.gndr
ess['rel'] = ess.rlgdnm; ess.loc[ess.rlgblg == 2, 'rel'] = 0; ess.loc[ess.rlgblg.isna(), 'rel'] = np.nan
ess['cntry_round'] = ess.cntry_ess.astype(str) + ess.essround.astype(int).astype(str)
ess['age10'] = pd.qcut(ess.age, 10, labels=False, duplicates='drop')
ess = ess.join(cd[['ENDORSE', 'ENDORSE_noenemy', 'ENDORSE_rel']], on='cntry')
base = ess[ess.rel.notna() & ess.health.notna() & ess.age.notna() & ess.gender.notna() & (ess.age > 17)]
for x in X3:
    for lab, rhs in [('cont0', 'lnyear_firstpub + lnnmbr_title'), ('cont1', 'lnyear_firstpub + lnnmbr_title + gender + C(rel) + C(health) + C(age10)')]:
        dd = base.dropna(subset=['lntrust_ess', x, 'lnyear_firstpub', 'lnnmbr_title'])
        m = smf.ols(f'lntrust_ess ~ {x} + {rhs} + C(cntry_round)', dd).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.cntry)[0]})
        R[f'S2-2_{lab}_{x}'] = res(m, x, dd.lntrust_ess.std(), dd[x].std()); R[f'S2-2_{lab}_{x}']['origin_countries'] = int(dd.cntry.nunique())
eam = rd('Motifs_EA_groups.dta').set_index('atlas')
ear = rd('Ethnographic_Atlas_Regressions_Ready.dta', columns=['atlas', 'v33', 'v34', 'v98', 'continent_EA', 'lnyear_firstpub', 'lnnmbr_title', 'motifs_total', 'tricksters_punish']).set_index('atlas')
ed = prep(ear.join(unit_scores(eam), how='inner'), lambda d: d.motifs_total > 4)
R['EA_n'] = int(len(ed))
for x in ['ENDORSE', 'ENDORSE_noenemy', 'ENDORSE_rel']:
    for lab, rhs in [('base', ''), ('highgods', ' + C(v34)')]:
        dd = ed.dropna(subset=['v33', x, 'lnyear_firstpub', 'lnnmbr_title', 'v98', 'continent_EA'] + (['v34'] if lab == 'highgods' else []))
        m = smf.ols(f'v33 ~ {x} + lnyear_firstpub + lnnmbr_title + C(continent_EA){rhs}', dd).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.v98)[0]})
        R[f'S2-3_{lab}_{x}'] = res(m, x, dd.v33.std(), dd[x].std()); R[f'S2-3_{lab}_{x}']['families'] = int(dd.v98.nunique())
# ---- exploratory: language survival (Glottolog AES 1 not endangered .. 6 extinct), higher = worse ----
soc = pd.read_csv('/root/data/dplace-cldf/cldf/societies.csv'); soc = soc[soc.Contribution_ID == 'dplace-dataset-ea']
norm = lambda x: re.sub(r'[^A-Z]', '', str(x).upper())
names = {}
for r in soc.itertuples():
    gl = r.Language_Level_Glottocodes if isinstance(r.Language_Level_Glottocodes, str) and r.Language_Level_Glottocodes else r.Glottocode
    for n in [r.Name] + str(r.alt_names_by_society).split(';'): names.setdefault(norm(n), gl)
def glot(a):
    k = norm(a)
    if k in names: return names[k]
    hits = {v for n, v in names.items() if n.startswith(k)} if len(k) >= 6 else set()
    return hits.pop() if len(hits) == 1 else None
ed['glottocode'] = [glot(a) for a in ed.index]
v = pd.read_csv('/root/data/ext2/glottolog-cldf/cldf/values.csv', usecols=['Language_ID', 'Parameter_ID', 'Value'])
aes = v[v.Parameter_ID == 'aes'].set_index('Language_ID').Value.astype(float)
ed['aes'] = ed.glottocode.map(aes)
R['lang_matched'] = int(ed.glottocode.notna().sum()); R['lang_with_aes'] = int(ed.aes.notna().sum())
dd = ed.dropna(subset=['aes', 'ENDORSE', 'lnyear_firstpub', 'lnnmbr_title', 'v33', 'continent_EA', 'v98']).copy()
dd['aes_i'] = dd.aes.astype(int)
Xo = pd.get_dummies(dd[['ENDORSE', 'lnyear_firstpub', 'lnnmbr_title', 'v33', 'continent_EA']].astype({'continent_EA': str}), columns=['continent_EA'], drop_first=True).astype(float)
try:
    om = OrderedModel(dd.aes_i, Xo, distr='logit').fit(method='bfgs', disp=0, maxiter=2000, cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.v98)[0]})
    b, se = om.params['ENDORSE'], om.bse['ENDORSE']
    R['lang_survival_ordered_logit'] = dict(OR_more_endangered=float(np.exp(b)), lo95=float(np.exp(b - 1.96 * se)), hi95=float(np.exp(b + 1.96 * se)), p=float(om.pvalues['ENDORSE']), n=int(len(dd)), families=int(dd.v98.nunique()))
except Exception as e:
    R['lang_survival_ordered_logit'] = dict(note=f'failed: {e.__class__.__name__}')
m = smf.ols('aes ~ ENDORSE + lnyear_firstpub + lnnmbr_title + v33 + C(continent_EA)', dd).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.v98)[0]})
R['lang_survival_ols'] = res(m, 'ENDORSE', dd.aes.std(), dd.ENDORSE.std()); R['lang_aes_distribution'] = dd.aes_i.value_counts().sort_index().to_dict()
# ---- decisions ----
p1 = R['S2-1_lntrust_wvsavg_cont1_ENDORSE']; p2 = R['S2-2_cont1_ENDORSE']
ps = sorted([('S2-1', p1['p']), ('S2-2', p2['p'])], key=lambda t: t[1]); holm = {}; run = 0
for i, (k, p) in enumerate(ps): run = max(run, min(1, (2 - i) * p)); holm[k] = run
sup = p1['b'] > 0 and p2['b'] > 0 and holm['S2-1'] < 0.05 and holm['S2-2'] < 0.05
fal = (p1['std_lo90'] > -0.34 and p1['std_hi90'] < 0.34) and (p2['std_lo90'] > -0.03 and p2['std_hi90'] < 0.03)
OUT['results'] = R; OUT['holm'] = holm; OUT['decision'] = 'supported' if sup else ('falsified' if fal else 'inconclusive')
json.dump(OUT, open(S2 + 's2r_results.json', 'w'), indent=1, default=float)
for k, v in R.items(): print(k, v if not isinstance(v, dict) else {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()})
print('decision', OUT['decision'], holm)
