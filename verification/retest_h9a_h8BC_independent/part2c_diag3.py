"""Which leaders have an entry year missing from V-Dem (for that COW code)?"""
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
src = open("/root/analysis/verify4/part2c_diag.py").read().split("base = rows()")[0]
ns = {}
exec(src, ns)
a, Vc, fit, rows = ns["a"], ns["Vc"], ns["fit"], ns["rows"]
base = rows()
base["entry_in_vdem"] = [(c, y) in Vc.index for c, y in zip(base["ccode"], base["sy"])]
base["entry_autoc_S"] = [((c, y) in Vc.index) and Vc.loc[(c, y), "autoc"] == 1 and pd.notna(Vc.loc[(c, y), "S"]) for c, y in zip(base["ccode"], base["sy"])]
cols = ["obsid", "sy", "gdp_year", "exit", "fate", "entry_in_vdem", "entry_autoc_S"]
print(base.loc[~base["entry_in_vdem"], cols].to_string())
# variant: region taken from entry year only (NaN if entry year not in V-Dem)
B = base.copy()
B["region"] = [str(int(Vc.loc[(c, y), "e_regiongeo"])) if (c, y) in Vc.index else np.nan for c, y in zip(B["ccode"], B["sy"])]
print("region from entry year:", fit(B))
# variant: covariates from entry year if present, else first available (already base); drop leaders whose entry year absent
C = base[base["entry_in_vdem"]]
print("drop leaders whose entry year absent from V-Dem:", fit(C))
