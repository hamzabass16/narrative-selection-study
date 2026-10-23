"""H6 meta-analysis (protocol h6_protocol.md, frozen 23 October 2026). Written before extraction results were read.
Effect sizes are computed here from the raw statistics recorded by the extractors (Hedges' g, positive = more prosocial
under treatment). Records: extractor A's records are primary; for records where extractor B's numbers differ, the third
coder's adjudication (adjudicated.json) is used when present.
Stratum P primary: incentivized outcomes; one effect per arm and outcome, all retained, dependence handled by RVE.
Estimators: random-effects REML; robust variance estimation (correlated effects, study clusters, CR1 small-sample factor);
PET-PEESE (PEESE if PET's intercept is significant at one-sided 0.05); three-parameter selection model (Vevea and Hedges,
one cut at one-sided p = 0.025). Decision rule as in the protocol."""
import json, sys, numpy as np, pandas as pd
from scipy import stats, optimize
H = '/root/analysis/h6/'
def g_from(stat, v, hp=True):
    s = 1.0 if hp else -1.0
    try:
        if stat == 'means_sd':
            nt, nc = v['n_t'], v['n_c']; sp = np.sqrt(((nt - 1) * v['sd_t'] ** 2 + (nc - 1) * v['sd_c'] ** 2) / (nt + nc - 2)); d = (v['m_t'] - v['m_c']) / sp
        elif stat == 'means_se':
            nt, nc = v['n_t'], v['n_c']; sdt, sdc = v['se_t'] * np.sqrt(nt), v['se_c'] * np.sqrt(nc)
            sp = np.sqrt(((nt - 1) * sdt ** 2 + (nc - 1) * sdc ** 2) / (nt + nc - 2)); d = (v['m_t'] - v['m_c']) / sp
        elif stat == 't':
            nt, nc = v['n_t'], v['n_c']; d = v['t'] * np.sqrt(1 / nt + 1 / nc)
        elif stat == 'F1':
            nt, nc = v['n_t'], v['n_c']; d = np.sign(v.get('sign', 1)) * np.sqrt(v['F']) * np.sqrt(1 / nt + 1 / nc)
        elif stat == 'chi2_1df':
            nt, nc = v['n_t'], v['n_c']; N = nt + nc; r = np.sign(v.get('sign', 1)) * np.sqrt(v['chi2'] / N); d = 2 * r / np.sqrt(1 - r ** 2)
        elif stat == 'proportions':
            nt, nc = v['n_t'], v['n_c']; pt, pc = np.clip(v['p_t'], 1e-3, 1 - 1e-3), np.clip(v['p_c'], 1e-3, 1 - 1e-3)
            lor = np.log(pt / (1 - pt)) - np.log(pc / (1 - pc)); d = lor * np.sqrt(3) / np.pi
        elif stat == 'regression':
            nt, nc = v['n_t'], v['n_c']; d = v['b'] / v['sd_y']
        elif stat == 'd_reported':
            nt, nc = v['n_t'], v['n_c']; d = v['d']
        else:
            return None
    except (KeyError, TypeError, ZeroDivisionError):
        return None
    N = nt + nc; J = 1 - 3 / (4 * (N - 2) - 1); g = s * J * d
    var = J ** 2 * (N / (nt * nc) + d ** 2 / (2 * N))
    return float(g), float(var)
def reml(y, v):
    def nll(t2):
        w = 1 / (v + t2); mu = (w * y).sum() / w.sum()
        return 0.5 * (np.log(v + t2).sum() + np.log(w.sum()) + (w * (y - mu) ** 2).sum())
    t2 = optimize.minimize_scalar(nll, bounds=(0, 10), method='bounded').x
    w = 1 / (v + t2); mu = (w * y).sum() / w.sum(); se = np.sqrt(1 / w.sum())
    return float(mu), float(se), float(t2)
def rve(y, v, cl, t2):
    w = 1 / (v + t2); X = np.ones(len(y)); mu = (w * y).sum() / w.sum(); e = y - mu
    u = pd.Series(w * e).groupby(cl).sum().values; G = len(u)
    V = (u ** 2).sum() / w.sum() ** 2 * G / (G - 1)
    se = np.sqrt(V); p = 2 * stats.t.sf(abs(mu / se), G - 1)
    return float(mu), float(se), float(p), int(G)
def wls(y, X, w):
    W = np.diag(w); B = np.linalg.solve(X.T @ W @ X, X.T @ W @ y); r = y - X @ B
    s2 = (w * r ** 2).sum() / (len(y) - X.shape[1]); V = s2 * np.linalg.inv(X.T @ W @ X)
    return B, np.sqrt(np.diag(V))
def pet_peese(y, v):
    se = np.sqrt(v); w = 1 / v
    B, S = wls(y, np.column_stack([np.ones(len(y)), se]), w); p_one = stats.t.sf(B[0] / S[0], len(y) - 2)
    if p_one < 0.05:
        B2, S2 = wls(y, np.column_stack([np.ones(len(y)), v]), w); return dict(method='PEESE', est=float(B2[0]), se=float(S2[0]), df=len(y) - 2)
    return dict(method='PET', est=float(B[0]), se=float(S[0]), df=len(y) - 2)
def three_psm(y, v):
    se = np.sqrt(v); z = y / se; sig = (z > stats.norm.ppf(0.975)).astype(float)
    def nll(par):
        mu, lt2, lw = par; t2 = np.exp(lt2); w2 = np.exp(lw); s = np.sqrt(v + t2)
        cut = stats.norm.ppf(0.975) * se
        p_sig = stats.norm.sf((cut - mu) / s); A = p_sig + w2 * (1 - p_sig)
        ll = stats.norm.logpdf(y, mu, s) + np.where(sig == 1, 0.0, np.log(w2)) - np.log(A)
        return -ll.sum()
    best = None
    for st in [(0.1, -3, 0), (0.3, -1, -1), (0.0, -5, 0.5)]:
        r = optimize.minimize(nll, st, method='Nelder-Mead', options=dict(maxiter=5000, xatol=1e-6, fatol=1e-8))
        if best is None or r.fun < best.fun: best = r
    mu = best.x[0]
    h = 1e-4; f0 = nll(best.x); fp = nll(best.x + [h, 0, 0]); fm = nll(best.x - [h, 0, 0])
    var = h ** 2 / max(fp - 2 * f0 + fm, 1e-12)
    return dict(est=float(mu), se=float(np.sqrt(var)), weight_nonsig=float(np.exp(best.x[2])), tau2=float(np.exp(best.x[1])))
if __name__ == '__main__':
    recs = json.load(open(H + 'extraction_final.json'))
    rows = []
    for r in recs:
        if not r.get('accessible', True): continue
        res = g_from(r.get('stat_type'), r.get('values') or {}, r.get('higher_is_more_prosocial', True))
        if res is None: continue
        rows.append(dict(study=r['study_id'], stratum=r.get('stratum'), g=res[0], v=res[1], incent=bool(r.get('incentivized')),
                         prereg=r.get('preregistered') == 'Y', ntype=r.get('narrative_type'), pop=r.get('population'), weird=r.get('weird'),
                         target=r.get('target'), delay=r.get('delay'), primary=bool(r.get('primary_outcome'))))
    E = pd.DataFrame(rows); E.to_csv(H + 'effects.csv', index=False)
    OUT = {'n_effects': int(len(E)), 'by_stratum': E.groupby('stratum').study.agg(['size', 'nunique']).to_dict()}
    def pool(d, lab):
        if len(d) < 2: return dict(k=int(len(d)), note='fewer than 2 effects')
        mu, se, t2 = reml(d.g.values, d.v.values); m2, se2, p2, G = rve(d.g.values, d.v.values, d.study.values, t2)
        out = dict(k=int(len(d)), studies=int(d.study.nunique()), g_reml=mu, se_reml=se, tau2=t2, g_rve=m2, se_rve=se2, p_rve=p2,
                   lo95_rve=m2 - stats.t.ppf(0.975, G - 1) * se2, hi95_rve=m2 + stats.t.ppf(0.975, G - 1) * se2)
        if len(d) >= 4:
            pp = pet_peese(d.g.values, d.v.values); out['pet_peese'] = pp
            out['pp_lo90'] = pp['est'] - stats.t.ppf(0.95, pp['df']) * pp['se']; out['pp_hi90'] = pp['est'] + stats.t.ppf(0.95, pp['df']) * pp['se']
            out['pp_lo95'] = pp['est'] - stats.t.ppf(0.975, pp['df']) * pp['se']; out['pp_hi95'] = pp['est'] + stats.t.ppf(0.975, pp['df']) * pp['se']
        if len(d) >= 8: out['three_psm'] = three_psm(d.g.values, d.v.values)
        return out
    P = E[(E.stratum == 'P') & E.incent]
    OUT['P_primary'] = pool(P, 'P'); OUT['P_preregistered'] = pool(P[P.prereg], 'Pprereg')
    for mod in ['ntype', 'pop', 'weird', 'target', 'delay']:
        OUT[f'P_by_{mod}'] = {str(k): pool(g, str(k)) for k, g in P.groupby(mod)}
    for s_ in ['N', 'R', 'H', 'D', 'T']:
        OUT[f'stratum_{s_}'] = pool(E[E.stratum == s_], s_)
    pp = OUT['P_primary']
    if 'pet_peese' in pp:
        sp = OUT.get('P_primary', {}).get('three_psm', {})
        disagree = sp and np.sign(sp['est']) != np.sign(pp['pet_peese']['est'])
        pr = OUT['P_preregistered']
        sup = pp['pp_lo95'] > 0 and pr.get('g_rve', -1) > 0 and not disagree
        fal = pp['pp_lo90'] > -0.15 and pp['pp_hi90'] < 0.15
        OUT['decision'] = 'inconclusive (PET-PEESE and selection model disagree in sign)' if disagree else ('supported' if sup else ('falsified' if fal else 'inconclusive'))
    else:
        OUT['decision'] = 'not estimable (fewer than 4 effects)'
    json.dump(OUT, open(H + 'h6_results.json', 'w'), indent=1, default=float)
    print(json.dumps(OUT, indent=1, default=float)[:6000])
