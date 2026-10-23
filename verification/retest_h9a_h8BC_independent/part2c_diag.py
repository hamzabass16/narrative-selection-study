"""Diagnostics for the Part C off-by-one: try covariate-window variants."""
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
src = open("/root/analysis/verify4/part2_h8.py").read().split("partB = {}")[0]
ns = {}
exec(src, ns)
v, A, clustered_logit = ns["v"], ns["A"], ns["clustered_logit"]

a = pd.read_stata("/root/data/ext2/archigos/Archigos_4.1_stata14.dta")
a["start"] = pd.to_datetime(a["startdate"])
a["end"] = pd.to_datetime(a["enddate"])
a = a[a["start"].dt.year >= 1875].copy()

Vc = v.dropna(subset=["COWcode"]).copy()
Vc["COWcode"] = Vc["COWcode"].astype(int)
Vc = Vc.merge(A[["country_id", "year", "S"]], on=["country_id", "year"], how="left")
Vc = Vc.set_index(["COWcode", "year"]).sort_index()


def rows(cov="window", region_from="window"):
    out = []
    for _, L in a.iterrows():
        sy, ey, cc = L["start"].year, L["end"].year, int(L["ccode"])
        years = list(range(sy, min(sy + 2, ey) + 1))
        keys = [(cc, y) for y in years if (cc, y) in Vc.index]
        if not keys:
            continue
        sub = Vc.loc[keys]
        s = sub.loc[sub["autoc"] == 1, "S"].dropna()
        if s.empty:
            continue
        if cov == "window":
            csub = sub
        elif cov == "autoc_years":
            csub = sub[sub["autoc"] == 1]
        elif cov == "S_years":
            csub = sub[sub["S"].notna() & (sub["autoc"] == 1)]
        elif cov == "full3":
            k3 = [(cc, y) for y in range(sy, sy + 3) if (cc, y) in Vc.index]
            csub = Vc.loc[k3]
        gdp, pop = csub["e_gdppc"].dropna(), csub["e_pop"].dropna()
        both = csub[["e_gdppc", "e_pop"]].dropna()
        reg = (sub if region_from == "window" else sub.iloc[:1])["e_regiongeo"].dropna()
        ten = (L["end"] - L["start"]).days / 365.25
        out.append({"obsid": L["obsid"], "ccode": cc, "sy": sy, "S3": s.mean(),
                    "lgdp": np.log(gdp.iloc[0]) if len(gdp) else np.nan,
                    "lpop": np.log(pop.iloc[0]) if len(pop) else np.nan,
                    "lgdp_j": np.log(both["e_gdppc"].iloc[0]) if len(both) else np.nan,
                    "lpop_j": np.log(both["e_pop"].iloc[0]) if len(both) else np.nan,
                    "gdp_year": gdp.index.get_level_values(1)[0] if len(gdp) else np.nan,
                    "ltenure": np.log(max(ten, 0.1)), "ten": ten,
                    "decade": str(sy // 10 * 10),
                    "region": str(int(reg.iloc[0])) if len(reg) else np.nan,
                    "exit": L["exit"], "fate": L["posttenurefate"]})
    D = pd.DataFrame(out)
    D["zS3"] = (D["S3"] - D["S3"].mean()) / D["S3"].std()
    D["irregular"] = np.where(D["exit"] == "Irregular", 1.0, np.where(D["exit"] == "Regular", 0.0, np.nan))
    D["badfate"] = np.where(D["fate"].isin(["Exile", "Imprisonment", "Death"]), 1.0,
                            np.where(D["fate"] == "OK", 0.0, np.nan))
    return D


def fit(D, g="lgdp", p="lpop"):
    res = {}
    for y in ["irregular", "badfate"]:
        M = D.dropna(subset=[y, g, p, "ltenure", "region"]).copy()
        r = clustered_logit(M.rename(columns={g: "G", p: "P"}), y,
                            ["zS3", "G", "P", "ltenure", "decade", "region"], "ccode")
        res[y] = (len(M), round(r.get("OR", np.nan), 4), round(r.get("lo", np.nan), 4), round(r.get("hi", np.nan), 4))
    return res


base = rows()
print("n leaders", len(base))
print("base", fit(base))
print("joint gdp+pop same year", fit(base, "lgdp_j", "lpop_j"))
for cov in ["autoc_years", "S_years", "full3"]:
    print(cov, fit(rows(cov=cov)))
# leaders whose covariates are not from the entry year, and tiny tenures / duplicate obsids
print("covariate year != entry year:")
print(base[base["gdp_year"] != base["sy"]][["obsid", "sy", "gdp_year", "exit", "fate"]].to_string())
print("tenure < 0.1 yr:", (base["ten"] < 0.1).sum(), " tenure <= 0:", (base["ten"] <= 0).sum())
print("dup obsid:", base["obsid"].duplicated().sum())
print(base[["lgdp", "lpop"]].describe())
