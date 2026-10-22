"""Stage 1 feasibility: count polity terminations in the open Seshat Equinox-era sample.
Step 1: keep one row per polity (drop Seshat's duplicate NGA rows).
Step 2: within each NGA, order polities by start date; the next one is the successor.
Step 3: the successor's Seshat code 'relationship to preceding (quasi)polity' tells us how the polity ended.
Step 4: map those codes to the protocol's termination types and count events."""
import sys, pandas as pd, numpy as np
d = sys.argv[1]
ex = pd.read_csv(f"{d}/exportdat.csv", low_memory=False)
pol = pd.read_csv(f"{d}/polities.csv")

# Step 2 uses all NGA rows (a polity can span several NGAs), then we dedupe events per polity
pol = pol.sort_values(["NGA", "Start"])
pol["successor"] = pol.groupby("NGA").PolID.shift(-1)

# Step 3: successor relationship codes (clean spelling variants)
rel = ex[ex.Variable == "relationship to preceding (quasi)polity"][["Polity", "Value From"]].copy()
rel["code"] = rel["Value From"].astype(str).str.strip().str.lower()
fix = {"continuation": "continuity", "continunity": "continuity", "contination": "continuity", "same cultural group": "continuity"}
rel["code"] = rel.code.replace(fix)

# Step 4: mapping to protocol termination types (Section 3)
typemap = {
    "continuity": "transformation (censored)",
    "elite migration": "conquest",
    "vassalage": "conquest", "feudal subordinates": "conquest",
    "cultural assimilation": "absorption",
    "population migration": "replacement",
    "replacement": "replacement",
    "overthrow": "internal", "regime change": "internal", "indigenous revolt": "internal",
    "not applicable": "uncoded",
}
rel["ttype"] = rel.code.map(typemap).fillna("uncoded")

def end_type(succ):
    if pd.isna(succ):
        return "right-censored (end of record)"
    t = rel[rel.Polity == succ].ttype.unique()
    if len(t) == 0:
        return "uncoded"
    if len(t) > 1:
        return "disputed: " + "/".join(sorted(t))
    return t[0]

pol["end_type"] = pol.successor.map(end_type)

# A polity counts as terminated if it ended non-continuously in ANY NGA it occupied;
# keep the most informative row per polity (prefer non-censored, non-continuity)
rank = {"conquest": 0, "internal": 0, "replacement": 0, "absorption": 0}
pol["r"] = pol.end_type.map(lambda t: 0 if t in rank else (1 if t.startswith("disputed") else 2))
one = pol.sort_values("r").drop_duplicates("PolID")

print("Unique polities:", one.PolID.nunique(), "| NGAs:", pol.NGA.nunique())
tab = one.end_type.value_counts()
print(tab.to_string())
events = one[one.end_type.isin(rank.keys())]
disputed = one[one.end_type.str.startswith("disputed")]
print("\nClear non-continuous terminations (events):", len(events))
print("Disputed codings (bounded counts):", len(disputed))
print("Upper bound if all disputed count as events:", len(events) + len(disputed))
print("\nEvents by world region:"); print(events["World Region"].value_counts().to_string())
era = pd.cut(events.End, [-1e5, -500, 1500, 3000], labels=["before 500 BCE", "500 BCE-1500 CE", "after 1500 CE"])
print("\nEvents by era (H7 bins):"); print(era.value_counts().sort_index().to_string())
print("\nInternal-type events (for H4a):", (events.end_type == "internal").sum())
one.drop(columns="r").to_csv(sys.argv[2], index=False)
