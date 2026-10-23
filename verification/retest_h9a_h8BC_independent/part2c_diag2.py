"""More Part C variants: untruncated S3 window, tenure definitions, near-zero tenures."""
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
src = open("/root/analysis/verify4/part2c_diag.py").read().split("base = rows()")[0]
ns = {}
exec(src, ns)
a, Vc, fit, rows = ns["a"], ns["Vc"], ns["fit"], ns["rows"]

base = rows()
print(base.loc[base["ten"] <= 0, ["obsid", "sy", "ten", "exit", "fate"]])
# leaders in both model samples
both = base.dropna(subset=["irregular", "badfate", "lgdp", "lpop"])
print("in both samples:", len(both))

# variant: untruncated S3 window (start..start+2 regardless of end)
def rows_untrunc():
    out = []
    for _, L in a.iterrows():
        sy, cc = L["start"].year, int(L["ccode"])
        keys = [(cc, y) for y in range(sy, sy + 3) if (cc, y) in Vc.index]
        if not keys:
            continue
        sub = Vc.loc[keys]
        s = sub.loc[sub["autoc"] == 1, "S"].dropna()
        if s.empty:
            continue
        out.append({"obsid": L["obsid"], "S3u": s.mean()})
    return pd.DataFrame(out)
U = rows_untrunc()
print("untruncated window leaders:", len(U))
m = base.merge(U, on="obsid", how="outer", indicator=True)
print(m["_merge"].value_counts())

# variant: tenure in calendar years / with 0.1 floor applied differently
for name, f in {"cal_years": lambda r: max(r["end"].year - r["start"].year, 0.1)}.items():
    t = a.set_index("obsid").apply(f, axis=1)
    B = base.copy(); B["ltenure"] = np.log(B["obsid"].map(t))
    print(name, fit(B))
