import sys, pandas as pd, numpy as np
from scipy.stats import norm
cldf = sys.argv[1]
za, zb90, zb80 = norm.ppf(0.975), norm.ppf(0.90), norm.ppf(0.80)
R2 = 0.5
def events_needed(hr, zb): return (za+zb)**2 / (np.log(hr)**2 * (1-R2))
def mdhr(D, zb): return float(np.exp(-(za+zb)/np.sqrt(D*(1-R2))))
print("Check protocol table (power 0.90):", {hr: round(events_needed(hr, zb90), 1) for hr in (0.70, 0.75, 0.80)})
for D in (48, 64, 81):
    print(f"D={D}: minimum detectable HR per SD  power0.90={mdhr(D,zb90):.2f}  power0.80={mdhr(D,zb80):.2f}")
soc = pd.read_csv(f"{cldf}/societies.csv"); par = pd.read_csv(f"{cldf}/parameters.csv")
vals = pd.read_csv(f"{cldf}/data.csv", low_memory=False)
print("\nD-PLACE datasets:", soc.columns[:8].tolist())
print("Total societies in D-PLACE:", len(soc))
for pid in ["EA034", "EA043", "EA008", "EA033"]:
    p = par[par.ID == pid]
    n = vals[vals.Parameter_ID == pid].Society_ID.nunique()
    print(pid, "|", p.Name.values[0] if len(p) else "?", "| societies coded:", n)
