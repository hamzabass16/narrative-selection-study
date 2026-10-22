"""Vectorized Breslow partial likelihood for counting-process data (same model as coxlib, faster)."""
import numpy as np

class Strat:
    def __init__(self, start, stop, event, w, X):
        self.X = X; self.w = w; self.start = start; self.stop = stop; self.event = event
        self.T = np.unique(stop[event == 1])
        self.os = np.argsort(stop, kind='stable'); self.ss = stop[self.os]
        self.ob = np.argsort(start, kind='stable'); self.sb = start[self.ob]
        self.ia = np.searchsorted(self.ss, self.T, 'left'); self.ib = np.searchsorted(self.sb, self.T, 'left')
        evr = np.where(event == 1)[0]
        self.evr = evr; self.evk = np.searchsorted(self.T, stop[evr])
        self.d = np.bincount(self.evk, weights=w[evr], minlength=len(self.T))
        self.wx = np.zeros((len(self.T), X.shape[1])); np.add.at(self.wx, self.evk, w[evr][:, None] * X[evr])
        self.weta_idx = evr

    def _suffix(self, v, order, idx):
        s = np.concatenate([np.cumsum(v[order][::-1], axis=0)[::-1], np.zeros((1,) + v.shape[1:])])
        return s[idx]

    def stats(self, beta):
        X, w = self.X, self.w
        eta = X @ beta; r = w * np.exp(eta)
        rX = r[:, None] * X; rXX = rX[:, :, None] * X[:, None, :]
        S0 = self._suffix(r, self.os, self.ia) - self._suffix(r, self.ob, self.ib)
        S1 = self._suffix(rX, self.os, self.ia) - self._suffix(rX, self.ob, self.ib)
        S2 = self._suffix(rXX, self.os, self.ia) - self._suffix(rXX, self.ob, self.ib)
        return eta, r, S0, S1, S2

def nll(beta, strata_objs):
    ll = 0.0; p = len(beta); g = np.zeros(p); H = np.zeros((p, p))
    for s in strata_objs:
        eta, r, S0, S1, S2 = s.stats(beta)
        ll += (s.w[s.evr] * eta[s.evr]).sum() - (s.d * np.log(S0)).sum()
        xbar = S1 / S0[:, None]
        g += s.wx.sum(0) - (s.d[:, None] * xbar).sum(0)
        H += np.einsum('k,kij->ij', s.d, S2 / S0[:, None, None] - xbar[:, :, None] * xbar[:, None, :])
    return -ll, -g, H

def score_resid(beta, s):
    eta, r, S0, S1, S2 = s.stats(beta)
    xbar = S1 / S0[:, None]
    L = np.zeros_like(s.X)
    L[s.evr] += s.w[s.evr][:, None] * (s.X[s.evr] - xbar[s.evk])
    a = s.d / S0; c1 = np.concatenate([[0], np.cumsum(a)]); c2 = np.vstack([np.zeros((1, s.X.shape[1])), np.cumsum(a[:, None] * xbar, axis=0)])
    hi = np.searchsorted(s.T, s.stop, 'right'); lo = np.searchsorted(s.T, s.start, 'right')
    A1 = c1[hi] - c1[lo]; A2 = c2[hi] - c2[lo]
    L -= r[:, None] * (s.X * A1[:, None] - A2)
    return L
