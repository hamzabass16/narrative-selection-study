"""H9b: phylogenetic signal of belief in a moralizing high god (Ethnographic Atlas EA034 = 4) and of any high god (EA034 >= 2),
measured with the D statistic of Fritz and Purvis (2010) on a global Glottolog classification tree assembled from D-PLACE family trees,
plus dependence on social scale (EA033 jurisdictional hierarchy beyond the local community)."""
import glob, re, json
import numpy as np, pandas as pd, dendropy
import statsmodels.api as sm
rng = np.random.default_rng(20261017)
C = '/root/data/dplace-cldf/cldf/'
soc = pd.read_csv(C + 'societies.csv'); dat = pd.read_csv(C + 'data.csv', low_memory=False)
sel = dat[dat.Var_ID.isin(['EA034', 'EA033'])].copy(); sel['code'] = sel.Code_ID.astype(str).str.split('-').str[-1]
ea = sel.pivot_table(index='Soc_ID', columns='Var_ID', values='code', aggfunc='first')
ea = ea.apply(pd.to_numeric, errors='coerce').dropna(subset=['EA034'])
ea = ea.join(soc.set_index('ID')[['Language_Level_Glottocodes', 'region']])
ea['mhg'] = (ea.EA034 == 4).astype(int); ea['hg'] = (ea.EA034 >= 2).astype(int)
# language-level trait: majority of societies speaking the language (ties count as present)
lang = ea.groupby('Language_Level_Glottocodes').agg(mhg=('mhg', 'mean'), hg=('hg', 'mean'), EA033=('EA033', 'mean'), n=('mhg', 'size'))
lang['mhg'] = (lang.mhg >= .5).astype(int); lang['hg'] = (lang.hg >= .5).astype(int)

# ---- build global tree ----
tns = dendropy.TaxonNamespace()
fams = []
for f in sorted(glob.glob(C + 'trees/*.trees')):
    if not re.match(r'^[a-z]{4}\d{4}$', f.split('/')[-1][:-6]):
        continue  # only Glottolog classification trees (skip published phylogenies)
    try:
        t = dendropy.Tree.get(path=f, schema='nexus', taxon_namespace=tns, preserve_underscores=True)
    except Exception as e:
        continue
    fams.append(t)
keep = set(lang.index)
root = dendropy.Tree(taxon_namespace=tns)
heights = []
sub = []
for t in fams:
    labels = [l.taxon.label for l in t.leaf_node_iter()]
    present = [x for x in labels if x in keep]
    if not present:
        continue
    t.retain_taxa_with_labels(present)
    for nd in t.preorder_node_iter():
        if nd.edge_length is None: nd.edge_length = 1.0
    sub.append(t)
in_tree = set(l.taxon.label for t in sub for l in t.leaf_node_iter())
isolates = [g for g in keep if g not in in_tree]
def height(t):
    best = 0.0
    for l in t.leaf_node_iter():
        d, n = 0.0, l
        while n.parent_node is not None:
            d += n.edge_length or 0.0; n = n.parent_node
        best = max(best, d)
    return best
H = max(height(t) for t in sub)
for t in sub:
    h = height(t)
    rn = t.seed_node; rn.edge_length = H + 1 - h
    root.seed_node.add_child(rn)
for g in isolates:
    tx = tns.get_taxon(g) or tns.new_taxon(g)
    nd = dendropy.Node(taxon=tx, edge_length=H + 1); root.seed_node.add_child(nd)
root.resolve_polytomies(limit=2, update_bipartitions=False, rng=__import__('random').Random(1))
for nd in root.preorder_node_iter():
    if nd.edge_length is None: nd.edge_length = 0.0
# index structure for fast computation
nodes = list(root.postorder_node_iter())
idx = {nd: i for i, nd in enumerate(nodes)}
leaves = [nd for nd in nodes if nd.is_leaf()]
leaf_lab = [nd.taxon.label for nd in leaves]
children = [[idx[c] for c in nd.child_nodes()] for nd in nodes]
blen = np.array([nd.edge_length or 0.0 for nd in nodes])
leaf_pos = np.array([idx[nd] for nd in leaves])
parent = np.full(len(nodes), -1)
for i, ch in enumerate(children):
    for c in ch: parent[c] = i
pre = list(reversed(range(len(nodes))))  # root last in postorder, so reversed is a valid preorder

def sum_d(tipvals):
    v = np.zeros(len(nodes)); v[leaf_pos] = tipvals; s = 0.0
    for i, ch in enumerate(children):
        if ch:
            a, b = v[ch[0]], v[ch[1]]
            s += abs(a - b); v[i] = (a + b) / 2
    return s

def brownian(nsim):
    out = []
    k = None
    for _ in range(nsim):
        x = np.zeros(len(nodes))
        for i in pre:
            if parent[i] >= 0:
                x[i] = x[parent[i]] + rng.normal(0, np.sqrt(blen[i]))
        out.append(x[leaf_pos])
    return np.array(out)

def D_stat(trait, nsim=1000):
    obs = trait.loc[leaf_lab].values.astype(float)
    sd_obs = sum_d(obs)
    sd_r = np.array([sum_d(rng.permutation(obs)) for _ in range(nsim)])
    B = brownian(nsim); prev = obs.mean()
    sd_b = np.array([sum_d((b > np.quantile(b, 1 - prev)).astype(float)) for b in B])
    D = (sd_obs - sd_b.mean()) / (sd_r.mean() - sd_b.mean())
    p_random = (np.sum(sd_r <= sd_obs) + 1) / (nsim + 1)      # H0: no signal (D = 1)
    p_brown = (np.sum(sd_b >= sd_obs) + 1) / (nsim + 1)       # H0: Brownian threshold (D = 0)
    return dict(D=float(D), p_vs_random=float(p_random), p_vs_brownian=float(p_brown), n_tips=len(obs), prevalence=float(prev))

res = {'n_languages': int(len(lang)), 'n_societies': int(len(ea)), 'isolates_at_root': len(isolates), 'families': len(sub)}
res['D_moralizing_high_god'] = D_stat(lang.mhg)
res['D_any_high_god'] = D_stat(lang.hg)
# social scale: logistic regression of moralizing high god on jurisdictional hierarchy, family-clustered
fam_of = {}
for t in sub:
    fid = t.seed_node
    for l in t.leaf_node_iter(): fam_of[l.taxon.label] = id(fid)
lg = lang.dropna(subset=['EA033']).copy(); lg['fam'] = [fam_of.get(g, g) for g in lg.index]
X = sm.add_constant(lg[['EA033']]); m = sm.GLM(lg.mhg, X, family=sm.families.Binomial()).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(lg.fam)[0]})
res['scale_logit'] = dict(OR_per_level=float(np.exp(m.params['EA033'])), lo=float(np.exp(m.conf_int().loc['EA033', 0])), hi=float(np.exp(m.conf_int().loc['EA033', 1])), p=float(m.pvalues['EA033']), n=int(len(lg)))
res['prevalence_by_EA033'] = lg.groupby(lg.EA033.round()).mhg.agg(['mean', 'size']).round(3).to_dict()
json.dump(res, open('/root/analysis/h9/h9b_results.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
