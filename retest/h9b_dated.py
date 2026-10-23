"""H9b strengthened (approved retest plan): D statistic on dated trees and Pagel's (1994) correlated-evolution test of
moralizing high god (EA034 = 4) and political hierarchy (EA033 >= 3, i.e. at least two levels above the local community).
Trees: gray_et_al2009 (Austronesian), grollemund_et_al2015 (Bantu), bouckaert_et_al2012 (Indo-European); other trees with
>= 30 coded societies belong to the same families and are not used (one tree per family).
Language-level traits: a language has the trait if at least half its EA societies do (as in the first run).
States for the joint model: 0 = (no hierarchy, no MHG), 1 = (no hierarchy, MHG), 2 = (hierarchy, no MHG), 3 = (hierarchy, MHG).
Independent model: 4 rates (hierarchy gain/loss, MHG gain/loss). Dependent model: 8 rates. LR test df 4 per tree; pooled by
summing statistics over trees (df 12). Decision (fixed here): order supported if the pooled LR test rejects independence
(p < 0.05) and, in the dependent fits, the MHG gain rate with hierarchy exceeds the gain rate without it (q23 > q01) on
every tree; contradicted if q23 < q01 on every tree with the pooled test significant; otherwise inconclusive.
Fitting checked by simulation (recovering known rates on the Austronesian tree) before the real fit."""
import sys, json, numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, '/root/analysis/retest'); import phylo
C = '/root/data/dplace-cldf/cldf/'
soc = pd.read_csv(C + 'societies.csv'); dat = pd.read_csv(C + 'data.csv', low_memory=False)
sel = dat[dat.Var_ID.isin(['EA034', 'EA033'])].copy(); sel['code'] = pd.to_numeric(sel.Code_ID.astype(str).str.split('-').str[-1], errors='coerce')
ea = sel.pivot_table(index='Soc_ID', columns='Var_ID', values='code', aggfunc='first').dropna()
ea = ea.join(soc.set_index('ID')[['Language_Level_Glottocodes']])
ea['mhg'] = (ea.EA034 == 4).astype(float); ea['hier'] = (ea.EA033 >= 3).astype(float)
lang = ea.groupby('Language_Level_Glottocodes')[['mhg', 'hier']].mean().ge(0.5).astype(int)
TREES = {'Austronesian': 'gray_et_al2009', 'Bantu': 'grollemund_et_al2015', 'Indo-European': 'bouckaert_et_al2012'}
IND = [(0, 1, 0), (1, 0, 1), (2, 3, 0), (3, 2, 1), (0, 2, 2), (2, 0, 3), (1, 3, 2), (3, 1, 3)]  # MHG gain a, loss b; hier gain c, loss d
DEP = [(0, 1, 0), (1, 0, 1), (2, 3, 2), (3, 2, 3), (0, 2, 4), (2, 0, 5), (1, 3, 6), (3, 1, 7)]
names = ['q01_mhg_gain_nohier', 'q10_mhg_loss_nohier', 'q23_mhg_gain_hier', 'q32_mhg_loss_hier', 'q02_hier_gain_nomhg', 'q20_hier_loss_nomhg', 'q13_hier_gain_mhg', 'q31_hier_loss_mhg']
starts = [(-1.0,), (0.5,), (-3.0,)]
OUT = {}
if '--simcheck' in sys.argv:
    tr = phylo.Tree(TREES['Austronesian'], set(lang.index))
    rng = np.random.default_rng(1); true = np.array([0.5, 2.0, 3.0, 0.5, 1.0, 1.0, 1.0, 1.0])
    Q = np.zeros((4, 4))
    for i, j, p in DEP: Q[i, j] = true[p]
    np.fill_diagonal(Q, -Q.sum(1)); from scipy.linalg import expm
    st = np.zeros(len(tr.nodes), int); st[tr.root] = rng.integers(4)
    for i in reversed(range(len(tr.nodes))):
        if tr.parent[i] >= 0: st[i] = rng.choice(4, p=expm(Q * tr.blen[i])[st[tr.parent[i]]])
    ts = {tr.tips[k]: int(st[i]) for k, i in enumerate(tr.leaves)}
    ll, est = phylo.fit_mk(tr, ts, 4, DEP, 8, starts=starts)
    print('true', true.round(2), 'est', est.round(2), 'tips', len(ts)); sys.exit()
pooled_lr = 0.0; dfp = 0
for fam, tid in TREES.items():
    tr = phylo.Tree(tid, set(lang.index))
    tl = lang.loc[tr.tips]
    ts = {g: int(2 * r.hier + r.mhg) for g, r in tl.iterrows()}
    D_m = phylo.D_stat(tr, {g: int(v) for g, v in tl.mhg.items()}) if 0 < tl.mhg.mean() < 1 else dict(note='no variation', prevalence=float(tl.mhg.mean()))
    D_h = phylo.D_stat(tr, {g: int(v) for g, v in tl.hier.items()}) if 0 < tl.hier.mean() < 1 else dict(note='no variation', prevalence=float(tl.hier.mean()))
    li, ri = phylo.fit_mk(tr, ts, 4, IND, 4, starts=starts)
    ld, rd_ = phylo.fit_mk(tr, ts, 4, DEP, 8, starts=starts)
    lr = max(0.0, 2 * (ld - li)); pooled_lr += lr; dfp += 4
    OUT[fam] = dict(tree=tid, tips=len(ts), mhg_prevalence=float(tl.mhg.mean()), hier_prevalence=float(tl.hier.mean()),
                    state_counts={k: int(v) for k, v in pd.Series(list(ts.values())).value_counts().sort_index().items()},
                    D_mhg=D_m, D_hier=D_h, loglik_independent=li, loglik_dependent=ld, LR=lr, p=float(stats.chi2.sf(lr, 4)),
                    rates_dependent=dict(zip(names, map(float, rd_))), rates_independent=dict(zip(['mhg_gain', 'mhg_loss', 'hier_gain', 'hier_loss'], map(float, ri))))
    print(fam, json.dumps(OUT[fam], default=float)[:600], flush=True)
OUT['pooled'] = dict(LR=pooled_lr, df=dfp, p=float(stats.chi2.sf(pooled_lr, dfp)))
up = [OUT[f]['rates_dependent']['q23_mhg_gain_hier'] > OUT[f]['rates_dependent']['q01_mhg_gain_nohier'] for f in TREES]
OUT['decision'] = ('order supported' if OUT['pooled']['p'] < 0.05 and all(up) else
                   ('contradicted' if OUT['pooled']['p'] < 0.05 and not any(up) else 'inconclusive'))
json.dump(OUT, open('/root/analysis/retest/h9b_dated_results.json', 'w'), indent=1, default=float)
print(json.dumps({k: OUT[k] for k in ['pooled', 'decision']}, indent=1))
