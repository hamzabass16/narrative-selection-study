"""Compile verification_A.json: claimed vs verifier values with verdicts.

Tolerance: counts exact; ratios/shares within 1 in the 2nd significant figure; p-values same side of 0.05.
"""
import json
import math
import warnings

warnings.filterwarnings("ignore")
V = "/root/analysis/verify4"
p1 = json.load(open(f"{V}/part1_results.json"))
p2 = json.load(open(f"{V}/part2_results.json"))

# Alternative Part B definition (autocratic share over years with a determined status)
src = open(f"{V}/part2_diag.py").read().split("variants = {")[0]
ns = {}
exec(src, ns)
altB = {lag: ns["fit"](ns["table"](ns["R2"], lag, share_col="autoc_nan")) for lag in (10, 0)}


def sig2_ok(claimed, mine):
    """Within 1 unit in the second significant figure of the claimed value."""
    if claimed == 0:
        return abs(mine) < 0.005
    unit = 10 ** (math.floor(math.log10(abs(claimed))) - 1)
    return abs(claimed - mine) <= unit + 1e-12


def verdict(kind, claimed, mine):
    if kind == "count":
        ok = claimed == mine
    elif kind == "ratio":
        ok = sig2_ok(claimed, mine)
    elif kind == "p":
        ok = (claimed < 0.05) == (mine < 0.05)
    elif kind == "list":
        ok = claimed == mine
    return "REPRODUCED" if ok else "DIFFERS"


claims = []


def add(cid, label, kind, claimed, mine, note=""):
    claims.append({"claim": cid, "item": label, "claimed": claimed, "verifier": mine,
                   "verdict": verdict(kind, claimed, mine), "note": note})


# ---- Part 1 ----
add(1, "passages", "count", 5172, p1["n_passages"])
add(1, "societies", "count", 53, p1["n_societies"])
add(1, "families", "count", 42, p1["n_families"])
add(2, "double-coded with both codes", "count", 1034, p1["n_both_coded"])
add(2, "relevance agreement", "count", 969, p1["relevance_agreement"])
add(2, "alpha relevance", "ratio", 0.837, round(p1["alpha_relevance"], 4))
add(2, "alpha valence (NA incl.)", "ratio", 0.830, round(p1["alpha_valence"], 4))
add(3, "first coder NEG", "count", 26, p1["first_coder_neg"])
add(3, "final NEG", "count", 25, p1["final_neg_including_disputed"])
add(3, "overturned", "list", ["W01848"], p1["overturned"])
add(3, "disputed", "count", 0, len(p1["disputed"]))
claimed4 = {"Family": (169, 6), "Group": (154, 0), "Reciprocity": (77, 4), "Heroism": (140, 1),
            "Deference": (116, 5), "Fairness": (17, 1), "Property": (171, 8)}
for dom, (pos, neg) in claimed4.items():
    row = p1["domain_table"][dom]
    add(4, f"{dom} POS", "count", pos, row["POS"])
    add(4, f"{dom} NEG", "count", neg, row["NEG"])
claimed5 = {"Family": 0.0347, "Group": 0.0, "Reciprocity": 0.0339, "Heroism": 0.0046,
            "Deference": 0.0319, "Fairness": 0.0370, "Property": 0.0517}
for dom, share in claimed5.items():
    add(5, f"{dom} weighted NEG share", "ratio", share, round(p1["domain_table"][dom]["weighted_share"], 4))
falsified = sorted(d for d, r in p1["domain_table"].items() if r["falsified"])
add(5, "behaviours above 0.05", "list", ["Property"], falsified)
claimed6 = {"GROUP": (90, 1), "KIN": (12, 0), "STRANGER": (9, 0), "ENEMY": (2, 4), "UNCLEAR": (58, 3)}
for tgt, (pos, neg) in claimed6.items():
    row = p1["property_by_target"].get(tgt, {"POS": 0, "NEG": 0})
    add(6, f"Property {tgt} POS", "count", pos, row["POS"])
    add(6, f"Property {tgt} NEG", "count", neg, row["NEG"])

# ---- Part 2 ----
B10 = p2["partB"]["lag10_S_zwith_S"]
B0 = p2["partB"]["lag0_S_zwith_S"]
gap = ("Spec-literal reading counts years with neither v2x_regime nor v2x_polyarchy as non-autocratic "
       "in the regime's autocratic share. Excluding those undetermined years from the share "
       "(share over years with a determined status) reproduces the claim exactly: ")
note10 = gap + "lag10 n_with_S %d, n_model %d, OR %.3f (%.3f to %.3f), p %.4f" % altB[10]
note0 = gap + "lag0 n_with_S %d, n_model %d, OR %.3f (%.3f to %.3f), p %.4f" % altB[0]
add(7, "regimes with S", "count", 552, B10["n_with_S"], note10)
add(7, "regimes violent/orderly", "count", 373, B10["n_model"], note10)
add(7, "OR", "ratio", 0.647, round(B10["OR"], 4))
add(7, "CI low", "ratio", 0.479, round(B10["lo"], 4))
add(7, "CI high", "ratio", 0.874, round(B10["hi"], 4))
add(7, "p", "p", 0.005, round(B10["p"], 5))
add(8, "OR", "ratio", 0.750, round(B0["OR"], 4), note0)
add(8, "CI low", "ratio", 0.633, round(B0["lo"], 4), note0)
add(8, "CI high", "ratio", 0.889, round(B0["hi"], 4), note0)
add(8, "n", "count", 1099, B0["n_model"], note0)
C = p2["partC"]["main"]
noteC = ("One extra leader in each model sample; not located. Ruled out: covariates from autocracy/S years only, "
         "untruncated 3-year window, joint gdp/pop availability, region from entry year, dropping zero-day tenures, "
         "calendar-year tenure. OR/CI identical to 3 decimals.")
add(9, "leaders", "count", 2020, C["n_leaders"])
add(9, "irregular OR", "ratio", 0.532, round(C["irregular"]["OR"], 4))
add(9, "irregular CI low", "ratio", 0.442, round(C["irregular"]["lo"], 4))
add(9, "irregular CI high", "ratio", 0.639, round(C["irregular"]["hi"], 4))
add(9, "irregular n", "count", 1700, C["irregular"]["n"], noteC)
add(9, "bad fate OR", "ratio", 0.577, round(C["badfate"]["OR"], 4))
add(9, "bad fate CI low", "ratio", 0.479, round(C["badfate"]["lo"], 4))
add(9, "bad fate CI high", "ratio", 0.695, round(C["badfate"]["hi"], 4))
add(9, "bad fate n", "count", 1728, C["badfate"]["n"], noteC)

out = {"claims": claims,
       "alternative_partB_share_over_determined_years": {
           f"lag{lag}": dict(zip(["n_with_S", "n_model", "OR", "lo", "hi", "p"], vals)) for lag, vals in altB.items()},
       "caveats": ["Part B logits report non-convergence in statsmodels (quasi-separation in some start "
                   "quarter-century / region dummies); the S coefficient is stable across variants.",
                   "Part 1: no duplicate pids, every passage coded, every society matched to a family; "
                   "all 26 first-coder NEG passages had a second and third code."]}
json.dump(out, open(f"{V}/verification_A.json", "w"), indent=1)
for c in claims:
    print(c["claim"], c["item"], "|", c["claimed"], "|", c["verifier"], "|", c["verdict"])
print(out["alternative_partB_share_over_determined_years"])
