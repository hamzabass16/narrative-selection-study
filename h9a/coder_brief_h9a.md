You are an independent coder of ethnographic passages. Each item is one paragraph from an old ethnography (published before 1929) about a named society, together with a behaviour type. For each item, decide whether the paragraph describes members of that society performing, expecting or evaluating that type of behaviour, and if so how the society regards it. Code only what the paragraph says. Do not use outside knowledge of the society, and do not infer an evaluation the text does not express. Another coder codes a random subset separately.

BEHAVIOUR TYPES (the "domain" field)
- Family: helping, protecting or providing for kin (parents, children, siblings, relatives, clan kin).
- Group: loyalty to one's own group (village, clan, tribe, comrades), unity, solidarity, conformity to the group.
- Reciprocity: returning favours or gifts, repaying debts, keeping exchanges balanced, keeping promises in an exchange.
- Heroism: bravery, courage, valour, fortitude in danger or contest.
- Deference: respect for or obedience to elders, chiefs, superiors or authorities.
- Fairness: dividing a disputed or shared resource fairly, equal shares, impartial settlement of a dispute.
- Property: respecting others' property or possession, not stealing, recognising prior possession or ownership.

QUESTIONS
Q1 relevant: Y if the paragraph describes members of the society performing, expecting, requiring, praising or condemning a behaviour of the given type; N otherwise (for example if the matching words are used in another sense, or the passage is about the ethnographer, about another society, or about the behaviour type only in passing with nothing about the society's practice).
Q2 valence (only if Q1 = Y): how the society regards the behaviour described:
   POS = approved, praised, expected as a duty, rewarded, or its violation is condemned or punished (for example "a man who fails to help his brother is despised" is POS for helping kin);
   NEG = the behaviour itself is disapproved, condemned, ridiculed or punished by the society (for example "it is shameful to share food with one's in-laws" is NEG for sharing with kin; "obedience to the chief is thought contemptible" is NEG for deference);
   NONE = the paragraph describes the behaviour without any indication of how the society evaluates it.
   Be strict: POS or NEG requires evaluative evidence in the paragraph itself (words of approval, duty, praise, shame, blame, punishment, reward, obligation). The ethnographer's own opinion is not the society's evaluation; code the society's view.
Q3 behaviour: up to 12 words naming the specific behaviour (for example "sons support aged parents").
Q4 quote: the shortest exact quotation (at most 25 words) from the paragraph that shows the evaluation; empty if Q2 is NONE or Q1 is N.

OUTPUT: return ONLY a JSON array (no prose before or after), one object per item, with exactly these keys:
{"pid": "V0001", "relevant": "Y", "valence": "POS", "behaviour": "...", "quote": "..."}
For Q1 = N use "valence": "NA", "behaviour": "", "quote": "".
