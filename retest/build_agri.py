"""Agricultural productivity index by NGA and century from the Seshat Agri dataset (agri_dataset.07.2020.csv, downloaded
23 October 2026 from seshat-db.com by the author's account; CC BY-SA 4.0). Built before any model using it was run.
Turchin et al. (2021) derive Agri from crop base yields times cropping-system, fertilizer and irrigation coefficients; the
crop base-yield table is not in the download, so this index uses the technique part only:
  Agri = cropping-system coefficient x fertilizer coefficient x irrigation coefficient (linear, like Turchin's t/ha scale;
  0 where the cropping coefficient is 0, i.e. no agriculture)
for the coefficients in force at the century midpoint. A coefficient without a value at that date takes the nearest
dated value in the same NGA; if the NGA never records it, it is 1 (neutral). Because every model using Agri has NGA fixed
effects, the missing base yield (fixed within NGA unless the staple crop changed) is absorbed; staple-crop changes are not.
Output: /root/data/ext2/seshat_agri.csv with columns nga, year (century midpoint), Agri."""
import numpy as np, pandas as pd
a = pd.read_csv('/root/data/ext2/seshat_agri_raw/agri_dataset.07.2020.csv')
a['Variable'] = a.Variable.str.strip()
co = a[a.Variable.isin(['Cropping System Coefficient', 'Fertilizer Coefficient', 'Irrigation Coefficient'])].copy()
co['v'] = pd.to_numeric(co['Value From'], errors='coerce')
co['d0'] = pd.to_numeric(co['Date From'], errors='coerce'); co['d1'] = pd.to_numeric(co['Date To'], errors='coerce').fillna(co.d0)
co = co.dropna(subset=['v', 'd0'])
rows = []
for nga, g in co.groupby('NGA'):
    for t in np.arange(-9950, 2050, 100):
        prod = 1.0
        for var in ['Cropping System Coefficient', 'Fertilizer Coefficient', 'Irrigation Coefficient']:
            h = g[g.Variable == var]
            if h.empty: continue
            cov = h[(h.d0 <= t) & (h.d1 >= t)]
            if len(cov): val = cov.v.mean()
            else:
                dist = np.minimum((h.d0 - t).abs(), (h.d1 - t).abs()); val = h.v.values[np.argmin(dist.values)]
            prod *= val
        rows.append(dict(nga=nga, year=t, Agri=float(prod)))
out = pd.DataFrame(rows); out.to_csv('/root/data/ext2/seshat_agri.csv', index=False)
print(out.nga.nunique(), len(out)); print(out.groupby('nga').Agri.agg(['min', 'max', 'nunique']).head(10))
