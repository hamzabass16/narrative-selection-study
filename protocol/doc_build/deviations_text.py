H = "12. Deviations from protocol\n"
P = [
"Logged 17 October 2026, before any association between narrative content, ruler accountability or moralizing gods and polity outcomes had been computed. The protocol as it stood before these deviations is frozen in Google Drive as 'FROZEN 2026-10-17 Narrative Selection and Societal Endurance: Registered Report Protocol (pre-analysis snapshot)'. Each entry states what changed, why, and what the change does to the strength of inference.",
"D1. No Stage 1 review and no public registration. The protocol has not been peer reviewed or registered. The frozen Drive copy fixes the plan, but it is not a public time-stamped registration that a third party can verify. No result reported here can be described as a Registered Report finding. Remedy open to the author: deposit the frozen copy on OSF Registries; the deposit then precedes any analysis not yet run.",
"D2. Data access before freezing. The header states that the plan was fixed before data access. The feasibility audits in Section 6.10 read Seshat polity dates, Seshat succession codes and CrisisDB, which contain the outcome, as well as the D-PLACE and Seshat distributions cited in Section 1.2. No predictor was linked to any outcome in those audits.",
"D3. Coders. Section 5 requires two trained human coders and admits a language model coder only after it matches human agreement on at least 500 held-out items. No human coders are available. All new coding (termination type and any other item-level judgement) is therefore done by independent instances of a large language model working from the frozen codebook, with a separate instance as adjudicator, and no human validation set exists. Agreement between instances measures the consistency of one model, not human reliability, and errors the instances share are invisible to it. Every analysis that uses these codes is exploratory, and the condition in Section 5.3 is not met in this run.",
"D4. Narrative content measure. A language model cannot be blinded to the narratives of known polities: it recognizes canonical texts and knows how the polities that carried them ended, so model-judged CCI codes would breach the blinding rule in Section 5.2. The CCI is instead scored by a fixed dictionary, the Morality-as-Cooperation Dictionary (MAC-D; Alfano, Cheong and Curry, 2024), applied to public-domain translations of each tradition's canonical texts and linked to polities through the Seshat religion variables. Dictionary scoring involves no coder judgement and is outcome-blind by construction. Its costs: word frequencies measure how salient a moral domain is, not whether it is endorsed; translation choices change the counts; the moral scope weight cannot be scored by dictionary and is dropped; and polities that share a tradition share a score, so the effective number of independent CCI values is the number of traditions, not the number of polities.",
"D5. Study 3 not run. A randomized experiment needs real participants, ethics approval and incentive payments. Simulated participants would be fabricated data. H6 remains untested, and the rows of the interpretation matrix that depend on H6 cannot be evaluated.",
"D6. Later deviations are appended to this list with their dates.",
]
T = H + "\n".join(P) + "\n"
def u16(s): return len(s.encode('utf-16-le'))//2
start = 42235
reqs = [{"insertText": {"location": {"index": start}, "text": T}}]
hend = start + u16(H)
tend = start + u16(T)
reqs.append({"updateParagraphStyle": {"range": {"startIndex": start, "endIndex": hend}, "paragraphStyle": {"namedStyleType": "HEADING_2"}, "fields": "namedStyleType"}})
reqs.append({"updateParagraphStyle": {"range": {"startIndex": hend, "endIndex": tend}, "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"}, "fields": "namedStyleType"}})
reqs.append({"updateTextStyle": {"range": {"startIndex": start, "endIndex": hend-1}, "textStyle": {"bold": True}, "fields": "bold"}})
reqs.append({"updateTextStyle": {"range": {"startIndex": hend, "endIndex": tend}, "textStyle": {"bold": False}, "fields": "bold"}})
# bold the D-labels
pos = hend
for p in P:
    if p.startswith("D") and not p.startswith("D6"):
        lab = p.split(". ")[0] + ". " + p.split(". ")[1] + "."
        reqs.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos+u16(lab)}, "textStyle": {"bold": True}, "fields": "bold"}})
    pos += u16(p) + 1
import json
assert '—' not in T
json.dump(reqs, open('/root/analysis/out/deviations_reqs.json','w'))
print(json.dumps(reqs)[:300]); print(len(reqs), tend)
