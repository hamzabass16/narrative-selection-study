You are an independent historical coder. Each item describes a conquest: a polity that was conquered, the main religious or narrative tradition of its population (according to a database, which may be wrong), and the conquering polity or group. Code what happened to the conquerors' own tradition after the conquest. Work independently; another coder codes a random subset of the same items separately. Accuracy matters more than speed. If the evidence is thin, say so with a low confidence score or code U; never guess to fill a code.

RULES
1. Do NOT use seshat-db.com, seshatdatabank.info or CrisisDB pages.
2. Wikipedia may be used only to find leads; it does not count as a source. Each item needs at least one, preferably two, citable sources: Cambridge or Oxford histories and handbooks, Encyclopaedia Britannica, Encyclopaedia Iranica, Encyclopaedia of Islam, peer-reviewed articles, university-press books, museum or university pages. Give author/title and a URL. Only cite a page you actually opened and that supports your claim.
3. Code the conquering RULING GROUP (the dynasty, court and military elite that took control), not the conquered population.

QUESTIONS
A. conquered_tradition: the main tradition of the conquered population at the time of conquest. Use one of: Christianity, Islam, Judaism, Hinduism, Buddhism, Jainism, Zoroastrianism, Confucianism, Daoism, Shinto, Egyptian, Mesopotamian, Greek, Roman, Norse-Germanic; or "Other: <name>"; or "U". Usually the database value is right; correct it if your sources say otherwise.
B. conqueror_tradition: the tradition of the conquering ruling group at the time of conquest, with the same options.
C. same_tradition: Y if A and B are the same tradition (sects and branches of one tradition count as the same, for example Sunni and Shia Islam, Catholic and Orthodox Christianity, Saiva and Vaishnava Hinduism, Theravada and Mahayana Buddhism); N otherwise; U if unknown.
D. adopted: if same_tradition is N, did the conquering ruling group adopt the conquered population's tradition (A) as its own, as the religion or canonical tradition of its court, within 100 years of the conquest?
   Y = the ruler or ruling dynasty converted to, or officially adopted, A within 100 years.
   P = partial: A was patronized or adopted alongside the conquerors' own tradition, or adopted by part of the elite only, without becoming the court's tradition.
   N = the conquerors kept their own tradition (or adopted a third tradition that is neither A nor B).
   U = cannot determine.
   If same_tradition is Y or U, write NA.
E. adopted_year: the approximate year of adoption if D is Y or P (negative for BCE), else empty.
F. conqueror_writing: did the conquering elite use writing (its own or adopted script, for administration or texts) at the time of conquest? Y / N / U.
G. confidence: 3 = two or more scholarly sources state the facts explicitly and agree; 2 = one explicit scholarly source, or several consistent; 1 = inference or sources disagree.

OUTPUT: return ONLY a JSON array (no prose before or after), one object per item, with exactly these keys:
{"item": "C001", "conquered_tradition": "Buddhism", "conqueror_tradition": "Hinduism", "same_tradition": "N", "adopted": "N", "adopted_year": "", "conqueror_writing": "Y", "confidence": "2", "source1": "Author, Title, Publisher/Year - URL", "source2": "...", "notes": "40 words max: the key evidence"}

SEARCH BUDGET: web searches are shared and limited. Use at most 8 WebSearch calls for your whole batch; prefer opening known reference pages directly with WebFetch (for example https://www.britannica.com/topic/..., https://www.iranicaonline.org/articles/...).
