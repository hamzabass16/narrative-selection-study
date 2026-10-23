"""Independent re-derivation of H8 Parts B and C (ruler conduct in autocracies).

Step by step:
  1. Autocracy-years from V-Dem v15; z-score inputs over autocracy-years.
  2. Dominance, Cooperation, S.
  3. Part B: regime-level S at lag L, end types, logit with clustered SEs.
  4. Part C: Archigos leaders, first-three-years S3, two logits with clustered SEs.
Variant choices (where the spec is silent) are run as sensitivity rows.
"""
import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore")
OUT = "/root/analysis/verify4/part2_results.json"

# ---------- 1. Autocracy-years ----------
v = pd.read_pickle("/root/analysis/verify4/vdem_sub.pkl")
v["year"] = v["year"].astype(int)
v["country_id"] = v["country_id"].astype(int)

regime = v["v2x_regime"]
autoc = (regime <= 1) | (regime.isna() & (v["v2x_polyarchy"] < 0.5))
v["autoc"] = autoc.astype(int)
A = v[v["autoc"] == 1].copy()


def z(series):
    return (series - series.mean()) / series.std()


DOM_VARS = ["v2clkill", "v2cltort", "v2csreprss"]
COOP_VARS = ["v2exrescon", "v2x_jucon", "v2xlg_legcon", "v2dlencmps"]
for col in DOM_VARS + COOP_VARS:
    A["z_" + col] = z(A[col])


def build_S(A, dom_rule="any"):
    """dom_rule: 'any' = mean of available dominance items; 'all' = require all three."""
    dom_items = pd.concat([-A["z_" + c] for c in DOM_VARS], axis=1)
    dom = dom_items.mean(axis=1, skipna=True)
    if dom_rule == "all":
        dom = dom.where(dom_items.notna().sum(axis=1) == 3)
    coop_items = A[["z_" + c for c in COOP_VARS]]
    coop = coop_items.mean(axis=1, skipna=True).where(coop_items.notna().sum(axis=1) >= 3)
    diff = coop - dom
    return z(diff)


A["S"] = build_S(A, "any")
A["S_domall"] = build_S(A, "all")


def clustered_logit(df, y, xcols, cluster):
    """Logit with cluster-robust SEs. Returns OR, CI, p for the first x column."""
    X = pd.get_dummies(df[xcols], drop_first=True, dtype=float)
    X = sm.add_constant(X, has_constant="add")
    # drop all-zero dummy columns (can appear after subsetting)
    X = X.loc[:, (X != 0).any(axis=0)]
    model = sm.Logit(df[y].astype(float), X)
    try:
        res = model.fit(disp=0, maxiter=200, cov_type="cluster",
                        cov_kwds={"groups": df[cluster].astype(int).values})
    except Exception as exc:  # perfect separation etc.
        return {"error": str(exc)}
    key = xcols[0]
    b = res.params[key]
    se = res.bse[key]
    return {"OR": float(np.exp(b)), "lo": float(np.exp(b - 1.959964 * se)),
            "hi": float(np.exp(b + 1.959964 * se)), "p": float(res.pvalues[key]),
            "n": int(res.nobs), "converged": bool(res.mle_retvals.get("converged", True))}


# ---------- 3. Part B ----------
VIOLENT = {0, 1, 3, 5, 8}
ORDERLY = {4, 9, 10, 11}

R = v.dropna(subset=["v2regidnr"]).copy()
R["v2regidnr"] = R["v2regidnr"].astype(int)
R = R.merge(A[["country_id", "year", "S", "S_domall"]], on=["country_id", "year"], how="left")


def mode_nonmissing(s):
    s = s.dropna()
    if s.empty:
        return np.nan
    return s.value_counts().sort_index().idxmax()  # ties -> smallest code (value_counts sorted by count first)


def regime_table(R, lag, s_col="S"):
    rows = []
    for rid, g in R.groupby("v2regidnr"):
        last = g["year"].max()
        first = g["year"].min()
        s_window = g.loc[g["year"] <= last - lag, s_col]
        endtype = g["v2regendtype"].dropna()
        endtype = endtype.value_counts().idxmax() if not endtype.empty else np.nan
        first_row = g.loc[g["year"].idxmin()]
        rows.append({"rid": rid, "country_id": g["country_id"].iloc[0],
                     "first": first, "last": last, "nyears": len(g),
                     "autoc_share": g["autoc"].mean(), "S": s_window.mean(),
                     "endtype": endtype, "region": first_row["e_regiongeo"]})
    T = pd.DataFrame(rows)
    T = T[(T["autoc_share"] >= 0.5) & T["S"].notna()].copy()
    T["violent"] = np.where(T["endtype"].isin(VIOLENT), 1.0,
                            np.where(T["endtype"].isin(ORDERLY), 0.0, np.nan))
    T["logyears"] = np.log(T["nyears"])
    T["qc"] = (T["first"] // 25 * 25).astype(int).astype(str)
    T["region"] = T["region"].astype(int).astype(str)
    return T


def part_b(lag, s_col="S", z_over="with_S"):
    T = regime_table(R, lag, s_col)
    n_with_S = len(T)
    M = T.dropna(subset=["violent"]).copy()
    if z_over == "with_S":
        mu, sd = T["S"].mean(), T["S"].std()
    else:
        mu, sd = M["S"].mean(), M["S"].std()
    M["zS"] = (M["S"] - mu) / sd
    res = clustered_logit(M, "violent", ["zS", "logyears", "qc", "region"], "country_id")
    res.update({"n_with_S": n_with_S, "n_model": len(M),
                "n_violent": int(M["violent"].sum())})
    return res


partB = {}
for lag in [10, 0]:
    for s_col in ["S", "S_domall"]:
        for z_over in ["with_S", "model"]:
            partB[f"lag{lag}_{s_col}_z{z_over}"] = part_b(lag, s_col, z_over)

# ---------- 4. Part C ----------
a = pd.read_stata("/root/data/ext2/archigos/Archigos_4.1_stata14.dta")
a["start"] = pd.to_datetime(a["startdate"], errors="coerce")
a["end"] = pd.to_datetime(a["enddate"], errors="coerce")
a = a[a["start"].dt.year >= 1875].copy()
n_archigos_1875 = len(a)

Vc = v.dropna(subset=["COWcode"]).copy()
Vc["COWcode"] = Vc["COWcode"].astype(int)
Vc = Vc.merge(A[["country_id", "year", "S", "S_domall"]], on=["country_id", "year"], how="left")
Vc = Vc.set_index(["COWcode", "year"]).sort_index()


def leader_rows(s_col="S", cov_window="three"):
    rows = []
    for _, L in a.iterrows():
        sy = L["start"].year
        ey = L["end"].year if pd.notna(L["end"]) else 2015
        years = list(range(sy, min(sy + 2, ey) + 1))
        keys = [(int(L["ccode"]), y) for y in years if (int(L["ccode"]), y) in Vc.index]
        if not keys:
            continue
        sub = Vc.loc[keys]
        s_vals = sub.loc[sub["autoc"] == 1, s_col].dropna()
        if s_vals.empty:
            continue
        # covariates: entry year, else first available year of the window
        gdp = sub["e_gdppc"].dropna()
        pop = sub["e_pop"].dropna()
        if cov_window == "entry_only":
            gdp = gdp[gdp.index.get_level_values(1) == sy]
            pop = pop[pop.index.get_level_values(1) == sy]
        region = sub["e_regiongeo"].dropna()
        tenure = (L["end"] - L["start"]).days / 365.25 if pd.notna(L["end"]) else np.nan
        rows.append({"ccode": int(L["ccode"]), "S3": s_vals.mean(),
                     "lgdp": np.log(gdp.iloc[0]) if len(gdp) else np.nan,
                     "lpop": np.log(pop.iloc[0]) if len(pop) else np.nan,
                     "ltenure": np.log(max(tenure, 0.1)),
                     "decade": str(sy // 10 * 10),
                     "region": str(int(region.iloc[0])) if len(region) else np.nan,
                     "exit": L["exit"], "fate": L["posttenurefate"]})
    D = pd.DataFrame(rows)
    D["zS3"] = (D["S3"] - D["S3"].mean()) / D["S3"].std()
    D["irregular"] = np.where(D["exit"] == "Irregular", 1.0, np.where(D["exit"] == "Regular", 0.0, np.nan))
    D["badfate"] = np.where(D["fate"].isin(["Exile", "Imprisonment", "Death"]), 1.0,
                            np.where(D["fate"] == "OK", 0.0, np.nan))
    return D


def part_c(s_col="S", cov_window="three", rezscore=False):
    D = leader_rows(s_col, cov_window)
    out = {"n_leaders": len(D)}
    xcols = ["zS3", "lgdp", "lpop", "ltenure", "decade", "region"]
    for y in ["irregular", "badfate"]:
        M = D.dropna(subset=[y, "lgdp", "lpop", "ltenure", "region"]).copy()
        if rezscore:
            M["zS3"] = (M["S3"] - M["S3"].mean()) / M["S3"].std()
        out[y] = clustered_logit(M, y, xcols, "ccode")
    return out


partC = {
    "main": part_c("S", "three"),
    "dom_all": part_c("S_domall", "three"),
    "cov_entry_only": part_c("S", "entry_only"),
    "z_in_model_sample": part_c("S", "three", rezscore=True),
}

results = {"n_autocracy_years": int(len(A)), "n_autocracy_years_with_S": int(A["S"].notna().sum()),
           "n_archigos_start_ge_1875": int(n_archigos_1875), "partB": partB, "partC": partC}
json.dump(results, open(OUT, "w"), indent=1, default=float)
print(json.dumps(results, indent=1, default=float))
