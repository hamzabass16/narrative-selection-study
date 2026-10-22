import sys, pandas as pd
d, f = sys.argv[1], sys.argv[2]
ex = pd.read_csv(f"{d}/exportdat.csv", low_memory=False)
one = pd.read_csv(f)
u = one[one.end_type == "uncoded"]
inexport = set(ex.Polity.unique())
print("uncoded whose successor has no export rows at all:", (~u.successor.isin(inexport)).sum(), "of", len(u))
print(u[["NGA","PolID","successor","End"]].head(12).to_string())
