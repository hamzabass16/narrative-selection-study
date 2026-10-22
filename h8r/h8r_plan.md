# H8 revised: dominance versus cooperative ruler strategies, and religious legitimation (plan fixed 23 October 2026, 00:35 Dubai, before any of these models were run)

Why: Hamza's revision of the H8 verification strategy (23 October 2026).
1. Rulers whose supporters claim divine moral sanction often use religion as a tribal tool of power. Seshat's "moralizing enforcement of rulers" therefore measures a claim, not conduct, and is the wrong exposure.
2. The test should compare rulers who use dominance and power strategies with rulers who use moral, cooperative strategies, and look at the long-term effect on their societies. Human data first. If no human test is possible, use the primate evidence.

Data: V-Dem v15 (vdeminstitute/vdemdata on GitHub, 1789 to 2025). It is coded by country experts, not by an AI. These analyses use no AI-coded variables.

Sample: autocratic country-years, the human analogue of rule without electoral accountability.
- From 1900: v2x_regime 0 or 1 (closed or electoral autocracy).
- Before 1900: v2x_polyarchy below 0.5.

Measures. The main V-Dem variables are measurement-model point estimates; each is z-scored within the autocracy sample.
- **Dominance conduct D:** the mean of the reversed z-scores of
  - freedom from political killings (v2clkill),
  - freedom from torture (v2cltort),
  - CSO repression (v2csreprss).
  A higher D means more killing, torture and repression.
- **Cooperative conduct C:** the mean of the z-scores of
  - executive respects the constitution (v2exrescon),
  - judicial constraints on the executive (v2x_jucon),
  - legislative constraints on the executive (v2xlg_legcon),
  - public-goods rather than particularistic spending (v2dlencmps).
  It is computed when at least 3 of the 4 are present.
- **Strategy S:** C minus D, re-standardized. A higher S means a more cooperative strategy. D and C are also reported separately.
- **Religious legitimation RL:** the share of coders who call the regime's legitimating ideology religious (v2exl_legitideolcr_4), times the extent to which ideology is used to legitimate the regime (v2exl_legitideol_osp divided by 4). The result runs from 0 to 1, for 1900 to 2023.

## Part A: is religious legitimation a constraint on rulers or a tool of power?
- **Sample:** autocracy-years, 1900 to 2023.
- **Model:** each outcome (z-scored) on RL, with log GDP per capita, log population, year fixed effects and region fixed effects. Errors are clustered by country. A robustness run replaces region fixed effects with country fixed effects (change within a country).
- **Outcomes:**
  - freedom of religion (v2clrelig);
  - repression of religious organizations (v2csrlgrep, reversed so that higher means more repression);
  - political killings, torture and CSO repression (D components, reversed);
  - executive respects the constitution, judicial and legislative constraints, and public goods (C components);
  - personalist legitimation of the leader (v2exl_legitlead).
- **Comparison:** the same models for nationalist (v2exl_legitideolcr_0) and socialist (v2exl_legitideolcr_1) legitimation, built the same way. This shows whether religion behaves differently from any other legitimating ideology.
- **Predictions:**
  - Tool-of-power reading (Hamza): RL goes with less religious freedom, more repression of other religious organizations, and no more constraint on the executive.
  - Constraint reading: RL goes with more respect for the constitution, more constraints and fewer political killings.

## Part B: do cooperative strategies leave societies better off in the long run?
- **B1, country-year panel.** Autocracy-years from 1789 to 2015, with outcomes measured forward from year t:
  - Y1: change in log GDP per capita from t to t+10 (e_gdppc, available to 2019);
  - Y2: change in log GDP per capita from t to t+20;
  - Y3: change in life expectancy from t to t+20 (e_pelifeex);
  - Y4: civil war onset in years t+1 to t+10, among years with no civil war at t (e_civil_war, 1816 to 2006);
  - Y5: a successful coup in t+1 to t+10 (e_pt_coup, from 1950).
- **B1 model:** each outcome on S_t, with log GDP per capita at t, log population at t, decade fixed effects and region fixed effects. Errors are clustered by country.
  - The growth models also control for growth over the previous 10 years.
  - The life-expectancy model controls for life expectancy at t.
  - Binary outcomes are run as linear probability models. Their coefficients are differences in probability.
- **B1 robustness:**
  - country fixed effects instead of region fixed effects;
  - only years ending in 0, which gives non-overlapping decade panels;
  - D and C entered separately.
- **B2, regime level.** For each autocratic regime (v2regidnr) that has ended (v2regendtype other than 13), S is averaged over the regime's years.
  - Primary outcome: an internal violent end, defined as a military coup (0), another coup (1), assassination (3), loss in civil war (5) or popular uprising (8).
  - Orderly ends: natural death of the leader (4), guided liberalization (9), guided transformation (10) or unguided liberalization (11).
  - External ends: inter-state war loss (6) and foreign intervention (7). They count in neither the violent nor the orderly group, and form a third outcome.
  - Model: logit of internal violent end against orderly end on mean S, with log regime duration, start decade and region fixed effects. Errors are clustered by country.
- **B3, regime duration.** A Cox model of regime duration on mean S, with start decade and region. The protocol (Section 2) predicts that dominance need not shorten regimes on average. The prediction concerns how they end.

## Predictions and decision rule for the revised H8
- **Supported** if, in B1, S predicts higher growth and life expectancy and lower civil war and coup risk, and, in B2, a lower probability of an internal violent end (p below 0.05 in the primary models).
- **Contradicted** if these come out significant in the opposite direction.
- **Inconclusive** otherwise.

## Limits stated in advance
- V-Dem covers 1789 to 2025, so this tests modern and early-modern rulers, not ancient ones.
- Repression and constraint respond to crises. Forward outcomes and controls for past growth reduce reverse causation but do not remove it.
- Strategy is measured at the regime level, not for individual rulers.

## Part C, primates
This part is complementary. The protocol already cites de Waal (1982), Foster et al. (2009) and Sapolsky and Share (2004). Long-term chimpanzee sites with documented alpha styles and tenures, and the macaque experiment that removed group "policers" (Flack et al. 2006), are summarized from the literature as a cross-species check. No new primate data are compiled in this run.
