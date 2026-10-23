"""H10 (new, optional; approved retest plan): are narratives that reward cooperation retained and spread more than other motifs?
Written before it was run. Motif classes from the frozen endorsement codes (pilot motifs excluded): pro = motif score > 0.
(a) Breadth: number of distinct language families (EA v98) and of continents (EA continent_EA) among the 1,265 EA groups
    carrying the motif; Poisson GLM with HC1 errors on pro + C(chapter) + log(1 + description words); chapter = leading
    letters of Berezkin's motif id.
(b) Retention: on the three dated trees of H9b (Austronesian, Bantu, Indo-European), for every motif present at >= 3 and
    absent at >= 3 tips, a two-rate Mk model (gain, loss) is fitted; log loss rate regressed on pro + C(chapter) per tree
    (HC1), and the pro coefficients pooled by inverse variance.
Decision: supported if the breadth IRR (families) > 1 with p < 0.05 and the pooled retention coefficient < 0 with p < 0.05;
contradicted if either is significant in the opposite direction; otherwise inconclusive.
(c) Individual-level transmission experiments come from the H6 search (stratum T) and are reported descriptively."""
import sys, re, json, numpy as np, pandas as pd, statsmodels.formula.api as smf, statsmodels.api as sm
sys.path.insert(0, '/root/analysis/retest'); import phylo
P = pd.read_csv('/root/analysis/s2r/codes/motif_codes_primary.csv').set_index('motif_id'); P = P[~P.pilot]
red = pd.read_csv('/root/analysis/s2r/motifs_redacted.csv').set_index('motif_id')
P['words'] = red.description.fillna('').str.split().str.len().reindex(P.index).fillna(0)
P['chapter'] = [re.match(r'[a-z]+', m).group(0) for m in P.index]
P['pro'] = (P.score > 0).astype(int)
M = '/root/data/mx_folklore/'
eam = pd.read_stata(M + 'Motifs_EA_groups.dta', convert_categoricals=False).set_index('atlas')
ear = pd.read_stata(M + 'Ethnographic_Atlas_Regressions_Ready.dta', columns=['atlas', 'v98', 'continent_EA'], convert_categoricals=False).set_index('atlas')
inc = eam[[c for c in eam.columns if c in P.index]].fillna(0).astype(float).gt(0)
fam = ear.v98.reindex(inc.index); cont = ear.continent_EA.reindex(inc.index)
P['n_groups'] = inc.sum(0).reindex(P.index).fillna(0)
P['n_families'] = pd.Series({m: fam[inc[m]].nunique() for m in inc.columns}).reindex(P.index).fillna(0)
P['n_continents'] = pd.Series({m: cont[inc[m]].nunique() for m in inc.columns}).reindex(P.index).fillna(0)
OUT = {'motifs': int(len(P)), 'pro_motifs': int(P.pro.sum()), 'anti_motifs': int((P.score < 0).sum())}
for y in ['n_families', 'n_continents', 'n_groups']:
    m = smf.glm(f'{y} ~ pro + C(chapter) + np.log1p(words)', P, family=sm.families.Poisson()).fit(cov_type='HC1')
    OUT[f'breadth_{y}'] = dict(IRR=float(np.exp(m.params['pro'])), lo95=float(np.exp(m.conf_int().loc['pro', 0])), hi95=float(np.exp(m.conf_int().loc['pro', 1])), p=float(m.pvalues['pro']),
                               mean_pro=float(P.loc[P.pro == 1, y].mean()), mean_other=float(P.loc[P.pro == 0, y].mean()))
m = smf.glm('n_families ~ C(np.sign(score)) + C(chapter) + np.log1p(words)', P, family=sm.families.Poisson()).fit(cov_type='HC1')
OUT['breadth_families_by_sign'] = {k: float(np.exp(v)) for k, v in m.params.items() if 'sign' in k}
# glottocodes for EA groups (same rule as s2r_analysis)
soc = pd.read_csv('/root/data/dplace-cldf/cldf/societies.csv'); se = soc[soc.Contribution_ID == 'dplace-dataset-ea']
norm = lambda x: re.sub(r'[^A-Z]', '', str(x).upper()); names = {}
for r in se.itertuples():
    gl = r.Language_Level_Glottocodes if isinstance(r.Language_Level_Glottocodes, str) and r.Language_Level_Glottocodes else r.Glottocode
    for n in [r.Name] + str(r.alt_names_by_society).split(';'): names.setdefault(norm(n), gl)
def glot(a):
    k = norm(a)
    if k in names: return names[k]
    hits = {v for n, v in names.items() if n.startswith(k)} if len(k) >= 6 else set()
    return hits.pop() if len(hits) == 1 else None
g = pd.Series([glot(a) for a in inc.index], index=inc.index)
inc_g = inc[g.notna() & (eam.motifs_total.reindex(inc.index) > 4)].copy(); inc_g.index = g[inc_g.index]
inc_g = inc_g[~inc_g.index.duplicated()]
TREES = {'Austronesian': 'gray_et_al2009', 'Bantu': 'grollemund_et_al2015', 'Indo-European': 'bouckaert_et_al2012'}
QI = [(0, 1, 0), (1, 0, 1)]
coefs = []
for famname, tid in TREES.items():
    tr = phylo.Tree(tid, set(inc_g.index))
    X = inc_g.loc[tr.tips]
    rows = []
    for mo in P.index:
        if mo not in X.columns: continue
        v = X[mo].astype(int); npres = int(v.sum())
        if npres < 3 or len(v) - npres < 3: continue
        ll, r = phylo.fit_mk(tr, {t: int(v[t]) for t in tr.tips}, 2, QI, 2, starts=[(-1.0,), (1.0,)])
        rows.append(dict(motif=mo, gain=r[0], loss=r[1], present=npres))
    D = pd.DataFrame(rows).set_index('motif').join(P[['pro', 'chapter', 'score']])
    D['logloss'] = np.log(D.loss)
    m = smf.ols('logloss ~ pro + C(chapter)', D).fit(cov_type='HC1')
    coefs.append((m.params['pro'], m.bse['pro'] ** 2))
    OUT[f'retention_{famname}'] = dict(tips=len(tr.tips), motifs_fitted=int(len(D)), pro_fitted=int(D.pro.sum()), b_logloss_pro=float(m.params['pro']),
                                       se=float(m.bse['pro']), p=float(m.pvalues['pro']), median_loss_pro=float(D[D.pro == 1].loss.median()),
                                       median_loss_other=float(D[D.pro == 0].loss.median()), share_at_bounds=float(((D.loss < 1e-3) | (D.loss > 140)).mean()))
    print(famname, OUT[f'retention_{famname}'], flush=True)
w = np.array([1 / v for _, v in coefs]); b = np.array([c for c, _ in coefs])
bp = float((w * b).sum() / w.sum()); sep = float(np.sqrt(1 / w.sum()))
from scipy import stats
OUT['retention_pooled'] = dict(b_logloss_pro=bp, se=sep, p=float(2 * stats.norm.sf(abs(bp / sep))))
br = OUT['breadth_n_families']; rp = OUT['retention_pooled']
OUT['decision'] = ('supported' if br['IRR'] > 1 and br['p'] < 0.05 and rp['b_logloss_pro'] < 0 and rp['p'] < 0.05 else
                   ('contradicted' if (br['IRR'] < 1 and br['p'] < 0.05) or (rp['b_logloss_pro'] > 0 and rp['p'] < 0.05) else 'inconclusive'))
json.dump(OUT, open('/root/analysis/retest/h10_results.json', 'w'), indent=1, default=float)
print(json.dumps({k: OUT[k] for k in OUT if not k.startswith('retention_') or k == 'retention_pooled'}, indent=1, default=float))
