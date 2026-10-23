"""Diagnostics for the Part B / Part C count gaps: try definition variants one at a time."""
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import importlib.util

spec = importlib.util.spec_from_file_location("p2", "/root/analysis/verify4/part2_h8.py")
# Reuse the verifier's own functions (part2_h8.py in verify4, not any original analysis script).
src = open("/root/analysis/verify4/part2_h8.py").read()
src = src.split("partB = {}")[0]  # definitions only, skip the main runs
ns = {}
exec(src, ns)
v, A, R, clustered_logit, VIOLENT, ORDERLY = (ns[k] for k in ["v", "A", "R", "clustered_logit", "VIOLENT", "ORDERLY"])

# autocracy indicator with undetermined years as missing
undet = v["v2x_regime"].isna() & v["v2x_polyarchy"].isna()
R2 = R.copy()
key = v.set_index(["country_id", "year"])
und = pd.Series(undet.values, index=pd.MultiIndex.from_arrays([v["country_id"], v["year"]]))
R2["undet"] = und.reindex(pd.MultiIndex.from_arrays([R2["country_id"], R2["year"]])).values
R2["autoc_nan"] = R2["autoc"].where(~R2["undet"].astype(bool))


def table(R, lag, share_col="autoc", tie="first", drop2025=False, last_from="all", strict=False):
    if drop2025:
        R = R[R["year"] <= 2024]
    rows = []
    for rid, g in R.groupby("v2regidnr"):
        last = g["year"].max() if last_from == "all" else g.loc[g["autoc"] == 1, "year"].max()
        s = g.loc[g["year"] <= last - lag, "S"].mean()
        et = g["v2regendtype"].dropna()
        if et.empty:
            et = np.nan
        elif tie == "first":
            et = et.value_counts().idxmax()
        elif tie == "last_year":
            et = g.loc[g["year"].idxmax(), "v2regendtype"]
        fr = g.loc[g["year"].idxmin()]
        rows.append({"rid": rid, "country_id": g["country_id"].iloc[0], "first": g["year"].min(),
                     "nyears": len(g), "share": g[share_col].mean(), "S": s, "endtype": et,
                     "region": fr["e_regiongeo"]})
    T = pd.DataFrame(rows)
    keep = (T["share"] > 0.5) if strict else (T["share"] >= 0.5)
    T = T[keep & T["S"].notna()].copy()
    T["violent"] = np.where(T["endtype"].isin(VIOLENT), 1.0, np.where(T["endtype"].isin(ORDERLY), 0.0, np.nan))
    T["logyears"] = np.log(T["nyears"])
    T["qc"] = (T["first"] // 25 * 25).astype(int).astype(str)
    T["region"] = T["region"].astype(int).astype(str)
    return T


def fit(T):
    M = T.dropna(subset=["violent"]).copy()
    M["zS"] = (M["S"] - T["S"].mean()) / T["S"].std()
    r = clustered_logit(M, "violent", ["zS", "logyears", "qc", "region"], "country_id")
    return len(T), len(M), r.get("OR"), r.get("lo"), r.get("hi"), r.get("p")


variants = {
    "base": dict(),
    "share_over_determined_years": dict(share_col="autoc_nan"),
    "endtype_last_year": dict(tie="last_year"),
    "drop_2025": dict(drop2025=True),
    "last_autoc_year": dict(last_from="autoc"),
    "strict_gt_half": dict(strict=True),
}
for name, kw in variants.items():
    for lag in [10, 0]:
        print(name, "lag", lag, fit(table(R2, lag, **kw)))
