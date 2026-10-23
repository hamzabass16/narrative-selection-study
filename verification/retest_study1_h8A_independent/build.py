"""Step 1: build one row per coded polity with event status and exposures.

Written independently for verification. Reads only raw inputs.
"""
import numpy as np
import pandas as pd

FRAME = '/root/analysis/frame/polities_frame.csv'
CODES = '/root/analysis/frame/final_codes.csv'
CODES_G = '/root/analysis/retest/term/final_codes_G.csv'
EXPO = '/root/analysis/retest/polity_exposures.csv'


def load_polities():
    frame = pd.read_csv(FRAME)
    codes = pd.read_csv(CODES)[['polity_id', 'Q2', 'Q3', 'end_year']]
    codes_g = pd.read_csv(CODES_G)[['polity_id', 'Q2', 'Q3', 'end_year']]
    # use G codes only for polities missing from the main codes file
    codes_g = codes_g[~codes_g.polity_id.isin(codes.polity_id)]
    allcodes = pd.concat([codes, codes_g], ignore_index=True)
    allcodes = allcodes.rename(columns={'end_year': 'code_end_year'})

    df = frame.merge(allcodes, left_on='id', right_on='polity_id', how='inner')

    # event coding
    q2 = df.Q2.astype(str).str.strip()
    q3 = df.Q3.astype(str).str.strip()
    event = pd.Series(np.nan, index=df.index)
    etype = pd.Series('none', index=df.index, dtype=object)

    internal = q2.isin(['T1a', 'T1b', 'T1c'])
    conquest = q2.eq('T2')
    other = q2.isin(['T3', 'T4', 'T5'])
    t9 = q2.eq('T9')
    nonevent = q2.isin(['T0', 'T6', 'T7', 'T8'])

    event[internal | conquest | other] = 1
    etype[internal] = 'internal'
    etype[conquest] = 'conquest'
    etype[other] = 'other'
    event[t9 & q3.eq('Y')] = 1
    etype[t9 & q3.eq('Y')] = 'other_T9'
    event[t9 & q3.eq('N')] = 0
    event[nonevent] = 0
    # censored_present overrides everything
    cens = df.censored_present.astype(str).str.lower().eq('true')
    event[cens] = 0
    etype[cens] = 'none'
    etype[event.isna()] = 'unknown'
    etype[event.eq(0)] = 'none'

    df['event'] = event
    df['etype'] = etype
    df['internal'] = (etype == 'internal').astype(int)
    df['conquest'] = (etype == 'conquest').astype(int)
    df['q2clean'] = q2

    expo = pd.read_csv(EXPO)[['name', 'EPI', 'CONSTR', 'rulers_eq_commoners']]
    df = df.merge(expo, on='name', how='left')
    return df


if __name__ == '__main__':
    d = load_polities()
    print(d.shape)
    print(d.etype.value_counts(dropna=False))
    print('event status unknown:', d.event.isna().sum())
