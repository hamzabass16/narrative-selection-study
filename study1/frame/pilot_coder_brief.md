You are an independent historical coder in a reliability pilot for a registered-report study. Apply the codebook below to each item in your batch. Work independently and rigorously; another coder is coding the same items separately and the results will be compared.

BLINDING RULES (strict)
1. Do NOT use seshat-db.com, seshatdatabank.info, or any CrisisDB page or dataset. Do not look for any existing dataset's classification of these transitions.
2. Do NOT look up or consider religion, mythology, narrative, ritual or moral-content information about these polities. Code only how the political transition happened.
3. Wikipedia may be used only to find leads; it does not count as a source. Each item needs at least two citable sources, preferably: Cambridge or Oxford histories and handbooks, Encyclopaedia Britannica, Encyclopaedia Iranica, peer-reviewed journal articles, university-press books (Google Books pages are fine), museum or university archaeology pages. Give author/title and a URL for each.

DEFINITIONS
- Core territory: area containing P's capital or principal centre and the NGA (region) given.
- Central authority: the institution exercising supreme political authority over the core (court, council, paramount chiefdom). A change of ruler or dynasty that leaves this apparatus in place is NOT an end of central authority.
- Transition window W: from 25 years before P's end date to 25 years after S's start date.
- Archaeological phase: a unit defined by material culture with no recorded central authority.

Q1. Is this pair a succession?
- S1 Succession: S replaced P as the principal polity controlling the core within W. Go to Q2.
- S2 Concurrent, not a succession: P and S coexisted as independent polities in the region for more than 25 years and neither replaced the other within W. Then Q2 = NA, Q3 = U.
- S3 Relabelled period of one continuous polity (same central authority, no break). Then Q2 = T0.
- S4 Archaeological phase boundary (both P and S are archaeological phases). Q2 may only be T0, T4 or T9.
- S9 Cannot determine. Then Q2 = T9.

Q2. How did P end in this region? Choose one:
- T0 Continuity: P's central authority continued into S (inheritance, dynastic change inside the same state apparatus; for archaeological phases, settlement and material continuity).
- T1a Internal collapse, fragmentation or civil war: central authority lost control of more than half the core for at least 25 years through civil war, provincial breakaway or fragmentation, with no external conquest of the core within W.
- T1b Internal collapse, abandonment or depopulation without documented conquest.
- T1c Internal collapse, revolution: insiders overthrew the state apparatus and replaced it with new institutions.
- T2 Conquest: an external polity or invading group took military control of the core within W (includes a foreign elite establishing itself as rulers, and vassalage imposed after military defeat).
- T3 Absorption: incorporation into a larger polity without decisive military conquest of the core (inheritance union, diplomatic annexation, client state made province).
- T4 Population replacement: archaeological or genetic evidence of substantial population change without documented conquest.
- T5 Secession: S formed when this region broke away from P while P continued elsewhere.
- T6 Voluntary union: negotiated merger.
- T9 Insufficient evidence.
- NA Not a succession (only with S2).
PRIORITY RULE: if the core was militarily conquered within W, code T2 even if an internal crisis came first, and record that crisis under Q4.

Q3. Did P's central authority end within W? Y / N / U. Must be N for T0 and T6; must be Y for T1a, T1b, T1c, T2 and T5. Use U for archaeological phases with no central authority and for NA.
Q4. Internal crisis (civil war, succession war, large revolt, fragmentation, famine-driven unrest) in the 50 years before P's end? Y / N / U.
Q5. Confidence: 3 = two or more independent scholarly sources state the mode of ending explicitly and agree; 2 = one explicit scholarly source, or several consistent without stating it; 1 = inference from indirect evidence, or sources disagree.

Note: the dates given come from a database and may be approximate; judge the historical relationship, and say in your notes if the dates look wrong.

OUTPUT: return ONLY a JSON array (no prose before or after), one object per item, with exactly these keys:
{"item": "P01", "Q1": "S1", "Q2": "T2", "Q3": "Y", "Q4": "N", "Q5": "2", "source1": "Author, Title, Publisher/Year - URL", "source2": "...", "notes": "40 words max: the key evidence for the code, and any date problems"}
