"""
Independent re-derivation of the H9a coding numbers.
Krippendorff's alpha (nominal) and the Wilson interval are implemented here by hand.
"""
import glob
import json
import math
from collections import Counter, defaultdict

BASE = "/root/analysis/h9a"
OUT = {}

passages = json.load(open(f"{BASE}/passages.json"))
pid_domain = {p["pid"]: p["domain"] for p in passages}
OUT["n_passages"] = len(passages)
OUT["n_unique_pids"] = len(pid_domain)


def load_codes(folder):
    rows = []
    for f in sorted(glob.glob(f"{BASE}/codes/{folder}/*.json")):
        for r in json.load(open(f)):
            r = dict(r)
            r["_file"] = f.split("/")[-1]
            rows.append(r)
    return rows


c1_rows = load_codes("pass1")
c2_rows = load_codes("pass2")


def summarise(rows, label):
    pids = [r["pid"] for r in rows]
    cnt = Counter(pids)
    dups = {p: n for p, n in cnt.items() if n > 1}
    # Do duplicate entries disagree?
    by = defaultdict(list)
    for r in rows:
        by[r["pid"]].append((r.get("relevant"), r.get("valence")))
    conflicting = {p: v for p, v in by.items() if len(set(v)) > 1}
    unknown = sorted(set(pids) - set(pid_domain))
    OUT[f"{label}_n_rows"] = len(rows)
    OUT[f"{label}_n_unique_pids"] = len(cnt)
    OUT[f"{label}_n_duplicate_pids"] = len(dups)
    OUT[f"{label}_n_conflicting_duplicates"] = len(conflicting)
    OUT[f"{label}_pids_not_in_passages"] = unknown[:20]
    OUT[f"{label}_relevant_values"] = dict(Counter(r.get("relevant") for r in rows))
    OUT[f"{label}_valence_values"] = dict(Counter(r.get("valence") for r in rows))
    OUT[f"{label}_relevant_x_valence"] = dict(Counter(f"{r.get('relevant')}|{r.get('valence')}" for r in rows))
    return {p: v[-1] for p, v in by.items()}, conflicting


c1, c1_conf = summarise(c1_rows, "coder1")
c2, c2_conf = summarise(c2_rows, "coder2")
OUT["coder1_covers_all_passages"] = set(c1) == set(pid_domain)
OUT["coder1_missing_pids"] = sorted(set(pid_domain) - set(c1))[:20]

# Does each society file in pass1 only contain passages from that society?
soc_of = {p["pid"]: p["society"] for p in passages}
mism = 0
for r in c1_rows:
    fname = r["_file"].replace(".json", "")
    soc = soc_of.get(r["pid"], "")
    norm = "".join(ch if ch.isalnum() else "_" for ch in soc)
    norm = "_".join(t for t in norm.split("_") if t)
    if norm != fname:
        mism += 1
OUT["coder1_rows_in_wrong_society_file"] = mism


# ---------------- Krippendorff's alpha, nominal, 2 coders ----------------
def kripp_alpha_nominal(pairs):
    """pairs: list of (a, b) values for units coded by both coders."""
    o = Counter()                    # coincidence matrix
    for a, b in pairs:
        o[(a, b)] += 1
        o[(b, a)] += 1
    n_c = Counter()
    for (a, _), v in o.items():
        n_c[a] += v
    n = sum(n_c.values())
    d_obs = sum(v for (a, b), v in o.items() if a != b) / n
    d_exp = sum(n_c[a] * n_c[b] for a in n_c for b in n_c if a != b) / (n * (n - 1))
    return 1 - d_obs / d_exp


both = sorted(set(c1) & set(c2))
OUT["n_double_coded"] = len(both)
OUT["coder2_pids_not_coded_by_coder1"] = sorted(set(c2) - set(c1))

rel_pairs = [(c1[p][0], c2[p][0]) for p in both]
val_pairs = [(c1[p][1], c2[p][1]) for p in both]
OUT["relevance_agree"] = sum(a == b for a, b in rel_pairs)
OUT["relevance_alpha"] = kripp_alpha_nominal(rel_pairs)
OUT["valence_agree"] = sum(a == b for a, b in val_pairs)
OUT["valence_alpha"] = kripp_alpha_nominal(val_pairs)

# Valence alpha restricted to units both coders called relevant (sensitivity)
vr = [(c1[p][1], c2[p][1]) for p in both if c1[p][0] == "Y" and c2[p][0] == "Y"]
OUT["valence_alpha_both_relevant"] = [len(vr), sum(a == b for a, b in vr), kripp_alpha_nominal(vr)]

# Is the double-coded set what double_coded_pids.json says?
try:
    dc = json.load(open(f"{BASE}/double_coded_pids.json"))
    dc_set = set(dc if isinstance(dc, list) else sum(dc.values(), []) if isinstance(dc, dict) else [])
    OUT["double_coded_file_n"] = len(dc_set)
    OUT["double_coded_file_equals_pass2"] = dc_set == set(c2)
except Exception as e:
    OUT["double_coded_file_error"] = str(e)


# ---------------- First-coder POS/NEG by domain + Wilson bounds ----------------
def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    ph = k / n
    den = 1 + z * z / n
    centre = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (centre - half, centre + half)


domains = ["Family", "Group", "Reciprocity", "Heroism", "Deference", "Fairness", "Property"]
tab = {}
for dom in domains:
    pids = [p for p in c1 if pid_domain.get(p) == dom]
    pos = sum(c1[p][1] == "POS" for p in pids)
    neg = sum(c1[p][1] == "NEG" for p in pids)
    pos_rel = sum(c1[p][1] == "POS" and c1[p][0] == "Y" for p in pids)
    neg_rel = sum(c1[p][1] == "NEG" and c1[p][0] == "Y" for p in pids)
    lo, hi = wilson(neg, pos + neg)
    tab[dom] = {"POS": pos, "NEG": neg, "POS_if_relevant": pos_rel, "NEG_if_relevant": neg_rel,
                "n_passages": len(pids), "wilson_upper": round(hi, 4)}
OUT["coder1_by_domain"] = tab

with open("/root/analysis/verify3/h9a_results.json", "w") as f:
    json.dump(OUT, f, indent=2)
print(json.dumps(OUT, indent=2))
