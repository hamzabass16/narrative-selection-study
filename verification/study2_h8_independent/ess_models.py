"""
Independent verification, step D: ESS second-generation immigrants (S2-2).

Follows European_Social_Surveys_Tables_Figures_FINAL.do, Table V Panel B col 2:
    g cntry_round = cntry_ess + essround
    g lntrust_ess = ln(1+ppltrst)
    age = agea, missing if agea>100; xtile age10_2imm = age, nq(10)  (on all non-missing ages)
    rel = rlgdnm (missing if .a/.b/.c); rel=0 if rlgblg==2; missing if rlgblg is .a/.b/.c
    sample: rel!=. & health not .a/.b/.c & age!=. & gender!=.a & age>17
    reghdfe lntrust_ess X lnyear_firstpub lnnmbr_title gender i.rel i.health i.age10_2imm,
            cluster(cntry) absorb(cntry_round)
reghdfe drops singleton FE groups (iteratively); FE are not nested in clusters, so the
small-sample factor counts the FE levels. Standardized = b*SD(x)/SD(y) in the estimation sample.
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
share = sys.argv[2] if len(sys.argv) > 2 else "w"


def stata_xtile(x, nq):
    """Stata xtile with default (non-altdef) percentiles."""
    v = np.sort(x.dropna().values)
    n = len(v)
    cuts = []
    for i in range(1, nq):
        p = 100 * i / nq
        np_ = n * p / 100
        j = int(np.floor(np_))
        if abs(np_ - j) < 1e-12:
            cuts.append((v[j - 1] + v[j]) / 2)
        else:
            cuts.append(v[int(np.ceil(np_)) - 1])
    out = pd.Series(np.nan, index=x.index)
    ok = x.notna()
    out[ok] = 1 + np.searchsorted(np.array(cuts), x[ok].values, side="left")
    return out


def is_ext(series, codes):
    """True where a convert_missing=True column holds one of the Stata extended missing codes."""
    return series.map(lambda v: getattr(v, "string", None) in codes)


def num(series):
    return pd.to_numeric(series.map(lambda v: np.nan if hasattr(v, "string") else v), errors="coerce")


def build_sample():
    raw = pd.read_stata(D + "European_Social_Surveys_Regressions_Ready.dta",
                        convert_categoricals=False, convert_missing=True)
    df = pd.DataFrame(index=raw.index)
    df["cntry"] = raw["cntry"]
    df["cntry_round"] = raw["cntry_ess"].astype(str) + raw["essround"].astype(int).astype(str)
    df["lntrust_ess"] = np.log(1 + num(raw["ppltrst"]))
    agea = num(raw["agea"])
    df["age"] = agea.where(agea <= 100)            # extended missing -> . as well
    df["gender"] = num(raw["gndr"])
    gender_is_a = is_ext(raw["gndr"], {".a"})
    # religion
    rel = num(raw["rlgdnm"])                        # .a/.b/.c (and .) -> NaN
    rel = rel.where(~(num(raw["rlgblg"]) == 2), 0.0)
    rel = rel.where(~is_ext(raw["rlgblg"], {".a", ".b", ".c"}))
    df["rel"] = rel
    df["health"] = num(raw["health"])
    health_bad = is_ext(raw["health"], {".a", ".b", ".c"})
    df["age10"] = stata_xtile(df["age"], 10)
    for c in ["lnyear_firstpub", "lnnmbr_title", "tricksters_punish"]:
        df[c] = raw[c].astype(float)
    cond = df.rel.notna() & ~health_bad & df.age.notna() & ~gender_is_a & (df.age > 17)
    return df[cond].copy()


def drop_singletons(d, fe):
    while True:
        cnt = d.groupby(fe)[fe].transform("size")
        if (cnt > 1).all():
            return d
        d = d[cnt > 1]


def reghdfe(df, y, x, controls, cats, fe, cl, level=0.90):
    d = df[[y, x, fe, cl] + controls + cats].dropna()
    d = drop_singletons(d, fe)
    dummies = [pd.get_dummies(d[c].astype(int), prefix=c, drop_first=True, dtype=float) for c in cats]
    fed = pd.get_dummies(d[fe], prefix="fe", drop_first=True, dtype=float)
    X = pd.concat([d[[x] + controls]] + dummies + [fed], axis=1)
    X = sm.add_constant(X)
    fit = sm.OLS(d[y], X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[cl])[0]})
    # statsmodels cluster: G/(G-1)*(N-1)/(N-K), t with G-1 df -> same as reghdfe (FE not nested)
    G = d[cl].nunique()
    b, se = fit.params[x], fit.bse[x]
    p = 2 * stats.t.sf(abs(b / se), G - 1)
    crit = stats.t.ppf(1 - (1 - level) / 2, G - 1)
    k = d[x].std(ddof=1) / d[y].std(ddof=1)
    return {"b": b, "se": se, "p": p, "n": int(len(d)), "n_origin": int(G),
            "n_fe": int(d[fe].nunique()), "std_beta": b * k,
            "std_ci90": [(b - crit * se) * k, (b + crit * se) * k]}


if __name__ == "__main__":
    s = build_sample()
    cci = pd.read_csv(OUT + f"cci_country_{share}_{variant}.csv").set_index("cntry")
    s = s.merge(cci[["CCI", "CCI_net"]], left_on="cntry", right_index=True, how="left")
    print("sample after do-file conditions:", len(s), "origin with CCI:", s.loc[s.CCI.notna(), "cntry"].nunique(),
          "origins total:", s.cntry.nunique())
    controls = ["lnyear_firstpub", "lnnmbr_title", "gender"]
    cats = ["rel", "health", "age10"]
    res = {}
    for x in ["CCI", "CCI_net", "tricksters_punish"]:
        r = reghdfe(s, "lntrust_ess", x, controls, cats, "cntry_round", "cntry")
        res[x] = r
        print(f"{x:18s} b={r['b']:.4f} p={r['p']:.4f} std={r['std_beta']:.4f} "
              f"CI90=[{r['std_ci90'][0]:.3f},{r['std_ci90'][1]:.3f}] n={r['n']} G={r['n_origin']} FE={r['n_fe']}")
    # baseline-controls-only spec (Table V Panel B col 1) for reference
    for x in ["CCI", "tricksters_punish"]:
        r = reghdfe(s, "lntrust_ess", x, ["lnyear_firstpub", "lnnmbr_title"], [], "cntry_round", "cntry")
        res[x + "_cont0"] = r
        print(f"[cont0] {x:18s} b={r['b']:.4f} p={r['p']:.4f} std={r['std_beta']:.4f} n={r['n']} G={r['n_origin']}")
    json.dump(res, open(OUT + f"ess_models_{share}_{variant}.json", "w"), indent=1)
