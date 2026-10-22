import pandas as pd, numpy as np
d = pd.read_pickle("/root/analysis/verify3/vdem_slim.pkl")
print(d.year.min(), d.year.max())
print(d.v2x_regime.value_counts(dropna=False))
print("regendtype", d.v2regendtype.value_counts(dropna=False).sort_index())
print("regidnr nunique", d.v2regidnr.nunique(), "na", d.v2regidnr.isna().sum())
print("regiongeo", d.e_regiongeo.value_counts(dropna=False).sort_index())
print(d[["v2exl_legitideolcr_4","v2exl_legitideol_osp","v2clrelig"]].describe())
print("last years with gdppc", d.loc[d.e_gdppc.notna(),"year"].max(), "pop", d.loc[d.e_pop.notna(),"year"].max(), "lifeex", d.loc[d.e_pelifeex.notna(),"year"].max())
# check unique country-year
print(d.duplicated(["country_id","year"]).sum())
# does regidnr span countries?
g = d.dropna(subset=["v2regidnr"]).groupby("v2regidnr").country_id.nunique()
print("regimes spanning >1 country", (g>1).sum())
