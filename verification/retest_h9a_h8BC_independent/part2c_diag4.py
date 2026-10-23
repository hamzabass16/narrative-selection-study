"""Test: are the zero-day tenures the off-by-one (log of 0 tenure treated as missing)?"""
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
src = open("/root/analysis/verify4/part2c_diag.py").read().split("base = rows()")[0]
ns = {}
exec(src, ns)
fit, rows = ns["fit"], ns["rows"]
base = rows()
z = base[base["ten"] <= 0]
print(z[["obsid", "ten", "lgdp", "irregular", "badfate"]])
B = base.copy()
B.loc[B["ten"] <= 0, "ltenure"] = np.nan
print("zero tenure -> missing:", fit(B))
