import sys, pandas as pd
c = sys.argv[1]
vals = pd.read_csv(f"{c}/data.csv", low_memory=False)
for p in ["EA034", "EA008", "EA033", "EA043"]:
    print(p, "societies coded:", vals[vals.Var_ID == p].Soc_ID.nunique())
print("EA034 (high gods) codes:", vals[vals.Var_ID == "EA034"].Value.value_counts().sort_index().to_dict())
