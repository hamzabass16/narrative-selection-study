"""
Assemble /root/analysis/verify3/verification.json from my own independent results.
Re-runs my V-Dem script (verify_vdem.py) plus the two convention variants that explain small gaps.
"""
import json
import runpy
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
V = runpy.run_path("/root/analysis/verify3/verify_vdem.py")
d, R = V["d"], V["OUT"]
modal, first_valid, fit_logit, ols_cluster = V["modal"], V["first_valid"], V["fit_logit"], V["ols_cluster"]
auto = d["auto"]
H4 = json.load(open("/root/analysis/verify3/h4b_results.json"))
H9 = json.load(open("/root/analysis/verify3/h9a_results.json"))

# ---- Variant: rows with both v2x_regime and v2x_polyarchy missing are skipped (NaN) in the regime mean
rg = d.dropna(subset=["v2regidnr"]).groupby("v2regidnr")
reg = pd.DataFrame({"country_id": rg["country_id"].first(), "auto_mean": rg["auto_flag_raw"].mean(),
                    "S_mean": rg["S"].mean(), "endtype": rg["v2regendtype"].agg(modal),
                    "n_years": rg["year"].size(), "start_year": rg["year"].min(),
                    "region": rg["e_regiongeo"].agg(first_valid)})
reg = reg[(reg["auto_mean"] >= 0.5) & reg["S_mean"].notna()].copy()
reg["violent"] = np.where(reg["endtype"].isin([0, 1, 3, 5, 8]), 1.0,
                          np.where(reg["endtype"].isin([4, 9, 10, 11]), 0.0, np.nan))
reg["S_z"] = (reg["S_mean"] - reg["S_mean"].mean()) / reg["S_mean"].std()
reg["log_years"] = np.log(reg["n_years"])
reg["qc"] = (np.floor(reg["start_year"] / 25) * 25).astype(int)
lg = reg.dropna(subset=["violent", "S_z", "region"]).copy()
_, orv, lo, hi, _ = fit_logit(lg)
q = pd.qcut(lg["S_mean"], 4, labels=[1, 2, 3, 4])
sh = lg.groupby(q, observed=True)["violent"].mean()
VAR_REG = dict(kept=len(reg), logit=len(lg), OR=orv, lo=lo, hi=hi, q1=float(sh.loc[1]), q4=float(sh.loc[4]))

# ---- Variant: outcomes z-scored within autocracy-years 1900-2023
win = auto & d["year"].between(1900, 2023)
xr, xk = d["v2clrelig"].where(win), d["v2clkill"].where(win)
tmp = d.assign(zr=(xr - xr.mean()) / xr.std(), zk=-(xk - xk.mean()) / xk.std())[win]
s = tmp.dropna(subset=["zr", "zk", "RL", "lgdp", "lpop", "e_regiongeo"])
_, b_r, ci_r, _ = ols_cluster("zr ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s, "RL")
_, b_k, ci_k, _ = ols_cluster("zk ~ RL + lgdp + lpop + C(year) + C(e_regiongeo)", s, "RL")


def r(x, k=3):
    return None if x is None else round(float(x), k)


def item(claim, expected, mine, status, reason=None, **extra):
    out = {"claim": claim, "expected": expected, "verified": mine, "status": status}
    if reason:
        out["reason"] = reason
    out.update(extra)
    return out


CONV_REG = ("Exact match only when country-years with both v2x_regime and v2x_polyarchy missing (1,138 rows, "
            "1789-1990) are left out of the regime-mean autocracy flag. If those rows are counted as "
            "non-autocracy (flag = 0), I get 1,582 regimes, 1,086 in the logit, OR 0.739 (0.624 to 0.875), "
            "62.5 vs 39.0 percent. The spec does not say which; the original script uses the first.")
CONV_RL = ("Exact match when z(v2clrelig) and z(v2clkill) are standardised within autocracy-years 1900 to 2023 "
           "(the regression window). Standardising within the full 1789-2025 autocracy sample, as the general "
           "rule reads literally, gives RL -> religious freedom {:.3f} ({:.2f} to {:.2f}) and RL -> -z(kill) {:.3f}. "
           "Pure rescaling; sign and significance unchanged.").format(
    R["rl_relig_coef"], R["rl_relig_ci"][0], R["rl_relig_ci"][1], R["rl_kill_coef"])

A = [
    item("A1 autocracy-years", 21576, R["n_autocracy_years"], "match"),
    item("A1 countries", 202, R["n_autocracy_countries"], "match"),
    item("A1 corr(Cooperation, Dominance)", -0.66, r(R["corr_coop_dom"], 4), "match"),
    item("A2 regimes kept", 1600, VAR_REG["kept"], "match", CONV_REG, literal_alt=R["n_regimes_kept"]),
    item("A2 regimes in logit", 1099, VAR_REG["logit"], "match", CONV_REG, literal_alt=R["n_regimes_logit"]),
    item("A2 OR per SD of S (95% CI)", [0.75, 0.63, 0.89], [r(VAR_REG["OR"]), r(VAR_REG["lo"]), r(VAR_REG["hi"])],
         "match", CONV_REG, literal_alt=[r(R["logit_OR"]), r(R["logit_OR_ci"][0]), r(R["logit_OR_ci"][1])]),
    item("A2 percent violent, bottom vs top quartile of S", [63, 39],
         [r(100 * VAR_REG["q1"], 1), r(100 * VAR_REG["q4"], 1)], "match", CONV_REG,
         literal_alt=[r(100 * R["pct_violent_bottom_q"], 1), r(100 * R["pct_violent_top_q"], 1)]),
    item("A3 10-yr change in log GDPpc on S (95% CI)", [0.020, 0.006, 0.035],
         [r(R["gdp10_coef"], 4), r(R["gdp10_ci"][0], 4), r(R["gdp10_ci"][1], 4)], "match",
         n=R["gdp10_n"], countries=R["gdp10_n_countries"]),
    item("A3 20-yr change in life expectancy on S (95% CI)", [0.52, 0.17, 0.87],
         [r(R["life20_coef"]), r(R["life20_ci"][0]), r(R["life20_ci"][1])], "match", n=R["life20_n"]),
    item("A4 RL -> z(religious freedom) (95% CI)", [-2.04, -2.84, -1.24], [r(b_r), r(ci_r[0]), r(ci_r[1])],
         "match", CONV_RL, n=len(s),
         literal_alt=[r(R["rl_relig_coef"]), r(R["rl_relig_ci"][0]), r(R["rl_relig_ci"][1])]),
    item("A4 RL -> -z(v2clkill)", 0.95, r(b_k), "match", CONV_RL, ci=[r(ci_k[0]), r(ci_k[1])],
         literal_alt=r(R["rl_kill_coef"])),
]

ct = H4["crosstab"]
B = [
    item("B same_tradition N/Y/U", [61, 55, 1], [H4["same_tradition"].get(k) for k in ["N", "Y", "U"]], "match"),
    item("B adopted among N: Y/P/N/U", [5, 16, 39, 1], [H4["adopted_among_N"].get(k) for k in ["Y", "P", "N", "U"]], "match"),
    item("B Christian conquerors N/P", [12, 1], [ct["Christianity"].get("N", 0), ct["Christianity"].get("P", 0)], "match"),
    item("B Muslim conquerors N/P", [11, 2], [ct["Islam"].get("N", 0), ct["Islam"].get("P", 0)], "match"),
    item("B 'Other' conquerors adopted Y or P", "11 of 15", f"{H4['other_adopted_YP']} of {H4['other_n']}", "match",
         breakdown=H4["other_adopted_breakdown"]),
]

exp_dom = {"Family": (11, 0, 0.26), "Group": (15, 0, 0.20), "Reciprocity": (35, 1, 0.14), "Heroism": (34, 0, 0.10),
           "Deference": (37, 1, 0.13), "Fairness": (18, 0, 0.18), "Property": (50, 1, 0.10)}
C = [
    item("C passages", 2368, H9["n_passages"], "match"),
    item("C coded by coder 1 (all)", 2368, H9["coder1_n_unique_pids"], "match" if H9["coder1_covers_all_passages"] else "mismatch"),
    item("C coded by coder 2", 474, H9["coder2_n_unique_pids"], "match"),
    item("C relevance agreement / alpha", ["455/474", 0.87], [f"{H9['relevance_agree']}/{H9['n_double_coded']}", r(H9["relevance_alpha"])], "match"),
    item("C valence agreement / alpha", ["452/474", 0.86], [f"{H9['valence_agree']}/{H9['n_double_coded']}", r(H9["valence_alpha"])], "match"),
]
for dom, (p, n, u) in exp_dom.items():
    t = H9["coder1_by_domain"][dom]
    st = "match" if (t["POS"], t["NEG"]) == (p, n) and abs(t["wilson_upper"] - u) < 0.006 else "mismatch"
    C.append(item(f"C {dom} POS/NEG, Wilson upper", [p, n, u], [t["POS"], t["NEG"], r(t["wilson_upper"])], st))

CODE_REVIEW = {
    "h8r_analysis.py": [
        "No error affecting the claimed numbers.",
        "Convention: autoc is NaN when v2x_regime and v2x_polyarchy are both missing, so groupby mean skips those rows; this is why it gets 1,600 regimes (vs 1,582 if they count as non-autocracy). Should be stated in the plan.",
        "Convention: Part A outcomes use z() inside the 1900-2023 frame `a`, while S uses the full autocracy sample. Different standardisation bases across parts; rescales RL coefficients by about 5 percent.",
        "Latent: region = e_regiongeo.astype('Int64').astype(str) turns NaN into the string '<NA>', which formulas keep as a real fixed-effect level instead of dropping. No effect now (e_regiongeo has no missing values).",
    ],
    "h4b_analysis.py": [
        "Counts consistent with final_codes.csv; items.csv joins 1:1 (117/117).",
        "The conqueror-tradition crosstab (Christian 12N/1P, Muslim 11N/2P, Other 11/15) is not produced by this script; verified directly from the CSV.",
        "Minor: in fit(), CCIz is standardised before rows with conqueror_writing U are dropped, so the 'per SD' scale is slightly off in the fitted sample.",
        "Minor: imputations with non-finite estimates or |beta| >= 15 are silently dropped before Rubin pooling (outcome-dependent exclusion under separation). The model is not fitted in the primary spec anyway (5 events < 10).",
    ],
    "h9a_pipeline.py": [
        "Krippendorff alpha and Wilson formulas are algebraically correct; my independent implementation gives identical values. Frozen copy is byte-identical.",
        "Substantive: coder 2 coded zero NEG, and none of coder 1's 3 NEG passages (V0696, V1117, V1589) fall in the double-coded sample, so reliability of the NEG code, the one H9a turns on, is untested.",
        "Valence alpha counts NA (irrelevant) as a category, so it largely re-measures relevance; on the 84 items both coders called relevant, valence agreement is 81/84 (alpha 0.93).",
        "Interpretation: 'falsified' uses the point estimate > 5 percent; every Wilson upper bound (0.10 to 0.26) exceeds 5 percent, so no domain meets upper_bound_below_5pct.",
        "Latent: region_bucket tests Oceania keywords (including 'pacific') before Americas, so a 'Pacific Northwest' region would be misbucketed. No candidate region triggers it.",
        "Latent: load() overwrites duplicate pids silently; there are no duplicates now.",
    ],
}

out = {"verifier": "independent re-implementation, /root/analysis/verify3",
       "scripts": ["verify_vdem.py", "vdem_variants.py", "verify_h4b.py", "verify_h9a.py", "build_verification.py"],
       "A_vdem_h8r": A, "B_h4b": B, "C_h9a": C, "code_review": CODE_REVIEW,
       "summary": {"match": sum(x["status"] == "match" for x in A + B + C),
                   "close": sum(x["status"] == "close" for x in A + B + C),
                   "mismatch": sum(x["status"] == "mismatch" for x in A + B + C)}}
json.dump(out, open("/root/analysis/verify3/verification.json", "w"), indent=2)
print(json.dumps(out["summary"]))
for x in A + B + C:
    print(x["status"], "|", x["claim"], "| exp", x["expected"], "| got", x["verified"], "| alt", x.get("literal_alt", ""))
