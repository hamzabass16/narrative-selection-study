import pandas as pd
df = pd.read_pickle("/root/data/ext_vdem/vdem.pkl")
print(type(df), df.shape)
need = ["country_name","country_text_id","country_id","year","v2x_regime","v2x_polyarchy",
        "v2clkill","v2cltort","v2csreprss","v2exrescon","v2x_jucon","v2xlg_legcon","v2dlencmps",
        "v2regidnr","v2regendtype","e_regiongeo","e_gdppc","e_pop","e_pelifeex",
        "v2exl_legitideolcr_4","v2exl_legitideol_osp","v2clrelig","v2exl_legitideol"]
missing = [c for c in need if c not in df.columns]
print("missing:", missing)
keep = [c for c in need if c in df.columns]
s = df[keep].copy()
print(s.dtypes)
s.to_pickle("/root/analysis/verify3/vdem_slim.pkl")
print(s.head())
