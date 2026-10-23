"""H9a passage extraction, version 2 (approved retest plan, H9a). Fixed 23 October 2026 before any version-2 passage was read.
Same cleaning and paragraph rules as extract_passages.py (version 1). New rule: a paragraph is a candidate for a domain if it
contains at least one MAC-D virtue or vice term of that domain AND at least one evaluation term from the list EVAL below.
Up to 30 candidates per domain per society are drawn at random (seed '20261023-<society>'). Societies: every text in
texts/ (30 sampled in version 1, 16 further verified candidates, 7 from the extra candidate search)."""
import sys, os, re, json, random, collections
sys.path.insert(0, '/root/analysis/cci'); sys.path.insert(0, '/root/analysis/h9a')
import macd
from extract_passages import clean, paragraphs, domains_in
EVAL = re.compile(r"\b(praise\w*|honou?r\w*|dishonou?r\w*|shame\w*|ashamed|disgrac\w*|punish\w*|penalt\w*|fined|approv\w*|disapprov\w*|"
                  r"despis\w*|contempt\w*|admir\w*|esteem\w*|virtu\w*|vices?|crimes?|criminal\w*|sins?|sinful|wrong\w*|wicked\w*|evil\w*|"
                  r"duty|duties|obligat\w*|obliged|improper\w*|forbid\w*|taboo\w*|tabu\w*|condemn\w*|blam\w*|reproach\w*|ridicul\w*|scorn\w*|"
                  r"reward\w*|reprehens\w*|laudabl\w*|commend\w*|applau\w*|infam\w*)\b", re.I)
def run(text_dir, out_path, per_domain=30):
    items = []; stats = {}
    for fn in sorted(os.listdir(text_dir)):
        if not fn.endswith('.txt'): continue
        soc = fn[:-4]
        ps = paragraphs(clean(open(os.path.join(text_dir, fn), encoding='utf-8', errors='replace').read()))
        cand = collections.defaultdict(list)
        for i, p in enumerate(ps):
            if not EVAL.search(p): continue
            for d in domains_in(p): cand[d].append(i)
        rng = random.Random(f'20261023-{soc}'); stats[soc] = {'paragraphs': len(ps)}
        for d in macd.DOMAINS:
            pick = sorted(rng.sample(cand[d], min(per_domain, len(cand[d]))))
            stats[soc][d] = [len(cand[d]), len(pick)]
            for i in pick: items.append(dict(society=soc, domain=d, para_index=i, text=ps[i]))
    rng = random.Random(20261023); rng.shuffle(items)
    for k, it in enumerate(items): it['pid'] = f'W{k + 1:05d}'
    json.dump(items, open(out_path, 'w'), indent=0); json.dump(stats, open(out_path.replace('.json', '_stats.json'), 'w'), indent=1)
    return items, stats
if __name__ == '__main__':
    items, stats = run('/root/analysis/h9a/texts', '/root/analysis/h9a/passages_v2.json')
    tot = collections.Counter(it['domain'] for it in items)
    print(len(items), dict(tot), 'societies', len(stats))
