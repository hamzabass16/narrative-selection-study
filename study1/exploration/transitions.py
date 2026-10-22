import sys, pandas as pd
d = sys.argv[1]
ex = pd.read_csv(f"{d}/exportdat.csv", low_memory=False)
pol = pd.read_csv(f"{d}/polities.csv")
pol = pol[pol.Dupl=="n"]
rel = ex[ex.Variable=="relationship to preceding (quasi)polity"]
print(rel["Value From"].str.strip().str.lower().value_counts(dropna=False).head(30))
print("polities with a coded relationship:", rel.Polity.nunique(), "of", pol.PolID.nunique())
print(pol.End.describe())
print("ending at/after 1800 CE:", (pol.End>=1800).sum())
