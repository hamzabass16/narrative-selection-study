"""Shared data builders for the Study 1 retest and H8 Part A (approved plan, Section 4). Written before any model was run.

Polity-century intervals: polity p with database dates [s, e] is split into intervals [s+100k, min(s+100(k+1), e)), k = 0, 1, ...;
an interval shorter than 100 years enters with exposure L/100 (offset in the complementary log-log model).
Time-varying covariates are sampled from Seshat's own template (SeshatDatasetAnalysis, 'zero' interpolation, uniform
sampling of ranges, one disputed value drawn at random) at each interval's START year, so they precede any event in the
interval. Draw m uses numpy seed 20261023 + m.
Social complexity PC1: first principal component of the eight Seshat characteristics (Pop, Terr, Cap, Hierarchy, Government,
Infrastructure, Information, Money), standardized, fitted within each draw after imputation, signed so that Hierarchy loads
positively."""
import sys, warnings, io, contextlib
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
sys.path.insert(0, '/root/data/seshat_polaris/SeshatDatasetAnalysis')
from seshatdatasetanalysis.TimeSeriesDataset import TimeSeriesDataset as TSD
A = '/root/analysis/'; R = A + 'retest/'
TEMPLATE = '/root/data/seshat_polaris/SeshatDatasetAnalysis/test_scripts/template.csv'
CC8 = ['Pop', 'Terr', 'Cap', 'Hierarchy', 'Government', 'Infrastructure', 'Information', 'Money']
WAR = ['Miltech', 'Iron', 'Cavalry']
INTERNAL = {'T1a', 'T1b', 'T1c'}; CONQ = {'T2'}; OTHER = {'T3', 'T4', 'T5'}

def frame(codes_g=None):
    f = pd.read_csv(A + 'frame/polities_frame.csv')
    fc = pd.read_csv(A + 'frame/final_codes.csv')[['polity_id', 'Q2', 'Q3', 'end_year']]
    g = codes_g or R + 'term/final_codes_G.csv'
    try:
        fg = pd.read_csv(g)[['polity_id', 'Q2', 'Q3', 'end_year']]
        fc = pd.concat([fc, fg[~fg.polity_id.isin(fc.polity_id)]])
    except FileNotFoundError:
        pass
    f = f.merge(fc.rename(columns={'polity_id': 'id', 'end_year': 'coder_end'}), on='id', how='left')
    ex = pd.read_csv(R + 'polity_exposures.csv')
    f = f.merge(ex.drop(columns=['match']), on='name', how='left')
    f.loc[f.censored_present == True, 'Q2'] = 'CENS'
    def ev(r):
        if r.Q2 in INTERNAL | CONQ | OTHER: return 1.0
        if r.Q2 == 'T9': return 1.0 if r.Q3 == 'Y' else (0.0 if r.Q3 == 'N' else np.nan)
        if r.Q2 in ('T0', 'CENS', 'T6', 'T7', 'T8'): return 0.0
        return np.nan
    f['ev_any'] = f.apply(ev, axis=1)
    f['cause'] = f.Q2.map(lambda q: 1 if q in INTERNAL else (2 if q in CONQ else (3 if q in OTHER else (9 if q == 'T9' else 0))))
    f['trad'] = f.trad_primary.fillna('none').map(lambda s: s.split(';')[0] if isinstance(s, str) else 'none')
    return f

def intervals(f):
    rows = []
    for r in f.itertuples():
        s, e = float(r.start_year), float(r.end_year)
        D = max(e - s, 1.0); K = int(np.ceil(D / 100.0))
        for k in range(K):
            a = s + 100 * k; b = min(s + 100 * (k + 1), s + D)
            last = k == K - 1
            rows.append(dict(id=r.id, name=r.name, nga=r.nga_name, k=k, a=a, b=b, L=(b - a) / 100.0, mid=(a + b) / 2,
                             ev=float(r.ev_any) if last else 0.0, cause=int(r.cause) if last and r.ev_any == 1 else 0))
    return pd.DataFrame(rows)

def sample(points, m):
    """points: DataFrame with columns id, name, nga, year. Returns sampled covariates for draw m (no imputation)."""
    with contextlib.redirect_stdout(io.StringIO()):
        ds = TSD(categories=['sc'], template_path=TEMPLATE)
    raw = points[['nga', 'id', 'name', 'year']].rename(columns={'nga': 'NGA', 'id': 'PolityID', 'name': 'PolityName', 'year': 'Year'})
    raw = raw.reset_index(drop=True)
    for key in ds.template.vars_in_template:  # pre-create as object columns so text-valued variables can be stored
        raw[key.split('/')[-1]] = pd.Series([None] * len(raw), dtype=object)
    ds.raw = raw
    np.random.seed(20261023 + m)
    with contextlib.redirect_stdout(io.StringIO()):
        ds.download_all_categories()
    for key in ds.template.vars_in_template:  # back to numeric where every stored value is numeric
        c = key.split('/')[-1]; s = ds.raw[c]; num = pd.to_numeric(s, errors='coerce')
        if num.notna().sum() == s.notna().sum(): ds.raw[c] = num.astype(float)
    with contextlib.redirect_stdout(io.StringIO()):
        ds.build_social_complexity(); ds.build_warfare(); ds.build_MSP()
    scv = ds.scv.reset_index(drop=True)
    out = points.reset_index(drop=True).copy()
    for c in CC8 + WAR + ['MSP']:
        out[c] = pd.to_numeric(scv[c], errors='coerce').values if c in scv else np.nan
    wr = ds.raw['written_record'] if 'written_record' in ds.raw else pd.Series(np.nan, index=ds.raw.index)
    out['writing'] = pd.to_numeric(wr.map(lambda v: 1.0 if str(v).lower() in ('1', '1.0', 'present', 'true') else
                                          (0.0 if str(v).lower() in ('0', '0.0', 'absent', 'false') else np.nan)), errors='coerce').values
    return out

_CLIO = None
def clio_terr(smp):
    """Within-polity territory change from Cliopatria (plan Section 4). Uses only Cliopatria features with a single SeshatID.
    For a polity whose sampled Seshat territory does not change over its rows: if Cliopatria gives an area at two or more of
    the polity's sample years, Terr = Seshat level + log10(area_t) - mean(log10 area) over those years (the Seshat level is
    kept, Cliopatria supplies only the change); if Seshat territory is missing, Terr = log10(area_t). Rows without a
    Cliopatria area keep the Seshat value."""
    global _CLIO
    if _CLIO is None:
        c = pd.read_csv('/root/data/ext2/cliopatria_areas.csv')
        _CLIO = c[~c.sid.str.contains(';|,', regex=True)]
    out = smp.copy(); out['terr_src'] = 'seshat'
    for name, g in out.groupby('name'):
        cl = _CLIO[_CLIO.sid == name]
        if cl.empty: continue
        ar = np.array([cl[(cl.y0 <= y) & (cl.y1 >= y)].area.sum() for y in g.year])
        ok = ar > 0
        if ok.sum() == 0: continue
        la = np.where(ok, np.log10(np.where(ok, ar, 1.0)), np.nan)
        st = g.Terr.dropna()
        if st.nunique() > 1: continue  # Seshat already dates territory within this polity
        if st.empty:
            out.loc[g.index[ok], 'Terr'] = la[ok]; out.loc[g.index[ok], 'terr_src'] = 'cliopatria'
        elif ok.sum() >= 2:
            out.loc[g.index[ok], 'Terr'] = st.iloc[0] + la[ok] - np.nanmean(la); out.loc[g.index[ok], 'terr_src'] = 'seshat+clio_change'
    return out

def add_pc1(df):
    """Standardize the eight characteristics over df and add PC1 (requires no missing values in CC8)."""
    Z = (df[CC8] - df[CC8].mean()) / df[CC8].std()
    U, S, Vt = np.linalg.svd(Z.values, full_matrices=False)
    v = Vt[0]; v = v if v[CC8.index('Hierarchy')] > 0 else -v
    df = df.copy(); df['PC1'] = Z.values @ v
    return df, dict(zip(CC8, v.round(3))), float(S[0] ** 2 / (S ** 2).sum())

def impute(df, cols, aux, m):
    from sklearn.experimental import enable_iterative_imputer  # noqa
    from sklearn.impute import IterativeImputer
    from sklearn.linear_model import BayesianRidge
    X = df[cols + aux].astype(float)
    imp = IterativeImputer(estimator=BayesianRidge(), sample_posterior=True, max_iter=15, random_state=1000 + m)
    Y = pd.DataFrame(imp.fit_transform(X), columns=cols + aux, index=df.index)
    out = df.copy()
    for c in cols: out[c] = Y[c]
    return out

def wild_score_boot_glm(model, params_r, k, groups, B=9999, seed=1):
    """Kline-Santos wild cluster score bootstrap for coefficient k of a statsmodels GLM, null (theta_k = 0) imposed.
    params_r: full-length parameter vector from the restricted fit with 0 at position k. Webb six-point weights."""
    s = model.score_obs(params_r); H = model.hessian(params_r)
    Ainv = np.linalg.pinv(-H)
    g = pd.factorize(groups)[0]; G = g.max() + 1
    Sg = np.zeros((G, s.shape[1]))
    np.add.at(Sg, g, s)
    a = Ainv[k]  # row k of A
    num = Sg @ a  # per-cluster contribution to (A U)_k
    t0 = num.sum() / np.sqrt((num ** 2).sum())
    rng = np.random.default_rng(seed)
    wv = np.array([-np.sqrt(1.5), -1, -np.sqrt(0.5), np.sqrt(0.5), 1, np.sqrt(1.5)])
    W = rng.choice(wv, size=(B, G))
    tb = (W @ num) / np.sqrt((W ** 2) @ (num ** 2))
    return float(np.mean(np.abs(tb) >= abs(t0))), float(t0)

def wild_boot_ols(y, X, k, groups, B=4999, seed=1):
    """Wild cluster bootstrap-t (null imposed, Webb weights) for coefficient k of OLS y ~ X; returns p and CR1 t."""
    y = np.asarray(y, float); X = np.asarray(X, float); g = pd.factorize(groups)[0]; G = g.max() + 1; n, p = X.shape
    XtXi = np.linalg.pinv(X.T @ X)
    def cr_t(yv):
        b = XtXi @ (X.T @ yv); e = yv - X @ b
        Sg = np.zeros((G, p)); np.add.at(Sg, g, X * e[:, None])
        V = XtXi @ (Sg.T @ Sg) @ XtXi * (G / (G - 1)) * ((n - 1) / (n - p))
        return b[k] / np.sqrt(V[k, k]), b
    t0, b = cr_t(y)
    Xr = np.delete(X, k, axis=1); br = np.linalg.pinv(Xr.T @ Xr) @ (Xr.T @ y); fr = Xr @ br; er = y - fr
    rng = np.random.default_rng(seed)
    wv = np.array([-np.sqrt(1.5), -1, -np.sqrt(0.5), np.sqrt(0.5), 1, np.sqrt(1.5)])
    cnt = 0
    for _ in range(B):
        w = rng.choice(wv, size=G)[g]
        tb, _ = cr_t(fr + w * er)
        cnt += abs(tb) >= abs(t0)
    return float(cnt / B), float(t0)

def rubin(betas, variances):
    betas = np.asarray(betas, float); variances = np.asarray(variances, float)
    m = len(betas); qbar = betas.mean(0); ubar = variances.mean(0); bvar = betas.var(0, ddof=1) if m > 1 else 0 * qbar
    T = ubar + (1 + 1 / m) * bvar
    return qbar, T
