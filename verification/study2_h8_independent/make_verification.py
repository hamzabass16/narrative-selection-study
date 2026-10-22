"""Assemble verification.json from my own outputs (no original code imported)."""
import json

V = "/root/analysis/verify2/"
L = lambda f: json.load(open(V + f))
A = L("motif_scoring_summary.json")
Cw, Cu = L("country_models_w_alpha_apos.json"), L("country_models_unw_alpha_apos.json")
Eg = L("ess_variants_w.json")
EA, EAh = L("ea_models_unw_alpha_apos.json"), L("ea_models_unw_alpha_apos_hyph.json")
F = L("crisisdb_models.json")
r = lambda x, k=3: round(float(x), k)


def item(claim, expected, mine, status, note=""):
    d = {"claim": claim, "expected": expected, "verified": mine, "status": status}
    if note:
        d["note"] = note
    return d


a = A["alpha_apos"]
out = {"method_notes": {
    "A": "Primary tokenizer: lowercase, curly apostrophes -> ', words = [a-z]+ with internal apostrophes; "
         "hyphens split words; dictionary terms tokenized the same way and matched as contiguous phrases "
         "(no wildcards exist in either .dic file). Variants in motif_scoring_summary.json.",
    "B": "Unit share = flagged/all present motifs. Country incidence values are continuous population-weighted "
         "fractions (row sums = motifs_total), not counts. Both weighted and unweighted shares were computed; "
         "expected numbers reproduce only with incidence-weighted shares. EA incidence is 0/1 (two cells = 2). "
         "8 incidence columns carry a trailing underscore (b28e_, d4aa_, e15_, e15a_, e15b_, e18_, h36g1_, m81_) "
         "and were mapped back to their motif ids. Units with <5 motifs dropped (0 countries, 31 EA groups) "
         "before z-scoring.",
    "p_values": "Mine use Stata conventions: HC1 with t(N-K); clustered with t(G-1). Original uses statsmodels "
                "normal-based p-values, which explains small p differences.",
}}

out["A_motif_scoring"] = [
    item("share of motifs with >=1 virtue term", "26.0%", f"{a['virtue_any_pct']}%", "match"),
    item("Family", "14.5%", f"{a['virtue_Family_pct']}%", "close",
         "14.47% if hyphenated words are kept as single tokens (then 'daughter-in-law' no longer matches 'in law')."),
    item("Group", "1.25%", f"{a['virtue_Group_pct']}%", "match"),
    item("Reciprocity", "2.1%", f"{a['virtue_Reciprocity_pct']}%", "close",
         "Difference is one motif (m30b, 'give and take back'): matched by the dictionary's 'give-and-take' only when hyphenated terms are split into phrases."),
    item("Heroism", "8.7%", f"{a['virtue_Heroism_pct']}%", "match"),
    item("Deference", "0.35%", f"{a['virtue_Deference_pct']}%", "match"),
    item("Fairness", "0.08%", f"{a['virtue_Fairness_pct']}%", "match"),
    item("Property", "2.8%", f"{a['virtue_Property_pct']}%", "match"),
    {"tokenization_sensitivity": {k: {"any": v["virtue_any_pct"], "Family": v["virtue_Family_pct"],
                                      "Group": v["virtue_Group_pct"], "Reciprocity": v["virtue_Reciprocity_pct"]}
                                  for k, v in A.items()},
     "what_matters": "(1) hyphen handling: splitting 'daughter-in-law' lets it match 'in law' (Family); "
                     "(2) apostrophe handling: keeping \"partner's\" as one token stops it matching 'partner' (Group); "
                     "(3) the original's extra -est/-eth stemmer ('noblest'->'noble', Heroism). "
                     "Only 4 of 2,564 motifs differ from the original's flags, but because the 7 domains are "
                     "equally weighted and some are near-empty (Fairness 2 motifs, Deference 9), those 4 flips move "
                     "the EA estimate from 0.071 to 0.077."}]

out["B_CCI_construction"] = item(
    "CCI = re-standardized mean of 7 z-scored domain shares; CCI_net uses virtue-vice; exclude <5 motifs",
    "procedure", "rebuilt independently: 199 countries, 1,234 EA groups (31 dropped); corr(CCI, CCI_net) = 0.86 (countries, weighted), 0.89 (EA)",
    "match", "Country results match the expected values only with incidence-weighted shares (see C).")

c = Cw
out["C_country_models"] = [
    item("CCI -> lntrust_wvsavg, standardized beta (90% CI), n", "-0.02 (-0.24, 0.19), n=104",
         f"{r(c['lntrust_wvsavg~CCI']['std_beta'],3)} ({r(c['lntrust_wvsavg~CCI']['std_ci90'][0])}, {r(c['lntrust_wvsavg~CCI']['std_ci90'][1])}), n={c['lntrust_wvsavg~CCI']['n']}",
         "match",
         f"Incidence-weighted shares. With unweighted presence shares (a literal reading of the task's rule, since country incidence is fractional, not counts): "
         f"{r(Cu['lntrust_wvsavg~CCI']['std_beta'])} ({r(Cu['lntrust_wvsavg~CCI']['std_ci90'][0])}, {r(Cu['lntrust_wvsavg~CCI']['std_ci90'][1])}); still null."),
    item("tricksters_punish -> lntrust_wvsavg: b, p, standardized, n", "1.86, p=0.0001, 0.34, n=104",
         f"{r(c['lntrust_wvsavg~tricksters_punish']['b'],3)}, p={r(c['lntrust_wvsavg~tricksters_punish']['p'],4)} (t, df=100), "
         f"{r(c['lntrust_wvsavg~tricksters_punish']['std_beta'],2)}, n={c['lntrust_wvsavg~tricksters_punish']['n']}",
         "match", "p = 0.0001 with a normal reference, 0.0002 with Stata's t(100)."),
    item("CCI -> trust_gps standardized beta, n", "+0.11, n=76",
         f"{r(c['trust_gps~CCI']['std_beta'],3)}, n={c['trust_gps~CCI']['n']}", "match",
         f"p={r(c['trust_gps~CCI']['p'])}; unweighted shares give {r(Cu['trust_gps~CCI']['std_beta'])}."),
]

k1 = "drop_singletons|cont1|"; k0 = "keep_singletons|cont0|"
g = lambda k: Eg[k]
out["D_ESS_second_generation"] = [
    item("CCI of origin: SD of trust per SD (90% CI), n, origins", "+0.001 (-0.03, 0.03), n=6,558, 117",
         f"do-file spec (individual controls, reghdfe): {r(g(k1+'CCI')['std_beta'],4)} ({r(g(k1+'CCI')['std_ci90'][0])}, {r(g(k1+'CCI')['std_ci90'][1])}), "
         f"n={g(k1+'CCI')['n']}, {g(k1+'CCI')['n_origin']} origins; baseline controls only: {r(g(k0+'CCI')['std_beta'],4)} "
         f"({r(g(k0+'CCI')['std_ci90'][0])}, {r(g(k0+'CCI')['std_ci90'][1])}), n={g(k0+'CCI')['n']}, {g(k0+'CCI')['n_origin']}",
         "close",
         "The expected numbers reproduce exactly only WITHOUT the individual controls (gender, i.rel, i.health, i.age10) "
         "and with singletons kept. The claim says individual controls were used; with them (Table V Panel B col 2) the "
         "estimate is +0.015, still null. reghdfe drops 4 singleton obs (n 6,554, 116 origin clusters)."),
    item("CCI_net: SD per SD, p", "+0.027, p=0.018",
         f"do-file spec: {r(g(k1+'CCI_net')['std_beta'],4)}, p={r(g(k1+'CCI_net')['p'],4)}; baseline only: "
         f"{r(g(k0+'CCI_net')['std_beta'],4)}, p={r(g(k0+'CCI_net')['p'],4)}",
         "close", "Same sign and conclusion; larger and more significant with the do-file's individual controls."),
    item("tricksters_punish: b, p", "1.10, p=0.003",
         f"do-file spec: {r(g(k1+'tricksters_punish')['b'],3)}, p={r(g(k1+'tricksters_punish')['p'],4)}; baseline only: "
         f"{r(g(k0+'tricksters_punish')['b'],3)}, p={r(g(k0+'tricksters_punish')['p'],4)}",
         "close", "Expected value equals the baseline-controls model (Table V Panel B col 1), not col 2."),
]

e1, e2 = EA["v33~CCI|base"], EA["v33~CCI|v34"]
h1, h2 = EAh["v33~CCI|base"], EAh["v33~CCI|v34"]
out["E_Ethnographic_Atlas"] = [
    item("v33 on CCI: SD per SD, p, groups, families", "+0.077, p=0.18, 1,105, 71",
         f"{r(e1['std_beta'])}, p={r(e1['p'])}, {e1['n']}, {e1['n_clusters']}", "close",
         f"Same N and clusters. With hyphenated words kept as tokens: {r(h1['std_beta'])}, p={r(h1['p'])}. "
         "Using the original's motif flags in my pipeline gives 0.0776 (0.0771 if the 8 underscore motifs are dropped, as the original does)."),
    item("+ i.v34 high-god dummies: SD per SD, p", "+0.063, p=0.17",
         f"{r(e2['std_beta'])}, p={r(e2['p'])}, n={e2['n']}, families={e2['n_clusters']}", "close",
         f"hyphen-kept tokenizer: {r(h2['std_beta'])}, p={r(h2['p'])}. n drops to 711 because v34 is missing for many groups."),
]

s, rm = F["severity|base"], F["removed|base"]
s2, rm2 = F["severity|+PolPop"], F["removed|+PolPop"]
out["F_CrisisDB"] = [
    item("severity OLS: coef, p, n, means MERb1 vs MERb0", "+0.19, p=0.19, n=135, 0.74 vs 0.54",
         f"{r(s['b'],3)}, p={r(s['p_normal'],3)} (t(G-1): {r(s['p_t'],3)}), n={s['n']}, {r(s['mean_MERb1'],2)} vs {r(s['mean_MERb0'],2)}",
         "match", f"{s['n_polities']} polity clusters; 24 MERb=0 crises in this sample."),
    item("removed logit: coef, OR (95% CI), p, n, shares, n MERb=0", "2.01, OR 7.4 (2.6, 21), p=0.0002, n=132, 67% vs 22%, 23",
         f"{r(rm['b'],3)}, OR {r(rm['OR'],2)} ({r(rm['OR_ci95'][0],2)}, {r(rm['OR_ci95'][1],2)}), p={r(rm['p'],4)}, n={rm['n']}, "
         f"{r(100*rm['share_MERb1'],0)}% vs {r(100*rm['share_MERb0'],0)}%, {rm['n_MERb0']}",
         "match"),
    item("+PolPop: severity coef, p; removed OR, p", "+0.12, p=0.51; OR 5.5, p=0.006",
         f"{r(s2['b'],3)}, p={r(s2['p_normal'],3)} (n={s2['n']}); OR {r(rm2['OR'],2)}, p={r(rm2['p'],4)} (n={rm2['n']})",
         "match", "Complete cases on PolPop drop 17 and 15 crises respectively."),
]

out["original_code_review"] = [
    {"file": "/root/analysis/study2/study2.py", "line": 19,
     "issue": "unit_scores keeps only incidence columns whose names are in the flag index, silently dropping 8 motifs whose "
              "incidence columns end in '_' (b28e_, d4aa_, e15_, e15a_, e15b_, e18_, h36g1_, m81_; d4aa is a vice-Property motif). "
              "Wrong merge key; effect tiny (EA 0.0776 -> 0.0771, WVS -0.0226 -> -0.0221).", "severity": "minor"},
    {"file": "/root/analysis/study2/study2.py", "line": "23-24, 43-46",
     "issue": "Country shares are weighted by the fractional population-weighted incidence; the stated rule says weight only "
              "if the file has counts. The expected values depend on this choice (unweighted: WVS -0.09, GPS +0.03). "
              "Weighting is defensible (README: unweighted presence picks up border slivers), but it should be stated.",
     "severity": "spec ambiguity"},
    {"file": "/root/analysis/study2/study2.py", "line": "62-66 (reporting)",
     "issue": "The S2-2 claim cites the cont0 results (no individual controls), but describes the model as following the do-file's "
              "individual controls. The cont1 results (+0.015; CCI_net +0.036, p=0.002; trickster 1.07, p=0.008) are the ones "
              "matching that description. Code is otherwise equivalent to the do-file (rel, health, gender, age deciles verified identical).",
     "severity": "reporting mismatch"},
    {"file": "/root/analysis/study2/study2.py", "line": 65,
     "issue": "C(cntry_round) dummies in OLS keep 4 singleton observations that reghdfe drops (n 6,558/117 vs 6,554/116). "
              "p-values here and at lines 52 and 76 use a normal reference, not Stata's t(N-K) or t(G-1): slightly smaller p.",
     "severity": "cosmetic"},
    {"file": "/root/analysis/cci/macd.py", "line": "12 and 18",
     "issue": "Dictionary keys split on whitespace only, but the text tokenizer splits on hyphens, so all 43 hyphenated "
              "dictionary terms ('in-law', 'mother-in-law', 'give-and-take', 'self-denial', 'even-handed', ...) and 'i.o.u.' "
              "can never match.", "severity": "minor"},
    {"file": "/root/analysis/cci/macd.py", "line": "19-26",
     "issue": "An unstated -est/-eth stemmer adds matches the described method would not ('noblest' -> 'noble'). "
              "Together with the hyphen issue this changes 4 motif flags.", "severity": "minor"},
    {"file": "/root/analysis/h8/h8_improved.py", "line": 198,
     "issue": "pd.cut bins are right-closed, so year -500 falls in 'pre500BCE' though the spec says 'before -500'. "
              "No crisis sits exactly on -500 or 1500, so there is no effect. Same at h8_3_population.py line 15.",
     "severity": "none in practice"},
    {"file": "/root/analysis/h8/h8_improved.py", "line": "193-207",
     "issue": "No coding errors found. Coding, severity min_count=2, removed=max, MERb, era fallback and polity clustering match the spec. "
              "The crisis 'polity' key matches the frame and covariate ids (169/169; names agree in 151, the rest are spelling variants). "
              "The PolPop omission was a coding slip; h8_3_population.py fixes it and reproduces exactly.",
     "severity": "none"},
]
json.dump(out, open(V + "verification.json", "w"), indent=1)
print(json.dumps(out, indent=1)[:6000])
