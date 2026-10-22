"""Copy the study files into the GitHub repo working tree. Large third-party archives are not copied (see README)."""
import shutil, os, sys
from pathlib import Path

A = Path('/root/analysis'); D = Path('/root/data'); R = Path('/home/claude/narrative-selection-study')
SKIP_DIRS = {'__pycache__', '.git'}
SKIP_EXT = {'.pyc', '.zip'}

def cp(src, dst):
    src, dst = Path(src), R / dst
    if src.is_dir():
        for p in src.rglob('*'):
            if any(part in SKIP_DIRS for part in p.parts) or p.suffix in SKIP_EXT or p.is_dir():
                continue
            t = dst / p.relative_to(src)
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, t)
    elif src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    else:
        print('MISSING', src, file=sys.stderr)

# Data
cp(A/'seshat/seshat_current_2026-10-17.json', 'data/seshat/seshat_current_2026-10-17.json')
# Study 1: frame, termination coding, analysis
cp(A/'frame', 'study1/frame')
cp(A/'study1', 'study1/analysis')
cp(A/'out/study1_termination_codes_full.csv', 'study1/study1_termination_codes_full.csv')
cp(A/'out/polity_terminations.csv', 'study1/polity_terminations.csv')
cp(A/'out/polity_terminations_audit.csv', 'study1/polity_terminations_audit.csv')
cp(A/'out/coder_brief.md', 'study1/frame/pilot_coder_brief.md')
cp(A/'out/llm_pilot_coding.csv', 'study1/pilot/llm_pilot_coding.csv')
cp(A/'out/pilot_key.csv', 'study1/pilot/pilot_key.csv')
cp(A/'out/pilot_coder_sheet.csv', 'study1/pilot/pilot_coder_sheet.csv')
for f in ['feasibility.py', 'transitions.py', 'explore.py', 'check_uncoded.py', 'power_and_dplace.py', 'dplace.py']:
    cp(A/f, f'study1/exploration/{f}')
cp(A/'out/feasibility.py', 'study1/exploration/feasibility_out.py')
# Narrative content index
cp(A/'cci', 'cci')
# Hypothesis-specific analyses
cp(A/'h4b', 'h4b')
cp(A/'h8', 'h8')
cp(A/'h9', 'h9b')
cp(A/'h9a', 'h9a')
cp(A/'study2', 'study2')
# Protocol text helpers and report
for f in ['docs_helper.py', 'addendum_text.py', 'results_text.py', 'deviations_text.py']:
    cp(A/'out'/f, f'protocol/doc_build/{f}')
cp(A/'report', 'report')
for f in ['unpack_b64.py', 'unpack_parts.py']:
    cp(A/f, f'tools/{f}')
print('synced')
