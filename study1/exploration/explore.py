import sys, pandas as pd
d = sys.argv[1]
ex = pd.read_csv(f"{d}/exportdat.csv", low_memory=False)
pol = pd.read_csv(f"{d}/polities.csv")
print("export rows", len(ex), "polities", len(pol), "NGAs", pol.NGA.nunique())
print(pol.Dupl.value_counts())
v = ex.Variable.value_counts()
for key in ["preced", "succeed", "Relationship", "centraliz", "Supra", "Moralizing", "moraliz"]:
    print("--", key); print(v[v.index.str.contains(key, case=False)].head(15))
