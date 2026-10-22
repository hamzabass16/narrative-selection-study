"""Added AFTER seeing h8_followup results (23 Oct 2026), so exploratory on top of exploratory:
(1) Fisher exact tests where a logit separated (zero cells); (2) test B restricted to crises the polity survived by more
than 10 years, to separate 'the removal crisis was the terminal crisis' from 'removal harms the polity afterwards'."""
import json, numpy as np, pandas as pd
from scipy import stats
exec(open('/root/analysis/h8/h8_followup.py').read().split('# ---------- A: what comes with removal')[0])
R2 = {}
for xv, c in [('removed', 'public_goods'), ('depose', 'public_goods'), ('assassination', 'public_goods'), ('assassination', 'century_plus'), ('removed', 'century_plus')]:
    d = cc.dropna(subset=[xv, c]); t = pd.crosstab(d[xv], d[c]).reindex(index=[0.0, 1.0], columns=[0.0, 1.0], fill_value=0)
    R2[f'fisher_{xv}_{c}'] = dict(table=t.values.tolist(), p=float(stats.fisher_exact(t.values)[1]))
exec(open('/root/analysis/h8/h8_followup.py').read().split('# ---------- B: fate of the polity after the crisis ----------')[1].split('# ---------- C:')[0].replace("R['", "R2['B_all_").replace("R2['B_all_E_", "R2['skipE_"))
R2['terminal_share'] = dict(removed=float((b[b.removed == 1].t <= 10).mean()), not_removed=float((b[b.removed == 0].t <= 10).mean()),
                            n_removed=int((b.removed == 1).sum()), n_not=int((b.removed == 0).sum()))
bs = b[b.t > 10].copy()
R2['B_survivors_cox_removed'] = cox(bs, ['removed', 'PolPop'] + ERA_X)
R2['B_survivors_internal_within100'] = logit(bs, 'int100', 'removed + PolPop', 'polity')
R2['B_survivors_median_years_to_end'] = dict(removed=float(bs[bs.removed == 1].t.median()), not_removed=float(bs[bs.removed == 0].t.median()))
R2['terminal_crisis_types'] = b[b.t <= 10].groupby(['removed', 'etype']).size().reset_index().values.tolist()
json.dump(R2, open('/root/analysis/h8/h8_followup_addendum_results.json', 'w'), indent=1, default=str)
for k, v in R2.items():
    if not k.startswith(('B_all', 'skipE')): print(k, json.dumps(v, default=str)[:500])
