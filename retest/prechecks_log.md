# Checks run before the retest plan was written (23 October 2026)

No exposure was linked to any outcome. Checks run:

1. Current Seshat API dump (seshat_current_2026-10-17.json):
   - 193 endpoints, of which about 5 percent of values carry a year inside the polity.
   - Polities with at least two dated values: population 87, territory 72, largest settlement 83.
   - Ideology variables (equality, elites or rulers equated with commoners, prosociality) are not in the API or in Polaris 2026.
2. Equinox 2020 (May 2023 release; Seshat-Global-History-Databank/build_polaris_dataset, cloned to /root/data/seshat_polaris):
   - 373 polities, 35 NGAs.
   - Value counts of the Religion and Normative Ideology and Institutional variables (present, absent, unknown).
3. Match of Equinox polity codes to current polities, made through the moralizing-gods polities.csv list (NGA plus dates):
   - 245 polities have at least 2 of 3 EPI items.
   - 238 overlap a current polity by at least 60 percent of the shorter span; 223 of those overlap uniquely.
   - 207 of these already have termination codes.
   - By start date: 56 before 500 BCE, 130 from 500 BCE to 1500 CE, 43 after 1500 CE.
4. First, cruder match (NGA plus start and end within 25 years):
   - 193 polities have at least 2 of 3 EPI items.
   - Share of EPI variance within religious traditions: 0.34 (118 polities with a tradition).
   - 75 polities have no scored tradition.
   - Termination-code type counts were printed for the 209 matched polities, with no link to EPI or any other exposure.
5. CrisisDB: 105 of 169 crises fall in EPI-matched polities.
6. Region-century panel size: about 1,019 NGA-centuries in 33 NGAs, median 21 per NGA (from polities.csv date spans).
7. Frame polity durations: median 190 years, interquartile range 108 to 308.
8. D-PLACE: 29 published dated trees are available in dplace-cldf/cldf/trees.
   - The motif-level MTurk classification files are not in the local copy of the Michalopoulos and Xue archive.

# Independent verification of Study 1 and H8 Part A (verify5, 23 October 2026)
All 38 checked values reproduced with separately written code. Notes from the verifier:
- The no-fixed-effects H1 model (HR 1.18) uses all 34 NGAs (555 polity-centuries); on the main model's 30 NGAs it is 1.31 [1.01, 1.71].
- Durations use the frame's database end_year. The coders' end_year differs for 138 polities, mostly by a few years;
  using it moves the NGA-stratified Cox HR from 1.25 to 1.19. This is the first run's convention, kept unchanged.
- Default IRLS from statsmodels' own start diverges on H1 as well; the analysis starts from Poisson estimates and, since
  D36, also checks Newton.
