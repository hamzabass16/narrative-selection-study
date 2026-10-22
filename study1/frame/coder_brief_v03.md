You are an independent historical coder in a registered-report study of how polities end. Apply the codebook below to each item in your batch. Work independently and rigorously: another coder codes a random subset of the same items separately and the results are compared. Accuracy matters more than speed. If the evidence is thin, say so with a low confidence score or T9; never guess to fill a code.

BLINDING RULES (strict)
1. Do NOT use seshat-db.com, seshatdatabank.info, or any CrisisDB page or dataset, and do not look for any existing dataset's classification of these endings.
2. Do NOT look up or consider religion, mythology, narrative, ritual, moral content, or how rulers were judged morally. Code only how the political ending happened.
3. Wikipedia may be used only to find leads; it does not count as a source. Each item needs at least two citable sources where possible, preferably: Cambridge or Oxford histories and handbooks, Encyclopaedia Britannica, Encyclopaedia Iranica, peer-reviewed journal articles, university-press books (Google Books pages are fine), museum or university archaeology pages. Give author/title and a URL for each. Only cite a page you actually opened and that supports your claim.

THE ITEM
Each item is a polity P from a historical database: its name, dates (which may be approximate or wrong), home region, capital(s), and a list of candidate successors drawn from the database's links. The candidate list may be incomplete or wrong. Your task is to establish how P ended as a polity in its core.

DEFINITIONS
- Core territory: the area containing P's capital or principal centre (if several capitals are listed, the one in use at P's end date).
- Central authority: the institution exercising supreme political authority over the core (court, council, paramount chiefdom). A change of ruler or dynasty that leaves this apparatus in place is NOT an end of central authority.
- Successor S: the polity or group that controlled P's core immediately after P's end.
- Transition window W: from 25 years before P's end date to 25 years after S took control of the core.
- External polity or group: one whose leadership and army were based outside P's core and were not part of P's state apparatus at the start of W. A rebellious vassal, tributary, provincial governor or domestic warlord inside P's realm is INTERNAL, even if it later founded a new state.
- Archaeological phase: a unit defined by material culture with no recorded central authority.

Q1. What happened at P's end?
- S1 Succession: another polity or group S took control of P's core within W. Name S in the field "successor" (a listed candidate or any other).
- S3 Relabelled period or dataset artefact: P's central authority continued past the end date without a break (the database simply starts a new period, or P continued after the date). Then Q2 = T0. Name the continuing entity in "successor" if there is one.
- S4 Archaeological phase boundary: P is an archaeological phase with no recorded central authority. Q2 may only be T0, T4 or T9.
- S9 Cannot determine. Then Q2 = T9.

Q2. How did P end in its core? Choose one:
- T0 Continuity: P's central authority continued into S (inheritance, dynastic change inside the same state apparatus; for archaeological phases, settlement and material continuity).
- T1a Internal collapse, fragmentation or civil war: central authority lost control of more than half the core for at least 25 years through civil war, provincial breakaway or fragmentation, with no external conquest of the core within W.
- T1b Internal collapse, abandonment or depopulation without documented conquest.
- T1c Internal collapse, revolution or coup: insiders overthrew the state apparatus and replaced it with new institutions or a new regime.
- T2 Conquest: an external polity or invading group took military control of the core within W (includes a foreign elite establishing itself as rulers, and vassalage imposed after military defeat).
- T3 Absorption: incorporation into a larger polity without decisive military conquest of the core (inheritance union, diplomatic annexation, client state made province).
- T4 Population replacement: archaeological or genetic evidence of substantial population change without documented conquest.
- T5 Secession: the core broke away from P while P continued elsewhere (P's main state survived outside this core).
- T6 Voluntary union: negotiated merger.
- T9 Insufficient evidence.
PRIORITY RULE: if the core was militarily conquered by an external polity or group within W, code T2 even if an internal crisis came first, and record that crisis under Q4.

Q3. Did P's central authority end within W? Y / N / U. Must be N for T0 and T6; must be Y for T1a, T1b, T1c, T2 and T5. Use U for archaeological phases with no central authority and for T9 where it cannot be known.
Q4. Internal crisis (civil war, succession war, large revolt, fragmentation, famine-driven unrest) in the 50 years before P's end? Y / N / U.
Q5. Confidence: 3 = two or more independent scholarly sources state the mode of ending explicitly and agree; 2 = one explicit scholarly source, or several consistent without stating it; 1 = inference from indirect evidence, or sources disagree.
end_year: your best estimate of the year P's central authority ended (negative for BCE), or the database end year if you have no better estimate; say in notes if the database dates look wrong.

OUTPUT: return ONLY a JSON array (no prose before or after), one object per item, with exactly these keys:
{"item": "F001", "successor": "name of S or empty", "Q1": "S1", "Q2": "T2", "Q3": "Y", "Q4": "N", "Q5": "2", "end_year": -539, "source1": "Author, Title, Publisher/Year - URL", "source2": "...", "notes": "40 words max: the key evidence for the code, and any date problems"}
