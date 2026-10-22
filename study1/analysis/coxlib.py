"""Weighted Cox regression (Breslow ties) in counting-process form, with left truncation, strata,
cluster-robust (sandwich) variance, and Fine-Gray subdistribution hazards via IPCW expansion."""
import numpy as np
from scipy import optimize


def _prep(start, stop, event, X, w, strata):
    n = len(stop)
    X = np.asarray(X, float).reshape(n, -1)
    w = np.ones(n) if w is None else np.asarray(w, float)
    strata = np.zeros(n, int) if strata is None else np.asarray(strata)
    return np.asarray(start, float), np.asarray(stop, float), np.asarray(event, int), X, w, strata


def _risk_struct(start, stop, event, strata):
    """List of (stratum, event time, indices at risk, indices with event)."""
    out = []
    for s in np.unique(strata):
        m = np.where(strata == s)[0]
        times = np.unique(stop[m][event[m] == 1])
        for t in times:
            risk = m[(start[m] < t) & (stop[m] >= t)]
            ev = m[(stop[m] == t) & (event[m] == 1)]
            out.append((s, t, risk, ev))
    return out


def _nll(beta, X, w, rs):
    eta = X @ beta
    ll = 0.0; g = np.zeros_like(beta); H = np.zeros((len(beta), len(beta)))
    for _, _, risk, ev in rs:
        r = w[risk] * np.exp(eta[risk])
        S0 = r.sum(); S1 = r @ X[risk]; S2 = (X[risk] * r[:, None]).T @ X[risk]
        d = w[ev].sum()
        ll += (w[ev] * eta[ev]).sum() - d * np.log(S0)
        xbar = S1 / S0
        g += (w[ev][:, None] * X[ev]).sum(0) - d * xbar
        H += d * (S2 / S0 - np.outer(xbar, xbar))
    return -ll, -g, H


def fit(start, stop, event, X, w=None, strata=None, cluster=None, names=None):
    start, stop, event, X, w, strata = _prep(start, stop, event, X, w, strata)
    import coxfast
    mu = X.mean(0); sd = X.std(0); sd[sd == 0] = 1.0
    X = (X - mu) / sd  # standardize for numerical stability; estimates are back-transformed below
    objs = [coxfast.Strat(start[strata == s], stop[strata == s], event[strata == s], w[strata == s], X[strata == s]) for s in np.unique(strata)]
    rows = [np.where(strata == s)[0] for s in np.unique(strata)]
    def _nll_(b, X_, w_, rs_):
        with np.errstate(all='ignore'):
            f_, g_, H_ = coxfast.nll(b, objs)
        if not np.isfinite(f_): f_ = np.inf
        return f_, g_, H_
    rs = None
    p = X.shape[1]
    beta = np.zeros(p); converged = False
    for it in range(100):
        f, g, H = _nll_(beta, X, w, rs)
        if not (np.isfinite(g).all() and np.isfinite(H).all()):
            break
        try:
            step = np.linalg.solve(H + 1e-9 * np.eye(p), -g)
        except np.linalg.LinAlgError:
            break
        # step halving; keep beta unchanged if no step improves the likelihood
        t = 1.0; accepted = False
        while t > 1e-8:
            nb = beta + t * step
            if _nll_(nb, X, w, rs)[0] <= f + 1e-12:
                accepted = True; break
            t /= 2
        if not accepted:
            converged = np.max(np.abs(g)) < 1e-4; break
        beta = nb
        if np.max(np.abs(t * step)) < 1e-9:
            converged = True; break
    f, g, H = _nll_(beta, X, w, rs)
    if not (np.isfinite(H).all() and np.isfinite(beta).all()) or np.max(np.abs(beta)) > 25:
        nanp = np.full(p, np.nan)
        return dict(beta=nanp, se_model=nanp, se=nanp, V=np.full((p, p), np.nan), Vmodel=np.full((p, p), np.nan),
                    loglik=np.nan, names=names, n=len(stop), events=float((w * event).sum()),
                    clusters=len(np.unique(cluster)) if cluster is not None else len(stop), converged=False)
    Hinv = np.linalg.pinv(H)
    # score residuals (Lin and Wei) per row
    L = np.zeros_like(X)
    for o, rw in zip(objs, rows):
        L[rw] = coxfast.score_resid(beta, o)
    if cluster is None:
        cluster = np.arange(len(stop))
    cluster = np.asarray(cluster)
    U = np.array([L[cluster == c].sum(0) for c in np.unique(cluster)])
    Vr = Hinv @ (U.T @ U) @ Hinv
    G = len(np.unique(cluster))
    if G < len(stop):
        Vr = Vr * G / (G - 1)  # small-sample cluster correction
    beta = beta / sd; Hinv = Hinv / np.outer(sd, sd); Vr = Vr / np.outer(sd, sd)
    return dict(beta=beta, se_model=np.sqrt(np.diag(Hinv)), se=np.sqrt(np.diag(Vr)), V=Vr, Vmodel=Hinv,
                loglik=-f, names=names, n=len(stop), events=float((w * event).sum()), clusters=G, converged=bool(converged))


def finegray_expand(time, status, cause, X, cluster, entry=None):
    """Expand data for the Fine-Gray model (Geskus 2011 IPCW approach).
    status: 0 censored, k>0 event of type k. Subjects with a competing event stay in the risk set
    after their event time with weight G(t)/G(T_i), piecewise constant between event times of the cause."""
    time = np.asarray(time, float); status = np.asarray(status, int)
    n = len(time); X = np.asarray(X, float).reshape(n, -1)
    entry = np.zeros(n) if entry is None else np.asarray(entry, float)
    # Kaplan-Meier of the censoring distribution G(t) (censoring = status 0)
    ut = np.unique(time)
    G = {}; surv = 1.0; prev = 1.0
    for t in ut:
        at_risk = ((entry < t) & (time >= t)).sum()
        c = ((time == t) & (status == 0)).sum()
        G[t] = surv  # G(t-) before censoring at t
        if at_risk > 0:
            surv *= 1 - c / at_risk
    Gfun = lambda t: G[ut[ut <= t].max()] if (ut <= t).any() else 1.0
    ev_times = np.unique(time[status == cause])
    rows = []
    for i in range(n):
        if status[i] in (0, cause):
            rows.append((entry[i], time[i], int(status[i] == cause), 1.0, i))
        else:
            rows.append((entry[i], time[i], 0, 1.0, i))
            Gi = Gfun(time[i])
            later = ev_times[ev_times > time[i]]
            lo = time[i]
            for t in later:
                rows.append((lo, t, 0, Gfun(t) / Gi if Gi > 0 else 0.0, i))
                lo = t
    rows = np.array(rows)
    idx = rows[:, 4].astype(int)
    return rows[:, 0], rows[:, 1], rows[:, 2].astype(int), X[idx], rows[:, 3], np.asarray(cluster)[idx]


def schoenfeld_test(start, stop, event, X, beta, strata=None):
    """Correlation between Schoenfeld residuals and the rank of event time, per covariate (approximate PH test)."""
    from scipy.stats import spearmanr
    start, stop, event, X, w, strata = _prep(start, stop, event, X, None, strata)
    rs = _risk_struct(start, stop, event, strata)
    eta = X @ beta; res = []; tt = []
    for _, t, risk, ev in rs:
        r = np.exp(eta[risk]); xbar = (r @ X[risk]) / r.sum()
        for i in ev:
            res.append(X[i] - xbar); tt.append(t)
    res = np.array(res); tt = np.array(tt)
    return [spearmanr(res[:, j], tt) for j in range(X.shape[1])]
