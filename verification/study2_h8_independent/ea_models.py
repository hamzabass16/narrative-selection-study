"""
Independent verification, step E: Ethnographic Atlas (S2-3).

Authors' do-file (Ethnographic_Atlas_Tables_Figures_FINAL.do), e.g. Table on king motifs / v33:
    global cont lnyear_firstpub lnnmbr_title if motifs_total>4
    areg Y X $cont, cluster(v98) a(continent_EA)
Here: v33 on CCI (+ i.v34 dummies in the second spec).
Stata areg with vce(cluster): small-sample factor (N-1)/(N-K) * G/(G-1), K includes absorbed FE,
t with G-1 df. Standardized = b*SD(x)/SD(y) in the estimation sample.
"""
import json
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

D = "/root/data/mx_folklore/"
OUT = "/root/analysis/verify2/"
variant = sys.argv[1] if len(sys.argv) > 1 else "alpha_apos"
share = sys.argv[2] if len(sys.argv) > 2 else "unw"


def areg_cluster(df, y, x, controls, cats, fe, cl, level=0.90):
    d = df[[y, x, fe, cl] + controls + cats].dropna()
    parts = [d[[x] + controls]]
    parts += [pd.get_dummies(d[c].astype(int), prefix=c, drop_first=True, dtype=float) for c in cats]
    parts += [pd.get_dummies(d[fe], prefix="fe", drop_first=True, dtype=float)]
    X = sm.add_constant(pd.concat(parts, axis=1))
    fit = sm.OLS(d[y], X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[cl])[0]})
    G = d[cl].nunique()
    b, se = fit.params[x], fit.bse[x]
    p = 2 * stats.t.sf(abs(b / se), G - 1)
    crit = stats.t.ppf(1 - (1 - level) / 2, G - 1)
    k = d[x].std(ddof=1) / d[y].std(ddof=1)
    return {"b": b, "se": se, "p": p, "n": int(len(d)), "n_clusters": int(G),
            "std_beta": b * k, "std_ci90": [(b - crit * se) * k, (b + crit * se) * k]}


if __name__ == "__main__":
    cols = ["atlas", "motifs_total", "v33", "v34", "v98", "continent_EA", "lnyear_firstpub", "lnnmbr_title"]
    ea = pd.read_stata(D + "Ethnographic_Atlas_Regressions_Ready.dta", columns=cols, convert_categoricals=False)
    cci = pd.read_csv(OUT + f"cci_ea_{share}_{variant}.csv").set_index("atlas")
    df = ea.merge(cci[["CCI", "CCI_net"]], left_on="atlas", right_index=True, how="left", validate="1:1")
    df = df[df.motifs_total > 4]
    print("EA groups motifs_total>4:", len(df), "with CCI:", df.CCI.notna().sum(), "with v33:", df.v33.notna().sum())
    res = {}
    base = ["lnyear_firstpub", "lnnmbr_title"]
    for x in ["CCI", "CCI_net"]:
        for lab, cats in [("base", []), ("v34", ["v34"])]:
            r = areg_cluster(df, "v33", x, base, cats, "continent_EA", "v98")
            res[f"v33~{x}|{lab}"] = r
            print(f"v33 ~ {x:8s} [{lab:4s}] b={r['b']:.4f} p={r['p']:.4f} std={r['std_beta']:.4f} "
                  f"CI90=[{r['std_ci90'][0]:.3f},{r['std_ci90'][1]:.3f}] n={r['n']} G={r['n_clusters']}")
    json.dump(res, open(OUT + f"ea_models_{share}_{variant}.json", "w"), indent=1)
