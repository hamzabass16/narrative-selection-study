# H6 research synthesis: protocol (fixed 23 October 2026, before any search)

Part of the approved retest plan, 'FROZEN 2026-10-23 Retest Plan (approved)'.

## Question

Does random exposure to a story, scripture or narrative text with cooperative moral content increase cooperation with anonymous others, compared with a neutral or matched text?

## Eligibility

Primary set (stratum P). A study enters P if all four hold:

1. Participants were randomly assigned to conditions, between or within subjects.
2. The treatment is a story, narrative, fable, scripture passage or other narrative text, read, heard or watched. Its content shows or endorses a cooperative behaviour: helping, sharing, generosity, fairness, reciprocity, trust, loyalty, honesty toward others, rescue or self-sacrifice.
3. The control is a neutral text or story, or one matched on form without the cooperative content. A no-text control is also accepted, but flagged.
4. The outcome is incentivized behaviour toward anonymous or unrelated others:
   - amount sent in a trust game;
   - dictator-game giving;
   - public-goods contribution;
   - prisoner's dilemma cooperation;
   - random-allocation game allocation to a distant other;
   - any real-stakes giving to strangers or to charity.

Separate strata. These are analysed separately, never pooled with P:

- N: non-narrative moral messages or appeals. Examples are a stated Golden Rule, a moral reminder, or "do the right thing" framing. The outcome must be as in P.
- R: implicit religious primes. Examples are scrambled-sentence primes and religious words or images shown without a narrative. The outcome must be as in P.
- H: narrative treatments as in P, but the outcome is non-incentivized helping or prosocial behaviour, such as picking up pens, volunteering or helping the experimenter.
- D: narrative treatments as in P, but the outcome is honesty or cheating, such as die rolls or self-reported performance.
- T (for H10): transmission-chain or serial-reproduction experiments that compare how well cooperative, prosocial or moral content is remembered or retold, against other content.

Excluded:

- correlational or survey studies;
- studies of violent or antisocial media unless they have a prosocial-narrative arm;
- studies whose only outcome is an attitude, intention, empathy or theory-of-mind score;
- studies whose only outcome is self-reported willingness, with no behaviour.

## Search (all of it, in this order)

1. WebSearch with each of these query strings, plus up to 3 follow-up queries each:
   - "story" "dictator game" experiment prosocial
   - narrative exposure "trust game" randomized
   - "prosocial story" children sharing experiment
   - "moral story" OR "moral stories" experiment children sharing OR honesty
   - "reading" fiction "dictator game" OR "economic game" experiment
   - scripture OR Bible OR Quran passage experiment "dictator game" OR "public goods"
   - "moral suasion" OR "moral message" "public goods game" experiment
   - narratives prosocial behavior experiment "positive narratives"
   - storytelling cooperation experiment hunter-gatherers OR field
   - "transmission chain" moral OR prosocial OR cooperative content memory
   - "serial reproduction" social information bias experiment
   - elevation video OR story "altruistic behavior" experiment
2. Reference lists, read through WebFetch where open, of these sources:
   - Shariff, Willard, Andersen and Norenzayan (2016), religious priming meta-analysis;
   - Coyne et al. (2018), prosocial media meta-analysis;
   - Dodell-Feder and Tamir (2018), fiction and social cognition meta-analysis (for narrative studies with behavioural outcomes only);
   - Smith, Mabulla and Apicella (2023), Human Nature;
   - Hillenbrand and Verrina (2022), Games and Economic Behavior;
   - Dal Bó and Dal Bó (2014), Journal of Public Economics;
   - any further meta-analysis found in step 1 that covers narrative or prosocial media and behaviour.
3. Forward citations, where a free index shows them (for example Semantic Scholar or Google Scholar result pages reachable by WebFetch), of:
   - Smith et al. 2023;
   - Hillenbrand and Verrina 2022;
   - Dal Bó and Dal Bó 2014;
   - Larsen, Lee and Ganea (2018), storybooks and sharing;
   - Lee et al. (2014), classic moral stories and honesty.
4. OSF Preprints and PsyArXiv searches for "story" OR "narrative" with "dictator", "trust game", "public goods" or "sharing".

Record every query and the number of results screened in search_log.csv.

## Screening

- Each record is screened on title and abstract against the eligibility rules. Full texts are opened for every record that passes and for every uncertain one.
- Record the decision and the reason in candidates.csv, with these columns: id, citation, year, doi_or_url, fulltext_url, stratum (P/N/R/H/D/T or EXCLUDE), reason, accessible (Y/N), preregistered (Y/N/unknown), notes.
- Do not extract effect sizes at this stage.

## Extraction (later, by two independent extractors)

For each comparison of treatment with control, record:

- design, sample size per arm, population (children or adults; country), and treatment and control descriptions;
- whether the narrative is traditional or religious, or modern or invented;
- the target of the outcome (stranger or in-group), the delay before the outcome, and the outcome measure with its scale;
- the reported statistics needed for an effect size: means, SDs and ns; or t, F (df 1) or chi-square; proportions with ns; or a regression coefficient with its SE and the outcome SD;
- the exact quote and the page, table or figure each number comes from;
- whether the study was preregistered.

Extractors do not compute effect sizes. The analysis script computes Hedges' g from the raw statistics.

## Analysis and decision rule (as in the approved plan)

The analysis uses:

- random-effects meta-analysis (REML) of Hedges' g;
- robust variance estimation clustered by study;
- PET-PEESE and a three-parameter selection model;
- a preregistered-only estimate.

The moderators are:

- traditional or religious narrative versus modern;
- children versus adults;
- non-WEIRD samples;
- stranger versus in-group target;
- delay.

Decision rule:

- Supported if the bias-corrected pooled g in P is positive with a 95 percent interval excluding 0, and is positive among preregistered studies.
- Falsified if the bias-corrected 90 percent interval lies inside -0.15 to 0.15.
- Otherwise inconclusive.

The bias-corrected estimate is PET-PEESE. If PET-PEESE and the selection model disagree in sign, the verdict is inconclusive. Strata N, R, H, D and T are reported descriptively with their own pooled estimates.
