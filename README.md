# Narrative Selection and Societal Endurance

Code, coding records and results for an exploratory run of the Registered Report protocol "Narrative Selection and Societal Endurance" (Hamza Bassatne, 2026). The study asks whether the cooperative moral content of a society's narratives predicts how long its polities last (H1 to H7), whether leadership legitimated by service outlasts leadership held by force (H8), and whether humans converged on the content of morality rather than on belief in a particular God (H9).

## Status: exploratory, not confirmatory

The plans in this repository were frozen in Google Drive before the data they use were examined, but the protocol has not been through Stage 1 peer review or registered on OSF. More importantly, every judgement-based code was made by independent instances of one AI language model, with no human coder validating them:

* termination types of 429 Seshat polities (Study 1),
* whether conquerors adopted the tradition of the conquered (H4b),
* how old ethnographies evaluate seven cooperative behaviours (H9a).

Agreement between model instances measures the model's consistency, not human reliability. Treat every estimate here as exploratory. The deviations from the protocol are listed as D1 onward in protocol Section 12.

The narrative-content measure (the Cooperative Content Index, CCI) uses a published dictionary, the Morality-as-Cooperation Dictionary (MAC-D), so it needs no judgement and is blind to outcomes. It measures how often each moral domain is mentioned, not whether a text endorses it.

## Results in one line each

| Hypothesis | Result |
|---|---|
| H1 content predicts endurance | Not supported: HR 1.08 per SD [0.90, 1.28], permutation p 0.51 |
| H2 robust to drivers of power | Not supported: HR 1.08 [0.92, 1.25] |
| H3 content precedes complexity | Not testable with a time-invariant score |
| H4a internal collapse, not conquest | Not supported: sub-HR 1.15 [0.80, 1.66] |
| H4b conquerors adopt high-content traditions | see `report/` |
| H5 content apart from moralizing gods | No content effect to separate |
| H6 experiment | Not run (needs real participants) |
| H7 same effect in every era | Uninterpretable (early era rests on two traditions) |
| H8 service-legitimated rule | Not supported by any available proxy |
| H9a behaviours judged good everywhere | see `report/` |
| H9b moralizing God spreads by descent and scale | Supported: D = -0.20; OR 2.37 per level of hierarchy |
| Study 2 folklore content and trust | Null for trust (pipeline check reproduces the trickster result) |

The full per-hypothesis account, with the reasons each result came out as it did and how each could be tested better, is in the Google Doc "Narrative Selection and Societal Endurance: Results by Hypothesis". Its source text is in `report/report_text.py`.

## Layout

| Folder | Contents |
|---|---|
| `data/seshat/` | Seshat Global History Databank, current public API release, downloaded 17 Oct 2026 (JSON of every table used) |
| `study1/frame/` | Polity frame, coder brief (codebook v0.3), item batches, raw coder outputs for both passes, adjudication, source audit |
| `study1/analysis/` | Covariates, Cox and Fine-Gray library, analysis script (frozen copy and post-freeze diff), results, specification curve, independent verification |
| `cci/` | Corpus specification, retrieval and cleaning briefs, raw and cleaned public-domain texts with removal audit, MAC-D scorer, tradition scores |
| `h4b/` | Conquest episodes, coder brief, batches, coder outputs, agreement, adjudication, analysis |
| `h8/` | Within-region, literate-state and CrisisDB analyses |
| `h9a/` | Sampling rule, candidate list, passages, coder brief, codes, results |
| `h9b/` | Phylogenetic signal (D statistic) and political-scale models on the Ethnographic Atlas |
| `study2/` | Folklore motif scoring and the trust, immigrant and political-scale models |
| `protocol/` | Scripts used to write protocol sections into the Google Doc |
| `report/` | Results report text and the repository sync script |
| `tools/` | Helpers for moving binary files through the browser |

## Reproducing

The scripts were run with Python 3.13, numpy, pandas, scipy, statsmodels, scikit-learn and dendropy. They use the absolute paths of the run environment (`/root/analysis/...` for this repository's contents, `/root/data/...` for third-party data). The frozen copies have to stay byte-identical, so the paths were left as they are. To rerun, put the repository folders at those paths, or edit the paths.

Third-party data not included here (size or licence), with where to get them:

* Michalopoulos and Xue (2021), "Folklore", replication archive: Harvard Dataverse, https://doi.org/10.7910/DVN/IXOHKB, unpacked to `/root/data/mx_folklore/`.
* D-PLACE CLDF data (Ethnographic Atlas, Glottolog trees): https://github.com/D-PLACE/dplace-cldf, cloned to `/root/data/dplace-cldf/`.
* MAC-D dictionaries: the eMACDscore package, https://github.com/medianeuroscience/eMACDscore, cloned to `/root/data/ext/eMACDscore/`. The package's dictionary files are `macdvirtue.dic` and `macdvice.dic`. The vice file is the same size as the OSF original (https://osf.io/86qry). The virtue file (28,332 bytes) is 9 bytes smaller than the OSF copy, and the OSF copy could not be downloaded to find the difference (see deviations).

## Licences

* Code in this repository: MIT, unless a file says otherwise.
* Seshat data: CC BY-NC-SA 4.0 (Seshat: Global History Databank, https://seshat-db.com). Non-commercial use only; cite Turchin et al. and the Seshat databank.
* The texts in `cci/texts` and `cci/clean` are public-domain translations, all published before 1929. Each one's source (Project Gutenberg, Sefaria, sacred-texts.com) is listed in `cci/texts/manifest.csv`. Licence headers and footers were stripped when the texts were retrieved. These files are not Project Gutenberg editions.
* The model-generated codes, briefs and results are released under CC BY 4.0.

## Citation

Bassatne, H. (2026). Narrative Selection and Societal Endurance: exploratory analyses of a Registered Report protocol. GitHub repository hamzabass16/narrative-selection-study.
