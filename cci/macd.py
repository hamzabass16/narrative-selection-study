"""MAC-D scoring functions (same rules as score_macd.py / corpus_spec.md section 3), importable."""
import re, collections
D = '/root/data/ext/eMACDscore/emacscore/dictionaries/'
DOMAINS = ['Family', 'Group', 'Reciprocity', 'Heroism', 'Deference', 'Fairness', 'Property']
def _load(fn):
    L = open(D + fn, encoding='utf-8').read().split('\n')
    i = [k for k, l in enumerate(L) if l.strip() == '%']
    cats = {l.split('\t')[0]: l.split('\t')[1] for l in L[i[0] + 1:i[1]]}
    lex = {}
    for l in L[i[1] + 1:]:
        if not l.strip(): continue
        p = l.split('\t'); lex[tuple(p[0].lower().split())] = [cats[x.strip()] for x in p[1:] if x.strip()]
    return lex
LEX = {}
for lx in (_load('macdvirtue.dic'), _load('macdvice.dic')):
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
    toks = [norm(t) for t in TOK.findall(str(text).lower().replace('’', "'"))]
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
