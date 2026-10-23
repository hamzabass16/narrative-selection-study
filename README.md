# Do the stories a society tells decide how long it survives?

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="report/figures/fig1_violent_end_by_strategy_dark.png">
  <img alt="Share of autocratic regimes that ended violently from within, by how cooperatively they ruled: 63% for the least cooperative quarter, 53%, 46%, and 39% for the most cooperative quarter" src="report/figures/fig1_violent_end_by_strategy_light.png" width="760">
</picture>

Genes cannot carry what a person learns in a lifetime. Language can. A lesson about how to live together can be told as a story and passed down for a thousand years. If stories are how societies inherit what they have learned, the societies whose stories teach cooperation should outlast the rest. And if people everywhere arrived at the same thing, perhaps it was the content of morality, not any one God.

This repository tests those ideas against world history, using:

- 864 polities in the Seshat Global History Databank, from the end of the last Ice Age to the present, 221 of them with coded ideology;
- 2,564 folklore motifs told across 1,265 societies;
- the religions of 775 societies;
- 1,600 autocratic regimes since 1789 and 2,020 national leaders since 1875;
- 5,172 passages from ethnographies of 53 societies written before 1929.

The tests come from a pre-registered research protocol, and each one names in advance what result would count against it.

The short answer so far: neither moral words in scriptures nor historians' codes of inclusive ideology predict how long states last. How rulers actually behave predicts how their regimes and their own careers end.

## The ideas being tested

1. **Stories as a second inheritance.** Biologists call the wall between what a body learns and what its genes pass on the Weismann barrier. Narratives cross it. If the moral content of stories is selected like a trait, then societies whose canonical stories carry more cooperative content (care for kin, loyalty, reciprocity, courage, respect, fairness, property) should endure longer. This should hold even after accounting for the armies, farms and populations that usually decide who survives.
2. **Service outlasts force.** Rulers who govern by serving and by accepting limits should leave sturdier societies than rulers who govern by fear. A simple model in the protocol predicts something more specific. Rule by force need not be shorter, but it should end more often in sudden internal collapse, because it holds only while the fear holds.
3. **Convergence on content, not on God.** If humanity converged on anything, it should be on the behaviours that make cooperation work, which would then be valued everywhere. Belief in a moralizing God, by contrast, should spread like an inherited institution of large states.

## What was found

These are the results of the retest of 23 October 2026, which replaced the first run's word counts with better measures. The first run's results are kept in the reports and summarized at the end of this section.

**Inclusive ideology does not predict how long states last.** Seshat's historians coded, for each polity, whether its ideology treats people as equals and holds elites and rulers to the same norms as commoners. Across 221 polities with 117 endings, comparing each region with its own past, the hazard ratio is 1.03 per standard deviation [0.72, 1.47]. Within the same religion it is 0.94 [0.71, 1.26]. It stays near 1 after controlling for agriculture, military technology, population, territory and social complexity century by century (1.18 [0.77, 1.81]). The same measure does not predict internal collapse, recovery from crises, or later growth in complexity. A strong protective effect is unlikely; a small one cannot be ruled out.

**How rulers behave predicts how regimes and leaders end.** Among autocracies since 1789, those that ruled more cooperatively ended violently from within less often, even when conduct is measured 10 or 20 years before the end (30 against 53 percent at 10 years). Among 2,020 leaders since 1875, those whose first three years were most cooperative left office irregularly 11 percent of the time, against 51 percent for the least cooperative, and ended in exile, prison or death 15 against 54 percent of the time. Two limits: the link disappears when each country is compared only with itself, and premodern constraints on rulers predict nothing.

**The cooperative behaviours are approved almost everywhere, and respect for property stops at the group's edge.** In 53 societies from 42 language families, 844 of 869 stated judgements approve helping kin, group loyalty, returning favours, bravery, respect for superiors, fair division and respect for property. By the rule set in advance (more than 5 percent condemnations), respect for property fails narrowly: 5.2 percent, family-weighted. Six of the eight condemnations concern the property of enemies or of landlords. Own-group property was condemned in 1 of 91 judgements.

**Belief in a moralizing God is inherited along language lineages.** On dated trees of Austronesian, Bantu and Indo-European languages, moralizing gods cluster strongly by ancestry. The trees do not show them following political hierarchy (p = 0.79).

**What folk tales reward does not predict trust; whether they punish the trickster does.** Coding what 2,436 motifs reward and punish gives a score that predicts neither trust across countries nor trust among children of immigrants. The published trickster-punishment measure still does. Stories that reward cooperation are not more widespread or longer-lived than other stories.

**Published experiments on cooperative stories are few and mostly unreadable here.** Of 24 eligible randomized experiments, only 5 could be read and converted, all with children or adolescents and modern stories, none preregistered. Their pooled effect is large (g = 0.74 [0.09, 1.39]) but varies widely, and after correcting for small-study bias it no longer excludes zero. The test the hypothesis actually needs, traditional stories with adults and real stakes, has essentially not been run.

**Rule in the name of religion looks like rule by force** (first run). Autocracies that legitimate themselves through religion grant less religious freedom, kill and torture more, are less constrained by courts, and spend less on public goods.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="report/figures/fig2_religious_legitimation_dark.png">
  <img alt="Autocracies that legitimate themselves through religion: less religious freedom, fewer public goods, weaker courts, more repression, killings and torture" src="report/figures/fig2_religious_legitimation_light.png" width="760">
</picture>

**The first run, in brief.** Moral word counts in 15 canonical traditions did not predict how long 253 states lasted (HR 1.08 [0.90, 1.28]). Believing that rulers answer to God did not protect states, and crises under such rulers more often ended in removals. Conquerors adopted the faith of the conquered only when they brought no codified religion of their own. These results, and why the word-count measure was retired, are in [`report/RESULTS.md`](report/RESULTS.md).

## Why it matters

The boldest claim, that the moral content of a society's stories helps decide how long it survives, has now failed with two different measures: word counts in scriptures, and historians' codes of each polity's ideology. Neither is a reading of the narratives themselves, so the claim is not refuted, but there is no positive evidence for it in the historical record.

The convergence claim holds in its in-group form. People everywhere approve of the behaviours that make cooperation work among their own, and belief in a moralizing God travels with descent, as an inherited institution does.

The leadership claim holds for how rule ends, not how long it lasts. Force does not shorten a regime's life; it changes how the regime and its rulers end. Whether that is cooperation itself or the kind of country that rules cooperatively is the question the next test must answer.

## How much to trust this

These results are exploratory. The protocol has not been peer reviewed. Every analysis plan was fixed before its data were linked to outcomes, every script was frozen with a hash, and every later change is logged (deviations D1 to D37 in the protocol).

The content and conduct measures in the retest were coded by human experts (Seshat, V-Dem, Archigos, the Ethnographic Atlas, the folklore catalogue). Three kinds of judgement were made by independent instances of an AI model (Claude), with no human coders: how each state ended, what folk motifs reward and punish, and how ethnographies evaluate behaviours. On 281 trickster motifs, the AI coder agreed with human MTurk coders as often as the humans agreed with each other. Agreement between AI instances shows the model is consistent, not that it is right. Independent agents re-derived the main numbers of the retest with their own code; all reproduced, and the points of wording they raised are logged (D37).

## Read the full reports

- [`report/RESULTS.md`](report/RESULTS.md): the result for every hypothesis, why it came out that way, and how it could be tested better.
- [`report/PROTOCOL.pdf`](report/PROTOCOL.pdf): the registered-report protocol, with its deviations log and results sections.

## Layout

| Folder | Contents |
|---|---|
| `report/` | Results report (Markdown), protocol (PDF), figures, and the scripts that build them |
| `data/seshat/` | Seshat Global History Databank, public API release downloaded 17 October 2026 |
| `study1/` | State endings: polity frame, coding brief, coder outputs for both passes, adjudication, source audit, survival models, specification curve |
| `cci/` | Public-domain canonical texts, cleaning audit, dictionary scorer and tradition scores |
| `study2/` | Folklore motif scoring and the trust, immigrant and political-scale models |
| `h4b/` | Conquest episodes, coding brief, coder outputs, agreement and analysis |
| `h8/` | Rulers under divine judgement: survival models, crisis models, and the costs of removal and collapse |
| `h8r/` | Ruler conduct (dominance versus cooperation) and religious legitimation, V-Dem v15; retest Parts A to C |
| `h9a/` | Ethnography sample, texts, passage extraction (versions 1 and 2), coding briefs and codes |
| `h9b/` | Phylogenetic signal of moralizing-god belief on the Ethnographic Atlas |
| `retest/` | Retest of Study 1 and H8 Part A: approved plan, Equinox matching, exposures, new termination codes, century-panel analysis, H9b dated trees, H10 |
| `study2_retest/` | Folklore motif endorsement coding (briefs, codes, reliability, human check) and the rerun of Study 2 |
| `h6/` | H6 systematic review: protocol, search log, screened records, extraction briefs, both extractions, verification and meta-analysis |
| `verification/` | Independent re-derivations of the first-run and retest results |
| `protocol/` | Scripts that wrote the protocol's later sections |
| `tools/` | Helpers for moving files through the browser |

## Reproducing

The scripts were run with Python 3.13, numpy, pandas, scipy, statsmodels, scikit-learn, dendropy and pyreadr. They use the absolute paths of the environment they ran in: `/root/analysis/...` for this repository's contents and `/root/data/...` for third-party data. Frozen copies of the analysis scripts must stay byte-identical, so the paths were left unchanged. To rerun, place the folders at those paths or edit the paths at the top of each script.

Third-party data not stored here, and where to get them:

- **Folklore:** Michalopoulos and Xue (2021), *Folklore*, replication archive: https://doi.org/10.7910/DVN/IXOHKB
- **V-Dem v15:** https://github.com/vdeminstitute/vdemdata (`data/vdem.RData`)
- **D-PLACE** (Ethnographic Atlas and Glottolog trees): https://github.com/D-PLACE/dplace-cldf
- **Seshat Equinox 2020 and power transitions:** https://github.com/Seshat-Global-History-Databank/build_polaris_dataset and https://github.com/matildaperuzzo/SeshatDatasetAnalysis
- **Seshat Agri dataset:** https://seshat-db.com (downloads page; free account required). The derived index is in `data/seshat/seshat_agri_index.csv`.
- **Cliopatria:** https://github.com/Seshat-Global-History-Databank/cliopatria
- **Archigos 4.1:** https://www.rochester.edu/college/faculty/hgoemans/data.htm
- **Glottolog CLDF (language endangerment):** https://github.com/glottolog/glottolog-cldf
- **MAC-D dictionaries:** the eMACDscore package, https://github.com/medianeuroscience/eMACDscore. These are the package's copies of the OSF originals (https://osf.io/86qry). The virtue file is 9 bytes smaller than the OSF listing; see deviation D15 in the protocol.

## Licences

- **Code:** MIT.
- **Seshat-derived files** (`data/seshat`, `study1`, `h8`, `retest`, and the premodern part of `h8r`): CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), under the Seshat Databank User Agreement. Changes made: polity matching, derived indices (ideology, executive constraint, agricultural productivity), century sampling and imputation, and new termination codes. No Seshat Private Data were used.

  This research used data from the Seshat Databank (https://seshat-db.com) under the Creative Commons Attribution–ShareAlike 4.0 International License (CC BY-SA 4.0): https://creativecommons.org/licenses/by-sa/4.0/.

  References: Benam, M. et al. (2022). Seshat Data: Equinox Packaged Data (1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.6642229. Turchin, P. et al. (2021). An integrative approach to estimating productivity in past societies using Seshat: Global History Databank. The Holocene 31(6): 1055-1065. https://doi.org/10.1177/0959683621994644
- **V-Dem-derived results** (`h8r`): CC BY-SA 4.0, following V-Dem's licence.
- **Texts in `cci/texts`, `cci/clean` and `h9a/texts`:** public-domain works, all published before 1929. Licence headers were stripped at retrieval, so these are not Project Gutenberg editions.
- **Other coding records, reports and figures:** CC BY 4.0.

## Author

Hamza Bassatné. Data collection, coding and analysis were carried out with the assistance of Claude (Anthropic), following the author's protocol.

Citation: Bassatné, H. (2026). *Narrative Selection and Societal Endurance: exploratory results.* https://github.com/hamzabass16/narrative-selection-study
