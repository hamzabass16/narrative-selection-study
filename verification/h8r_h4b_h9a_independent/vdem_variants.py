"""
Sensitivity variants to diagnose small gaps between my numbers and the claimed ones.
Reuses the building blocks in verify_vdem.py by re-running it as a module namespace.
"""
import runpy
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings("ignore")

ns = runpy.run_path("/root/analysis/verify3/verify_vdem.py")
d = ns["d"]
modal, first_valid, fit_logit, ols_cluster = ns["modal"], ns["first_valid"], ns["fit_logit"], ns["ols_cluster"]
auto = d["auto"]
print("\n================ VARIANTS ================")


def regime_table(frame, flag_col):
    rg = frame.dropna(subset=["v2regidnr"]).groupby("v2regidnr")
    return pd.DataFrame({
        "country_id": rg["country_id"].first(),
        "auto_mean": rg[flag_col].mean(),
        "S_mean": rg["S"].mean(),
        "endtype": rg["v2regendtype"].agg(modal),
        "n_years": rg["year"].size(),
        "start_year": rg["year"].min(),
        "region": rg["e_regiongeo"].agg(first_valid),
    })


def run_regime(reg, label):
    reg = reg[(reg["auto_mean"] >= 0.5) & reg["S_mean"].notna()].copy()
    reg["violent"] = np.where(reg["endtype"].isin([0, 1, 3, 5, 8]), 1.0,
                              np.where(reg["endtype"].isin([4, 9, 10, 11]), 0.0, np.nan))
    reg["S_z"] = (reg["S_mean"] - reg["S_mean"].mean()) / reg["S_mean"].std()
    reg["log_years"] = np.log(reg["n_years"])
    reg["qc"] = (np.floor(reg["start_year"] / 25) * 25).astype(int)
    lg = reg.dropna(subset=["violent", "S_z", "region"]).copy()
    r, o, lo, hi, p = fit_logit(lg)
    q = pd.qcut(lg["S_mean"], 4, labels=[1, 2, 3, 4])
    sh = lg.groupby(q, observed=True)["violent"].mean()
    print(f"{label}: kept={len(reg)} logit={len(lg)} OR={o:.3f} ({lo:.3f}-{hi:.3f}) "
          f"Q1={sh.loc[1]:.3f} Q4={sh.loc[4]:.3f}")


# V1: base (both-missing rows count as non-autocracy, i.e. 0)
run_regime(regime_table(d, "auto"), "V1 base (missing flag = 0)")
# V2: both-missing rows excluded from the regime mean (NaN)
run_regime(regime_table(d, "auto_flag_raw"), "V2 missing flag = NaN (skipped)")

# V3: v2x_polyarchy fallback also used when v2x_regime is missing but polyarchy is missing too -> NaN dropped
# V4: regime grouping restricted to rows with any non-missing S
# V5: also treat regime-years where 'year' rows are duplicated? (none). Instead: n_years = autocracy years only
reg = regime_table(d, "auto")
rg_auto = d[auto].dropna(subset=["v2regidnr"]).groupby("v2regidnr")["year"].size()
reg5 = reg.copy()
reg5["n_years"] = rg_auto.reindex(reg5.index).fillna(1)
run_regime(reg5, "V5 log(autocracy years in regime)")

# V6: end type taken from the last year of the regime instead of the mode
rg = d.dropna(subset=["v2regidnr"]).sort_values("year").groupby("v2regidnr")
reg6 = reg.copy()
reg6["endtype"] = rg["v2regendtype"].last()
run_regime(reg6, "V6 endtype = last value")

# Missing-flag rows: which regimes contain them?
miss = d[d["auto_flag_raw"].isna()]
print("rows with both v2x_regime and v2x_polyarchy missing:", len(miss),
      "| of which have v2regidnr:", miss["v2regidnr"].notna().sum(),
      "| years", miss["year"].min(), "-", miss["year"].max())

# Dominance requiring all three components
print("\n-- Religious legitimation variants --")
rl_base = d[auto & d["year"].between(1900, 2023)]
for label, sub in [
    ("z in all autocracy years (base)", None),
    ("z in autocracy 1900-2023", rl_base),
]:
    if sub is None:
        zr, zk = d["z_relig"], d["neg_z_kill"]
    else:
        xr, xk = d["v2clrelig"].where(rl_base.index.to_series().reindex(d.index).notna()), \
                 d["v2clkill"].where(rl_base.index.to_series().reindex(d.index).notna())
        zr = (xr - xr.mean()) / xr.std()
        zk = -(xk - xk.mean()) / xk.std()
    tmp = d.assign(zr=zr, zk=zk)[auto & d["year"].between(1900, 2023)]
    s = tmp.dropna(subset=["zr", "RL", "lgdp", "lpop", "e_regiongeo"])
    _, b, ci, _ = ols_cluster("zr ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s, "RL")
    _, b2, ci2, _ = ols_cluster("zk ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s, "RL")
    print(f"{label}: relig {b:.3f} ({ci[0]:.2f},{ci[1]:.2f})  kill {b2:.3f} ({ci2[0]:.2f},{ci2[1]:.2f})  n={len(s)}")

# z within the full V-Dem panel (all regimes)
for label, base_mask in [("z in full panel", pd.Series(True, index=d.index)),
                         ("z in full panel 1900-2023", d["year"].between(1900, 2023))]:
    xr = d["v2clrelig"].where(base_mask); xk = d["v2clkill"].where(base_mask)
    tmp = d.assign(zr=(xr - xr.mean()) / xr.std(), zk=-(xk - xk.mean()) / xk.std())
    tmp = tmp[auto & d["year"].between(1900, 2023)]
    s = tmp.dropna(subset=["zr", "RL", "lgdp", "lpop", "e_regiongeo"])
    _, b, ci, _ = ols_cluster("zr ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s, "RL")
    _, b2, ci2, _ = ols_cluster("zk ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s, "RL")
    print(f"{label}: relig {b:.3f} ({ci[0]:.2f},{ci[1]:.2f})  kill {b2:.3f} ({ci2[0]:.2f},{ci2[1]:.2f})")

# Ratio check: is the gap a pure rescaling? Compare raw-scale coefficients
s = rl_base.dropna(subset=["v2clrelig", "RL", "lgdp", "lpop", "e_regiongeo"])
_, braw, _, _ = ols_cluster("v2clrelig ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s, "RL")
print("raw-scale relig coef", round(braw, 3), "| implied SD for -2.04:", round(braw / -2.04, 3),
      "| SD all auto:", round(d.loc[auto, 'v2clrelig'].std(), 3),
      "| SD reg sample:", round(s['v2clrelig'].std(), 3))
s = rl_base.dropna(subset=["v2clkill", "RL", "lgdp", "lpop", "e_regiongeo"])
_, brawk, _, _ = ols_cluster("v2clkill ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s, "RL")
print("raw-scale kill coef", round(brawk, 3), "| implied SD for 0.95:", round(-brawk / 0.95, 3),
      "| SD all auto:", round(d.loc[auto, 'v2clkill'].std(), 3),
      "| SD reg sample:", round(s['v2clkill'].std(), 3))
