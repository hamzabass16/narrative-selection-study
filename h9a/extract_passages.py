"""H9a passage extraction (Addendum 14.3): fixed rules, written before any text was retrieved.
For each society text: strip Project Gutenberg header/footer; split into paragraphs on blank lines
(Internet Archive OCR text: also on lines ending a sentence followed by an indented or capitalised line is NOT used; blank lines only);
drop the first 3% and last 7% of paragraphs (front matter, appendices, index); keep paragraphs of 40 to 400 words
in which at least 70% of characters are letters or spaces; for each MAC-D domain, candidates are paragraphs containing
at least one virtue or vice term of that domain; draw up to 12 per domain per society at random (seed 20261022)."""
import sys, os, re, json, random, collections
sys.path.insert(0, '/root/analysis/cci'); import macd
def clean(t):
    t = t.replace('\r\n', '\n')
    s = re.search(r'\*\*\* ?START OF[^\n]*\n', t)
    if s: t = t[s.end():]
    e = re.search(r'\*\*\* ?END OF', t)
    if e: t = t[:e.start()]
    return t
def paragraphs(t):
    ps = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'\n\s*\n', t)]
    ps = [p for p in ps if p]
    n = len(ps); ps = ps[int(0.03 * n): n - int(0.07 * n)]
    out = []
    for p in ps:
        w = len(p.split())
        if 40 <= w <= 400 and sum(c.isalpha() or c.isspace() for c in p) / len(p) >= 0.70: out.append(p)
    return out
def domains_in(p):
    n, c = macd.score(p)
    return {d for d in macd.DOMAINS if c.get(f'Virtue{d}', 0) + c.get(f'Vice{d}', 0) > 0}
def run(text_dir, out_path, per_domain=12, seed=20261022):
    items = []; stats = {}
    for fn in sorted(os.listdir(text_dir)):
        if not fn.endswith('.txt'): continue
        soc = fn[:-4]; ps = paragraphs(clean(open(os.path.join(text_dir, fn), encoding='utf-8', errors='replace').read()))
        cand = collections.defaultdict(list)
        for i, p in enumerate(ps):
            for d in domains_in(p): cand[d].append(i)
        rng = random.Random(f'{seed}-{soc}'); stats[soc] = {'paragraphs': len(ps)}
        for d in macd.DOMAINS:
            pick = sorted(rng.sample(cand[d], min(per_domain, len(cand[d]))))
            stats[soc][d] = [len(cand[d]), len(pick)]
            for i in pick: items.append(dict(society=soc, domain=d, para_index=i, text=ps[i]))
    rng = random.Random(seed); rng.shuffle(items)
    for k, it in enumerate(items): it['pid'] = f'V{k+1:04d}'
    json.dump(items, open(out_path, 'w'), indent=0); json.dump(stats, open(out_path.replace('.json', '_stats.json'), 'w'), indent=1)
    return items, stats
if __name__ == '__main__':
    items, stats = run(sys.argv[1], sys.argv[2]); print(len(items)); print(json.dumps(stats)[:2000])
