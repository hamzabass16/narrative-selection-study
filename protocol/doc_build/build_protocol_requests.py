"""Insert Section 16 (before References) and deviations D24 to D37 (after D23) into the protocol Doc.
Text is inserted before the newline of the preceding normal paragraph, so it inherits normal style; headings and bold labels set after."""
import json, importlib.util
def u16(s): return len(s.encode('utf-16-le')) // 2
def mod(p):
    spec = importlib.util.spec_from_file_location('m', p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
d = json.load(open('/root/analysis/out/protocol_doc_2026-10-23b.json')); body = d['content']['tabs'][0]['documentTab']['body']['content']
def ptxt(el): return ''.join(r.get('textRun', {}).get('content', '') for r in el['paragraph']['elements'])
paras_doc = [el for el in body if 'paragraph' in el]
d23 = next(el for el in paras_doc if ptxt(el).startswith('D23.'))
ref_i = next(i for i, el in enumerate(paras_doc) if ptxt(el).startswith('References'))
prev = paras_doc[ref_i - 1]
assert prev['paragraph']['paragraphStyle']['namedStyleType'] == 'NORMAL_TEXT'
S16 = mod('/root/analysis/out/section16_text.py').S
DV = mod('/root/analysis/out/deviations3_text.py').D
EN_OK = 'Attribution–ShareAlike'
for t in [x[0] for x in S16] + DV:
    assert '—' not in t and '–' not in t.replace(EN_OK, ''), t[:60]
def plan(at, items):
    """items: list of (text, style, bold_label). Insert '\n' + join at index 'at'. Returns chunks and style requests."""
    text = '\n' + '\n'.join(t for t, _, _ in items)
    pos = at + 1; style = []
    for t, st, lab in items:
        L = u16(t) + 1
        if st != 'NORMAL_TEXT':
            style.append({"updateParagraphStyle": {"range": {"startIndex": pos, "endIndex": pos + L}, "paragraphStyle": {"namedStyleType": st}, "fields": "namedStyleType"}})
            style.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + L - 1}, "textStyle": {"bold": True}, "fields": "bold"}})
        elif lab:
            style.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + u16(lab)}, "textStyle": {"bold": True}, "fields": "bold"}})
        pos += L
    # chunk the text at paragraph boundaries (~5000 chars)
    parts = text.split('\n')[1:]; chunks = []; cur = []; n = 0
    for p in parts:
        cur.append(p); n += len(p) + 1
        if n > 5000: chunks.append(cur); cur = []; n = 0
    if cur: chunks.append(cur)
    out = []; ip = at
    for c in chunks:
        t = '\n' + '\n'.join(c); out.append(dict(index=ip, text=t)); ip += u16(t)
    return out, style
def dlabel(t):
    j = t.find('. ', 5)
    return t[:j + 1] if 0 < j < 90 else t[:t.find('.') + 1]
s16_items = [(t, st, lab) for t, st, lab in S16]
s16_chunks, s16_style = plan(prev['endIndex'] - 1, s16_items)
dv_items = [(t, 'NORMAL_TEXT', dlabel(t)) for t in DV]
dv_chunks, dv_style = plan(d23['endIndex'] - 1, dv_items)
assert d23['endIndex'] - 1 < prev['endIndex'] - 1
json.dump(dict(s16_chunks=s16_chunks, s16_style=s16_style, dv_chunks=dv_chunks, dv_style=dv_style), open('/root/analysis/out/protocol_requests.json', 'w'), ensure_ascii=False)
print('S16 chunks', [(c['index'], len(c['text'])) for c in s16_chunks], 'style', len(s16_style))
print('DV chunks', [(c['index'], len(c['text'])) for c in dv_chunks], 'style', len(dv_style))
print([dlabel(t) for t in DV])
