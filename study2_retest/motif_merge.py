"""Merge motif codes, compute reliability on the 20% double-coded set, and compare with the MTurk human codes.
Primary codes: main batches (first coder); pilot motifs keep coder A's codes but are excluded from society scores
(protocol Section 5.5). Fixed before any outcome is linked."""
import json, glob, numpy as np, pandas as pd, krippendorff
from motif_scores import motif_row, BEH
B = '/root/analysis/s2r/codes/'
main = []
for f in sorted(glob.glob(B + 'out/main_*.json')): main += json.load(open(f))
dbl = []
for f in sorted(glob.glob(B + 'out/dbl_*.json')): dbl += json.load(open(f))
pilotA = json.load(open(B + 'out/pilot_A.json'))
smp = json.load(open(B + 'samples.json'))
red = pd.read_csv('/root/analysis/s2r/motifs_redacted.csv')
ids_main = [x['motif_id'] for x in main]; assert len(ids_main) == len(set(ids_main)) == 2436
assert set(ids_main) | set(smp['pilot']) == set(red.motif_id)
P = pd.DataFrame([motif_row(x) for x in main + pilotA]).set_index('motif_id')
P['pilot'] = P.index.isin(smp['pilot'])
Dd = pd.DataFrame([motif_row(x) for x in dbl]).set_index('motif_id'); assert set(Dd.index) == set(smp['double'])
A1 = P.loc[Dd.index]
def al(a, b, lvl): return float(krippendorff.alpha(reliability_data=np.vstack([np.asarray(a, float), np.asarray(b, float)]), level_of_measurement=lvl))
rel = {'n_double': int(len(Dd)), 'score_interval': al(A1.score.clip(-3, 3), Dd.score.clip(-3, 3), 'interval'),
       'sign_ordinal': al(np.sign(A1.score), np.sign(Dd.score), 'ordinal'), 'any_act': al(A1.n_acts > 0, Dd.n_acts > 0, 'nominal')}
for b in BEH:
    rel[f'{b}_presence'] = al(A1[f'has_{b}'], Dd[f'has_{b}'], 'nominal')
    rel[f'{b}_sign'] = al(np.sign(A1[f's_{b}']), np.sign(Dd[f's_{b}']), 'ordinal')
    rel[f'{b}_n_acts_coder1'] = int(A1[f'has_{b}'].sum())
rel['trick_class'] = al(A1.trick_class.map({'no': 0, 'success': 1, 'notsuccess': 2, 'unclear': 3}), Dd.trick_class.map({'no': 0, 'success': 1, 'notsuccess': 2, 'unclear': 3}), 'nominal')
# human check against MTurk (281 trick/deceive/cheat motifs; about 18 workers each)
mt = pd.read_stata('/root/data/mx_folklore/orig/trick_deceive_cheat_motifs_classifications.dta').set_index('motif_id')
cats = ['anti_success', 'anti_notsuccess', 'anti_unclear', 'anti_no']
mt['human_major'] = mt[cats].idxmax(axis=1).str.replace('anti_', '')
mt['human_share_major'] = mt[cats].max(axis=1)
common = mt.index.intersection(P.index)
ai = P.loc[common, 'trick_class']
hc = mt.loc[common, 'human_major']
lab = {'success': 0, 'notsuccess': 1, 'unclear': 2, 'no': 3}
hum = {'n_motifs': int(len(common)), 'agree_with_human_majority': float((ai == hc).mean()),
       'alpha_ai_vs_majority': al(ai.map(lab), hc.map(lab), 'nominal'),
       'ai_class_counts': ai.value_counts().to_dict(), 'human_majority_counts': hc.value_counts().to_dict()}
# among motifs where humans saw an antisocial act whose outcome they agreed on (success or notsuccess majority)
sub = hc.isin(['success', 'notsuccess']) & ai.isin(['success', 'notsuccess'])
hum['agree_on_outcome_when_both_code_outcome'] = float((ai[sub] == hc[sub]).mean()); hum['n_both_outcome'] = int(sub.sum())
# expected agreement between two random human workers (from the shares) and Fleiss kappa
pk = mt.loc[common, cats].values; n = mt.loc[common, 'nmbr_classifications'].values
Pi = ((pk * n[:, None]) * (pk * n[:, None] - 1)).sum(1) / (n * (n - 1))
pbar = Pi.mean(); pj = (pk * n[:, None]).sum(0) / n.sum(); pe = (pj ** 2).sum()
hum['human_pairwise_agreement'] = float(pbar); hum['human_fleiss_kappa'] = float((pbar - pe) / (1 - pe))
# AI agreement with a random worker, comparable to the human pairwise figure
hum['ai_agreement_with_random_worker'] = float(np.mean([mt.loc[m, 'anti_' + c] for m, c in zip(common, ai)]))
json.dump({'reliability_double': rel, 'human_check': hum}, open(B + 'reliability_and_human_check.json', 'w'), indent=1, default=float)
P.to_csv(B + 'motif_codes_primary.csv')
print(json.dumps({'reliability_double': rel, 'human_check': hum}, indent=1, default=float))
