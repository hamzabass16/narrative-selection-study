"""Own Cox proportional hazards implementation (no lifelines available).

- Stratified partial likelihood, Breslow or Efron ties.
- Newton-Raphson.
- Model-based SE from inverse information.
- Robust SE clustered on a grouping variable, computed as in lifelines /
  R coxph(cluster=): delta-betas = score residuals x I^-1, summed within
  cluster, V = D'D (no small-sample correction).
"""
import numpy as np
from scipy import stats


def _stratum_terms(time, event, X, beta, ties):
    """Return loglik, score, information and score residuals for one stratum."""
    n, p = X.shape
    eta = X @ beta
    w = np.exp(eta)
    ll = 0.0
    U = np.zeros(p)
    H = np.zeros((p, p))
    resid = np.zeros((n, p))
    event_times = np.unique(time[event == 1])
    for t in event_times:
        risk = time >= t
        dead = (time == t) & (event == 1)
        d = int(dead.sum())
        S0 = w[risk].sum()
        S1 = (w[risk, None] * X[risk]).sum(0)
        S2 = (w[risk, None, None] * X[risk, :, None] * X[risk, None, :]).sum(0)
        if ties == 'breslow' or d == 1:
            xbar = S1 / S0
            ll += eta[dead].sum() - d * np.log(S0)
            U += X[dead].sum(0) - d * xbar
            H += d * (S2 / S0 - np.outer(xbar, xbar))
            # score residuals
            resid[dead] += X[dead] - xbar
            resid[risk] -= (d * w[risk] / S0)[:, None] * (X[risk] - xbar)
        else:  # efron
            S0d = w[dead].sum()
            S1d = (w[dead, None] * X[dead]).sum(0)
            S2d = (w[dead, None, None] * X[dead, :, None] * X[dead, None, :]).sum(0)
            ll += eta[dead].sum()
            U += X[dead].sum(0)
            xbars = []
            for m in range(d):
                f = m / d
                s0 = S0 - f * S0d
                s1 = S1 - f * S1d
                s2 = S2 - f * S2d
                xb = s1 / s0
                xbars.append(xb)
                ll -= np.log(s0)
                U -= xb
                H += s2 / s0 - np.outer(xb, xb)
                # compensator part of score residuals
                c = np.where(dead, 1.0 - f, 1.0)
                idx = risk
                resid[idx] -= (c[idx] * w[idx] / s0)[:, None] * (X[idx] - xb)
            mean_xbar = np.mean(xbars, axis=0)
            resid[dead] += X[dead] - mean_xbar
    return ll, U, H, resid


def cox_fit(time, event, X, strata=None, cluster=None, ties='breslow',
            maxiter=100, tol=1e-10):
    time = np.asarray(time, float)
    event = np.asarray(event, int)
    X = np.asarray(X, float)
    if X.ndim == 1:
        X = X[:, None]
    n, p = X.shape
    if strata is None:
        strata = np.zeros(n)
    strata = np.asarray(strata)
    groups = [np.where(strata == s)[0] for s in np.unique(strata)]

    def evaluate(beta):
        ll, U, H = 0.0, np.zeros(p), np.zeros((p, p))
        R = np.zeros((n, p))
        for g in groups:
            l_, u_, h_, r_ = _stratum_terms(time[g], event[g], X[g], beta, ties)
            ll += l_
            U += u_
            H += h_
            R[g] = r_
        return ll, U, H, R

    beta = np.zeros(p)
    ll, U, H, R = evaluate(beta)
    for _ in range(maxiter):
        step = np.linalg.solve(H, U)
        new = beta + step
        ll_new, U_new, H_new, R_new = evaluate(new)
        # step halving if needed
        k = 0
        while ll_new < ll - 1e-12 and k < 30:
            step /= 2
            new = beta + step
            ll_new, U_new, H_new, R_new = evaluate(new)
            k += 1
        beta, ll, U, H, R = new, ll_new, U_new, H_new, R_new
        if np.max(np.abs(step)) < tol:
            break
    Vinv = np.linalg.inv(H)
    se = np.sqrt(np.diag(Vinv))
    out = dict(beta=beta, se=se, loglik=ll, score_resid=R, n=n,
               events=int(event.sum()))
    out['p'] = 2 * stats.norm.sf(np.abs(beta / se))
    if cluster is not None:
        cluster = np.asarray(cluster)
        D = R @ Vinv
        Dg = np.array([D[cluster == c].sum(0) for c in np.unique(cluster)])
        Vr = Dg.T @ Dg
        se_r = np.sqrt(np.diag(Vr))
        out['se_robust'] = se_r
        out['p_robust'] = 2 * stats.norm.sf(np.abs(beta / se_r))
    return out
