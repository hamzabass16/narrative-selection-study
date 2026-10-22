"""H8-3 as planned in Addendum 14.4 ('adjusted for population and era'). The 22 Oct script omitted log population from the
formula (coding slip, logged as a deviation). This adds it. Rows with missing population are dropped (complete case)."""
import json, numpy as np, pandas as pd, statsmodels.formula.api as smf
pol = pd.read_csv('/root/analysis/frame/polities_frame.csv', index_col=0)
cov = pd.read_csv('/root/analysis/study1/covariates.csv', index_col=0)
db = json.load(open('/root/analysis/seshat/seshat_current_2026-10-17.json'))
cc = pd.DataFrame(db['crisisdb/crisis-consequences']['rows'], columns=db['crisisdb/crisis-consequences']['cols'])
P = lambda s: s.map({'P': 1, 'IP': 1, 'A': 0, 'IA': 0})
for c in ['civil_war', 'extermination', 'collapse', 'depose', 'assassination']: cc[c] = P(cc[c])
cc['severity'] = cc[['civil_war', 'extermination', 'collapse']].sum(axis=1, min_count=2)
cc['removed'] = cc[['depose', 'assassination']].max(axis=1)
cc['MER'] = cc.polity.map(cov.MER); cc['MERb'] = (cc.MER >= 0.5).astype(float).where(cc.MER.notna())
cc['PolPop'] = cc.polity.map(cov.PolPop)
cc['year'] = pd.to_numeric(cc.year_from, errors='coerce').fillna(cc.polity.map(pol.start_year))
cc['era'] = pd.cut(cc.year, [-1e5, -500, 1500, 3000], labels=['pre500BCE', '500BCE_1500CE', 'post1500CE']).astype(str)
R = {}
for y in ['severity', 'removed']:
    dd = cc.dropna(subset=[y, 'MERb', 'PolPop']).copy(); dd = dd[dd.era != 'nan']
    g = pd.factorize(dd.polity)[0]; f = f'{y} ~ MERb + PolPop + C(era)'
    m = smf.ols(f, dd).fit(cov_type='cluster', cov_kwds={'groups': g}) if y == 'severity' else smf.logit(f, dd).fit(disp=0, cov_type='cluster', cov_kwds={'groups': g})
    lo, hi = m.conf_int().loc['MERb']
    R[y] = dict(coef=float(m.params['MERb']), lo95=float(lo), hi95=float(hi), p=float(m.pvalues['MERb']), n=int(m.nobs),
                n_MER0=int((dd.MERb == 0).sum()), polities=int(dd.polity.nunique()), PolPop_coef=float(m.params['PolPop']), PolPop_p=float(m.pvalues['PolPop']))
json.dump(R, open('/root/analysis/h8/h8_3_population_results.json', 'w'), indent=1)
print(json.dumps(R, indent=1))
