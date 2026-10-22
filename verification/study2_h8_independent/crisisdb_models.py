"""
Independent verification, step F: CrisisDB (H8-3).

Coding per crisis row of 'crisisdb/crisis-consequences':
  civil_war, extermination, collapse, depose, assassination: P/IP -> 1, A/IA -> 0, else missing
  severity = civil_war + extermination + collapse, needs >= 2 of 3 non-missing
             (computed as the sum of the non-missing items)
  removed  = max(depose, assassination)  (missing only if both missing)
  MERb     = 1 if polity MER >= 0.5, 0 if < 0.5, missing if MER missing
  era      = from year_from (fallback polity start_year): < -500, -500..1500, > 1500
Models: severity OLS on MERb + era dummies, cluster by polity;
        removed logit on MERb + era dummies, cluster by polity; then + PolPop.
"""
import json

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

OUT = "/root/analysis/verify2/"
J = json.load(open("/root/analysis/seshat/seshat_current_2026-10-17.json"))
tab = J["crisisdb/crisis-consequences"]
cr = pd.DataFrame(tab["rows"], columns=tab["cols"])
cov = pd.read_csv("/root/analysis/study1/covariates.csv", index_col="id")
frame = pd.read_csv("/root/analysis/frame/polities_frame.csv", index_col="id")

CODE = {"P": 1.0, "IP": 1.0, "A": 0.0, "IA": 0.0}
for v in ["civil_war", "extermination", "collapse", "depose", "assassination"]:
    cr[v + "_c"] = cr[v].map(CODE)          # anything else (SU, DIS, None) -> NaN

sev_items = cr[["civil_war_c", "extermination_c", "collapse_c"]]
cr["severity"] = sev_items.sum(axis=1, min_count=1).where(sev_items.notna().sum(axis=1) >= 2)
cr["removed"] = cr[["depose_c", "assassination_c"]].max(axis=1)   # NaN only if both NaN

cr["polity"] = pd.to_numeric(cr["polity"], errors="coerce").astype("Int64")
cr["MER"] = cr["polity"].map(cov["MER"])
cr["PolPop"] = cr["polity"].map(cov["PolPop"])
cr["MERb"] = np.where(cr["MER"].isna(), np.nan, (cr["MER"] >= 0.5).astype(float))
yr = pd.to_numeric(cr["year_from"], errors="coerce")
yr = yr.fillna(cr["polity"].map(frame["start_year"]))
cr["year_used"] = yr
cr["era"] = pd.cut(yr, [-np.inf, -500 - 1e-9, 1500, np.inf], labels=["early", "mid", "late"])
# boundaries: 'before -500' -> < -500 ; '-500 to 1500' inclusive ; 'after 1500' -> > 1500
print("crises:", len(cr), "polity unmatched in covariates:", cr.MER.isna().sum(),
      "year_from missing:", pd.to_numeric(cr["year_from"], errors="coerce").isna().sum())
print(cr.era.value_counts(dropna=False).to_dict())


def cluster_fit(model, d):
    return model.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["polity"])[0]}, disp=0) \
        if isinstance(model, sm.Logit) else model.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["polity"])[0]})


def design(d, extra):
    X = pd.concat([d[["MERb"] + extra],
                   pd.get_dummies(d["era"], prefix="era", drop_first=True, dtype=float)], axis=1)
    X = X.loc[:, X.std() > 0]
    return sm.add_constant(X)


res = {}
for extra in [[], ["PolPop"]]:
    tag = "base" if not extra else "+PolPop"
    # severity OLS
    d = cr.dropna(subset=["severity", "MERb", "era"] + extra).copy()
    d["era"] = d["era"].cat.remove_unused_categories()
    fit = sm.OLS(d["severity"], design(d, extra)).fit(cov_type="cluster",
                                                     cov_kwds={"groups": pd.factorize(d["polity"])[0]})
    G = d.polity.nunique()
    r = {"b": fit.params["MERb"], "se": fit.bse["MERb"], "p_normal": fit.pvalues["MERb"],
         "p_t": 2 * stats.t.sf(abs(fit.params["MERb"] / fit.bse["MERb"]), G - 1),
         "n": int(len(d)), "n_polities": int(G),
         "mean_MERb1": d.loc[d.MERb == 1, "severity"].mean(), "mean_MERb0": d.loc[d.MERb == 0, "severity"].mean(),
         "n_MERb0": int((d.MERb == 0).sum())}
    res[f"severity|{tag}"] = r
    print(f"severity {tag}: b={r['b']:.3f} p(z)={r['p_normal']:.3f} p(t)={r['p_t']:.3f} n={r['n']} "
          f"G={G} means {r['mean_MERb1']:.2f} vs {r['mean_MERb0']:.2f} nMERb0={r['n_MERb0']}")
    # removed logit
    d = cr.dropna(subset=["removed", "MERb", "era"] + extra).copy()
    d["era"] = d["era"].cat.remove_unused_categories()
    m = sm.Logit(d["removed"], design(d, extra))
    fit = m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["polity"])[0]}, disp=0)
    b, se = fit.params["MERb"], fit.bse["MERb"]
    r = {"b": b, "se": se, "OR": float(np.exp(b)), "OR_ci95": [float(np.exp(b - 1.959964 * se)), float(np.exp(b + 1.959964 * se))],
         "p": fit.pvalues["MERb"], "n": int(len(d)), "n_polities": int(d.polity.nunique()),
         "share_MERb1": d.loc[d.MERb == 1, "removed"].mean(), "share_MERb0": d.loc[d.MERb == 0, "removed"].mean(),
         "n_MERb0": int((d.MERb == 0).sum())}
    res[f"removed|{tag}"] = r
    print(f"removed  {tag}: b={b:.3f} OR={r['OR']:.2f} CI95=[{r['OR_ci95'][0]:.2f},{r['OR_ci95'][1]:.2f}] "
          f"p={r['p']:.4f} n={r['n']} G={r['n_polities']} shares {r['share_MERb1']:.2f} vs {r['share_MERb0']:.2f} "
          f"nMERb0={r['n_MERb0']}")
json.dump(res, open(OUT + "crisisdb_models.json", "w"), indent=1, default=float)
cr.to_csv(OUT + "crisisdb_coded.csv", index=False)
