"""
Independent verification, step B: build the folklore CCI per unit.

For each unit (country or EA group):
  share_d = share of the unit's motifs flagged in domain d
  CCI     = mean over 7 domains of z(share_d), z computed across units, then re-standardized
  CCI_net = same, using (virtue flag - vice flag) per motif
Units with fewer than 5 motifs are excluded.

Two share definitions are computed so we can see which one matters:
  'unw' : motif present if incidence > 0; share = (# present & flagged) / (# present)
  'w'   : incidence-weighted share = sum(v * flag) / sum(v)
Note: country incidence values are continuous population-weighted fractions in [0,1],
not counts, so by the task's rule the primary country measure is 'unw'.
"""
import sys

import numpy as np
import pandas as pd

D = "/root/data/mx_folklore/"
OUT = "/root/analysis/verify2/"
DOMAINS = ["Family", "Group", "Reciprocity", "Heroism", "Deference", "Fairness", "Property"]

variant = sys.argv[1] if len(sys.argv) > 1 else "alpha_apos"
flags = pd.read_csv(OUT + f"flags_{variant}.csv").set_index("motif_id")


def load_incidence(fname, key):
    df = pd.read_stata(D + fname, convert_categoricals=False)
    # 8 motif columns carry a trailing underscore in the incidence files (e.g. 'd4aa_')
    ren = {c: c[:-1] for c in df.columns if c.endswith("_") and c[:-1] in flags.index}
    df = df.rename(columns=ren)
    mot = [c for c in df.columns if c in flags.index]
    assert len(mot) == len(flags), (fname, len(mot))
    X = df.set_index(key)[mot].astype(float).fillna(0.0)
    meta = df.set_index(key)[["motifs_total"]]
    return X, meta


def zscore(s):
    return (s - s.mean()) / s.std(ddof=1)


def build(X, weighted):
    present = (X > 0).astype(float)
    n_present = present.sum(axis=1)
    keep = n_present >= 5
    X, present = X[keep], present[keep]
    W = X if weighted else present
    denom = W.sum(axis=1)
    res = pd.DataFrame(index=X.index)
    res["n_motifs"] = n_present[keep]
    F = flags.loc[X.columns]
    for d in DOMAINS:
        v = F[f"virtue_{d}"].values
        net = F[f"virtue_{d}"].values - F[f"vice_{d}"].values
        res[f"sh_{d}"] = W.values @ v / denom
        res[f"shnet_{d}"] = W.values @ net / denom
    res["CCI"] = zscore(pd.concat([zscore(res[f"sh_{d}"]) for d in DOMAINS], axis=1).mean(axis=1))
    res["CCI_net"] = zscore(pd.concat([zscore(res[f"shnet_{d}"]) for d in DOMAINS], axis=1).mean(axis=1))
    return res


if __name__ == "__main__":
    Xc, mc = load_incidence("Motifs_Countries.dta", "cntry")
    Xe, me = load_incidence("Motifs_EA_groups.dta", "atlas")
    out = {}
    for lab, X in [("country", Xc), ("ea", Xe)]:
        for w in [False, True]:
            r = build(X, w)
            tag = f"{lab}_{'w' if w else 'unw'}"
            r.to_csv(OUT + f"cci_{tag}_{variant}.csv")
            print(tag, "units", len(r), "excluded", len(X) - len(r),
                  "corr(CCI,CCI_net)=%.3f" % r.CCI.corr(r.CCI_net))
