"""Independent re-derivation of H9a v2 claims (moral evaluations in ethnographies).

Step by step:
  1. Load passages, first-pass codes, second codes (D files), review codes (N2, N3).
  2. Count passages, societies, language families.
  3. Agreement on the double-coded sample (percent agreement, Krippendorff alpha nominal).
  4. Final valence per pre-registered rule.
  5. POS/NEG by domain, family-weighted NEG share, Property by target.
"""
import csv
import glob
import json
import re
from collections import Counter, defaultdict

BASE = "/root/analysis/h9a"
OUT = "/root/analysis/verify4/part1_results.json"


def society_key(name):
    # every run of non-alphanumeric characters -> '_', then strip leading/trailing '_'
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def load_code_files(pattern):
    records = {}
    duplicates = []
    for path in sorted(glob.glob(pattern)):
        for rec in json.load(open(path)):
            if rec["pid"] in records:
                duplicates.append(rec["pid"])
            records[rec["pid"]] = rec
    return records, duplicates


def coded_valence(rec):
    """A coder's valence: their valence if they said relevant = Y, else NA."""
    if rec is None:
        return None
    if rec["relevant"] == "Y":
        return rec["valence"]
    return "NA"


def krippendorff_alpha_nominal(pairs):
    """Nominal alpha for two coders, no missing values. pairs = list of (a, b)."""
    coincidence = Counter()
    for a, b in pairs:
        coincidence[(a, b)] += 1
        coincidence[(b, a)] += 1
    n_c = Counter()
    for (a, b), cnt in coincidence.items():
        n_c[a] += cnt
    n = sum(n_c.values())
    observed_disagree = sum(cnt for (a, b), cnt in coincidence.items() if a != b)
    expected_disagree = sum(n_c[a] * n_c[b] for a in n_c for b in n_c if a != b) / (n - 1)
    return 1 - observed_disagree / expected_disagree


# ---------- 1. Load ----------
passages = json.load(open(f"{BASE}/passages_v2.json"))
pass1, dup1 = load_code_files(f"{BASE}/codes_v2/pass1/*.json")
dcodes, dupD = load_code_files(f"{BASE}/codes_v2/pass2/D*.json")
n2, dupN2 = load_code_files(f"{BASE}/codes_v2/pass2/N2.json")
n3, dupN3 = load_code_files(f"{BASE}/codes_v2/pass2/N3.json")
sample_pids = json.load(open(f"{BASE}/codes_v2/double_coded_pids.json"))

families = {}
for csv_path in [f"{BASE}/candidates.csv", f"{BASE}/candidates_extra.csv"]:
    with open(csv_path, newline="") as fh:
        for row in csv.DictReader(fh):
            families[society_key(row["society"])] = row["family"]

checks = {
    "duplicate_pids_pass1": dup1,
    "duplicate_pids_D": dupD,
    "duplicate_pids_N2": dupN2,
    "duplicate_pids_N3": dupN3,
    "passages_without_pass1": [p["pid"] for p in passages if p["pid"] not in pass1],
    "relevance_values": dict(Counter(r["relevant"] for r in pass1.values())),
    "valence_values": dict(Counter(r["valence"] for r in pass1.values())),
}

# ---------- 2. Counts ----------
society_of = {}
domain_of = {}
for p in passages:
    society_of[p["pid"]] = p["society"]
    domain_of[p["pid"]] = p["domain"]

societies = sorted(set(society_of.values()))
unmatched = sorted(s for s in societies if society_key(s) not in families)
family_of_society = {s: families.get(society_key(s)) for s in societies}
n_families = len(set(f for f in family_of_society.values() if f is not None))
checks["societies_without_family"] = unmatched

# ---------- 3. Agreement on double-coded sample ----------
both = [pid for pid in sample_pids if pid in pass1 and pid in dcodes]
checks["sample_pids_not_in_D"] = [pid for pid in sample_pids if pid not in dcodes]
checks["D_pids_not_in_sample"] = [pid for pid in dcodes if pid not in set(sample_pids)]
rel_pairs = [(pass1[pid]["relevant"], dcodes[pid]["relevant"]) for pid in both]
val_pairs = [(coded_valence(pass1[pid]), coded_valence(dcodes[pid])) for pid in both]
rel_agree = sum(a == b for a, b in rel_pairs)
alpha_rel = krippendorff_alpha_nominal(rel_pairs)
alpha_val = krippendorff_alpha_nominal(val_pairs)

# ---------- 4. Final valence ----------
final = {}
neg_review = []
for pid, rec in pass1.items():
    first = coded_valence(rec)
    if first != "NEG":
        final[pid] = first
        continue
    if pid in dcodes:
        second_rec, second_src = dcodes[pid], "D"
    else:
        second_rec, second_src = n2.get(pid), "N2"
    third_rec = n3.get(pid)
    codes = [first, coded_valence(second_rec), coded_valence(third_rec)]
    counts = Counter(c for c in codes if c is not None)
    top, top_n = counts.most_common(1)[0]
    outcome = top if top_n >= 2 else "DISPUTED"
    final[pid] = outcome
    neg_review.append({"pid": pid, "codes": codes, "second_source": second_src,
                       "missing_second": second_rec is None, "missing_third": third_rec is None,
                       "final": outcome})

first_neg = len(neg_review)
final_neg_or_disputed = sum(1 for r in neg_review if r["final"] in ("NEG", "DISPUTED"))
disputed = [r["pid"] for r in neg_review if r["final"] == "DISPUTED"]
overturned = [r["pid"] for r in neg_review if r["final"] not in ("NEG", "DISPUTED")]
# any first-coder non-NEG that ended NEG? (cannot happen by rule, but count all final NEG)
total_final_neg = sum(1 for v in final.values() if v in ("NEG", "DISPUTED"))


def is_neg(v):
    return v in ("NEG", "DISPUTED")


# ---------- 5. Domain tables ----------
society_count_in_family = Counter(family_of_society.values())
domain_counts = defaultdict(lambda: {"POS": 0, "NEG": 0})
domain_weights = defaultdict(lambda: {"POS": 0.0, "NEG": 0.0})
for pid, v in final.items():
    dom = domain_of[pid]
    if v == "POS":
        key = "POS"
    elif is_neg(v):
        key = "NEG"
    else:
        continue
    w = 1.0 / society_count_in_family[family_of_society[society_of[pid]]]
    domain_counts[dom][key] += 1
    domain_weights[dom][key] += w

domain_table = {}
for dom in sorted(domain_counts):
    c = domain_counts[dom]
    w = domain_weights[dom]
    raw_share = c["NEG"] / (c["POS"] + c["NEG"])
    wshare = w["NEG"] / (w["POS"] + w["NEG"])
    domain_table[dom] = {"POS": c["POS"], "NEG": c["NEG"], "raw_share": raw_share,
                         "weighted_share": wshare, "falsified": wshare > 0.05}

# Property by first coder's target
prop_target = defaultdict(lambda: {"POS": 0, "NEG": 0})
for pid, v in final.items():
    if domain_of[pid] != "Property":
        continue
    tgt = pass1[pid]["target"]
    if v == "POS":
        prop_target[tgt]["POS"] += 1
    elif is_neg(v):
        prop_target[tgt]["NEG"] += 1

results = {
    "n_passages": len(passages),
    "n_societies": len(societies),
    "n_families": n_families,
    "n_both_coded": len(both),
    "relevance_agreement": rel_agree,
    "alpha_relevance": alpha_rel,
    "alpha_valence": alpha_val,
    "first_coder_neg": first_neg,
    "final_neg_including_disputed": final_neg_or_disputed,
    "total_final_neg_all_passages": total_final_neg,
    "overturned": overturned,
    "disputed": disputed,
    "neg_review": neg_review,
    "domain_table": domain_table,
    "property_by_target": {k: dict(v) for k, v in sorted(prop_target.items())},
    "checks": checks,
}
json.dump(results, open(OUT, "w"), indent=1)

print("passages", len(passages), "societies", len(societies), "families", n_families)
print("both coded", len(both), "rel agree", rel_agree, "alpha rel %.4f val %.4f" % (alpha_rel, alpha_val))
print("first NEG", first_neg, "final NEG", final_neg_or_disputed, "overturned", overturned, "disputed", disputed)
for dom, row in domain_table.items():
    print(dom, row)
print("Property by target", {k: dict(v) for k, v in prop_target.items()})
print("checks", {k: (v if not isinstance(v, list) else v[:10]) for k, v in checks.items()})
