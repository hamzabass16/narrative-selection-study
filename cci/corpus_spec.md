# CCI corpus and scoring specification (fixed 17 October 2026, before any text was scored)

Purpose: an outcome-blind Cooperative Content Index (CCI) for each narrative tradition, scored by a fixed dictionary, with no coder judgement (Deviation D4).

## 1. Tradition assignment (polity level)
- Primary: the traditions of the polity's most prevalent widespread religion (Seshat rt/widespread-religions, order 1), mapped by tradition_map.py; if none maps, the traditions of its official religion (rt/official-religions).
- Sensitivity A: official religion only. Sensitivity B: widespread order 1 only.
- A polity assigned several traditions receives the mean of their CCI values.

## 2. Corpus rule
One corpus per tradition: the text or collection the tradition treats as its primary scripture or, for traditions without a scripture, its principal sacred narrative texts, in a complete public-domain English translation published before 1929. Fixed list:

| Tradition | Texts | Translation |
|---|---|---|
| Christianity | Bible, Old and New Testaments (no Apocrypha) | King James Version (1611) |
| Judaism | Tanakh (Hebrew Bible) | Jewish Publication Society (1917) |
| Islam | Qur'an | J. M. Rodwell (1861); if unavailable, E. H. Palmer (1880) |
| Hinduism | Rig Veda; Bhagavad Gita | R. T. H. Griffith (1896); K. T. Telang (1882), else E. Arnold (1885) |
| Buddhism | Dhammapada; Sutta Nipata | F. Max Muller (1881); V. Fausboll (1881) (Sacred Books of the East vol. 10) |
| Jainism | Akaranga, Kalpa, Uttaradhyayana and Sutrakritanga Sutras | H. Jacobi (1884, 1895; SBE vols 22 and 45) |
| Zoroastrianism | Avesta (Vendidad, Yasna, Visperad, Yashts, Khorda Avesta) | J. Darmesteter and L. H. Mills (SBE vols 4, 23, 31) |
| Confucianism | Analects; Mencius; Great Learning; Doctrine of the Mean | J. Legge (1861 onward) |
| Daoism | Tao Te Ching; Zhuangzi | J. Legge (1891; SBE vols 39 and 40) |
| Shinto | Kojiki | B. H. Chamberlain (1882) |
| Egyptian | Book of the Dead (Papyrus of Ani) | E. A. W. Budge (1895) |
| Mesopotamian | Epic of Gilgamesh; Enuma Elish | R. C. Thompson (1928) or W. Muss-Arnolt (1901), else M. Jastrow and A. T. Clay (1920); L. W. King (1902) |
| Greek | Iliad; Odyssey; Hesiod's Theogony and Works and Days | S. Butler (1898, 1900); H. G. Evelyn-White (1914) |
| Roman | Aeneid | J. W. Mackail (1885), else T. C. Williams (1910) |
| Norse-Germanic | Poetic Edda | H. A. Bellows (1923) |

Front matter, translators' prefaces, introductions, footnotes, commentary, indexes and Project Gutenberg licence text are removed; only the translated text is scored. Where a removal rule cannot be applied cleanly, the whole file is scored and the fact is logged.

## 3. Scoring
- Dictionary: MAC-D virtue and vice sub-dictionaries (macdvirtue.dic, macdvice.dic, 7 domains each) from github.com/medianeuroscience/eMACDscore, unmodified.
- Tokens: lowercase, letters and apostrophes only. Multi-word entries are matched first (longest match), and each token counts at most once.
- Archaic inflection: a token not in the dictionary that ends in -eth or -est is retried as its stem, stem + e, and stem + s, in that order (loveth to love, keepeth to keep). The pronouns thee, thou, thy, thine and ye are counted as tokens but are not dictionary terms.
- Domain rate: virtue hits per 10,000 tokens, per domain. Vice rates are computed the same way and reported.
- CCI: mean across the seven domains of the z-scored virtue rates, with z computed across the 15 traditions. Secondary index: the same with virtue minus vice rates.
- No weighting for moral scope (dropped; Deviation D4).

## 4. Inference
CCI is constant within a tradition, so the effective sample for H1 is the number of traditions. Primary inference for the CCI hazard ratio is a tradition-level permutation test: CCI values are permuted across traditions (all permutations if feasible, else 10,000 random), the Cox model is refitted, and the two-sided p-value is the share of permuted |log HR| at least as large as the observed. Model-based confidence intervals use standard errors clustered on tradition and are reported as descriptive.
