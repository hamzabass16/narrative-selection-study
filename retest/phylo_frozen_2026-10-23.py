"""Tree utilities for the retest (H9b dated trees, H10 retention). Written before use on real data.
Trees: D-PLACE published summary trees. Tips are mapped to Glottolog language-level codes through D-PLACE societies.csv;
when several tips share a language, the first in the tree is kept. Trees are rescaled to unit root-to-tip height;
polytomies are resolved at random (seed) with zero-length edges. Mk models are fitted by maximum likelihood with
Felsenstein pruning; the root prior is equal state frequencies."""
import numpy as np, pandas as pd, dendropy, random
from scipy.linalg import expm
from scipy.optimize import minimize
C = '/root/data/dplace-cldf/cldf/'
_soc = pd.read_csv(C + 'societies.csv')

class Tree:
    def __init__(self, tree_id, keep, seed=1):
        t = dendropy.Tree.get(path=C + f'trees/{tree_id}.trees', schema='nexus', preserve_underscores=True)
        s = _soc[_soc.Contribution_ID == f'dplace-phylogeny-{tree_id}'].set_index('ID')
        lab2g = {}
        for i, r in s.iterrows():
            g = r.Language_Level_Glottocodes if isinstance(r.Language_Level_Glottocodes, str) and r.Language_Level_Glottocodes else r.Glottocode
            lab2g[i] = g
        seen = set(); keep_labels = []
        for l in t.leaf_node_iter():
            g = lab2g.get(l.taxon.label)
            if g in keep and g not in seen: seen.add(g); keep_labels.append(l.taxon.label)
        t.retain_taxa_with_labels(keep_labels)
        for l in t.leaf_node_iter(): l.taxon.label = lab2g[l.taxon.label]
        for nd in t.preorder_node_iter():
            if nd.edge_length is None: nd.edge_length = 0.0
        t.resolve_polytomies(limit=2, update_bipartitions=False, rng=random.Random(seed))
        for nd in t.preorder_node_iter():
            if nd.edge_length is None: nd.edge_length = 0.0
        H = max(l.distance_from_root() for l in t.leaf_node_iter())
        for nd in t.preorder_node_iter(): nd.edge_length = (nd.edge_length or 0.0) / H
        self.nodes = list(t.postorder_node_iter()); idx = {nd: i for i, nd in enumerate(self.nodes)}
        self.children = [[idx[c] for c in nd.child_nodes()] for nd in self.nodes]
        self.blen = np.array([nd.edge_length or 0.0 for nd in self.nodes])
        self.leaves = [i for i, nd in enumerate(self.nodes) if nd.is_leaf()]
        self.tips = [self.nodes[i].taxon.label for i in self.leaves]
        self.root = len(self.nodes) - 1
        self.parent = np.full(len(self.nodes), -1)
        for i, ch in enumerate(self.children):
            for c in ch: self.parent[c] = i

    def loglik(self, Q, tipstates, k):
        """tipstates: dict tip -> state index (or list of allowed states). Returns log-likelihood."""
        L = np.zeros((len(self.nodes), k)); logscale = 0.0
        Pcache = {}
        for i, ch in enumerate(self.children):
            if not ch:
                s = tipstates[self.nodes[i].taxon.label]
                v = np.zeros(k); v[s if isinstance(s, (list, tuple)) else [s]] = 1.0; L[i] = v
            else:
                v = np.ones(k)
                for c in ch:
                    b = self.blen[c]
                    P = Pcache.get(b)
                    if P is None: P = expm(Q * b); Pcache[b] = P
                    v = v * (P @ L[c])
                m = v.max()
                if m <= 0: return -np.inf
                L[i] = v / m; logscale += np.log(m)
        return float(np.log((L[self.root] / k).sum()) + logscale)

def fit_mk(tree, tipstates, k, qindex, nfree, starts=((-1.0,),), bounds=(-7, 5)):
    """qindex: list of (i, j, param_index) defining Q off-diagonals; params are log-rates (log of rate per unit tree height).
    Returns (loglik, rates)."""
    def build(lr):
        Q = np.zeros((k, k))
        for i, j, p in qindex: Q[i, j] = np.exp(lr[p])
        np.fill_diagonal(Q, -Q.sum(1)); return Q
    best = (-np.inf, None)
    for st in starts:
        x0 = np.array(list(st) * nfree)[:nfree] if len(st) < nfree else np.array(st)
        f = lambda lr: -tree.loglik(build(lr), tipstates, k)
        try:
            r = minimize(f, x0, method='L-BFGS-B', bounds=[bounds] * nfree)
            if -r.fun > best[0]: best = (-r.fun, np.exp(r.x))
        except Exception:
            continue
    return best

def D_stat(tree, trait, nsim=1000, seed=20261023):
    """Fritz and Purvis D for a binary trait on a (binary) tree; trait: dict tip -> 0/1."""
    rng = np.random.default_rng(seed)
    obs = np.array([trait[t] for t in tree.tips], float)
    leaf_pos = np.array(tree.leaves)
    def sum_d(tipvals):
        v = np.zeros(len(tree.nodes)); v[leaf_pos] = tipvals; s = 0.0
        for i, ch in enumerate(tree.children):
            if ch:
                a, b = v[ch[0]], v[ch[1]]; s += abs(a - b); v[i] = (a + b) / 2
        return s
    pre = list(reversed(range(len(tree.nodes))))
    def brown():
        x = np.zeros(len(tree.nodes))
        for i in pre:
            if tree.parent[i] >= 0: x[i] = x[tree.parent[i]] + rng.normal(0, np.sqrt(tree.blen[i]))
        return x[leaf_pos]
    so = sum_d(obs); sr = np.array([sum_d(rng.permutation(obs)) for _ in range(nsim)])
    prev = obs.mean(); sb = np.array([sum_d((b > np.quantile(b, 1 - prev)).astype(float)) for b in (brown() for _ in range(nsim))])
    D = (so - sb.mean()) / (sr.mean() - sb.mean())
    return dict(D=float(D), p_vs_random=float((np.sum(sr <= so) + 1) / (nsim + 1)), p_vs_brownian=float((np.sum(sb >= so) + 1) / (nsim + 1)),
                n_tips=int(len(obs)), prevalence=float(prev))
