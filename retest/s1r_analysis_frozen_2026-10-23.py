"""Study 1 retest: H1, H2, H3, H4a, H4b*, H5, H7 (approved plan 'FROZEN 2026-10-23 Retest Plan (approved)', Sections 4-5).
Written in full, debugged only on simulated outcomes (--simulate), and hashed before its first run on real outcomes.

Fixed rules (beyond the plan text):
- Exposure EPI (polity level), z-scored over the H1 analysis sample. Sample: polities with EPI, a termination code or
  censoring at the present, and a known event status (T9 with unknown Q3 dropped).
- Discrete-time complementary log-log hazard on polity-centuries, offset log(L/100); age terms C(agecat) with categories
  0, 1, 2, 3+ centuries; calendar era bins of the interval midpoint: <-1000, -1000..0, 0..1000, 1000..1500, >1500
  (a bin without events in the estimation sample is merged with the next later bin, the last with the one before).
- Region fixed effects: home NGA; NGAs without any event in the estimation sample are dropped (they carry no
  within-region information). Tradition companion: first listed primary tradition ('none' if none) as fixed effects
  instead of NGA, traditions without events dropped, errors clustered by NGA.
- Inference: estimates pooled over M = 20 draws (Seshat sampling plus imputation) by Rubin's rules with cluster-robust
  (NGA) variances. Decision p-value = median over draws of the wild cluster score-bootstrap p (Webb weights, null imposed,
  B = 9999). Holm over the seven Study 1 hypotheses on these p-values.
- H2 controls (sampled at interval start): Miltech, Iron, Cavalry, Pop, Terr, Cap (log10 scales as in Seshat), PC1, writing;
  plus Agri if /root/data/ext2/seshat_agri.csv exists (not available at freezing; see log).
- H4a: cause-specific discrete-time models (internal; conquest), H2 specification; Fine-Gray on polity level (polity means
  of the draw's controls) as secondary.
- H4b*: CrisisDB crises in sample polities; survival = no non-continuous termination with database end <= 50 years after
  crisis onset; controls Pop and PC1 sampled at the onset year, era; logit with errors clustered by polity.
- H5: H2 model plus MSP (sampled), moralizing high god, moral concern is primary; joint Wald test of the vessel terms.
- H7: H2 model with EPI x era3 (interval midpoint: <-500, -500..1500, >1500); 2-df interaction Wald test.
- H3: region-century panel at century midpoints; governing polity = frame polity of that home NGA covering the year, the one
  with known EPI, then the larger sampled territory, then the earlier start. Standardized variables, NGA fixed effects and
  era bins, errors clustered by NGA, wild cluster bootstrap-t (B = 4999)."""
import sys, json, warnings, argparse
import numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import stats
warnings.filterwarnings('ignore')
sys.path.insert(0, '/root/analysis/retest'); sys.path.insert(0, '/root/analysis/study1')
import s1r_data as D, coxlib
ap = argparse.ArgumentParser(); ap.add_argument('--simulate', action='store_true'); ap.add_argument('--M', type=int, default=20)
ap.add_argument('--B', type=int, default=9999); args = ap.parse_args()
M = args.M; OUT = {'simulated': bool(args.simulate), 'M': M}
EQ_LO, EQ_HI = 0.90, 1.11

f = D.frame()
if args.simulate:  # debugging only: outcomes replaced by noise unrelated to any exposure
    rng = np.random.default_rng(7); f['ev_any'] = rng.binomial(1, 0.5, len(f)).astype(float)
    f['cause'] = np.where(f.ev_any == 1, rng.choice([1, 2, 3], len(f), p=[.3, .6, .1]), 0)
S = f[f.EPI.notna() & f.ev_any.notna()].copy()
S['EPIz'] = (S.EPI - S.EPI.mean()) / S.EPI.std()
OUT['sample'] = dict(polities=int(len(S)), events=int(S.ev_any.sum()), internal=int((S.cause == 1).sum()), conquest=int((S.cause == 2).sum()),
                     other=int((S.cause == 3).sum()), unknown_type=int((S.cause == 9).sum()), ngas=int(S.nga_name.nunique()),
                     no_tradition=int((S.trad == 'none').sum()), EPI_mean=float(S.EPI.mean()), EPI_sd=float(S.EPI.std()))
iv = D.intervals(S).merge(S[['id', 'EPIz', 'trad', 'mhg', 'moral_concern_primary']], on='id')
iv['agecat'] = iv.k.clip(upper=3)
iv['era3'] = pd.cut(iv['mid'], [-1e5, -500, 1500, 3000], labels=['e1', 'e2', 'e3']).astype(str)
def erabin(df, col='mid'):
    edges = [-1e5, -1000, 0, 1000, 1500, 3000]; lab = pd.cut(df[col], edges, labels=False).astype(int)
    ev = df.groupby(lab).ev.sum().reindex(range(5), fill_value=0)
    mp = {}; groups = []; cur = []
    for b in range(5):
        cur.append(b)
        if ev[cur].sum() > 0: groups.append(cur); cur = []
    if cur:
        if groups: groups[-1] += cur
        else: groups.append(cur)
    for gi, gg in enumerate(groups):
        for b in gg: mp[b] = gi
    return lab.map(mp).astype(str)

# ---------- draws: sampling + imputation ----------
CTRL = ['Miltech', 'Iron', 'Cavalry', 'Pop', 'Terr', 'Cap', 'PC1', 'writing']
cc = None
import json as _j
db = _j.load(open('/root/analysis/seshat/seshat_current_2026-10-17.json'))
cc = pd.DataFrame(db['crisisdb/crisis-consequences']['rows'], columns=db['crisisdb/crisis-consequences']['cols'])
B01 = lambda s: s.map({'P': 1.0, 'IP': 1.0, 'A': 0.0, 'IA': 0.0})
for c in ['civil_war', 'extermination', 'collapse', 'fragmentation', 'public_goods', 'constitution', 'depose', 'assassination']: cc[c] = B01(cc[c])
cc['y0'] = pd.to_numeric(cc.year_from, errors='coerce')
cc = cc[cc.y0.notna() & cc.polity.isin(S.id)].copy()
pmeta = S.set_index('id')
cc['y0c'] = [min(max(y, pmeta.at[p, 'start_year']), pmeta.at[p, 'end_year']) for p, y in zip(cc.polity, cc.y0)]
# region-century panel points (H3): all frame polities with EPI (no outcome needed)
FE = f[f.EPI.notna()].copy(); FE['EPIraw'] = FE.EPI
allp = f[['id', 'name', 'nga_name', 'start_year', 'end_year', 'EPI']].copy()
rc_rows = []
for g, gp in allp.groupby('nga_name'):
    lo, hi = gp.start_year.min(), gp.end_year.max()
    for t in np.arange(lo + 50, hi, 100):
        cov = gp[(gp.start_year <= t) & (gp.end_year > t)]
        for r in cov.itertuples(): rc_rows.append(dict(nga=g, t=t, id=r.id, name=r.name, EPI=r.EPI))
rc = pd.DataFrame(rc_rows)

pts_iv = iv[['id', 'name', 'nga', 'a']].rename(columns={'a': 'year'})
pts_cc = pd.DataFrame({'id': cc.polity.values, 'name': cc.polity.map(pmeta.name).values, 'nga': cc.polity.map(pmeta.nga_name).values, 'year': cc.y0c.values})
pts_rc = rc[['id', 'name', 'nga', 't']].rename(columns={'t': 'year'})
pts = pd.concat([pts_iv.assign(src='iv'), pts_cc.assign(src='cc'), pts_rc.assign(src='rc')], ignore_index=True)

agri_path = '/root/data/ext2/seshat_agri.csv'
import os
HAVE_AGRI = os.path.exists(agri_path); OUT['agri_available'] = HAVE_AGRI
if HAVE_AGRI:
    CTRL = CTRL + ['Agri']

def draw(m):
    smp = D.sample(pts[['id', 'name', 'nga', 'year']], m)
    smp['src'] = pts.src.values
    smp = D.clio_terr(smp)  # within-polity territory change from Cliopatria where Seshat has none
    if HAVE_AGRI:
        ag = pd.read_csv(agri_path)  # columns: nga, year, Agri
        smp['cent'] = (np.floor(smp.year / 100) * 100)
        ag['cent'] = np.floor(ag.year / 100) * 100
        smp = smp.merge(ag[['nga', 'cent', 'Agri']], on=['nga', 'cent'], how='left')
    imp_cols = D.CC8 + D.WAR + ['MSP', 'writing'] + (['Agri'] if HAVE_AGRI else [])
    smp['yr'] = smp.year / 1000.0
    smp = D.impute(smp, imp_cols, ['yr'], m)
    smp, load, share = D.add_pc1(smp)
    return smp, load, share

def fit_glm(df, rhs, fe, cluster, offset=True):
    d = df.copy()
    d['eb'] = erabin(d)
    if fe:
        keep = d.groupby(fe).ev.transform('sum') > 0; d = d[keep]
    f_ = 'ev ~ ' + rhs + ' + C(agecat) + C(eb)' + (f' + C({fe})' if fe else '')
    fam = sm.families.Binomial(link=sm.families.links.CLogLog())
    mod = smf.glm(f_, d, family=fam, offset=np.log(d.L) if offset else None)
    # IRLS for the cloglog model is started from the Poisson (piecewise-exponential) estimates; default starts can diverge
    st = sm.GLM(mod.endog, mod.exog, family=sm.families.Poisson(), offset=mod.offset).fit().params
    res = mod.fit(start_params=np.asarray(st), cov_type='cluster', cov_kwds={'groups': pd.factorize(d[cluster])[0]})
    return mod, res, d

def boot_p(mod, res, term, d, cluster, B):
    k = list(res.params.index).index(term)
    # restricted fit: same design with the term's coefficient fixed at 0
    X = mod.exog; y = mod.endog; off = mod.offset
    Xr = np.delete(X, k, axis=1)
    st = sm.GLM(y, Xr, family=sm.families.Poisson(), offset=off).fit().params
    rr = sm.GLM(y, Xr, family=mod.family, offset=off).fit(start_params=np.asarray(st))
    pr = np.insert(rr.params, k, 0.0)
    return D.wild_score_boot_glm(mod, pr, k, d[cluster].values, B=B, seed=11)[0]

def collect(rows, term):
    b = [r['b'][term] for r in rows]; v = [r['V'][term] for r in rows]
    q, T = D.rubin(b, v); se = np.sqrt(T)
    ps = [r['p'][term] for r in rows if term in r.get('p', {})]
    return dict(HR=float(np.exp(q)), lo95=float(np.exp(q - 1.96 * se)), hi95=float(np.exp(q + 1.96 * se)),
                lo90=float(np.exp(q - 1.645 * se)), hi90=float(np.exp(q + 1.645 * se)), p_cluster=float(2 * stats.norm.sf(abs(q / se))),
                p_boot_median=float(np.median(ps)) if ps else None, logHR=float(q), se=float(se))

rows = {k: [] for k in ['H1', 'H1_trad', 'H1_noFE', 'H2', 'H2_between', 'H4a_int', 'H4a_conq', 'H5', 'H7', 'H5_vessel']}
H7rows = []; H5joint = []; FG = {'int': [], 'conq': []}; H4b = {k: [] for k in ['survive', 'severity', 'reform', 'removed']}
H3rows = {'fwd': [], 'rev': [], 'turchin': []}; H3es = []; within_share = {}; pcinfo = []
for m in range(M):
    smp, load, share = draw(m); pcinfo.append((load, share))
    sv = smp[smp.src == 'iv'].reset_index(drop=True)
    d = iv.reset_index(drop=True).copy()
    for c in CTRL + ['MSP']: d[c] = sv[c].values
    if m == 0:
        within_share = {c: float(d.groupby('id')[c].nunique().gt(1).mean()) for c in ['Pop', 'Terr', 'Cap', 'Miltech', 'PC1']}
        within_share['terr_source_counts'] = smp[smp.src == 'iv'].terr_src.value_counts().to_dict()
    ctrl = ' + '.join(CTRL)
    def run(key, rhs, fe, terms, dd=d, boot_term='EPIz'):
        mod, res, dfit = fit_glm(dd, rhs, fe, 'nga')
        r = dict(b={t: res.params[t] for t in terms}, V={t: res.cov_params().loc[t, t] for t in terms}, p={})
        if boot_term:
            r['p'][boot_term] = boot_p(mod, res, boot_term, dfit, 'nga', args.B)
        r['n'] = int(dfit.shape[0]); r['events'] = int(dfit.ev.sum()); r['ngas'] = int(dfit.nga.nunique())
        rows[key].append(r); return mod, res, dfit
    run('H1', 'EPIz', 'nga', ['EPIz'])
    run('H1_trad', 'EPIz', 'trad', ['EPIz'])
    run('H1_noFE', 'EPIz', None, ['EPIz'])
    run('H2', 'EPIz + ' + ctrl, 'nga', ['EPIz'])
    run('H2_between', 'EPIz + ' + ctrl, None, ['EPIz'])
    for key, cz in [('H4a_int', 1), ('H4a_conq', 2)]:
        dd = d.copy(); dd['ev'] = (dd.cause == cz).astype(float)
        run(key, 'EPIz + ' + ctrl, 'nga', ['EPIz'], dd=dd)
    mod, res, dfit = run('H5', 'EPIz + ' + ctrl + ' + MSP + mhg + moral_concern_primary', 'nga', ['EPIz', 'MSP', 'mhg', 'moral_concern_primary'],
                         dd=D.impute(d, ['mhg', 'moral_concern_primary'], ['EPIz', 'Pop', 'PC1', 'MSP'], m))
    vt = ['MSP', 'mhg', 'moral_concern_primary']
    H5joint.append((res.params[vt].values, res.cov_params().loc[vt, vt].values))
    # H7
    d7 = d.copy()
    for e in ['e2', 'e3']: d7[f'EPIx{e}'] = d7.EPIz * (d7.era3 == e)
    mod7, res7, dfit7 = fit_glm(d7, 'EPIz + EPIxe2 + EPIxe3 + ' + ctrl, 'nga', 'nga')
    tt = ['EPIz', 'EPIxe2', 'EPIxe3']
    H7rows.append((res7.params[tt].values, res7.cov_params().loc[tt, tt].values, int(dfit7.groupby('era3').ev.sum().get('e1', 0)),
                   int(dfit7.groupby('era3').ev.sum().get('e2', 0)), int(dfit7.groupby('era3').ev.sum().get('e3', 0))))
    # Fine-Gray (polity level)
    pl = d.groupby('id').agg(t=('b', 'max'), s=('a', 'min'), **{c: (c, 'mean') for c in CTRL}).join(S.set_index('id')[['EPIz', 'ev_any', 'cause', 'nga_name']])
    pl['dur'] = (pl.t - pl.s).clip(lower=1)
    for key, cz in [('int', 1), ('conq', 2)]:
        st = np.where(pl.ev_any == 1, np.where(pl.cause == cz, 1, 2), 0)
        Xp = pl[['EPIz'] + CTRL].values
        a0, a1, e_, Xe, we, cle = coxlib.finegray_expand(pl.dur.values, st, 1, Xp, pl.nga_name.values)
        fr = coxlib.fit(a0, a1, e_, Xe, w=we, cluster=cle)
        FG[key].append((fr['beta'][0], fr['se'][0] ** 2))
    # H4b*
    sc = smp[smp.src == 'cc'].reset_index(drop=True)
    c2 = cc.reset_index(drop=True).copy(); c2['Pop'] = sc.Pop.values; c2['PC1'] = sc.PC1.values
    c2['EPIz'] = c2.polity.map(S.set_index('id').EPIz)
    ev_ = c2.polity.map(S.set_index('id').ev_any); end_ = c2.polity.map(S.set_index('id').end_year)
    c2['survive'] = np.where(ev_.isna(), np.nan, np.where((ev_ == 1) & ((end_ - c2.y0) <= 50), 0.0, 1.0))
    c2['severity'] = c2[['civil_war', 'extermination', 'collapse', 'fragmentation']].sum(axis=1, min_count=1)
    c2['reform'] = c2[['public_goods', 'constitution']].max(axis=1)
    c2['removed'] = c2[['depose', 'assassination']].max(axis=1)
    c2['era3'] = pd.cut(c2.y0, [-1e5, -500, 1500, 3000], labels=['e1', 'e2', 'e3']).astype(str)
    for y in H4b:
        dd = c2.dropna(subset=[y, 'EPIz', 'Pop', 'PC1'])
        try:
            if y == 'severity':
                r_ = smf.glm(f'{y} ~ EPIz + Pop + PC1 + C(era3)', dd, family=sm.families.Poisson()).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.polity)[0]})
            else:
                r_ = smf.logit(f'{y} ~ EPIz + Pop + PC1 + C(era3)', dd).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.polity)[0]})
            H4b[y].append((r_.params['EPIz'], r_.cov_params().loc['EPIz', 'EPIz'], int(len(dd)), float(dd[y].mean())))
        except Exception as ex_:
            H4b[y].append((np.nan, np.nan, int(len(dd)), float(dd[y].mean()) if len(dd) else np.nan))
    # H3: region-century panel
    sr = smp[smp.src == 'rc'].reset_index(drop=True)
    r3 = rc.reset_index(drop=True).copy()
    for c in ['PC1', 'Miltech', 'Terr'] + (['Agri'] if HAVE_AGRI else []): r3[c] = sr[c].values
    r3['hasEPI'] = r3.EPI.notna().astype(int)
    r3 = r3.sort_values(['nga', 't', 'hasEPI', 'Terr'], ascending=[True, True, False, False]).drop_duplicates(['nga', 't'])
    r3 = r3.sort_values(['nga', 't'])
    for c in ['PC1', 'EPI', 'Miltech'] + (['Agri'] if HAVE_AGRI else []):
        r3[c + '_n'] = r3.groupby('nga')[c].shift(-1)
    r3['next_t'] = r3.groupby('nga').t.shift(-1)
    r3 = r3[r3.next_t == r3.t + 100]
    zc = ['PC1', 'EPI', 'Miltech'] + (['Agri'] if HAVE_AGRI else [])
    for c in zc:
        mu, sd = r3[c].mean(), r3[c].std(); r3[c + 'z'] = (r3[c] - mu) / sd; r3[c + '_nz'] = (r3[c + '_n'] - mu) / sd
    r3['eb'] = pd.cut(r3.t, [-1e5, -1000, 0, 1000, 1500, 3000], labels=False).astype(str)
    q = r3.dropna(subset=['PC1z', 'EPIz', 'Miltechz', 'PC1_nz', 'EPI_nz'])
    extra = ' + Agriz' if HAVE_AGRI else ''
    for key, ydep, xk in [('fwd', 'PC1_nz', 'EPIz'), ('rev', 'EPI_nz', 'PC1z')]:
        rhs = f'PC1z + EPIz + Miltechz{extra} + C(eb) + C(nga)'
        mm = smf.ols(f'{ydep} ~ {rhs}', q).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(q.nga)[0]})
        Xm = mm.model.exog; kk = list(mm.params.index).index(xk)
        pb, _ = D.wild_boot_ols(mm.model.endog, Xm, kk, q.nga.values, B=4999 if args.B > 999 else 199, seed=5)
        H3rows[key].append((mm.params[xk], mm.cov_params().loc[xk, xk], pb, int(len(q)), int(q.nga.nunique())))
    q2 = q.copy(); q2['dPC1'] = q2.PC1_nz - q2.PC1z
    mt = smf.ols(f'dPC1 ~ PC1z + Miltechz{extra} + EPIz + C(eb) + C(nga)', q2).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(q2.nga)[0]})
    H3rows['turchin'].append((mt.params['EPIz'], mt.cov_params().loc['EPIz', 'EPIz']))
    if m == 0:  # event study on draw 0 (descriptive)
        ev3 = r3.copy(); T0 = {}
        for g, gp in ev3.groupby('nga'):
            gp = gp.sort_values('t'); seen_low = False
            for r in gp.itertuples():
                if pd.notna(r.EPI) and r.EPI < 2 / 3: seen_low = True
                if seen_low and pd.notna(r.EPI) and r.EPI >= 2 / 3: T0[g] = r.t; break
        ev3['rel'] = ev3.apply(lambda r: (r.t - T0[r.nga]) / 100 if r.nga in T0 else np.nan, axis=1)
        for k_ in range(-5, 6):
            if k_ == -1: continue
            ev3[f'D{k_ + 5}'] = (ev3.rel == k_).astype(float)
        dd = ev3.dropna(subset=['PC1z'])
        rhs = ' + '.join(f'D{k_ + 5}' for k_ in range(-5, 6) if k_ != -1)
        me = smf.ols(f'PC1z ~ {rhs} + C(eb) + C(nga)', dd).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(dd.nga)[0]})
        H3es = [dict(rel=k_, b=float(me.params[f'D{k_ + 5}']), se=float(me.bse[f'D{k_ + 5}'])) for k_ in range(-5, 6) if k_ != -1]
        OUT['H3_event_ngas'] = len(T0)
    print('draw', m, 'done', flush=True)

# ---------- pooling ----------
R = {k: collect(v, 'EPIz') for k, v in rows.items() if k != 'H5_vessel' and v}
for k in R: R[k].update(n=rows[k][0]['n'], events=rows[k][0]['events'], ngas=rows[k][0]['ngas'])
for t in ['MSP', 'mhg', 'moral_concern_primary']:
    q_, T_ = D.rubin([r['b'][t] for r in rows['H5']], [r['V'][t] for r in rows['H5']]); R['H5_' + t] = dict(logHR=float(q_), se=float(np.sqrt(T_)))
bq = np.mean([x[0] for x in H5joint], 0); Ubar = np.mean([x[1] for x in H5joint], 0); Bv = np.cov(np.array([x[0] for x in H5joint]).T)
Tm = Ubar + (1 + 1 / M) * Bv; W = float(bq @ np.linalg.pinv(Tm) @ bq); R['H5_vessel_joint'] = dict(chi2=W, df=3, p=float(stats.chi2.sf(W, 3)))
bq = np.mean([x[0] for x in H7rows], 0); Ubar = np.mean([x[1] for x in H7rows], 0); Bv = np.cov(np.array([x[0] for x in H7rows]).T)
Tm = Ubar + (1 + 1 / M) * Bv
L = np.array([[1, 0, 0], [1, 1, 0], [1, 0, 1]]); est = L @ bq; Ve = L @ Tm @ L.T
R['H7_eras'] = {e: dict(HR=float(np.exp(est[i])), lo95=float(np.exp(est[i] - 1.96 * np.sqrt(Ve[i, i]))), hi95=float(np.exp(est[i] + 1.96 * np.sqrt(Ve[i, i]))),
                        events=int(H7rows[0][2 + i])) for i, e in enumerate(['pre500BCE', '500BCE_1500CE', 'post1500CE'])}
iw = bq[1:]; Vi = Tm[1:, 1:]; Wi = float(iw @ np.linalg.pinv(Vi) @ iw); R['H7_interaction'] = dict(chi2=Wi, df=2, p=float(stats.chi2.sf(Wi, 2)))
ratios = {}
for (i, j) in [(0, 1), (0, 2), (1, 2)]:
    c_ = np.zeros(3); c_[i] = 1; c_[j] = -1; dlt = c_ @ est; sd_ = np.sqrt(c_ @ Ve @ c_)
    ratios[f'{i}{j}'] = dict(ratio=float(np.exp(dlt)), lo90=float(np.exp(dlt - 1.645 * sd_)), hi90=float(np.exp(dlt + 1.645 * sd_)))
R['H7_ratios'] = ratios
for key in FG:
    q_, T_ = D.rubin([x[0] for x in FG[key]], [x[1] for x in FG[key]]); se_ = np.sqrt(T_)
    R[f'H4a_FG_{key}'] = dict(SHR=float(np.exp(q_)), lo95=float(np.exp(q_ - 1.96 * se_)), hi95=float(np.exp(q_ + 1.96 * se_)), p=float(2 * stats.norm.sf(abs(q_ / se_))))
for y in H4b:
    ok = [x for x in H4b[y] if np.isfinite(x[0])]
    if not ok: R[f'H4b_{y}'] = dict(note='not estimable', n=H4b[y][0][2]); continue
    q_, T_ = D.rubin([x[0] for x in ok], [x[1] for x in ok]); se_ = np.sqrt(T_)
    R[f'H4b_{y}'] = dict(ratio=float(np.exp(q_)), lo95=float(np.exp(q_ - 1.96 * se_)), hi95=float(np.exp(q_ + 1.96 * se_)), lo90=float(np.exp(q_ - 1.645 * se_)),
                         hi90=float(np.exp(q_ + 1.645 * se_)), p=float(2 * stats.norm.sf(abs(q_ / se_))), n=ok[0][2], mean_outcome=ok[0][3])
for key in ['fwd', 'rev']:
    q_, T_ = D.rubin([x[0] for x in H3rows[key]], [x[1] for x in H3rows[key]]); se_ = np.sqrt(T_)
    R[f'H3_{key}'] = dict(b=float(q_), lo95=float(q_ - 1.96 * se_), hi95=float(q_ + 1.96 * se_), p_cluster=float(2 * stats.norm.sf(abs(q_ / se_))),
                          p_boot_median=float(np.median([x[2] for x in H3rows[key]])), n=H3rows[key][0][3], ngas=H3rows[key][0][4])
q_, T_ = D.rubin([x[0] for x in H3rows['turchin']], [x[1] for x in H3rows['turchin']]); R['H3_turchin_EPI'] = dict(b=float(q_), se=float(np.sqrt(T_)), p=float(2 * stats.norm.sf(abs(q_ / np.sqrt(T_)))))
R['H3_event_study'] = H3es; R['within_polity_share_varying'] = within_share
R['PC1_loadings_draw0'] = pcinfo[0][0]; R['PC1_share_draw0'] = pcinfo[0][1]
# Cox on polity durations (EPI only; no imputation needed), stratified by NGA
dur = (S.end_year - S.start_year).clip(lower=1).values
cx = coxlib.fit(np.zeros(len(S)), dur, S.ev_any.values.astype(int), S[['EPIz']].values, strata=pd.factorize(S.nga_name)[0], cluster=S.nga_name.values)
R['H1_cox_NGAstrata'] = dict(HR=float(np.exp(cx['beta'][0])), lo95=float(np.exp(cx['beta'][0] - 1.96 * cx['se'][0])), hi95=float(np.exp(cx['beta'][0] + 1.96 * cx['se'][0])),
                             p=float(2 * stats.norm.sf(abs(cx['beta'][0] / cx['se'][0]))))

# ---------- decisions ----------
P = {'H1': R['H1']['p_boot_median'], 'H2': R['H2']['p_boot_median'], 'H3': R['H3_fwd']['p_boot_median'], 'H4a': R['H4a_int']['p_boot_median'],
     'H4b*': R['H4b_survive'].get('p'), 'H5': R['H5']['p_boot_median'], 'H7': R['H7_interaction']['p']}
idx = sorted([k for k in P if P[k] is not None and np.isfinite(P[k])], key=lambda k: P[k]); holm = {}; run_ = 0
for i, k in enumerate(idx):
    run_ = max(run_, min(1, (len(idx) - i) * P[k])); holm[k] = run_
dec = {}
def hr_rule(r, hp, same_sign_ok=True):
    if r['HR'] < 1 and hp < 0.05 and same_sign_ok: return 'supported'
    if (r['lo90'] >= EQ_LO and r['hi90'] <= EQ_HI) or (r['HR'] > 1 and r['p_cluster'] < 0.05): return 'falsified'
    return 'inconclusive'
dec['H1'] = hr_rule(R['H1'], holm['H1'], R['H1_trad']['HR'] < 1)
dec['H2'] = hr_rule(R['H2'], holm['H2'], R['H1_trad']['HR'] < 1)
f3, r3_ = R['H3_fwd'], R['H3_rev']
dec['H3'] = ('supported' if (f3['b'] > 0 and holm['H3'] < 0.05 and abs(f3['b']) > abs(r3_['b'])) else
             ('falsified' if (f3['p_boot_median'] >= 0.05 and r3_['p_boot_median'] < 0.05 and abs(r3_['b']) > abs(f3['b'])) else 'inconclusive'))
ri, rq = R['H4a_int'], R['H4a_conq']
dec['H4a'] = ('supported' if (ri['HR'] < 1 and holm['H4a'] < 0.05 and np.log(ri['HR']) <= np.log(rq['HR'])) else
              ('falsified' if (ri['lo90'] >= EQ_LO and ri['hi90'] <= EQ_HI and rq['HR'] < 1 and rq['p_cluster'] < 0.05) else 'inconclusive'))
s_ = R['H4b_survive']
if 'ratio' in s_:
    sev = R.get('H4b_severity', {})
    dec['H4b*'] = ('supported' if (s_['ratio'] > 1 and holm['H4b*'] < 0.05 and not (sev.get('ratio', 1) > 1 and sev.get('p', 1) < 0.05)) else
                   ('falsified' if (s_['lo90'] >= 0.80 and s_['hi90'] <= 1.25) else 'inconclusive'))
else:
    dec['H4b*'] = 'not estimable'
b0, b1 = np.log(R['H2']['HR']), np.log(R['H5']['HR'])
shrunk = abs(b1) < 0.5 * abs(b0)
dec['H5'] = ('falsified' if (shrunk or (R['H5']['lo90'] >= EQ_LO and R['H5']['hi90'] <= EQ_HI)) and dec['H2'] == 'supported' else
             ('supported' if (R['H5']['HR'] < 1 and holm['H5'] < 0.05 and R['H5_vessel_joint']['p'] >= 0.05) else
              ('estimate only (no content effect in H2)' if dec['H2'] != 'supported' else 'inconclusive')))
e = R['H7_eras']; hrs = [e[k]['HR'] for k in e]
reversal = (holm['H7'] < 0.05) and (min(hrs) < 1 < max(hrs))
inv = all(h < 1 for h in hrs) and all(0.67 <= v['lo90'] and v['hi90'] <= 1.5 for v in R['H7_ratios'].values())
dec['H7'] = 'falsified (sign reversal)' if reversal else ('invariance supported' if inv else 'not falsified, not shown')
OUT['results'] = R; OUT['p'] = P; OUT['holm'] = holm; OUT['decisions'] = dec
json.dump(OUT, open('/root/analysis/retest/' + ('s1r_results_SIMULATED.json' if args.simulate else 's1r_results.json'), 'w'), indent=1, default=float)
print(json.dumps({'sample': OUT['sample'], 'decisions': dec, 'holm': holm}, indent=1, default=float))
