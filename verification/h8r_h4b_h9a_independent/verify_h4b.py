"""
Independent re-derivation of the H4b counts from final_codes.csv.
"""
import json
import pandas as pd

df = pd.read_csv("/root/analysis/h4b/codes/final_codes.csv", dtype=str)
for c in ["same_tradition", "adopted", "conqueror_tradition"]:
    df[c] = df[c].str.strip()

OUT = {}
OUT["n_rows"] = len(df)
OUT["n_unique_items"] = int(df["item"].nunique())
OUT["items_expected_present"] = sorted(set(f"C{i:03d}" for i in range(1, 118)) - set(df["item"])) == []

# Step 1: same_tradition counts
OUT["same_tradition"] = df["same_tradition"].value_counts(dropna=False).to_dict()

# Step 2: adoption among different-tradition episodes
n = df[df["same_tradition"] == "N"].copy()
OUT["adopted_among_N"] = n["adopted"].fillna("missing").value_counts().to_dict()
OUT["adopted_nonmissing_among_Y"] = int(df.loc[df["same_tradition"] == "Y", "adopted"].notna().sum())


# Step 3: crosstab by conqueror tradition among N
def group(t):
    if isinstance(t, str) and t.startswith("Other"):
        return "Other*"
    return t


n["cq_group"] = n["conqueror_tradition"].map(group)
ct = pd.crosstab(n["cq_group"], n["adopted"].fillna("missing"))
OUT["crosstab"] = {k: {kk: int(vv) for kk, vv in row.items() if vv} for k, row in ct.iterrows()}

oth = n[n["cq_group"] == "Other*"]
OUT["other_n"] = len(oth)
OUT["other_adopted_YP"] = int(oth["adopted"].isin(["Y", "P"]).sum())
OUT["other_adopted_breakdown"] = oth["adopted"].fillna("missing").value_counts().to_dict()

with open("/root/analysis/verify3/h4b_results.json", "w") as f:
    json.dump(OUT, f, indent=2)
print(json.dumps(OUT, indent=2))
