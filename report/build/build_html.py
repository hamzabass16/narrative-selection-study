"""Render report_text.R to HTML for upload to Drive as a Google Doc."""
import html, importlib.util, sys
spec = importlib.util.spec_from_file_location('rt', '/root/analysis/report/report_text.py'); rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
out = ['<html><head><meta charset="utf-8"></head><body>']
inlist = False
for st, tx in rt.R:
    assert '—' not in tx and '–' not in tx, tx[:80]
    for ph in ['RESULT_H4B_SUMMARY', 'RESULT_H9A_SUMMARY', 'H4B_TEXT', 'H9A_TEXT', 'REMOVE_DUP']:
        if ph in tx and '--draft' not in sys.argv: raise SystemExit(f'placeholder left: {ph}')
    if st == 'BULLET':
        if not inlist: out.append('<ul>'); inlist = True
        out.append(f'<li>{html.escape(tx)}</li>'); continue
    if inlist: out.append('</ul>'); inlist = False
    tag = {'TITLE': 'h1', 'HEADING_2': 'h2', 'HEADING_3': 'h3', 'NORMAL_TEXT': 'p'}[st]
    out.append(f'<{tag}>{html.escape(tx)}</{tag}>')
if inlist: out.append('</ul>')
out.append('</body></html>')
open('/root/analysis/report/report.html', 'w').write('\n'.join(out))
print('ok', sum(len(t) for _, t in rt.R), 'chars')
