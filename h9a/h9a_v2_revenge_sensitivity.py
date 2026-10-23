"""POST HOC check (written after coder reports showed a split on revenge, before the H9a v2 results were computed).
Coders disagreed on whether blood revenge counts as Reciprocity. This script reruns two quantities with revenge passages
removed from the Reciprocity domain, using the final codes written by h9a_v2_analysis.py's logic:
 1. Reciprocity relevance and valence agreement on the double-coded sample, excluding passages whose paragraph text
    mentions revenge (reveng*, aveng*, vengeance, retaliat*, blood feud).
 2. Reciprocity POS/NEG counts and NEG share, excluding passages whose first-coder behaviour or quote mentions revenge.
Read-only: it imports nothing from the frozen script and changes no file except h9a_v2_revenge_sensitivity.json."""
import json, glob, re, numpy as np, krippendorff
B = '/root/analysis/h9a/'
RX = re.compile(r'reveng|aveng|vengeance|retaliat|blood[- ]feud|blood[- ]money', re.I)
def load(p):
    out = {}
    for f in sorted(glob.glob(p)):
        for r in json.load(open(f)): out[r['pid']] = r
    return out
items = {it['pid']: it for it in json.load(open(B + 'passages_v2.json'))}
p1 = load(B + 'codes_v2/pass1/*.json'); p2 = load(B + 'codes_v2/pass2/D*.json')
def al(a, b):
    lab = {v: i for i, v in enumerate(sorted(set(a) | set(b)))}
    if len(lab) < 2: return float('nan')
    return float(krippendorff.alpha(reliability_data=np.vstack([[lab[x] for x in a], [lab[x] for x in b]]).astype(float), level_of_measurement='nominal'))
OUT = {}
for lab, keep in [('all_reciprocity', lambda p: True), ('reciprocity_no_revenge_text', lambda p: not RX.search(items[p]['text']))]:
    ps = [p for p in p2 if p in p1 and items[p]['domain'] == 'Reciprocity' and keep(p)]
    ra = [p1[p]['relevant'] for p in ps]; rb = [p2[p]['relevant'] for p in ps]
    va = [p1[p]['valence'] for p in ps]; vb = [p2[p]['valence'] for p in ps]
    OUT[lab] = dict(n=len(ps), relevance_agree=sum(a == b for a, b in zip(ra, rb)), relevance_alpha=al(ra, rb),
                    valence_agree=sum(a == b for a, b in zip(va, vb)), valence_alpha=al(va, vb))
rec = [p for p, r in p1.items() if items[p]['domain'] == 'Reciprocity' and r['relevant'] == 'Y' and r['valence'] in ('POS', 'NEG')]
rev = [p for p in rec if RX.search(p1[p]['behaviour'] + ' ' + p1[p]['quote'])]
OUT['first_coder_reciprocity'] = dict(valenced=len(rec), revenge_valenced=len(rev),
                                      revenge_pos=sum(p1[p]['valence'] == 'POS' for p in rev), revenge_neg=sum(p1[p]['valence'] == 'NEG' for p in rev),
                                      pos_without_revenge=sum(p1[p]['valence'] == 'POS' for p in rec if p not in rev),
                                      neg_without_revenge=sum(p1[p]['valence'] == 'NEG' for p in rec if p not in rev), revenge_pids=rev)
json.dump(OUT, open(B + 'h9a_v2_revenge_sensitivity.json', 'w'), indent=1)
print(json.dumps(OUT, indent=1))
