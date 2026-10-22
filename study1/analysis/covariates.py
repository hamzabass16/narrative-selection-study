"""Polity-level covariates from the current Seshat release (Turchin et al. 2018 and 2022 constructions, simplified).
Binary codes: present / inferred present = 1; absent / inferred absent = 0; A~P or P~A = 0.5; unknown, uncoded = missing.
Several records per polity (time-specific or disputed) are averaged."""
import json, numpy as np, pandas as pd
db = json.load(open('/root/analysis/seshat/seshat_current_2026-10-17.json'))
T = lambda k: pd.DataFrame(db[k]['rows'], columns=db[k]['cols'])
BIN = {'present': 1, 'inferred present': 1, 'absent': 0, 'inferred absent': 0, 'A~P': .5, 'P~A': .5, 'inferred A~P': .5}
def binvar(k):
    t = T(k); col = t.columns[7]; t['v'] = t[col].map(BIN)
    return t.dropna(subset=['v', 'polity']).groupby('polity').v.mean()
def numvar(k):
    t = T(k); a, b = t.columns[7], t.columns[8]
    t['v'] = t[[a, b]].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    return t.dropna(subset=['v', 'polity']).groupby('polity').v.mean()
pol = T('core/polities').set_index('id')
C = pd.DataFrame(index=pol.index)
# Social complexity characteristics (Turchin et al. 2018)
C['PolPop'] = np.log10(numvar('sc/polity-populations').clip(lower=1))
C['PolTerr'] = np.log10(numvar('sc/polity-territories').clip(lower=1))
C['CapPop'] = np.log10(numvar('sc/population-of-the-largest-settlements').clip(lower=1))
C['Hierarchy'] = pd.concat([numvar(f'sc/{k}') for k in ['settlement-hierarchies', 'administrative-levels', 'religious-levels', 'military-levels']], axis=1).mean(axis=1)
def share(keys):
    m = pd.concat([binvar(f'sc/{k}') for k in keys], axis=1)
    return m.mean(axis=1).where(m.notna().sum(axis=1) >= max(1, len(keys) // 2))
C['Government'] = share(['professional-military-officers', 'professional-soldiers', 'professional-priesthoods', 'full-time-bureaucrats', 'examination-systems', 'merit-promotions', 'specialized-government-buildings', 'formal-legal-codes', 'judges', 'courts', 'professional-lawyers'])
C['Infrastructure'] = share(['irrigation-systems', 'drinking-water-supplies', 'markets', 'food-storage-sites', 'roads', 'bridges', 'canals', 'ports', 'mines-or-quarries'])
C['Writing'] = share(['mnemonic-devices', 'nonwritten-records', 'written-records', 'scripts', 'non-phonetic-writings', 'phonetic-alphabetic-writings'])
C['Texts'] = share(['lists-tables-and-classifications', 'calendars', 'sacred-texts', 'religious-literatures', 'practical-literatures', 'histories', 'philosophies', 'scientific-literatures', 'fictions'])
C['Money'] = share(['articles', 'tokens', 'precious-metals', 'foreign-coins', 'indigenous-coins', 'paper-currencies'])
C['script'] = binvar('sc/scripts')
# Military technology (Turchin et al. 2022): within-category share present, summed over 6 categories
cats = {'metal': ['coppers', 'bronzes', 'irons', 'steels'],
        'projectile': ['javelins', 'atlatls', 'slings', 'self-bows', 'composite-bows', 'crossbows', 'tension-siege-engines', 'sling-siege-engines', 'gunpowder-siege-artilleries', 'handheld-firearms'],
        'weapon': ['war-clubs', 'battle-axes', 'daggers', 'swords', 'spears', 'polearms'],
        'animal': ['dogs', 'donkeys', 'horses', 'camels', 'elephants'],
        'armor': ['wood-bark-etc', 'leathers', 'shields', 'helmets', 'breastplates', 'limb-protections', 'scaled-armors', 'laminar-armors', 'plate-armors', 'chainmails'],
        'fort': ['settlement-in-defensive-positions', 'wooden-palisades', 'earth-ramparts', 'ditches', 'moats', 'stone-walls-non-mortared', 'stone-walls-mortared', 'fortified-camps', 'complex-fortifications', 'modern-fortifications']}
parts = {}
for c, ks in cats.items():
    m = pd.concat([binvar(f'wf/{k}') for k in ks], axis=1)
    parts[c] = m.mean(axis=1).where(m.notna().sum(axis=1) >= len(ks) // 2)
P = pd.DataFrame(parts)
C['MilTech'] = P.sum(axis=1, min_count=4) * 6 / P.notna().sum(axis=1).replace(0, np.nan)
C['iron'] = binvar('wf/irons'); C['cavalry'] = binvar('wf/horses')
# Religion variables (Seshat expert codes)
rt = lambda k: binvar(f'rt/{k}')
C['MSP'] = rt('moralizing-supernatural-punishment-and-reward')
C['MER'] = rt('moralizing-enforcement-of-rulers')
# Impersonal institutions (H5 mediator): formal legal code, courts, judges, professional lawyers
C['ImpInst'] = share(['formal-legal-codes', 'courts', 'judges', 'professional-lawyers'])
# Geography: absolute latitude of the polity's capital (first verified capital), else home NGA
cap = T('general/polity-capitals'); capt = T('core/capitals').set_index('id')
cap['lat'] = pd.to_numeric(cap.polity_cap.map(capt.latitude), errors='coerce')
lat = cap.dropna(subset=['lat']).groupby('polity').lat.first()
nga = T('core/ngas').set_index('id'); nlat = pd.to_numeric(pol.home_nga.map(nga.latitude), errors='coerce')
C['abslat'] = lat.reindex(pol.index).fillna(nlat).abs()
C['macro_region'] = pol.home_seshat_region.map(T('core/regions').set_index('id').mac_region)
C['region'] = pol.home_seshat_region
# CrisisDB polity-ending crisis severity (H8b): count of severe consequences present
cc = T('crisisdb/crisis-consequences')
sev = ['civil_war', 'extermination', 'collapse', 'fragmentation', 'conquest', 'decline']
for s in sev: cc[s] = cc[s].map({'P': 1, 'IP': 1, 'A': 0, 'IA': 0})
cce = cc[cc.crisis_case_id.astype(str).str.endswith('@end')]
C['crisis_end_severity'] = cce.assign(sv=cce[['civil_war', 'extermination', 'collapse']].sum(axis=1, min_count=1)).groupby('polity').sv.max()
C.to_csv('/root/analysis/study1/covariates.csv')
print(C.describe().T[['count', 'mean', 'std']].round(2).to_string())
