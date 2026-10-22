"""Score cleaned canonical texts with MAC-D per corpus_spec.md section 3. Run once; outputs cci_traditions.csv."""
import re, glob, os, collections, pandas as pd, numpy as np
D = '/root/data/ext/eMACDscore/emacscore/dictionaries/'
def load(fn):
    L = open(D + fn, encoding='utf-8').read().split('\n')
    i = [k for k, l in enumerate(L) if l.strip() == '%']
    cats = {l.split('\t')[0]: l.split('\t')[1] for l in L[i[0] + 1:i[1]]}
    lex = {}
    for l in L[i[1] + 1:]:
        if not l.strip(): continue
        p = l.split('\t'); lex[tuple(p[0].lower().split())] = [cats[x.strip()] for x in p[1:] if x.strip()]
    return lex
VIR, VIC = load('macdvirtue.dic'), load('macdvice.dic')
LEX = {}
for lx in (VIR, VIC):
    for k, v in lx.items(): LEX.setdefault(k, []).extend(v)
MAXN = max(len(k) for k in LEX)
TOK = re.compile(r"[a-z]+(?:'[a-z]+)*")
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
        else:
            i += 1
    return n, cnt
rows = []
for f in sorted(glob.glob('/root/analysis/cci/clean/*.txt')):
    trad = os.path.basename(f).split('__')[0]
    n, c = score(open(f, encoding='utf-8').read())
    rows.append(dict(tradition=trad, file=os.path.basename(f), tokens=n, **c))
df = pd.DataFrame(rows).fillna(0)
df.to_csv('/root/analysis/cci/macd_counts_by_file.csv', index=False)
dom = ['Family', 'Group', 'Reciprocity', 'Heroism', 'Deference', 'Fairness', 'Property']
g = df.groupby('tradition').sum(numeric_only=True)
out = pd.DataFrame(index=g.index); out['tokens'] = g.tokens
for d in dom:
    out[f'vir_{d}'] = 1e4 * g.get(f'Virtue{d}', 0) / g.tokens
    out[f'vic_{d}'] = 1e4 * g.get(f'Vice{d}', 0) / g.tokens
z = lambda s: (s - s.mean()) / s.std(ddof=1)
out['CCI'] = np.mean([z(out[f'vir_{d}']) for d in dom], axis=0)
out['CCI_net'] = np.mean([z(out[f'vir_{d}'] - out[f'vic_{d}']) for d in dom], axis=0)
out.to_csv('/root/analysis/cci/cci_traditions.csv')
pd.set_option('display.width', 250)
print(out[['tokens'] + [f'vir_{d}' for d in dom] + ['CCI', 'CCI_net']].round(2).sort_values('CCI').to_string())
