"""
Independent re-derivation of the revised H8 numbers from V-Dem v15.
Written from scratch for verification; does not import the original scripts.

Steps
  1. Flag autocracy-years.
  2. Build z-scores inside the autocracy sample, then Dominance, Cooperation, S.
  3. Regime-level logit: violent vs orderly end on regime-mean S.
  4. Forward outcomes: 10-year GDP growth and 20-year life expectancy change.
  5. Religious legitimation vs religious freedom and vs killings.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

OUT = {}
d = pd.read_pickle("/root/analysis/verify3/vdem_slim.pkl")
d = d.sort_values(["country_id", "year"]).reset_index(drop=True)

# ---------------------------------------------------------------
# 1. Autocracy flag
#    v2x_regime <= 1 where v2x_regime exists, else v2x_polyarchy < 0.5
# ---------------------------------------------------------------
has_regime = d["v2x_regime"].notna()
flag = pd.Series(np.nan, index=d.index)
flag[has_regime] = (d.loc[has_regime, "v2x_regime"] <= 1).astype(float)
has_poly = (~has_regime) & d["v2x_polyarchy"].notna()
flag[has_poly] = (d.loc[has_poly, "v2x_polyarchy"] < 0.5).astype(float)
d["auto_flag_raw"] = flag              # NaN when both are missing
d["auto"] = flag.fillna(0).astype(bool)  # treat "both missing" as not autocracy

auto = d["auto"]
OUT["n_autocracy_years"] = int(auto.sum())
OUT["n_autocracy_countries"] = int(d.loc[auto, "country_id"].nunique())
OUT["n_rows_both_missing"] = int(flag.isna().sum())


# ---------------------------------------------------------------
# 2. z-scores within the autocracy sample
# ---------------------------------------------------------------
def z_in_auto(col):
    x = d[col].where(auto)
    return (x - x.mean()) / x.std()   # pandas std uses ddof=1


dom_parts = pd.concat([-z_in_auto("v2clkill"),
                       -z_in_auto("v2cltort"),
                       -z_in_auto("v2csreprss")], axis=1)
d["dominance"] = dom_parts.mean(axis=1)        # mean of whatever is available

coop_parts = pd.concat([z_in_auto("v2exrescon"),
                        z_in_auto("v2x_jucon"),
                        z_in_auto("v2xlg_legcon"),
                        z_in_auto("v2dlencmps")], axis=1)
n_coop = coop_parts.notna().sum(axis=1)
d["cooperation"] = coop_parts.mean(axis=1).where(n_coop >= 3)

raw_s = (d["cooperation"] - d["dominance"]).where(auto)
d["S"] = (raw_s - raw_s.mean()) / raw_s.std()

OUT["n_dominance_nonmissing_auto"] = int(d.loc[auto, "dominance"].notna().sum())
OUT["n_dominance_all3_auto"] = int(dom_parts[auto].notna().all(axis=1).sum())
OUT["n_cooperation_nonmissing_auto"] = int(d.loc[auto, "cooperation"].notna().sum())
OUT["n_S_nonmissing_auto"] = int(d["S"].notna().sum())
OUT["corr_coop_dom"] = float(d.loc[auto, ["cooperation", "dominance"]].corr().iloc[0, 1])


# ---------------------------------------------------------------
# 3. Regime level
# ---------------------------------------------------------------
def modal(series):
    s = series.dropna()
    if s.empty:
        return np.nan
    counts = s.value_counts()
    top = counts[counts == counts.max()].index
    return float(min(top))     # ties broken by the lowest code


def first_valid(series):
    s = series.dropna()
    return s.iloc[0] if len(s) else np.nan


rg = d.dropna(subset=["v2regidnr"]).groupby("v2regidnr")
reg = pd.DataFrame({
    "country_id": rg["country_id"].first(),
    "auto_mean": rg["auto"].mean(),
    "S_mean": rg["S"].mean(),
    "endtype": rg["v2regendtype"].agg(modal),
    "n_years": rg["year"].size(),
    "start_year": rg["year"].min(),
    "region": rg["e_regiongeo"].agg(first_valid),
    "endtype_nunique": rg["v2regendtype"].nunique(),
})
OUT["n_regimes_total"] = int(len(reg))
OUT["n_regimes_with_multiple_endtypes"] = int((reg["endtype_nunique"] > 1).sum())

reg = reg[(reg["auto_mean"] >= 0.5) & reg["S_mean"].notna()].copy()
OUT["n_regimes_kept"] = int(len(reg))

violent_codes = [0, 1, 3, 5, 8]
orderly_codes = [4, 9, 10, 11]
reg["violent"] = np.where(reg["endtype"].isin(violent_codes), 1.0,
                          np.where(reg["endtype"].isin(orderly_codes), 0.0, np.nan))
reg["S_z"] = (reg["S_mean"] - reg["S_mean"].mean()) / reg["S_mean"].std()
reg["log_years"] = np.log(reg["n_years"])
reg["qc"] = (np.floor(reg["start_year"] / 25) * 25).astype(int)

lg = reg.dropna(subset=["violent", "S_z", "log_years", "region"]).copy()
OUT["n_regimes_logit"] = int(len(lg))
OUT["n_logit_violent"] = int(lg["violent"].sum())


def fit_logit(data, z_col="S_z"):
    m = smf.logit(f"violent ~ {z_col} + log_years + C(qc) + C(region)", data=data)
    try:
        r = m.fit(disp=0, maxiter=200, cov_type="cluster",
                  cov_kwds={"groups": data["country_id"].astype(int).values})
    except Exception:
        r = m.fit(disp=0, method="bfgs", maxiter=2000, cov_type="cluster",
                  cov_kwds={"groups": data["country_id"].astype(int).values})
    b = r.params[z_col]
    lo, hi = r.conf_int().loc[z_col]
    return r, float(np.exp(b)), float(np.exp(lo)), float(np.exp(hi)), float(r.pvalues[z_col])


r, orv, orlo, orhi, p = fit_logit(lg)
OUT["logit_n_used"] = int(r.nobs)
OUT["logit_OR"] = orv
OUT["logit_OR_ci"] = [orlo, orhi]
OUT["logit_p"] = p

# Sensitivity: re-standardise S within the logit sample itself
lg["S_z2"] = (lg["S_mean"] - lg["S_mean"].mean()) / lg["S_mean"].std()
_, orv2, lo2, hi2, _ = fit_logit(lg, "S_z2")
OUT["logit_OR_zwithin_logit_sample"] = [orv2, lo2, hi2]

# Quartiles of S among the logit sample
q = pd.qcut(lg["S_mean"], 4, labels=[1, 2, 3, 4])
share = lg.groupby(q, observed=True)["violent"].mean()
OUT["pct_violent_by_quartile"] = {str(k): float(v) for k, v in share.items()}
OUT["pct_violent_bottom_q"] = float(share.loc[1])
OUT["pct_violent_top_q"] = float(share.loc[4])

# Quartiles among all kept regimes, for reference
q_all = pd.qcut(reg["S_mean"], 4, labels=[1, 2, 3, 4])
sh_all = reg.dropna(subset=["violent"]).groupby(q_all, observed=True)["violent"].mean()
OUT["pct_violent_by_quartile_cut_on_all_kept"] = {str(k): float(v) for k, v in sh_all.items()}


# ---------------------------------------------------------------
# 4. Forward outcomes (autocracy-years up to 2015)
#    Leads and lags are taken from the full panel by year, not by row.
# ---------------------------------------------------------------
d["lgdp"] = np.log(d["e_gdppc"])
d["lpop"] = np.log(d["e_pop"])
panel = d.set_index(["country_id", "year"])


def shifted(col, k):
    """Value of col at year + k for the same country (NaN if absent)."""
    key = pd.MultiIndex.from_arrays([d["country_id"], d["year"] + k])
    return panel[col].reindex(key).values


d["lgdp_f10"] = shifted("lgdp", 10)
d["lgdp_l10"] = shifted("lgdp", -10)
d["life_f20"] = shifted("e_pelifeex", 20)
d["g_fwd10"] = d["lgdp_f10"] - d["lgdp"]
d["g_past10"] = d["lgdp"] - d["lgdp_l10"]
d["dlife20"] = d["life_f20"] - d["e_pelifeex"]
d["decade"] = (np.floor(d["year"] / 10) * 10).astype(int)


def ols_cluster(formula, data, var):
    r = smf.ols(formula, data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data["country_id"].astype(int).values})
    lo, hi = r.conf_int().loc[var]
    return r, float(r.params[var]), [float(lo), float(hi)], float(r.pvalues[var])


fw = d[auto & (d["year"] <= 2015)]
s1 = fw.dropna(subset=["g_fwd10", "S", "lgdp", "lpop", "g_past10", "e_regiongeo"])
r, b, ci, p = ols_cluster("g_fwd10 ~ S + lgdp + lpop + g_past10 + C(decade) + C(e_regiongeo)", s1, "S")
OUT["gdp10_coef"], OUT["gdp10_ci"], OUT["gdp10_p"], OUT["gdp10_n"] = b, ci, p, int(r.nobs)
OUT["gdp10_n_countries"] = int(s1["country_id"].nunique())

s2 = fw.dropna(subset=["dlife20", "S", "lgdp", "lpop", "e_pelifeex", "e_regiongeo"])
r, b, ci, p = ols_cluster("dlife20 ~ S + lgdp + lpop + e_pelifeex + C(decade) + C(e_regiongeo)", s2, "S")
OUT["life20_coef"], OUT["life20_ci"], OUT["life20_p"], OUT["life20_n"] = b, ci, p, int(r.nobs)


# ---------------------------------------------------------------
# 5. Religious legitimation (autocracy-years 1900 to 2023)
# ---------------------------------------------------------------
d["RL"] = d["v2exl_legitideolcr_4"] * d["v2exl_legitideol_osp"] / 4
d["z_relig"] = z_in_auto("v2clrelig")
d["neg_z_kill"] = -z_in_auto("v2clkill")

rl = d[auto & d["year"].between(1900, 2023)]
s3 = rl.dropna(subset=["z_relig", "RL", "lgdp", "lpop", "e_regiongeo"])
r, b, ci, p = ols_cluster("z_relig ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s3, "RL")
OUT["rl_relig_coef"], OUT["rl_relig_ci"], OUT["rl_relig_p"], OUT["rl_relig_n"] = b, ci, p, int(r.nobs)

s4 = rl.dropna(subset=["neg_z_kill", "RL", "lgdp", "lpop", "e_regiongeo"])
r, b, ci, p = ols_cluster("neg_z_kill ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s4, "RL")
OUT["rl_kill_coef"], OUT["rl_kill_ci"], OUT["rl_kill_p"], OUT["rl_kill_n"] = b, ci, p, int(r.nobs)

# Sensitivity: z-score the outcomes within the 1900-2023 regression sample instead
for name, col, base in [("relig", "v2clrelig", s3), ("kill", "v2clkill", s4)]:
    x = base[col]
    sign = -1 if name == "kill" else 1
    base = base.assign(yz=sign * (x - x.mean()) / x.std())
    _, b2, ci2, _ = ols_cluster("yz ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", base, "RL")
    OUT[f"rl_{name}_coef_z_in_reg_sample"] = [b2, ci2]

with open("/root/analysis/verify3/vdem_results.json", "w") as f:
    json.dump(OUT, f, indent=2)
for k, v in OUT.items():
    print(k, v)
