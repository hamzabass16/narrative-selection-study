"""Build Docs batchUpdate requests that put the retest (Part 1) at the top of the report Doc, keeping the first run as Part 2.
Inserted text inherits the intro paragraph's normal style; headings and bullets are set explicitly."""
import json, importlib.util
spec = importlib.util.spec_from_file_location('rt', '/root/analysis/report/report_retest_text.py'); rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
def u16(s): return len(s.encode('utf-16-le')) // 2
d = json.load(open('/root/analysis/report/report_doc_2026-10-23b.json')); body = d['content']['tabs'][0]['documentTab']['body']['content']
intro = body[2]; txt = ''.join(r['textRun']['content'] for r in intro['paragraph']['elements'] if 'textRun' in r)
assert txt.startswith('Exploratory run, 16 to 23 October 2026') and intro['startIndex'] == 67, txt[:60]
S, E = intro['startIndex'], intro['endIndex'] - 1   # keep the paragraph's newline
paras = []
items = rt.R[1:]   # drop the title (the Doc already has it)
for st, tx in items:
    if st == 'HEADING_2': paras.append((tx, 'HEADING_1'))
    elif st == 'HEADING_3': paras.append((tx, 'HEADING_2'))
    elif st == 'BULLET': paras.append((tx, 'BULLET'))
    else: paras.append((tx, 'NORMAL_TEXT'))
paras.append(("Part 2. The first run (16 to 23 October 2026)", 'HEADING_1'))
paras.append(("The sections below are the report of the first run, unchanged. Its content measure (moral word counts in canonical texts) was retired in the retest; where Part 1 and Part 2 differ, Part 1 is current.", 'NORMAL_TEXT'))
ALLOWED_EN = 'Attribution–ShareAlike'
for t, _ in paras:
    assert '—' not in t, t[:80]
    assert '–' not in t.replace(ALLOWED_EN, ''), t[:80]
text = '\n'.join(t for t, _ in paras)
reqs = [{"deleteContentRange": {"range": {"startIndex": S, "endIndex": E}}},
        {"insertText": {"location": {"index": S}, "text": text}}]
pos = S; runs = []; cur = None
for t, st in paras:
    L = u16(t) + 1
    if st in ('HEADING_1', 'HEADING_2'):
        reqs.append({"updateParagraphStyle": {"range": {"startIndex": pos, "endIndex": pos + L}, "paragraphStyle": {"namedStyleType": st}, "fields": "namedStyleType"}})
        reqs.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + L - 1}, "textStyle": {"bold": True}, "fields": "bold"}})
    if st == 'BULLET':
        cur = [pos, pos + L] if cur is None else [cur[0], pos + L]
    elif cur is not None:
        runs.append(cur); cur = None
    pos += L
if cur: runs.append(cur)
for a, b in runs:
    reqs.append({"createParagraphBullets": {"range": {"startIndex": a, "endIndex": b - 1}, "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}})
json.dump(reqs, open('/root/analysis/report/retest_requests.json', 'w'), ensure_ascii=False)
print(len(reqs), 'requests;', len(text), 'chars; bullet runs', runs, '; ends at', pos)
