# H8 follow-up: is internal breakdown costly to the society? (plan fixed 23 October 2026, before these outcomes were computed)

Why: the first H8 run found that crises in polities whose rulers were held under divine moral sanction ended more often with the ruler deposed or assassinated. The report suggested this might be accountability working. That suggestion was an interpretation, not a test. Hamza's objection: a sudden internal breakdown is not the same as a society where it does not happen, and it plausibly signals something wrong and costly in the long run. These tests ask whether ruler removal and internal collapse are followed by worse outcomes, and whether moral sanction of rulers changes that.

Already known before this plan: the H8 results in Sections 13 and 15. Not yet computed: everything below.

Data: Seshat current release (17 October 2026): CrisisDB crisis consequences (169 crises, 153 polities), polity covariates, home Natural Geographic Area (NGA), and the Study 1 termination codes (AI-coded, exploratory).

Definitions:
- **Removed:** the CrisisDB variables depose or assassination are present (P or IP). They count as absent if coded A or IA. Any other code is missing.
- **Complexity (SC_mean):** for each polity, the mean of the z-scores of the nine Seshat complexity measures. A polity needs at least five of the nine to be scored. It is not imputed, so polities outside the Study 1 frame can be scored as well.
- **Successor in the region:** the polity in the same home NGA whose start year is closest to the predecessor's end year, within 50 years before to 300 years after it.
- **Gap:** the successor's start year minus the predecessor's end year.
- **Recovery time:** years from a polity's end until the first polity in the same NGA whose SC_mean is at least the predecessor's. If none appears, the case is censored at the last polity end recorded in that NGA.
- **Ending type** (Study 1 codes):
  - internal collapse: T1a, T1b, T1c;
  - conquest: T2;
  - continuity: T0. Continuity is the benchmark: the same society carries on without a break;
  - other: T3 to T6;
  - T9 (insufficient evidence) and polities still existing today are excluded.

Tests:
- **A. What comes with removal.** In the 169 crises, the odds that each other consequence is present when the ruler was removed. The consequences are: decline, collapse, extermination, civil war, fragmentation, conquest, epidemic, downward mobility, a crisis lasting a century or more, loss of the capital, constitutional change, and new public goods.
  - Model: logistic regression with era, errors clustered by polity.
  - Run three times: for removal, for deposition alone, and for assassination alone.
  - Holm correction within each set of 12.
  - Under the accountability reading, removal goes with constitutional change and public goods. Under the breakdown reading, it goes with civil war, decline and fragmentation.
- **B. What happens to the polity after the crisis.** Time from the crisis end (year_to) to the polity's end, where the event is a non-continuous ending (internal collapse, conquest or other).
  - Continuity endings are censored, and so are polities still existing.
  - Model: Cox with removed, era and log population; errors clustered by polity.
  - Binary versions: a non-continuous end within 100 years, and an internal collapse within 100 years.
  - Sensitivity: add civil war and extermination, to see whether removal predicts a later fate beyond the violence of the crisis itself.
- **C. Does crisis follow crisis.** Whether another CrisisDB crisis starts in the same NGA within 100 years after the crisis ends.
  - Model: logit with removed and era, errors clustered by NGA.
- **D. Cost of internal collapse to the society.** For coded endings with a successor in the region, compare internal collapse with continuity, and conquest with continuity, on five outcomes:
  - change in SC_mean;
  - change in log population;
  - change in log territory;
  - gap;
  - recovery time.
  - Models: OLS with era, errors clustered by NGA, and again with NGA fixed effects. Recovery time uses a Cox model.
  - The breakdown reading predicts that internal collapse is followed by larger losses and slower recovery than continuity.
- **E. Does moral sanction of rulers change the cost?** Add the interaction MERb x removed in B, and MERb x internal collapse in D.
  - The accountability reading predicts that removal and collapse cost less where rulers were under moral sanction.
  - The breakdown reading predicts no such cushion.

Limits stated in advance:
- CrisisDB records crises only for polities that have been studied. Polities with no recorded crisis are not crisis-free, so the comparisons are between crises (A to C) and between kinds of endings (D).
- Complexity is a polity-lifetime average, so it misses change within a polity.
- The termination codes are AI-made.
- All results are exploratory.
