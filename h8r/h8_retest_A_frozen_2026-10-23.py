"""H8 retest, Part A: premodern conduct (approved retest plan). Written before it was run; estimates only.
Exposures (Seshat Equinox 2020, human-coded): CONSTR = mean of executive constraint by government, by non-government
actors, impeachment (>= 2 known); secondary: 'ideological thought equates rulers and commoners'. Both z-scored.
Outcomes and models:
 1. Polity hazards (frame polities with the exposure and a termination code): Cox, cause-specific internal collapse
    (T1a-c) and all non-continuous ends, era strata, errors clustered by NGA; Fine-Gray for internal collapse.
 2. Violent internal end among ended or continued polities: logit internal collapse (1) versus continuity T0 (0), era terms.
 3. CrisisDB crises in these polities: ruler deposed or assassinated; civil war; severity count. Logit / Poisson with era
    terms, errors clustered by polity.
 4. Ruler transitions (Seshat CrisisDB power transitions, SeshatDatasetAnalysis power_transitions.xlsx): irregular = any of
    overturn, predecessor assassination, military revolt, popular uprising coded >= 0.9; regular if all <= 0.1; else missing.
    Logit with era terms, errors clustered by polity; and log tenure (duration + 1) by OLS.
Prediction (Section 2 model): constraint does not lengthen polity life but lowers internal collapse and violent ends."""
import sys, json, warnings, numpy as np, pandas as pd, statsmodels.formula.api as smf, statsmodels.api as sm
from scipy import stats
warnings.filterwarnings('ignore')
sys.path.insert(0, '/root/analysis/retest'); sys.path.insert(0, '/root/analysis/study1')
import s1r_data as D, coxlib
f = D.frame()
z = lambda s: (s - s.mean()) / s.std()
R = {}
for expo in ['CONSTR', 'rulers_eq_commoners']:
    S = f[f[expo].notna() & f.ev_any.notna()].copy(); S['X'] = z(S[expo])
    S['era'] = pd.cut(S.start_year, [-1e5, -500, 1500, 3000], labels=[0, 1, 2]).astype(int)
    dur = (S.end_year - S.start_year).clip(lower=1).values
    out = dict(polities=int(len(S)), events=int(S.ev_any.sum()), internal=int((S.cause == 1).sum()), conquest=int((S.cause == 2).sum()))
    for lab, ev in [('all_ends', S.ev_any.values.astype(int)), ('internal', (S.cause == 1).astype(int).values)]:
        r = coxlib.fit(np.zeros(len(S)), dur, ev, S[['X']].values, strata=S.era.values, cluster=S.nga_name.values)
        out[f'cox_{lab}'] = dict(HR=float(np.exp(r['beta'][0])), lo95=float(np.exp(r['beta'][0] - 1.96 * r['se'][0])), hi95=float(np.exp(r['beta'][0] + 1.96 * r['se'][0])),
                                 p=float(2 * stats.norm.sf(abs(r['beta'][0] / r['se'][0]))))
    st = np.where(S.ev_any == 1, np.where(S.cause == 1, 1, 2), 0)
    a0, a1, e_, Xe, we, cle = coxlib.finegray_expand(dur, st, 1, S[['X']].values, S.nga_name.values)
    r = coxlib.fit(a0, a1, e_, Xe, w=we, cluster=cle)
    out['finegray_internal'] = dict(SHR=float(np.exp(r['beta'][0])), lo95=float(np.exp(r['beta'][0] - 1.96 * r['se'][0])), hi95=float(np.exp(r['beta'][0] + 1.96 * r['se'][0])),
                                    p=float(2 * stats.norm.sf(abs(r['beta'][0] / r['se'][0]))))
    L = S[S.Q2.isin(['T1a', 'T1b', 'T1c', 'T0'])].copy(); L['y'] = L.Q2.isin(['T1a', 'T1b', 'T1c']).astype(float)
    try:
        m = smf.logit('y ~ X + C(era)', L).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(L.nga_name)[0]})
        out['internal_vs_continuity_logit'] = dict(OR=float(np.exp(m.params['X'])), lo95=float(np.exp(m.conf_int().loc['X', 0])), hi95=float(np.exp(m.conf_int().loc['X', 1])), p=float(m.pvalues['X']), n=int(m.nobs), events=int(L.y.sum()))
    except Exception as ex:
        out['internal_vs_continuity_logit'] = dict(note=str(ex)[:80])
    # crises
    db = json.load(open('/root/analysis/seshat/seshat_current_2026-10-17.json'))['crisisdb/crisis-consequences']
    cc = pd.DataFrame(db['rows'], columns=db['cols'])
    B01 = lambda s: s.map({'P': 1.0, 'IP': 1.0, 'A': 0.0, 'IA': 0.0})
    for c in ['civil_war', 'extermination', 'collapse', 'fragmentation', 'depose', 'assassination']: cc[c] = B01(cc[c])
    cc = cc[cc.polity.isin(S.id)].copy(); cc['X'] = cc.polity.map(S.set_index('id').X)
    cc['y0'] = pd.to_numeric(cc.year_from, errors='coerce'); cc['era'] = pd.cut(cc.y0, [-1e5, -500, 1500, 3000], labels=[0, 1, 2]).astype(float)
    cc['removed'] = cc[['depose', 'assassination']].max(axis=1); cc['severity'] = cc[['civil_war', 'extermination', 'collapse', 'fragmentation']].sum(axis=1, min_count=1)
    for y in ['removed', 'civil_war', 'severity']:
        d = cc.dropna(subset=[y, 'X', 'era'])
        try:
            if y == 'severity':
                m = smf.glm(f'{y} ~ X + C(era)', d, family=sm.families.Poisson()).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.polity)[0]})
            else:
                m = smf.logit(f'{y} ~ X + C(era)', d).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(d.polity)[0]})
            out[f'crisis_{y}'] = dict(ratio=float(np.exp(m.params['X'])), lo95=float(np.exp(m.conf_int().loc['X', 0])), hi95=float(np.exp(m.conf_int().loc['X', 1])), p=float(m.pvalues['X']), n=int(m.nobs), polities=int(d.polity.nunique()))
        except Exception as ex:
            out[f'crisis_{y}'] = dict(note=str(ex)[:80], n=int(len(d)))
    # ruler transitions
    pt = pd.read_excel('/root/data/seshat_polaris/SeshatDatasetAnalysis/test_scripts/power_transitions.xlsx', sheet_name='Raw',
                       usecols=['PolityName', 'Year', 'overturn', 'predecessor_assassination', 'military_revolt', 'popular_uprising', 'duration'])
    V = pt[['overturn', 'predecessor_assassination', 'military_revolt', 'popular_uprising']]
    pt['irregular'] = np.where((V >= 0.9).any(axis=1), 1.0, np.where((V <= 0.1).all(axis=1) & V.notna().all(axis=1), 0.0, np.nan))
    pt = pt[pt.PolityName.isin(S.name)].copy(); pt['X'] = pt.PolityName.map(S.set_index('name').X)
    pt['era'] = pd.cut(pt.Year, [-1e5, -500, 1500, 3000], labels=[0, 1, 2]).astype(float)
    d = pt.dropna(subset=['irregular', 'X', 'era'])
    m = smf.logit('irregular ~ X + C(era)', d).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(d.PolityName)[0]})
    q = d.X.quantile([.25, .75]).values
    out['transition_irregular'] = dict(OR=float(np.exp(m.params['X'])), lo95=float(np.exp(m.conf_int().loc['X', 0])), hi95=float(np.exp(m.conf_int().loc['X', 1])), p=float(m.pvalues['X']),
                                       n=int(m.nobs), polities=int(d.PolityName.nunique()), share_irregular=float(d.irregular.mean()),
                                       share_bottomQ=float(d[d.X <= q[0]].irregular.mean()), share_topQ=float(d[d.X >= q[1]].irregular.mean()))
    d = pt.dropna(subset=['duration', 'X', 'era']); d['ltenure'] = np.log1p(d.duration)
    m = smf.ols('ltenure ~ X + C(era)', d).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.PolityName)[0]})
    out['transition_log_tenure'] = dict(b=float(m.params['X']), lo95=float(m.conf_int().loc['X', 0]), hi95=float(m.conf_int().loc['X', 1]), p=float(m.pvalues['X']), n=int(m.nobs))
    R[expo] = out
    print(expo, json.dumps(out, default=float)[:1500], flush=True)
json.dump(R, open('/root/analysis/h8r/h8_retest_A_results.json', 'w'), indent=1, default=float)
