"""Build Google Docs batchUpdate requests to insert styled paragraphs before a given heading."""
import json, sys
def load(path):
    d = json.load(open(path)); c = d['content']
    return c, c['tabs'][0]['documentTab']['body']['content']
def find_para(body, startswith):
    for el in body:
        if 'paragraph' in el:
            txt = ''.join(r.get('textRun', {}).get('content', '') for r in el['paragraph']['elements'])
            if txt.startswith(startswith): return el['startIndex'], el['endIndex'], txt
    raise KeyError(startswith)
def u16(s): return len(s.encode('utf-16-le')) // 2
def build(start, paras):
    """paras: list of (text, style, bold_label_or_None)"""
    text = ''.join(p[0] + '\n' for p in paras)
    reqs = [{"insertText": {"location": {"index": start}, "text": text}}]
    pos = start
    for t, st, lab in paras:
        L = u16(t) + 1
        reqs.append({"updateParagraphStyle": {"range": {"startIndex": pos, "endIndex": pos + L}, "paragraphStyle": {"namedStyleType": st}, "fields": "namedStyleType"}})
        reqs.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + L - 1}, "textStyle": {"bold": st != 'NORMAL_TEXT'}, "fields": "bold"}})
        if lab: reqs.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + u16(lab)}, "textStyle": {"bold": True}, "fields": "bold"}})
        pos += L
    assert '—' not in text and '–' not in text
    return reqs, pos
