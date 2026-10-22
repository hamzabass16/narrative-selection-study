"""Diagnostic: effect of (i) dropping the 8 underscore-suffixed motif columns and (ii) original vs my flags.
Uses my own build/regression helpers."""
import pandas as pd, numpy as np, sys
sys.argv = ['x', 'alpha_apos']
import build_cci as B, ea_models as EAM, country_models as CM
o = pd.read_csv('/root/analysis/study2/motif_macd_flags.csv').set_index('motif_id')
mine = pd.read_csv('flags_alpha_apos.csv').set_index('motif_id')
under = ['b28e','d4aa','e15','e15a','e15b','e18','h36g1','m81']
print(mine.loc[under, ['virtue_any','vice_any','virtue_hits','vice_hits']])
orig_as_mine = mine.copy()
for d in B.DOMAINS:
    orig_as_mine[f'virtue_{d}'] = o.loc[mine.index, f'v_{d}']
    orig_as_mine[f'vice_{d}'] = o.loc[mine.index, f'x_{d}']
ea = pd.read_stata(B.D + 'Ethnographic_Atlas_Regressions_Ready.dta', columns=['atlas','motifs_total','v33','v34','v98','continent_EA','lnyear_firstpub','lnnmbr_title'], convert_categoricals=False)
c = pd.read_stata(B.D + 'Country_Regressions_Ready.dta', columns=['cntry','lntrust_wvsavg','trust_gps','lnyear_firstpub','lnnmbr_title'])
for flabel, F in [('my flags', mine), ('orig flags', orig_as_mine)]:
    for drop8 in [False, True]:
        B.flags = F
        Xe, _ = B.load_incidence('Motifs_EA_groups.dta', 'atlas')
        Xc, _ = B.load_incidence('Motifs_Countries.dta', 'cntry')
        if drop8:
            Xe = Xe.drop(columns=under); Xc = Xc.drop(columns=under)
        r = B.build(Xe, weighted=False)
        df = ea.merge(r[['CCI','CCI_net']], left_on='atlas', right_index=True, how='left')
        df = df[df.motifs_total > 4]
        e1 = EAM.areg_cluster(df, 'v33', 'CCI', ['lnyear_firstpub','lnnmbr_title'], [], 'continent_EA', 'v98')
        e2 = EAM.areg_cluster(df, 'v33', 'CCI', ['lnyear_firstpub','lnnmbr_title'], ['v34'], 'continent_EA', 'v98')
        rc = B.build(Xc, weighted=True)
        dc = c.merge(rc[['CCI']], left_on='cntry', right_index=True)
        c1 = CM.ols_hc1(dc, 'lntrust_wvsavg', 'CCI', CM.CONT0); c2 = CM.ols_hc1(dc, 'trust_gps', 'CCI', CM.CONT0)
        print(f"{flabel:10s} drop8={drop8!s:5s} EA std={e1['std_beta']:.4f} p={e1['p']:.3f} | +v34 std={e2['std_beta']:.4f} p={e2['p']:.3f}"
              f" | WVS std={c1['std_beta']:.4f} | GPS std={c2['std_beta']:.4f}")
