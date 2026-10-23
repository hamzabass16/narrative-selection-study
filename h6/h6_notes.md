# H6 notes (23 October 2026)

1. Round P1: 16 P studies; both extractors could read the same 5 (S001, S009, S045, S053, S089). h6_merge compare:
   4 studies agree on usable effects (S001, S009, S045, S089); S053 gives only a p-value (stat 'other') and is not usable;
   11 inaccessible to both. No disputes. Random 20 percent verification draw: S045.
2. Direction of F-based effects. h6_meta.g_from takes the sign of an F(1) effect from values.sign, defaulting to +1.
   Extractors did not record a sign. Checked from the extractors' own notes, before any pooling:
   - S001: prosocial-cartoon cell means (4.28, 4.38) exceed control (3.23, 2.79), so +1 is correct.
   - S089: intervention group rose (paired t(24) = -2.89, post > pre), control did not change, so +1 is correct.
   - S045: Group x Run interaction unsigned; the verifier was asked to establish the sign from the paper or set it to null
     (a null sign makes g_from return nothing, so the effect would be dropped rather than assumed positive).
3. Measurement caveats to report: S001's F comes from a three-way ANOVA (partial effect, likely inflates d); S045 and S089
   are group x time interactions, so their d is on the change-score scale; S009's sharing outcome is secondary in the paper.
4. Verifier (S045): all numbers correct. Direction of the Group x Run interaction is not stated anywhere readable
   (Fig 4 image could not be opened), so values.sign = null and the effect is dropped by g_from, as pre-set. The authors
   say both groups were stable across runs. Charity payout real or hypothetical: not stated. Preregistration timing unchecked.
   Usable P effects after verification: S001, S009, S089 (3). h6_meta needs 4 for PET-PEESE, so unless the completed search
   adds readable P studies the pre-set decision is 'not estimable'.
5. Search completed (Steps 2 to 4, 23 October): 1,047 results screened, 55 new records (S094 to S148): P 8, N 14, R 1,
   D 8, EXCLUDE 24. Two P records gained an open text (S045, S052). The search agent flagged two decisions for review
   without changing them: S081 (Rathje et al., live theatre) may be quasi-experimental without cooperative content, and
   S144 (Shreedhar et al., climate-fiction video with real donations) was excluded because pro-environmental action is not
   on the protocol's list of cooperative behaviours. Both decisions stand as screened; they are reported, not changed.
6. Round P2 (written before any P2 extraction was read): 12 studies (the 8 new P records, S052 now open, and S050, S054,
   S064 with newly located copies). Extractors were also asked to record the sign of interaction F statistics.
   Verification for P2: h6_merge.py compare is rerun on all files; its 20 percent draw then covers P1 and P2 together, but
   S045 has already been verified. Rule fixed now: the P2 verification sample is 20 percent (rounded, at least 1) of the
   P2 studies that agree, drawn with random.Random(20261024), and verified.json gains their records.
