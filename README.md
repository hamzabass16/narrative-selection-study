# Do the stories a society tells decide how long it survives?

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="report/figures/fig1_violent_end_by_strategy_dark.png">
  <img alt="Share of autocratic regimes that ended violently from within, by how cooperatively they ruled: 63% for the least cooperative quarter, 53%, 46%, and 39% for the most cooperative quarter" src="report/figures/fig1_violent_end_by_strategy_light.png" width="760">
</picture>

Genes cannot carry what a person learns in a lifetime. Language can. A lesson about how to live together can be told as a story and passed down for a thousand years. If stories are how societies inherit what they have learned, the societies whose stories teach cooperation should outlast the rest. And if people everywhere arrived at the same thing, perhaps it was the content of morality, not any one God.

This repository tests those ideas against world history, using:

- 864 polities in the Seshat Global History Databank, from the end of the last Ice Age to the present;
- 2,564 folklore motifs told across 1,265 societies;
- the religions of 775 societies;
- 1,600 autocratic regimes since 1789.

The tests come from a pre-registered research protocol, and each one names in advance what result would count against it.

The short answer so far: counting moral words in sacred texts does not predict how long states last. How rulers actually behave predicts how their regimes end.

## The ideas being tested

1. **Stories as a second inheritance.** Biologists call the wall between what a body learns and what its genes pass on the Weismann barrier. Narratives cross it. If the moral content of stories is selected like a trait, then societies whose canonical stories carry more cooperative content (care for kin, loyalty, reciprocity, courage, respect, fairness, property) should endure longer. This should hold even after accounting for the armies, farms and populations that usually decide who survives.
2. **Service outlasts force.** Rulers who govern by serving and by accepting limits should leave sturdier societies than rulers who govern by fear. A simple model in the protocol predicts something more specific. Rule by force need not be shorter, but it should end more often in sudden internal collapse, because it holds only while the fear holds.
3. **Convergence on content, not on God.** If humanity converged on anything, it should be the behaviours that make cooperation work, valued everywhere. Belief in a moralizing God should instead spread like an inherited institution of large states.

## What was found

**Moral words in scriptures do not predict how long states last.** The canonical texts of 15 traditions were scored with a published dictionary of cooperative morality (the Bible, the Qur'an, the Rig Veda, the Analects, the Kojiki, the Iliad, and others). The score did not predict how long 253 states lasted: hazard ratio 1.08 per standard deviation [0.90, 1.28]. A strong protective effect is ruled out; a small one is not. The test was weak, though. Only 15 traditions vary, and a word count measures how often morality is mentioned, not whether a story endorses it. The Kojiki scores highest because its genealogies are full of kinship words.

**In folklore, what predicts trust is how a story ends, not which moral words it uses.** Earlier work found that societies whose folk tales punish the trickster are more trusting today, even among the children of immigrants. That result reproduced exactly here. Counting cooperative words in the same tales predicted nothing.

**Belief in a moralizing God spreads like an inherited institution of large states.** Across 775 societies on a global language tree, belief in a moralizing high god clusters by ancestry (D = -0.20, where 1 would be a random scatter). Each extra level of political hierarchy multiplies its odds by 2.4, and prevalence rises from 6 percent in village societies to 61 percent in societies with four levels of hierarchy. This fits the idea that people converged on moral content while the God travelled with states, conquest and conversion.

**Believing that rulers answer to God did not protect states.** Polities whose rulers were believed to be under divine moral judgement suffered no less in their crises. Their crises more often ended with the ruler deposed or killed: 67 versus 22 percent. Those removals came with civil war, not reform; none of 93 removals was followed by new public goods. After an internal collapse, the next state in the same region was less complex than after an ordinary transition; after a conquest it was not.

**What rulers do matters more than what is claimed for them.** Human experts (V-Dem) rated every autocracy since 1789 on dominance (political killings, torture, repression) and on cooperation (respecting the constitution, accepting courts and legislatures, spending on public goods rather than favours). The results:
- **How regimes end:** the most cooperative quarter ended violently from within 39 percent of the time, against 63 percent for the least cooperative quarter (chart above).
- **How long they last:** cooperative regimes did not last longer. That is exactly what the protocol's model predicted.
- **Prosperity and health:** for each standard deviation more cooperative, a country grew 2 percent more over the following decade and gained half a year more of life expectancy over two decades.
- **Not supported:** civil wars and coups were no less frequent.

**Rule in the name of religion looks like rule by force.** Autocracies that legitimate themselves through religion grant less religious freedom to others. They kill and torture more, are less constrained by courts, and spend less on public goods. Nationalist and socialist regimes share parts of this profile; only religious legitimation has all of it.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="report/figures/fig2_religious_legitimation_dark.png">
  <img alt="Autocracies that legitimate themselves through religion: less religious freedom, fewer public goods, weaker courts, more repression, killings and torture" src="report/figures/fig2_religious_legitimation_light.png" width="760">
</picture>

**Conquerors adopt the faith of the conquered only when they bring none to rival it.** The theory predicts that conquerors adopt the stories of the conquered when those stories carry more cooperative content, as the Mongols became Muslims and the Manchus became Confucian emperors. In 61 conquests where the two sides held different traditions, conquerors adopted the conquered tradition fully in 5 and partly in 16. Adoption was, if anything, less likely for high-content traditions (odds ratio 0.60 [0.31, 1.15]). What mattered was what the conquerors brought. Peoples with no codified religion of their own adopted in 11 of 15 conquests; Christian and Muslim conquerors kept their own in 23 of 26.

**Still running:** whether a new sample of old ethnographies, one society per language family, shows the seven cooperative behaviours valued everywhere.

## Why it matters

The boldest claim, that the moral content of stories selects which societies survive, did not show up when content was measured by word counts. That leaves two possibilities: the claim is wrong, or the measure is too blunt. The folklore result points to the second. Readers respond to whether a story rewards the cheat, not to how often it says "brother". The next test has to code what stories endorse.

The leadership claim held up once it was measured by conduct rather than by belief. Force does not shorten a regime's life. It changes how the regime dies: in coups, assassinations and uprisings instead of orderly transitions, with poorer and less healthy societies left behind. And a ruler who claims God's authority is, on the evidence of the last century, more likely to rule by force than to be bound by morality.

## How much to trust this

These results are exploratory. The protocol has not been peer reviewed, and every analysis plan was fixed before its data were examined. Every deviation from plan is logged (D1 to D23 in the protocol).

Three kinds of judgement were made by independent instances of an AI model (Claude), with no human coders:
- how each state ended;
- whether conquerors adopted the conquered tradition;
- how ethnographies evaluate behaviours.

Agreement between those instances shows the model is consistent, not that it is right. The other main sources were coded by human experts: Seshat, V-Dem, the Ethnographic Atlas and the folklore catalogue. A separate verification run re-derived the folklore and crisis numbers from scratch, and the errors it found are corrected and logged.

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
| `h8r/` | Ruler conduct (dominance versus cooperation) and religious legitimation, V-Dem v15 |
| `h9a/` | Ethnography sample, passage extraction, coding brief and codes |
| `h9b/` | Phylogenetic signal of moralizing-god belief on the Ethnographic Atlas |
| `verification/` | Independent re-derivation of the folklore and crisis results |
| `protocol/` | Scripts that wrote the protocol's later sections |
| `tools/` | Helpers for moving files through the browser |

## Reproducing

The scripts were run with Python 3.13, numpy, pandas, scipy, statsmodels, scikit-learn, dendropy and pyreadr. They use the absolute paths of the environment they ran in: `/root/analysis/...` for this repository's contents and `/root/data/...` for third-party data. Frozen copies of the analysis scripts must stay byte-identical, so the paths were left unchanged. To rerun, place the folders at those paths or edit the paths at the top of each script.

Third-party data not stored here, and where to get them:

- **Folklore:** Michalopoulos and Xue (2021), *Folklore*, replication archive: https://doi.org/10.7910/DVN/IXOHKB
- **V-Dem v15:** https://github.com/vdeminstitute/vdemdata (`data/vdem.RData`)
- **D-PLACE** (Ethnographic Atlas and Glottolog trees): https://github.com/D-PLACE/dplace-cldf
- **MAC-D dictionaries:** the eMACDscore package, https://github.com/medianeuroscience/eMACDscore. These are the package's copies of the OSF originals (https://osf.io/86qry). The virtue file is 9 bytes smaller than the OSF listing; see deviation D15 in the protocol.

## Licences

- **Code:** MIT.
- **Seshat-derived files** (`data/seshat`, `study1`, `h8`): CC BY-NC-SA 4.0, as the Seshat licence requires. Non-commercial use only; cite the Seshat Global History Databank (https://seshat-db.com).
- **V-Dem-derived results** (`h8r`): CC BY-SA 4.0, following V-Dem's licence.
- **Texts in `cci/texts` and `cci/clean`:** public-domain translations, all published before 1929. Sources are listed in `cci/texts/manifest.csv`. Licence headers were stripped at retrieval, so these are not Project Gutenberg editions.
- **Other coding records, reports and figures:** CC BY 4.0.

## Author

Hamza Bassatné. Data collection, coding and analysis were carried out with the assistance of Claude (Anthropic), following the author's protocol.

Citation: Bassatné, H. (2026). *Narrative Selection and Societal Endurance: exploratory results.* https://github.com/hamzabass16/narrative-selection-study
