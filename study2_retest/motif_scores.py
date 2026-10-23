"""Motif-level scores from coder output (retest plan, Section 3.2). Fixed 23 October 2026, before any outcome was linked.

For each act: pro = +1 if (coop and rewarded) or (violation and punished); -1 if (violation and rewarded) or (coop and punished);
0 if the outcome is none.
Motif score (primary) = sum of pro over all acts (all targets). Secondary: the same excluding acts whose target is 'enemy'.
Per-behaviour score = sum of pro over acts of that behaviour.
Motif-level classification for the human check (trickster motifs): over violations of reciprocity, property, fairness,
group or family:
  'success' if at least one is rewarded and none punished;
  'notsuccess' if at least one is punished and none rewarded;
  'unclear' if such violations exist but outcomes are none or mixed;
  'no' if there is no such violation."""
import json
BEH = ['family', 'group', 'reciprocity', 'bravery', 'deference', 'fairness', 'property']
def pro(a):
    t, o = a.get('type'), a.get('outcome')
    if o == 'rewarded': return 1 if t == 'coop' else -1
    if o == 'punished': return -1 if t == 'coop' else 1
    return 0
def motif_row(rec):
    acts = rec.get('acts', []) or []
    r = {'motif_id': rec['motif_id'], 'n_acts': len(acts), 'score': sum(pro(a) for a in acts),
         'score_noenemy': sum(pro(a) for a in acts if a.get('target') != 'enemy')}
    for b in BEH:
        ab = [a for a in acts if a.get('behaviour') == b]
        r[f'has_{b}'] = int(len(ab) > 0); r[f's_{b}'] = sum(pro(a) for a in ab)
    v = [a for a in acts if a.get('type') == 'violation' and a.get('behaviour') in ('reciprocity', 'property', 'fairness', 'group', 'family')]
    rw = any(a.get('outcome') == 'rewarded' for a in v); pu = any(a.get('outcome') == 'punished' for a in v)
    r['trick_class'] = 'no' if not v else ('success' if rw and not pu else ('notsuccess' if pu and not rw else 'unclear'))
    return r
def load(path):
    return [motif_row(x) for x in json.load(open(path))]
