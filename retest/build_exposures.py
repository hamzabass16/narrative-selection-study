"""Build polity-level exposures for the retest (plan Sections 3.1, 5 H5, 5 H8 Part A). No outcome is read here.
Value rule: present / inferred present = 1; absent / inferred absent = 0; unknown, suspected unknown, other = missing.
Several rows for one Equinox polity (several NGAs, disputed values) are averaged.
EPI = mean of the three egalitarian items, required >= 2 known.
Constraint index (H8 Part A) = mean of executive constraint by government, by non-government, impeachment; required >= 2 known.
Vessel codes (H5): moralizing high god (2019 Seshat export, 'High Gods (creator gods)' = moralizing), moral concern is primary
(Equinox), and MSP from Seshat's own 100-year dataset (polity mean)."""
import pandas as pd, numpy as np, io, re
R = '/root/analysis/retest/'
EQ = '/root/data/seshat_polaris/build_polaris_dataset/Equinox2020.05.2023.xlsx'
EPI_ITEMS = ['Ideological reinforcement of equality', 'Ideological thought equates elites and commoners', 'Ideological thought equates rulers and commoners']
DESC_ITEMS = ['Ideology reinforces prosociality', 'production of public goods', 'Moralizing norms are broad', 'Rulers are legitimated by gods']
CON_ITEMS = ['Constraint on executive by government', 'Constraint on executive by non-government', 'Impeachment']
VESSEL_EQ = ['Moral concern is primary']
def val(x):
    x = str(x).lower().strip()
    if 'unknown' in x: return np.nan
    if 'present' in x: return 1.0
    if 'absent' in x: return 0.0
    return np.nan

m = pd.read_csv(R + 'equinox_match_auto.csv')
dec = pd.read_csv(R + 'ambiguous_matches_decided.csv').set_index('current_polity')
m.loc[m.status == 'ambiguous', 'equinox_code'] = m.loc[m.status == 'ambiguous', 'name'].map(dec.chosen_code)
m['match'] = np.where(m.status == 'none', '', m.equinox_code.fillna(''))
m[['name', 'long_name', 'nga', 'start', 'end', 'status', 'equinox_code', 'overlap', 'candidates']].to_csv(R + 'equinox_match_final.csv', index=False)

e = pd.read_excel(EQ); e['code'] = e.Polity.str.replace('*', '', regex=False).str.strip()
e['v'] = e['Value.From'].map(val)
w = e[e.Variable.isin(EPI_ITEMS + DESC_ITEMS + CON_ITEMS + VESSEL_EQ)].groupby(['code', 'Variable']).v.mean().unstack()
ren = {EPI_ITEMS[0]: 'equality', EPI_ITEMS[1]: 'elites_eq_commoners', EPI_ITEMS[2]: 'rulers_eq_commoners',
       DESC_ITEMS[0]: 'prosociality', DESC_ITEMS[1]: 'public_goods_ideol', DESC_ITEMS[2]: 'norms_broad', DESC_ITEMS[3]: 'rulers_legit_gods',
       CON_ITEMS[0]: 'constr_gov', CON_ITEMS[1]: 'constr_nongov', CON_ITEMS[2]: 'impeachment', VESSEL_EQ[0]: 'moral_concern_primary'}
w = w.rename(columns=ren)
# moralizing high god from the 2019 export (old codes are the same as Equinox codes)
raw = open('/root/data/moralizing-gods/exportdat.csv', 'rb').read().decode('latin1').replace('\r\n', '\n').replace('\r', '\n')
x = pd.read_csv(io.StringIO(raw), low_memory=False); x['code'] = x.Polity.str.replace('*', '', regex=False).str.strip()
hg = x[x.Variable == 'High Gods (creator gods)'].copy()
hg['mhg'] = hg['Value From'].astype(str).str.lower().map(lambda s: 1.0 if 'moraliz' in s else (np.nan if 'unknown' in s or s in ('nan', '') else 0.0))
w = w.join(hg.groupby('code').mhg.mean(), how='outer')

out = m[['name', 'match']].merge(w, left_on='match', right_index=True, how='left')
out['epi_n'] = out[['equality', 'elites_eq_commoners', 'rulers_eq_commoners']].notna().sum(axis=1)
out['EPI'] = out[['equality', 'elites_eq_commoners', 'rulers_eq_commoners']].mean(axis=1).where(out.epi_n >= 2)
out['con_n'] = out[['constr_gov', 'constr_nongov', 'impeachment']].notna().sum(axis=1)
out['CONSTR'] = out[['constr_gov', 'constr_nongov', 'impeachment']].mean(axis=1).where(out.con_n >= 2)
cy = pd.read_excel('/root/data/seshat_polaris/SeshatDatasetAnalysis/test_scripts/100_yr_dataset.xlsx', sheet_name='SCV')
out = out.merge(cy.groupby('PolityName').MSP.mean().rename('MSP'), left_on='name', right_index=True, how='left')
out.to_csv(R + 'polity_exposures.csv', index=False)
fc = pd.read_csv('/root/analysis/frame/final_codes.csv')
f = pd.read_csv('/root/analysis/frame/polities_frame.csv')
has = out[out.EPI.notna()]
coded = set(fc.name)
print('current polities with EPI:', len(has), '| already termination-coded:', has.name.isin(coded).sum(),
      '| to code:', (~has.name.isin(coded)).sum())
hc = out[out.CONSTR.notna()]
print('with constraint index:', len(hc), '| coded:', hc.name.isin(coded).sum())
need = has[~has.name.isin(coded)].merge(f[['name', 'id', 'long_name', 'start_year', 'end_year', 'nga_name', 'censored_present']], on='name')
need.to_csv(R + 'to_code_terminations.csv', index=False)
print('censored at present among to-code:', int(need.censored_present.sum()))
