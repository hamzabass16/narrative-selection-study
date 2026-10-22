"""
Independent verification, step C: country models (S2-1).

Authors' do-file (Country_Tables_Figures_FINAL.do, Table V Panel A col 1):
    global cont0 lnyear_firstpub lnnmbr_title
    reg lntrust_wvsavg tricksters_punish $cont0, r      <- HC1 robust, no continent dummies
We swap the measure for CCI (and keep the trickster version as positive control).
Standardized beta = b * SD(x) / SD(y) in the estimation sample.
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

CONT0 = ["lnyear_firstpub", "lnnmbr_title"]


def ols_hc1(df, y, x, controls, level=0.90):
    d = df[[y, x] + controls].dropna()
    X = sm.add_constant(d[[x] + controls])
    fit = sm.OLS(d[y], X).fit(cov_type="HC1")
    b, se, p = fit.params[x], fit.bse[x], fit.pvalues[x]
    # Stata 'reg, r' uses t with N-K df for p and CI
    dfree = fit.df_resid
    t = b / se
    p_t = 2 * stats.t.sf(abs(t), dfree)
    crit = stats.t.ppf(1 - (1 - level) / 2, dfree)
    k = d[x].std(ddof=1) / d[y].std(ddof=1)
    return {"b": b, "se": se, "p": p_t, "n": int(len(d)),
            "std_beta": b * k, "std_ci90": [(b - crit * se) * k, (b + crit * se) * k]}


if __name__ == "__main__":
    cols = ["cntry", "lntrust_wvsavg", "trust_gps", "tricksters_punish"] + CONT0
    c = pd.read_stata(D + "Country_Regressions_Ready.dta", columns=cols)
    assert c.cntry.is_unique
    cci = pd.read_csv(OUT + f"cci_country_{share}_{variant}.csv").set_index("cntry")
    df = c.merge(cci[["CCI", "CCI_net"]], left_on="cntry", right_index=True, how="left", validate="1:1")
    print("countries in reg file", len(c), "with CCI", df.CCI.notna().sum())
    res = {}
    for y, x in [("lntrust_wvsavg", "CCI"), ("lntrust_wvsavg", "CCI_net"),
                 ("lntrust_wvsavg", "tricksters_punish"), ("trust_gps", "CCI"),
                 ("trust_gps", "tricksters_punish")]:
        r = ols_hc1(df, y, x, CONT0)
        res[f"{y}~{x}"] = r
        print(f"{y:15s} ~ {x:18s} b={r['b']:.4f} p={r['p']:.4f} std={r['std_beta']:.3f} "
              f"CI90=[{r['std_ci90'][0]:.3f},{r['std_ci90'][1]:.3f}] n={r['n']}")
    json.dump(res, open(OUT + f"country_models_{share}_{variant}.json", "w"), indent=1)
