"""Check of a scorer bug found by the independent verifier (23 Oct 2026): dictionary entries containing hyphens
(e.g. 'mother-in-law', 'give-and-take') were keyed on whitespace only, while text tokens never contain hyphens, so these
43 entries could never match. Fix: tokenize dictionary entries with the same rule as the text (corpus_spec section 3).
This script re-scores the canonical texts with the fixed key and compares tradition CCIs with the originals."""
import re, glob, os, sys, collections, numpy as np, pandas as pd
sys.path.insert(0, '/root/analysis/cci'); import macd
TOK = macd.TOK
LEX = {}
for lx in (macd._load('macdvirtue.dic'), macd._load('macdvice.dic')):
    for k, v in lx.items():
        key = tuple(TOK.findall(' '.join(k).replace('’', "'")))
        if key: LEX.setdefault(key, []).extend(v)
hy = [k for k in macd.LEX if any('-' in w for w in k)]
print('hyphenated entries:', len(hy), hy[:12])
MAXN = max(len(k) for k in LEX)
def norm(t):
    if (t,) in LEX: return t
    for suf in ('eth', 'est'):
        if t.endswith(suf) and len(t) > len(suf) + 2:
            s = t[:-len(suf)]
            for c in (s, s + 'e', s + 's'):
                if (c,) in LEX: return c
    return t
def score(text):
    toks = [norm(t) for t in TOK.findall(text.lower().replace('’', "'"))]
    n = len(toks); cnt = collections.Counter(); i = 0
    while i < n:
        for L in range(min(MAXN, n - i), 0, -1):
            key = tuple(toks[i:i + L])
            if key in LEX:
                for c in LEX[key]: cnt[c] += 1
                i += L; break
        else: i += 1
    return n, cnt
rows = []
for f in sorted(glob.glob('/root/analysis/cci/clean/*.txt')):
    n, c = score(open(f, encoding='utf-8').read()); rows.append(dict(tradition=os.path.basename(f).split('__')[0], tokens=n, **c))
df = pd.DataFrame(rows).fillna(0); g = df.groupby('tradition').sum(numeric_only=True)
dom = macd.DOMAINS; z = lambda s: (s - s.mean()) / s.std(ddof=1)
out = pd.DataFrame(index=g.index)
for d in dom:
    out[f'vir_{d}'] = 1e4 * g.get(f'Virtue{d}', 0) / g.tokens; out[f'vic_{d}'] = 1e4 * g.get(f'Vice{d}', 0) / g.tokens
out['CCI'] = np.mean([z(out[f'vir_{d}']) for d in dom], axis=0)
out['CCI_net'] = np.mean([z(out[f'vir_{d}'] - out[f'vic_{d}']) for d in dom], axis=0)
old = pd.read_csv('/root/analysis/cci/cci_traditions.csv', index_col=0)
cmp = pd.DataFrame({'CCI_old': old.CCI, 'CCI_fixed': out.CCI, 'net_old': old.CCI_net, 'net_fixed': out.CCI_net})
cmp['rank_old'] = cmp.CCI_old.rank(ascending=False).astype(int); cmp['rank_fixed'] = cmp.CCI_fixed.rank(ascending=False).astype(int)
print(cmp.round(3).sort_values('rank_old').to_string())
print('r CCI', round(cmp.CCI_old.corr(cmp.CCI_fixed), 5), 'r net', round(cmp.net_old.corr(cmp.net_fixed), 5), 'max abs diff', round((cmp.CCI_old - cmp.CCI_fixed).abs().max(), 4))
out.to_csv('/root/analysis/cci/fix/cci_traditions_hyphenfix.csv'); cmp.to_csv('/root/analysis/cci/fix/cci_hyphenfix_comparison.csv')
