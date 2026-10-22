"""ESS robustness grid: controls (cont0 vs cont1) x singleton handling. Imports my own ess_models.py."""
import json, sys
import pandas as pd
import ess_models as E

share = sys.argv[1] if len(sys.argv) > 1 else "w"
s = E.build_sample()
cci = pd.read_csv(E.OUT + f"cci_country_{share}_alpha_apos.csv").set_index("cntry")
s = s.merge(cci[["CCI", "CCI_net"]], left_on="cntry", right_index=True, how="left")
keep_singletons = lambda d, fe: d
grid = {}
for sing_name, fn in [("drop_singletons", E.drop_singletons), ("keep_singletons", keep_singletons)]:
    E.drop_singletons_impl = fn
    orig = E.drop_singletons
    E.drop_singletons = fn
    for spec, controls, cats in [("cont1", ["lnyear_firstpub", "lnnmbr_title", "gender"], ["rel", "health", "age10"]),
                                 ("cont0", ["lnyear_firstpub", "lnnmbr_title"], [])]:
        for x in ["CCI", "CCI_net", "tricksters_punish"]:
            r = E.reghdfe(s, "lntrust_ess", x, controls, cats, "cntry_round", "cntry")
            grid[f"{sing_name}|{spec}|{x}"] = r
            print(f"{sing_name:16s} {spec} {x:18s} b={r['b']:.4f} p={r['p']:.4f} std={r['std_beta']:.4f} "
                  f"CI90=[{r['std_ci90'][0]:.3f},{r['std_ci90'][1]:.3f}] n={r['n']} G={r['n_origin']}")
    E.drop_singletons = orig
json.dump(grid, open(E.OUT + f"ess_variants_{share}.json", "w"), indent=1)
