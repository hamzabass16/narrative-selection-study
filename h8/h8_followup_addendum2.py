"""Added after seeing results (23 Oct 2026): a smaller successor polity after internal collapse is partly definitional
(fragmentation makes smaller polities), and SC_mean includes population, territory and capital size. This re-runs test D with
complexity built only from the six non-scale measures (hierarchy, government, infrastructure, writing, texts, money)."""
import json, numpy as np, pandas as pd, statsmodels.formula.api as smf
pol = pd.read_csv('/root/analysis/frame/polities_frame.csv', index_col=0)
cov = pd.read_csv('/root/analysis/study1/covariates.csv', index_col=0)
D = pd.read_csv('/root/analysis/h8/h8_followup_transitions.csv')
NS = ['Hierarchy', 'Government', 'Infrastructure', 'Writing', 'Texts', 'Money']
Z = (cov[NS] - cov[NS].mean()) / cov[NS].std()
sc = Z.mean(axis=1).where(cov[NS].notna().sum(axis=1) >= 4)
D['dSC_ns'] = D.succ.map(sc) - D.polity.map(sc)
D['dCap'] = D.succ.map(cov.CapPop) - D.polity.map(cov.CapPop)
R = {}
Dm = D[D.etype.isin(['internal', 'conquest', 'continuity'])].copy()
for y in ['dSC_ns', 'dCap']:
    d = Dm.dropna(subset=[y]); out = dict(means=d.groupby('etype')[y].mean().round(3).to_dict(), n=d.etype.value_counts().to_dict())
    for lab, extra in [('clustered', ''), ('nga_fe', ' + C(nga)')]:
        m = smf.ols(f"{y} ~ C(etype, Treatment('continuity')) + C(era){extra}", d).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.nga)[0]})
        for t in ['internal', 'conquest']:
            k = f"C(etype, Treatment('continuity'))[T.{t}]"
            out[f'{lab}_{t}'] = dict(coef=round(float(m.params[k]), 3), lo95=round(float(m.conf_int().loc[k, 0]), 3), hi95=round(float(m.conf_int().loc[k, 1]), 3), p=round(float(m.pvalues[k]), 4))
    R[y] = out
json.dump(R, open('/root/analysis/h8/h8_followup_addendum2_results.json', 'w'), indent=1)
print(json.dumps(R, indent=1))
