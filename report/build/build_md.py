"""Render report_text.R to Markdown (report/RESULTS.md in the repo). Placeholders for analyses still running become a pending note."""
import importlib.util, re
spec = importlib.util.spec_from_file_location('rt', '/root/analysis/report/report_text.py'); rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
PENDING = {
    'RESULT_H4B_SUMMARY': 'coding finished for 107 of 117 conquest episodes; the analysis runs when the last batch is coded.',
    'RESULT_H9A_SUMMARY': 'in progress: the sample of public-domain ethnographies is being compiled, then passages are coded.',
    'H4B_TEXT': '*In progress.* Independent AI coders have coded whether the conquering elite adopted the conquered population\'s tradition within 100 years for 107 of 117 conquest episodes; agreement on the double-coded fifth so far is 18 of 19 (alpha 0.92). The pre-specified analysis (Section 14.2 of the protocol, `h4b/h4b_analysis.py`) runs when the last batch is coded.',
    'H9A_TEXT': '*In progress.* A new sample of about 30 societies, one per language family and none from earlier studies, is being drawn from public-domain ethnographies published before 1929. Passages mentioning each of the seven behaviours will be coded for whether the society approves or condemns them (Section 14.3 of the protocol, `h9a/`).',
}
def pic(name, alt):
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="figures/{name}_dark.png">\n'
            f'  <img alt="{alt}" src="figures/{name}_light.png" width="760">\n</picture>\n')
FIG_AFTER = {
    'Is divine legitimation a constraint on rulers or a tool of power?': None,
}
out = []; inlist = False
for st, tx in rt.R:
    for k, v in PENDING.items(): tx = tx.replace(k, v)
    assert '—' not in tx and '–' not in tx
    if st == 'BULLET':
        out.append(f'- {tx}'); inlist = True; continue
    if inlist: out.append(''); inlist = False
    if st == 'TITLE': out.append(f'# {tx}\n')
    elif st == 'HEADING_2': out.append(f'## {tx}\n')
    elif st == 'HEADING_3':
        out.append(f'### {tx}\n')
    else:
        out.append(tx + '\n')
        if tx.startswith('Comparison with other ideologies'):
            out.append(pic('fig2_religious_legitimation', 'Effects of religious legitimation on repression, constraints and public goods in autocracies') + '\n')
        if tx.startswith('Verdict on the revised H8'):
            out.append(pic('fig1_violent_end_by_strategy', 'Share of autocratic regimes ending violently from within, by quarter of cooperative strategy') + '\n')
md = '\n'.join(out)
open('/root/analysis/report/export/RESULTS.md', 'w').write(md)
print(len(md), md.count('<picture>'))
