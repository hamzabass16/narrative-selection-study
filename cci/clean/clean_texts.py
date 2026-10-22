#!/usr/bin/env python3
"""
clean_texts.py - re-runnable, auditable cleaning of the 28 corpus texts.

Reads   /root/analysis/cci/texts/<file>      (never modified)
Writes  /root/analysis/cci/clean/<file>      (same file names)
        /root/analysis/cci/clean/cleaning_log.csv
        /root/analysis/cci/clean/audit/<file>.removed.txt   (what was deleted, for audit)

Rules from cleaning_brief.md, applied in this order:
  R1 site artefacts      page markers ("p. 12", "{p. 12}", Kojiki "[82]"), "[paragraph continues]",
                         scan / public-domain / site notices
  R2 footnotes           per-page "Footnotes" blocks, bracketed "[1. ...]" note blocks, endnote
                         sections, and inline reference markers ("[1]", "^1", "{1}", bare "1")
  R3 front/back matter   everything before the first and after the last line of the translation,
                         plus the introductions of each part inside multi-part volumes
  R4 interleaved editorial matter (translator's notes, summaries, gap notes set apart from the text)
  R5 keep the translated text, its headings and its verse numbers

Every file has its own function below with explicit start/end markers and regular expressions.
Whitespace: trailing spaces are stripped and runs of blank lines are collapsed to one blank line
after the rules have been applied (no words are changed by this).
"""
import csv
import os
import re
import sys

SRC = '/root/analysis/cci/texts'
DST = '/root/analysis/cci/clean'
AUDIT = os.path.join(DST, 'audit')


# ----------------------------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------------------------

def read_lines(name):
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        return f.read().split('\n')


class Cleaner:
    """Holds the working lines of one file plus an audit trail of everything removed."""

    def __init__(self, name):
        self.name = name
        self.lines = read_lines(name)
        self.chars_before = len('\n'.join(self.lines))
        self.removed = []          # (rule, text) pairs, written to the audit file
        self.rules = []            # rules that actually changed something
        self.notes = []            # free-text notes for the log
        self.page_pos = []         # (page label, line index) recorded by R1, used by R2

    # -- bookkeeping ---------------------------------------------------------------------------
    def used(self, rule):
        if rule not in self.rules:
            self.rules.append(rule)

    def drop(self, rule, text):
        if text.strip():
            self.removed.append((rule, text))
            self.used(rule)

    def note(self, text):
        self.notes.append(text)

    # -- R3: cut to the translated text --------------------------------------------------------
    def cut(self, start_re, end_re=None, start_occurrence=1, end_inclusive=False,
            end_after_start=True):
        """Keep lines from the start_occurrence-th line matching start_re up to (not including)
        the first line matching end_re after the start (or the end of the file)."""
        start = None
        seen = 0
        for i, l in enumerate(self.lines):
            if re.search(start_re, l):
                seen += 1
                if seen == start_occurrence:
                    start = i
                    break
        if start is None:
            raise RuntimeError('%s: start marker %r not found' % (self.name, start_re))
        end = len(self.lines)
        if end_re is not None:
            for i in range(start + 1 if end_after_start else 0, len(self.lines)):
                if re.search(end_re, self.lines[i]):
                    end = i + 1 if end_inclusive else i
                    break
            else:
                raise RuntimeError('%s: end marker %r not found' % (self.name, end_re))
        self.drop('R3', '\n'.join(self.lines[:start]))
        self.drop('R3', '\n'.join(self.lines[end:]))
        # keep page positions consistent
        self.page_pos = [(p, i - start) for p, i in self.page_pos if start <= i < end]
        self.lines = self.lines[start:end]

    def delete_line_range(self, rule, a, b):
        """Delete lines a..b-1 (indices into self.lines)."""
        self.drop(rule, '\n'.join(self.lines[a:b]))
        del self.lines[a:b]

    def delete_indices(self, rule, idxs):
        """Delete the lines whose indices are in idxs (overlapping spans are safe)."""
        idxs = set(idxs)
        keep = []
        run = []
        for i, l in enumerate(self.lines):
            if i in idxs:
                run.append(l)
            else:
                if run:
                    self.drop(rule, '\n'.join(run))
                    run = []
                keep.append(l)
        if run:
            self.drop(rule, '\n'.join(run))
        self.lines = keep

    def delete_matching_lines(self, rule, regex):
        keep = []
        for l in self.lines:
            if re.search(regex, l):
                self.drop(rule, l)
            else:
                keep.append(l)
        self.lines = keep

    def sub(self, rule, regex, repl='', flags=0):
        """Regex substitution inside lines; everything matched is logged as removed."""
        out = []
        for l in self.lines:
            for m in re.finditer(regex, l, flags):
                self.drop(rule, m.group(0))
            out.append(re.sub(regex, repl, l, flags=flags))
        self.lines = out

    # -- output --------------------------------------------------------------------------------
    def finish(self):
        text_lines = [l.rstrip() for l in self.lines]
        out = []
        for l in text_lines:
            if l == '' and (not out or out[-1] == ''):
                continue
            out.append(l)
        while out and out[-1] == '':
            out.pop()
        text = '\n'.join(out) + '\n'
        with open(os.path.join(DST, self.name), 'w', encoding='utf-8') as f:
            f.write(text)
        with open(os.path.join(AUDIT, self.name + '.removed.txt'), 'w', encoding='utf-8') as f:
            for rule, t in self.removed:
                f.write('=== %s ===\n%s\n' % (rule, t))
        nonblank = [l for l in out if l.strip()]
        return {
            'file': self.name,
            'chars_before': self.chars_before,
            'chars_after': len(text),
            'first_retained_line': nonblank[0][:150] if nonblank else '',
            'last_retained_line': nonblank[-1][:150] if nonblank else '',
            'rules_applied': ';'.join(sorted(self.rules)) if self.rules else 'none needed',
            'notes': ' | '.join(self.notes),
        }


# ----------------------------------------------------------------------------------------------
# R1 helpers (sacred-texts artefacts)
# ----------------------------------------------------------------------------------------------

# whole-line page markers: "p. 12", "p. xiv", "p. 2 p. 3", "p. 8p. 9", Kojiki "p. 98 [82]", "[126]",
# Book of the Dead "{p. 246}"
PAGE_LINE = re.compile(
    r'^\s*(?:(?:p\.\s?(?:A\d+|[0-9ivxlcdmIVXLCDM]+)\s*(?:\[\d+\])?\s*)+|\[\d+\]|\{p\.\s?[0-9ivxlcdm]+\})\s*$')
PAGE_LABEL = re.compile(r'p\.\s?([0-9ivxlcdmIVXLCDM]+)')


def r1_page_markers(c):
    """Delete whole-line page markers, remembering where each page started (for R2)."""
    out = []
    for l in c.lines:
        if PAGE_LINE.match(l):
            for lab in PAGE_LABEL.findall(l):
                c.page_pos.append((lab, len(out)))
            c.drop('R1', l)
        else:
            out.append(l)
    c.lines = out


def r1_paragraph_continues(c):
    c.sub('R1', r'\[paragraph continues\]\s*')


def r1_inline_page_markers(c, extra=None):
    """Page markers that the site set inside a running line ("... It p. 320 is ...").
    Only removed between two words of running text, so bibliographic references
    ("p. 108 ff.", "Essays, p. 253 seq.") are left alone."""
    pat = r'(?<=[a-zA-Z\]\)’”\'"!?;:]) p\. ?[0-9ivxlc]+(?! ?(?:ff|f\.|seq|sqq|note|n\.|\d))(?= +[\w\[\(\'"‘“])'
    c.sub('R1', pat, '')
    c.sub('R1', r'(?<=[a-z.;:!?\'"’”]) p\. ?[0-9]+$', '')        # marker left at the end of a verse line
    if extra:
        c.sub('R1', extra, '')


# ----------------------------------------------------------------------------------------------
# R2 helpers
# ----------------------------------------------------------------------------------------------

FN_ENTRY = re.compile(r'^([0-9ivxlcdmIVXLCDM]+|A\d+):(\d+[a-z]?)(?:\s|$)')


def is_caps_heading(s):
    letters = [ch for ch in s if ch.isalpha()]
    if len(letters) < 2:
        return False
    return not any(ch.islower() for ch in letters) and len(s) <= 220


def is_page_start(s, extra=None):
    """First line of a new site page after a footnote block: a heading in capitals, a bare
    section numeral ("I.", "V.", "I a."), or a file-specific pattern."""
    return (is_caps_heading(s) or bool(re.match(r'^[IVXL]+( [a-z])?\.$', s))
            or bool(extra and re.search(extra, s)))


def marker_regex(n):
    return re.compile(r'(?:(?<=\s)|(?<=^))' + re.escape(str(n)) + r'(?![\da-z]|[-–]\d)(?=[\s.,;:!?)\]\[(\'"’”—–\-]|$|[A-Z])',
                      re.M)


OCR_I = re.compile(r'\b(when|When|should|could|would|shall|will|and|but|that|if|as|then|Then|so|So|what|'
                   r'What|which|have|how|How|may|can|did|do|Do|now|Now|where|Where|said|for|For|than)\s$')
SKIP_BEFORE = re.compile(r'(?:p\.|pp\.|§|§§|ll?\.|vv?\.|Note|Notes|Sect\.|chap\.|No\.|[IVXLC]+,)\s*$')


def find_marker(text, n, start, end=None, strict=True):
    """Next occurrence of note marker n in text[start:end].  strict=False (used only inside the
    known span of the marker's page) keeps just the line-start and reference exclusions."""
    for m in marker_regex(n).finditer(text, start, end if end is not None else len(text)):
        i = m.start()
        line_start = (i == 0 or text[i - 1] == '\n')
        after = text[m.end():m.end() + 4]
        if line_start and re.match(r'\.|\s+\d|\s*\(', after):
            continue            # verse number at line start ("5.", "2 (4).", "3 2.")
        if SKIP_BEFORE.search(text[max(0, i - 8):i]):
            continue            # page / section / line reference, not a note marker
        if strict:
            before = text[max(0, i - 2):i]
            if re.match(r'[.,]', after) and re.match(r'^[.!?:;,]\s$', before):
                continue        # verse number or enumeration inside a line ("praise. 2. And", ": 1. hard")
            if str(n) == '1' and OCR_I.search(text[max(0, i - 12):i]) and re.match(r',?\s+[a-z]', after):
                continue        # the letter I misread as 1 ("When 1 was", "how should 1, through")
        return m
    return None


DUP_PREV_WORD = re.compile(r'\b(to|and|or|is|are|was|of|by|from|with|in|at|on|for|than|verse|verses|section|'
                           r'sections|Nos?\.|year|years|page|note|line|lines|a|an|the|See|see|cf\.|Cf\.)\s$')


def dup_ok(text, m):
    """Stricter test for the duplicate sweep: the number must hang on a word or a closing
    bracket/quote ('Phäng Mäng 1,', 'Anu] 2') and must not look like an enumeration, a range,
    a count or a reference."""
    i, j = m.start(), m.end()
    if i < 3 or not re.match(r'[\w\]\)\'"’”?]', text[i - 2]) or text[i - 1] != ' ':
        return False
    if text[i - 3] == '(':
        return False            # "(I 3)": an OCR-damaged verse number such as (13)
    if DUP_PREV_WORD.search(text[max(0, i - 12):i]):
        return False
    after = text[j:j + 3]
    if re.match(r'[-–,]\s?\d|\.\s?[a-z]|\s?[A-Z]\.?[A-Z]|\s*\(', after) or re.match(r'\s+(to|and|or)\s+\d', text[j:j + 9]):
        return False
    return True


def remove_marker(text, m):
    i, j = m.start(), m.end()
    if i > 0 and text[i - 1] in ' \t':
        i -= 1                  # "word 1 next" -> "word next"
    elif i == 0 or text[i - 1] == '\n':
        while j < len(text) and text[j] == ' ':
            j += 1              # "1He ..." / "1 He" at line start
    return text[:i] + text[j:], i


def r2_footnote_blocks(c, extra_boundary=None, page_bounded=True, continuous=False):
    """sacred-texts per-page notes: a line 'Footnotes' followed by entries 'P:n text'.
    The block runs to the start of the next site page, i.e. the next heading line (is_page_start).
    Everything in between (entries, continuation paragraphs of long notes, a page's notes that
    spill over) is deleted.

    Inline markers: entry 'P:n' is the n-th note of printed page P.  With page_bounded=True the
    marker n is searched between the page marker 'p. P' (the last one before the block, as
    recorded by R1) and the next page marker, in order of the entries (a page may start in the
    previous site page, so the search is not limited to the current site page).  Without page
    bounds (Kojiki, numbered per section) the markers are searched in order in the text of the
    site page that precedes the block.  Unmatched entries are counted."""
    L = c.lines
    out = []
    blocks = []
    old_to_new = {}
    i = 0
    while i < len(L):
        if L[i].strip() == 'Footnotes':
            j = i + 1
            entries = []
            other = []
            while j < len(L):
                s = L[j].strip()
                m = FN_ENTRY.match(s)
                if s == '' or s == 'Footnotes' or PAGE_LINE.match(L[j]):
                    j += 1
                    continue
                if m:
                    entries.append((m.group(1), m.group(2)))
                    j += 1
                    continue
                if is_page_start(s, extra_boundary):
                    break
                other.append(s)
                j += 1
            c.drop('R2', '\n'.join(L[i:j]))
            for x in range(i, j):
                old_to_new[x] = len(out)
            blocks.append({'pos': len(out), 'entries': entries, 'other': other})
            i = j
        else:
            old_to_new[i] = len(out)
            out.append(L[i])
            i += 1
    old_to_new[len(L)] = len(out)
    c.page_pos = [(p, old_to_new.get(ix, len(out))) for p, ix in c.page_pos]
    c.lines = out

    # global text with line offsets
    offs = []
    o = 0
    for l in out:
        offs.append(o)
        o += len(l) + 1
    offs.append(o)
    text = '\n'.join(out)
    pages = sorted(((offs[ix], p) for p, ix in c.page_pos), key=lambda t: t[0])
    page_starts = [t[0] for t in pages]

    matches = []          # (start, end, label)
    page_numbers = {}     # page index -> note numbers matched on that page
    used = set()
    found = missing = 0
    prev_block = 0
    for b in blocks:
        block_off = offs[b['pos']]
        seg_start = offs[prev_block]
        prev_block = b['pos']
        seg_cursor = seg_start
        page_cursor = {}
        last_n = 0
        for p, n in b['entries']:
            m = None
            k = None
            if continuous:
                # notes numbered through a whole section (Kojiki): an entry that breaks the
                # sequence (a source slip such as '23:9' among 22:14 and 23:15) is not searched
                if int(re.match(r'\d+', n).group(0)) <= last_n:
                    missing += 1
                    c.missing_markers = getattr(c, 'missing_markers', []) + ['%s:%s (out of sequence)' % (p, n)]
                    continue
                last_n = int(re.match(r'\d+', n).group(0))
            if page_bounded:
                # the page marker p nearest before this block (or, if the page only starts after
                # the block, the first one after it); the search covers that whole printed page,
                # which may straddle two site pages
                before = [x for x, (off, lab) in enumerate(pages) if lab == p and off <= block_off]
                after_ = [x for x, (off, lab) in enumerate(pages) if lab == p and off > block_off]
                cand = before[-1:] or after_[:1]
                if cand:
                    k = cand[0]
                    pstart = pages[k][0]
                    nxt = [off for off, lab in pages[k + 1:] if off > pstart]
                    pend = nxt[0] if nxt else len(text)
                    cur = page_cursor.get(k, pstart)
                    # in order from the last marker of the page; then (markers printed out of
                    # order, e.g. 1 2 3 4 6 7 5) anywhere in the page
                    for frm, strict in ((cur, True), (cur, False), (pstart, True), (pstart, False)):
                        m = find_marker(text, n, frm, pend, strict)
                        while m is not None and m.start() in used:
                            m = find_marker(text, n, m.end(), pend, strict)
                        if m is not None:
                            break
                    if m is not None:
                        page_cursor[k] = max(cur, m.end())
            if m is None and k is None:
                # page unknown: markers in order in the text of the site page before the block
                m = find_marker(text, n, seg_cursor, block_off)
                while m is not None and m.start() in used:
                    m = find_marker(text, n, m.end(), block_off)
                if m is not None:
                    seg_cursor = m.end()
            if m is None:
                missing += 1
                c.missing_markers = getattr(c, 'missing_markers', []) + ['%s:%s' % (p, n)]
                continue
            used.add(m.start())
            matches.append((m.start(), m.end(), '%s:%s' % (p, n)))
            if k is not None:
                page_numbers.setdefault(k, set()).add(n)
            found += 1
    # second sweep: the source sometimes prints the same number for several markers on one page
    # ('gifts 2, self-restraint 2, ... truth 2'); remove further bare occurrences of a page's note
    # numbers inside that page's span
    dups = 0
    for k, nums in page_numbers.items():
        pstart = pages[k][0]
        pend = pages[k + 1][0] if k + 1 < len(pages) else len(text)
        for n in nums:
            pos = pstart
            while True:
                m = find_marker(text, n, pos, pend)
                if m is None:
                    break
                pos = m.end()
                if m.start() in used or not dup_ok(text, m):
                    continue
                used.add(m.start())
                matches.append((m.start(), m.end(), 'dup %s:%s' % (pages[k][1], n)))
                dups += 1
    c.dup_markers = dups
    # apply removals from the end so offsets stay valid
    for st, en, lab in sorted(matches, reverse=True):
        c.drop('R2', '[marker %s] ...%s...' % (lab, text[max(0, st - 30):en + 10].replace('\n', ' ')))
        i, j = st, en
        if i > 0 and text[i - 1] in ' \t':
            i -= 1
        elif i == 0 or text[i - 1] == '\n':
            while j < len(text) and text[j] == ' ':
                j += 1
        text = text[:i] + text[j:]
    new = text.split('\n')
    assert len(new) == len(out), (c.name, 'line count changed')
    c.lines = new
    return found, missing, sum(len(b['other']) for b in blocks)


def r2_bracket_blocks(c, opener=r'^\[(\d+|\*)\.|^\[\*'):
    """Bracketed note blocks '[1. ... 2. ...]' (Sutta-Nipata, Book of the Dead):
    from a line opening with '[1.' to the next line ending in ']'."""
    out = []
    i = 0
    L = c.lines
    n = 0
    while i < len(L):
        if re.match(opener, L[i].strip()):
            j = i
            # the block closes at a line ending in ']' that is not an inline reference '[*]'/'[2]'
            while j < len(L) and not (L[j].rstrip().endswith(']')
                                      and not re.search(r'\[(\d+|\*)\]$', L[j].rstrip())):
                j += 1
            c.drop('R2', '\n'.join(L[i:j + 1]))
            n += 1
            i = j + 1
        else:
            out.append(L[i])
            i += 1
    c.lines = out
    return n


def remove_numbered_markers(text, numbers, log, label=''):
    """Endnote markers 1..N printed as digits attached to a word ('East.1', 'Merciful2') or
    standing alone ('mixing bowl 175 and').  Searched in order; an attached digit is preferred,
    a free-standing number is accepted only if it comes before the next attached marker."""
    pos = 0
    missing = []
    spaced = []
    for idx, n in enumerate(numbers):
        att = re.compile(r'(?<=[^\s\d])%d(?!\d)' % n).search(text, pos)
        sp = re.compile(r'(?<=\s)%d(?=[\s,.;:!?—)]|$)' % n, re.M).search(text, pos)
        use = None
        if att and (not sp or att.start() < sp.start()):
            use = att
        elif sp:
            nxt = None
            if idx + 1 < len(numbers):
                nxt = re.compile(r'(?<=[^\s\d])%d(?!\d)' % numbers[idx + 1]).search(text, pos)
            if nxt is None or sp.start() < nxt.start():
                use = sp
                spaced.append('%s%d: ...%s...' % (label, n, text[max(0, sp.start() - 25):sp.end() + 15]
                                                 .replace('\n', ' ')))
        if use is None:
            missing.append(n)
            continue
        log('[marker %s%d] ...%s...' % (label, n, text[max(0, use.start() - 25):use.end() + 10]))
        i, j = use.start(), use.end()
        if use is sp and i > 0 and text[i - 1] == ' ':
            i -= 1
        text = text[:i] + text[j:]
        pos = i
    return text, missing, spaced


# ----------------------------------------------------------------------------------------------
# Paragraph helpers (R4)
# ----------------------------------------------------------------------------------------------

def paragraphs(lines):
    """Split into paragraphs: list of (start, end) line index pairs of non-blank runs."""
    res = []
    i = 0
    while i < len(lines):
        if lines[i].strip():
            j = i
            while j < len(lines) and lines[j].strip():
                j += 1
            res.append((i, j))
            i = j
        else:
            i += 1
    return res


def wrapped_in_parens(s):
    """True if s starts with '(' whose matching ')' is the last bracket of the string."""
    s = s.strip()
    if not s.startswith('('):
        return False
    depth = 0
    for k, ch in enumerate(s):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                rest = s[k + 1:].strip()
                return rest in ('', '.', ':', ').')
    return False


# ----------------------------------------------------------------------------------------------
# File-specific functions
# ----------------------------------------------------------------------------------------------

def clean_dhammapada(c):
    c.cut(r'^Chapter I\. The Twin-Verses$')
    c.note('Removed title page, digitizer note and contents; text has no notes or markers.')


def clean_sutta_nipata(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    nb = r2_bracket_blocks(c)
    c.sub('R2', r'\[\d+\]')
    c.cut(r'^I\. URAGAVAGGA\.$', r'^Suttanipâta is ended\.$', end_inclusive=True)
    # R4: Fausboll's one-paragraph argument printed under each sutta title
    head = re.compile(r'^\d+\. [A-ZÂÎÛÑ\' ]+?(SUTTA|SUTTA OR KAPILASUTTA|GÂTHÂ|PUKKHÂ?)\.$')
    paras = paragraphs(c.lines)
    kill = []
    for k, (a, b) in enumerate(paras):
        if head.match(c.lines[a].strip()) and b - a == 1 and k + 1 < len(paras):
            na, nb_ = paras[k + 1]
            first = c.lines[na].strip()
            if not re.match(r'^(\d+\. |So it was heard|Thus I heard|Thus it was heard)', first):
                kill.append((na, nb_))
    for a, b in reversed(kill):
        c.delete_line_range('R4', a, b)
    c.note('Removed title page incl. "{scanned, proofread...}" line, contents, glossary, introduction, '
           '%d bracketed note blocks (incl. Pali verses) and the editor\'s one-line argument under '
           '%d sutta titles.' % (nb, len(kill)))


def clean_kjv(c):
    c.cut(r'^The Old Testament of the King James Version of the Bible$', start_occurrence=2)
    c.note('Removed the list of books at the top; Testament and book headings kept; no notes in source.')


def clean_analects(c):
    c.cut(r'^BOOK I\.  HSIO R\.$')
    c.note('Removed digitizer note and Chinese Classics title page. Blank lines inside sentences are '
           'the printed page breaks kept by the digitizer (not markers, left as is).')


def clean_mean(c):
    c.cut(r'^What Heaven has conferred', r'^THE END$')
    c.note('Removed header lines (500 BC / title / Confucius / translator) and closing "THE END".')


def clean_great_learning(c):
    c.cut(r'^WHAT THE GREAT LEARNING teaches', r'^THE END$')
    c.note('Removed header lines (500 BC / title / Confucius / translator) and closing "THE END". '
           '"COMMENTARY OF THE PHILOSOPHER TSANG" is part of the classic and kept.')


def clean_mencius(c):
    c.note('Nothing to remove: no page markers, notes, notices or front matter in the file; '
           '"Mencius Chapter N" headings kept.')


def clean_ttc(c):
    c.cut(r'^PART 1\.$')
    c.note('Removed producer line and title page.')


def clean_zhuangzi(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c)
    r1_inline_page_markers(c)
    c.cut(r'^BOOK I\.$')
    c.delete_matching_lines('R3', r'^THE TEXTS OF TAOISM\.$')      # SBE 40 volume running title
    c.note('Removed Legge\'s introduction (notices of the books) and SBE title lines; %d footnote '
           'markers removed (%d listed notes not matched in text); %d continuation lines of long '
           'footnotes removed with their blocks. The 39 empty "( )" (Chinese characters shown as '
           'images on the site) were all in the removed introduction and notes.' % (found, missing, other))
    return found, missing


# ---- Book of the Dead -------------------------------------------------------------------------

BOD_HEAD = re.compile(r'^PLATES? [IVXL]+\.?([ -].*)?$')
BOD_VIG_HEAD = re.compile(r'^(PLATE [IVXL]+\.)--Vignette')
BOD_EDIT = re.compile(r'^(§\s?\S+\.\s*)?Vignettes?\b|^Appendix\b|^In (the|other) [^:]{0,90}(papyr|recension)'
                      r'|^Closely connected with|^The whole of Plate')
BOD_APP_TEXT = re.compile(r'^Appendix(\[\d+\])?:\s*(?=Rubric)')
BOD_TEXT = re.compile(r'^Text\b|^\[?Rubric|^\[(Litany|Chapter|CHAPTER|WORDS)|^"?\(\s*[0-9IVX]+[\.,)]'
                      r'|^[IVX]+\. (\(|A HYMN|THE )|^THE [A-Z-]+ PYLON\.|^"If this chapter be known')


def clean_book_of_dead(c):
    r1_page_markers(c)
    c.sub('R1', r'\s*\{p\. ?[0-9ivxlc]+[}\]]\s*', ' ')       # also the misprinted "{p. 279]"
    nb = r2_bracket_blocks(c)
    c.sub('R2', r'\[(\d+|\*|l)\]')                  # "[l]" is an OCR slip for "[1]"
    c.sub('R2', r'\{footnote p\. ?\d+\}')
    c.cut(r'^PLATE I\.$')
    # R4: Budge's vignette descriptions and appendix commentary, paragraph by paragraph
    paras = paragraphs(c.lines)
    mode = 'text'
    pending_text = False
    kill = []
    decisions = []
    for a, b in paras:
        s = c.lines[a].strip()
        whole = ' '.join(x.strip() for x in c.lines[a:b])
        if BOD_VIG_HEAD.match(s):
            c.drop('R4', s[len(BOD_VIG_HEAD.match(s).group(1)):])
            c.lines[a] = BOD_VIG_HEAD.match(s).group(1)
            for x in range(a + 1, b):
                kill.append((x, x + 1))
            mode = 'edit'
            decisions.append(('HEAD+edit', s))
            continue
        if BOD_HEAD.match(s):
            decisions.append(('head', s))
            continue
        if BOD_APP_TEXT.match(s):
            c.drop('R4', BOD_APP_TEXT.match(s).group(0))
            c.lines[a] = BOD_APP_TEXT.sub('', c.lines[a].lstrip())
            mode = 'text'
            pending_text = False
            decisions.append(('keep', s))
            continue
        if BOD_EDIT.match(s):
            kill.append((a, b))
            mode = 'edit'
            # an Appendix sentence that introduces a translated passage ("... reads as follows:--")
            pending_text = (not re.match(r'^(§\s?\S+\.\s*)?Vignettes?\b', s)
                            and bool(re.search(r':\s*-*\s*$', whole)))
            decisions.append(('DEL', s))
            continue
        if BOD_TEXT.match(s) or pending_text:
            mode = 'text'
            pending_text = False
            decisions.append(('keep', s))
            continue
        if mode == 'edit':
            kill.append((a, b))
            decisions.append(('DEL', s))
        else:
            decisions.append(('keep', s))
    for a, b in sorted(kill, reverse=True):
        c.delete_line_range('R4', a, b)
    # "Text:" labels are Budge's; the bracketed chapter number after them is kept as a heading
    c.sub('R4', r'^Text:?\s*(?=\S)', '')
    with open(os.path.join(AUDIT, 'Egyptian__BookOfTheDead.decisions.txt'), 'w', encoding='utf-8') as f:
        for d, s in decisions:
            f.write('%-9s %s\n' % (d, s[:160]))
    c.note('Removed title page incl. "scanned at www.sacred-texts.com" line, preface, contents, '
           'Budge\'s introduction and chapter list, %d bracketed note blocks and inline [n] markers. '
           'R4: Budge\'s "Vignette" descriptions of the illustrations and his "Appendix" commentary '
           'paragraphs removed (state machine, decisions in audit/Egyptian__BookOfTheDead.decisions.txt); '
           'the variant versions he translates from other papyri, rubrics and litanies are kept. '
           'Vignette paragraphs also quote short translated captions (e.g. names of Ani\'s wife) and '
           'the funeral-ceremony appendix quotes ritual speeches: est. 1-2k chars of translated '
           'wording lost with them. Budge\'s "Text:" labels removed; his bracketed chapter numbers '
           '("[Chapter XV.]") and "PLATE" headings kept as headings.' % nb)


def clean_iliad(c):
    c.cut(r'^BOOK I\.$')
    paras = paragraphs(c.lines)
    kill = []
    for k, (a, b) in enumerate(paras):
        if re.match(r'^BOOK [IVXL]+\.?$', c.lines[a].strip()) and k + 1 < len(paras):
            kill.append(paras[k + 1])
    for a, b in reversed(kill):
        c.delete_line_range('R4', a, b)
    c.note('Removed title page and contents; R4: Butler\'s italic argument paragraph under each of '
           'the %d BOOK headings removed. No notes in source.' % len(kill))


def clean_odyssey(c):
    c.cut(r'^BOOK I$', r'^FOOTNOTES:$', start_occurrence=1)
    text = '\n'.join(c.lines)
    text, missing, spaced = remove_numbered_markers(text, list(range(1, 188)),
                                                    lambda t: c.drop('R2', t))
    c.lines = text.split('\n')
    c.note('Removed title, dedication, contents, both prefaces and the FOOTNOTES section (Butler\'s 187 '
           'notes); %d inline note numbers removed (%d free-standing), missing: %s. Butler\'s '
           'capitalised chapter titles under each BOOK heading kept as headings (R5); bracketed '
           'passages are Butler\'s marking of suspected interpolations inside the translation and are '
           'kept.' % (187 - len(missing), len(spaced), missing or 'none'))


def clean_theogony(c):
    c.cut(r'^\(ll\. 1-25\)')
    c.sub('R2', r' ?\b16[0-3]\d\b')
    c.note('Removed title line; inline endnote numbers 1601-1631 removed; "(ll. N-M)" line numbers kept.')


def clean_works_days(c):
    c.cut(r'^\(ll\. 1-10\)')
    c.sub('R2', r' ?\b13[0-4]\d\b')
    c.sub('R1', r' ?\{\[0-9\]\}')
    c.note('Removed title line; inline endnote numbers 1301-1343 and a stray "{[0-9]}" artefact removed; '
           '"(ll. N-M)" line numbers kept.')


def clean_gita(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c)
    r1_inline_page_markers(c)
    c.cut(r'^CHAPTER I\.$')
    c.sub('R2', r'(?<=himself) 1(?=by himself)', ' ')    # note marker glued to the next word (106:1)
    c.note('Removed Telang\'s introduction to the Gita; %d footnote markers removed (%d not matched); '
           'speaker lines ("Arguna said:") kept as part of the text.' % (found, missing))
    return found, missing


def clean_rigveda(c):
    c.delete_matching_lines('R4', r'^\(The following Hymn was originally only found in the Appendix'
                                  r'|^The deified object of this omitted hymn|^M\. Bergaigne is of opinion'
                                  r'|^By \'both classes\' probably')
    c.note('Hymn text only in source. R4: removed the editor\'s note (JBH) and Griffith\'s three prose '
           'notes at hymn 1.179; Griffith\'s Latin rendering of stanzas 3-4 of that hymn kept as '
           'translation (4 lines of Latin). Book headings are absent in the source (hymn numbers '
           'restart at HYMN I. ten times).')


def clean_quran(c):
    c.cut(r'^SURA1 XCVI\.')
    out = []
    sura_idx = [i for i, l in enumerate(c.lines) if l.startswith('SURA')] + [len(c.lines)]
    tot_missing = []
    tot_spaced = []
    nnotes = 0
    for k in range(len(sura_idx) - 1):
        seg = c.lines[sura_idx[k]:sura_idx[k + 1]]
        sep = [x for x, l in enumerate(seg) if re.match(r'^_{5,}\s*$', l)]
        if sep:
            body, notes = seg[:sep[0]], seg[sep[0]:]
            c.drop('R2', '\n'.join(notes))
        else:
            body, notes = seg, []
        # note numbers = the run 1, 2, 3 ... of numbers opening a note line (gaps allowed)
        nums = []
        for l in notes:
            m = re.match(r'^(\d+)\s', l)
            if m:
                v = int(m.group(1))
                if v == (nums[-1] + 1 if nums else 1) or (nums and nums[-1] < v <= nums[-1] + 2):
                    nums.append(v)
        top = max(nums) if nums else 0
        nnotes += top
        text = '\n'.join(body)
        text, missing, spaced = remove_numbered_markers(text, list(range(1, top + 1)),
                                                        lambda t: c.drop('R2', t), label=seg[0][:12] + ' ')
        tot_missing += ['%s:%d' % (seg[0].split('-')[0].split(' [')[0], m) for m in missing]
        tot_spaced += spaced
        out += text.split('\n')
    c.lines = out
    c.used('R2')
    with open(os.path.join(AUDIT, 'Islam__Quran.free_standing_markers.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(tot_spaced) + '\n')
    c.note('Removed Margoliouth\'s introduction, Rodwell\'s preface and sura table, and Rodwell\'s '
           'notes after each sura (%d notes); inline note numbers removed (attached digits, plus %d '
           'free-standing ones listed in audit/Islam__Quran.free_standing_markers.txt); not found in '
           'text: %s. "MECCA.-19 Verses" lines and Rodwell\'s chronological numbers "[I.]" in the '
           'sura headings kept as heading matter.' % (nnotes, len(tot_spaced), ', '.join(tot_missing) or 'none'))


def clean_sbe22(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c, extra_boundary=r'^Life of Mahâvîra, Lecture \d')
    r1_inline_page_markers(c)
    c.cut(r'^ÂKÂRÂṄGA SÛTRA\.$', r'^INDEX$', start_occurrence=2)
    c.note('Removed title page with the site\'s scan/public-domain notice, contents, Jacobi\'s '
           'introduction and the index; %d footnote markers removed (%d not matched); %d continuation '
           'lines of long footnotes removed with their blocks.' % (found, missing, other))
    return found, missing


def clean_sbe45(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c)
    r1_inline_page_markers(c)
    c.cut(r'^UTTARÂDHYAYANA\.$', r'^INDEX OF NAMES AND SUBJECTS\.$', start_occurrence=2)
    c.note('Removed title page with the site\'s notice, contents, Jacobi\'s introduction and additional '
           'note, and both indexes; %d footnote markers removed (%d not matched); %d continuation lines '
           'of long footnotes removed with their blocks.' % (found, missing, other))
    return found, missing


def clean_tanakh(c):
    c.note('Nothing to remove: API-built file with book/chapter headings and numbered verses only; the '
           'three bracketed repeated verses are printed text and kept.')


def clean_enuma(c):
    c.cut(r'^THE FIRST TABLET$', r'^END OF THE CREATION EPIC$')
    paras = paragraphs(c.lines)
    kill = []
    for a, b in paras:
        # a bracketed explanatory note may share a paragraph with verse lines: test line by line
        x = a
        while x < b:
            if c.lines[x].strip().startswith('['):
                y = x
                while y < b and not c.lines[y].rstrip().endswith(']'):
                    y += 1
                if y < b:
                    kill.append((x, y + 1))
                    x = y + 1
                    continue
            x += 1
    for a, b in reversed(kill):
        c.delete_line_range('R4', a, b)
    c.note('Removed title lines and the closing "END OF THE CREATION EPIC"; R4: %d bracketed notes on '
           'gaps set apart from the verse removed; short bracketed glosses inside lines '
           '("[Tiamat]", "[Marduk]") kept.' % len(kill))


GILG_EDIT = re.compile(r'\b(wanting|gap|missing|mutilated|lost|broken|breaks? off|Version|Edition|Column|'
                       r'Columns|text|lines?|remainder|fragment|continues thus|With this ends|interpolated)\b')


def clean_gilgamesh(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c)
    c.cut(r'^THE FIRST TABLET$', r'^THE END OF THE EPIC OF GILGAMISH\.$')
    kill = []
    for a, b in paragraphs(c.lines):
        for x in range(a, b):
            s = c.lines[x].strip()
            if wrapped_in_parens(s) and GILG_EDIT.search(s):
                kill.append((x, x + 1))
    for a, b in reversed(kill):
        c.delete_line_range('R4', a, b)
    c.note('Removed title page incl. the site\'s stale copyright notice, dedication, preface, addenda, '
           'and the closing "THE END OF THE EPIC OF GILGAMISH." and printer\'s line; '
           '%d footnote markers removed (%d not matched). R4: %d parenthesised editorial notes on gaps, '
           'mutilated lines and versions removed; Thompson\'s short parenthesised section titles '
           '("(The Creation of Enkidu).") kept as headings; line numbers kept.' % (found, missing, len(kill)))
    return found, missing


def clean_edda(c):
    c.cut(r'^PART I$', r'^PRONOUNCING INDEX OF PROPER NAMES$')
    # R4: "INTRODUCTORY NOTE" and "NOTES" blocks run to the next gap of >= 4 blank lines
    i = 0
    n_intro = n_notes = 0
    L = c.lines
    out = []
    while i < len(L):
        if L[i].strip() in ('INTRODUCTORY NOTE', 'NOTES', 'NOTE'):
            kind = L[i].strip()
            j = i + 1
            while j < len(L):
                if L[j].strip() == '':
                    k = j
                    while k < len(L) and L[k].strip() == '':
                        k += 1
                    if k - j >= 4:
                        break
                    j = k
                else:
                    j += 1
            c.drop('R4', '\n'.join(L[i:j]))
            if kind in ('NOTES', 'NOTE'):
                n_notes += 1
            else:
                n_intro += 1
            i = j
        else:
            out.append(L[i])
            i += 1
    c.lines = out
    c.note('Removed acknowledgement, general introduction and the pronouncing index; R4: Bellows\'s '
           '%d introductory notes and %d notes sections ("NOTES"/"NOTE" after each poem or prose piece) removed; the prose '
           'passages of the manuscripts (e.g. "Of Hjorvarth and Sigrlin") and speaker lines kept.'
           % (n_intro, n_notes))


def clean_aeneid(c):
    c.cut(r'^BOOK FIRST$', r'^THE END\.$')
    c.note('Removed transcriber\'s note, title page, preface, Mackail\'s notes and the transcriber\'s '
           'list of corrections; the bracketed Latin line numbers "[20-53]" are kept as verse '
           'numbering (R5) as are the book subtitles.')


def clean_kojiki(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c, continuous=True)
    r1_inline_page_markers(c)
    c.sub('R1', r' ?\[\d{1,3}\](?= ?)')          # original-edition page numbers set inline: "[4]"
    c.cut(r'^RECORDS OF ANCIENT MATTERS$', r'^APPENDIX I\.$')
    c.note('Removed title page with the site\'s notice, Chamberlain\'s introduction, the notes after '
           'each section, and the two appendices (romanized song texts, chronology); Yasumaro\'s '
           'preface is part of the work and kept; %d note markers removed (%d not matched); inline '
           '"[N]" original-edition page numbers removed (R1). The 95 empty "( )" (characters shown as '
           'images) were all in the removed introduction and notes; Chamberlain\'s bracketed supplied '
           'words kept (R4 exception).' % (found, missing))
    return found, missing


def clean_vendidad(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c)
    r1_inline_page_markers(c)
    c.cut(r'^VENDÎDÂD\.$')
    # R4: Darmesteter's introduction to each Fargard: from the line after the heading (and its short
    # title) to the first section mark "I." / "I a." / "1." of the translation
    start_re = re.compile(r'^(I|I a|1)\.( |$)|^\[1\. ')
    L = c.lines
    heads = [i for i, l in enumerate(L) if re.match(r'^FARGARD [IVXL]+\.?$', l.strip())]
    # Fargard XV lost its heading on the site: its introduction starts with "I (1-8). On five sins"
    xv = [i for i, l in enumerate(L) if l.startswith('I (1-8). On five sins')]
    spans = []
    for h in heads:
        j = h + 1
        while not L[j].strip():
            j += 1
        if len(L[j]) < 60 and not start_re.match(L[j]) and not re.match(r'^[IVX]+ \(\d', L[j]):
            j += 1                                       # keep the short title line ("The Earth.")
        k = j
        while k < len(L) and not start_re.match(L[k].strip()):
            k += 1
        spans.append((j, k))
    for h in xv:
        k = h
        while not start_re.match(L[k].strip()):
            k += 1
        spans.append((h, k))
    for a, b in sorted(spans, reverse=True):
        c.delete_line_range('R4', a, b)
    c.note('Removed title page with the site\'s notice, contents, Darmesteter\'s general introduction '
           'and abbreviations; %d footnote markers removed (%d not matched); %d continuation lines of '
           'long footnotes removed with their blocks. R4: Darmesteter\'s introduction to each of the '
           '22 Fargards removed (short Fargard title kept). The heading "FARGARD XV." is missing in the '
           'source, and the four summary lines that open that Fargard there ("I (1-8). On five sins ...") '
           'were removed together with the note block that precedes them.' % (found, missing, other))
    return found, missing


def clean_yashts(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c)
    r1_inline_page_markers(c)
    c.cut(r'^SÎRÔZAH I\.$', r'^INDEX TO THE VENDÎDÂD,$')
    # a broken scrap of a footnote left in the running text by the site ("; it has the same ...}")
    c.delete_matching_lines('R2', r'^; it has the same meaning in Vend\. XVIII, 9 \[23\]; cf\. Yt\. XXII, 18\.\}$')
    L = c.lines
    sep = re.compile(r'^_{5,}\s*$')
    yast_head = re.compile(r'^([IVX]+\.? [A-ZÂÎÛÊÔ ]+ (YAST|YAST HÂDHÔKHT)\.?|III\. ARDIBEHIST 1 YAST\.'
                           r'|XXI\. YAST FRAGMENT\.|YAST XXII\.|XXI AND XXII\. YAST FRAGMENTS\.'
                           r'|XXIII-XXIV\. ÂFRÎN PAIGHAMBAR ZARTÛST AND VÎSTÂSP YAST\.|NYÂYIS\.)$')
    spans = []
    for i, l in enumerate(L):
        if yast_head.match(l.strip()):
            j = i + 1
            while j < len(L) and not (sep.match(L[j]) or yast_head.match(L[j].strip())
                                      or re.match(r'^(I|1)\.( |$)', L[j].strip())):
                j += 1
            if j < len(L) and sep.match(L[j]):
                spans.append((i + 1, j + 1))             # intro + separator line
            elif j < len(L) and (yast_head.match(L[j].strip()) or re.match(r'^(I|1)\.( |$)', L[j].strip())):
                if any(x.strip() for x in L[i + 1:j]):
                    spans.append((i + 1, j))             # intro without separator (Ashi Yast, groups)
    for a, b in sorted(spans, reverse=True):
        c.delete_line_range('R4', a, b)
    c.note('Removed title page with the site\'s notice, contents, Darmesteter\'s introduction, the '
           'general introductions to the Yasts and Sirozahs and the index to vols IV and XXIII; '
           '%d footnote markers removed (%d not matched); %d continuation lines of long footnotes '
           'removed with their blocks. R4: Darmesteter\'s introduction to each Yast, to the Yast '
           'fragments, to Yasts XXIII-XXIV and to the Nyayis removed (%d intros).'
           % (found, missing, other, len(spans)))
    return found, missing


def clean_yasna(c):
    r1_page_markers(c)
    r1_paragraph_continues(c)
    found, missing, other = r2_footnote_blocks(c)
    r1_inline_page_markers(c)
    c.cut(r'^THE GÂTHA\(Â\) AHUNAVAITI\(Î\)\.$', r'^INDEX\.$')
    L = c.lines
    kill = set()
    # Gatha and Yasna introductions: group heading kept, its paragraphs dropped up to the next
    # heading or up to "Translation." (the Vahistoishti Gatha has no separate YASNA LIII heading)
    for i, l in enumerate(L):
        if l.strip().startswith('THE GÂTHA(Â) ') or l.strip() == 'THE YASNA.':
            a = i + 1
            while a < len(L) and (not L[a].strip() or is_caps_heading(L[a].strip())):
                a += 1                                  # second line of the heading "(SPENTÂMAINYU(Û))."
            j = a
            while j < len(L) and not ((L[j].strip() and is_caps_heading(L[j].strip()))
                                      or L[j].strip() == 'Translation.'):
                j += 1
            kill.update(range(a, j))
    # Mills's introductions to the Hôm Yast (Y. IX) and the Haptanghaiti (Y. XXXV), and his notes
    # that stand in place of a chapter ("This chapter is identical with ...", "(See Y. XV, 2 ...)")
    for head, first in (('THE HÔM YAST.', r'^1\. At the hour of Hâvani'),
                        ('YASNA HAPTANGHÂITI.', r'^PRAISE TO AHURA AND THE IMMORTALS')):
        occ = [i for i, l in enumerate(L) if l.strip() == head]
        for i in occ:
            j = i + 1
            while j < len(L) and not re.match(first, L[j].strip()):
                j += 1
            kill.update(range(i + 1, j))
    for i, l in enumerate(L):
        if re.match(r'^(This chapter is identical with Yasna [IVXL]+\.|This chapter is composed of fragments: .*'
                    r'|\(See Y\. [^()]*\)\.?)$', l.strip()):
            kill.add(i)
    # Mills's analysis of each Gatha chapter: from the line after the nearest heading above
    # (chapter title) down to "Translation." inclusive
    for i, l in enumerate(L):
        if l.strip() == 'Translation.':
            k = i - 1
            while k > 0 and not (L[k].strip() and is_caps_heading(L[k].strip())):
                k -= 1
            c.note_span = getattr(c, 'note_span', []) + [(L[k].strip()[:40], i - k)]
            kill.update(range(k + 1, i + 1))
    # introductions to the Afrinagan and the Gahs (second occurrence of the heading)
    for title, first in (('ÂFRÎNAGÂN.', r'^I\. ÂFRÎN'), ('THE GÂHS.', r'^I\. THE GÂH HÂVAN')):
        occ = [i for i, l in enumerate(L) if l.strip() == title]
        if len(occ) >= 2:
            j = occ[1] + 1
            while not re.match(first, L[j].strip()):
                j += 1
            kill.update(range(occ[1] + 1, j))
    c.delete_indices('R4', kill)
    c.note('Removed title page with the site\'s notice, contents, Mills\'s preface, introduction, '
           'abbreviations, the general introduction to the Gathas and the index; %d footnote markers '
           'removed (%d not matched); %d lines of Mills\'s commentary set between or after the '
           'footnotes (literal renderings, Pahlavi and Neryosangh versions, supplementary notes) '
           'removed with the note blocks. R4: introductions to each Gatha, Mills\'s analysis before '
           '"Translation." in each of the 17 Gatha chapters, and the introductions to the Yasna, '
           'Afrinagan and Gahs removed; Mills\'s chapter titles and speaker labels ("Ahura speaks.") kept.'
           % (found, missing, other))
    return found, missing


def clean_dummy(c):
    pass


FILES = [
    ('Buddhism__Dhammapada.txt', clean_dhammapada),
    ('Buddhism__SuttaNipata.txt', clean_sutta_nipata),
    ('Christianity__KJV_Bible.txt', clean_kjv),
    ('Confucianism__Analects.txt', clean_analects),
    ('Confucianism__DoctrineOfTheMean.txt', clean_mean),
    ('Confucianism__GreatLearning.txt', clean_great_learning),
    ('Confucianism__Mencius.txt', clean_mencius),
    ('Daoism__TaoTeChing.txt', clean_ttc),
    ('Daoism__Zhuangzi.txt', clean_zhuangzi),
    ('Egyptian__BookOfTheDead.txt', clean_book_of_dead),
    ('Greek__Iliad.txt', clean_iliad),
    ('Greek__Odyssey.txt', clean_odyssey),
    ('Greek__Theogony.txt', clean_theogony),
    ('Greek__WorksAndDays.txt', clean_works_days),
    ('Hinduism__BhagavadGita.txt', clean_gita),
    ('Hinduism__RigVeda.txt', clean_rigveda),
    ('Islam__Quran.txt', clean_quran),
    ('Jainism__JainaSutras_SBE22.txt', clean_sbe22),
    ('Jainism__JainaSutras_SBE45.txt', clean_sbe45),
    ('Judaism__Tanakh_JPS1917.txt', clean_tanakh),
    ('Mesopotamian__EnumaElish.txt', clean_enuma),
    ('Mesopotamian__Gilgamesh.txt', clean_gilgamesh),
    ('Norse-Germanic__PoeticEdda.txt', clean_edda),
    ('Roman__Aeneid.txt', clean_aeneid),
    ('Shinto__Kojiki.txt', clean_kojiki),
    ('Zoroastrianism__Avesta_SBE04_Vendidad.txt', clean_vendidad),
    ('Zoroastrianism__Avesta_SBE23_Yashts.txt', clean_yashts),
    ('Zoroastrianism__Avesta_SBE31_Yasna.txt', clean_yasna),
]

# Residual problems found in the audit (reading first/last 30 lines, random passages, and scans for
# leftover digits, page markers, notices and scholarly vocabulary).  Estimates are of editorial
# characters still in the cleaned file.
RESIDUAL = {
    'Buddhism__Dhammapada.txt': 'Residual: none found.',
    'Buddhism__SuttaNipata.txt': 'Residual: none found; Fausboll\'s parenthesised supplied words and the '
        'running verse numbers "(1)" are part of the translation. Paragraphs cut by a page break or a removed '
        'note block are left split by a blank line.',
    'Christianity__KJV_Bible.txt': 'Residual: none found.',
    'Confucianism__Analects.txt': 'Residual: none found (the printed page breaks remain as blank lines '
        'inside sentences).',
    'Confucianism__DoctrineOfTheMean.txt': 'Residual: none found.',
    'Confucianism__GreatLearning.txt': 'Residual: none found.',
    'Confucianism__Mencius.txt': 'Residual: the 28 "Mencius Chapter N" lines are the site\'s page headings '
        '(each of the 14 parts split over two pages), kept as headings (about 500 chars).',
    'Daoism__TaoTeChing.txt': 'Residual: none found.',
    'Daoism__Zhuangzi.txt': 'Residual: 2 notes (p. 135) have no marker in the text and 1-2 markers stand '
        'before a parenthesis and were not removed ("the Human 2 (in him"); five places where the '
        'source misreads "I" as "1" ("When 1 was crossing") are left as printed; Legge\'s parenthesised '
        'supplied words kept (about 4% of characters are in parentheses).',
    'Egyptian__BookOfTheDead.txt': 'Residual: one stray note number ("hath a portion 3 with him") and '
        'about ten places where the source misreads "I" as "1" ("(8) 1 have become") left as printed; about 1.2k chars of Budge\'s bracketed chapter tags and the '
        'PLATE headings; some interpretive glosses in parentheses ("(i.e., Seti I.)") kept.',
    'Greek__Iliad.txt': 'Residual: none found.',
    'Greek__Odyssey.txt': 'Residual: Butler\'s capitalised chapter titles under each BOOK heading (about '
        '2.3k chars, 0.4%) are summaries in heading form; kept under R5 as headings, unlike the Iliad\'s '
        'arguments, which are set as a paragraph. Remove them if headings should be book numbers only.',
    'Greek__Theogony.txt': 'Residual: none found.',
    'Greek__WorksAndDays.txt': 'Residual: none found.',
    'Hinduism__BhagavadGita.txt': 'Residual: none found.',
    'Hinduism__RigVeda.txt': 'Residual: five places where the source misreads "I" as "1" ("will 1 '
        'proclaim") left as printed.',
    'Islam__Quran.txt': 'Residual: the 114 "MECCA.-19 Verses" lines (about 2k chars) kept as part of the '
        'sura headings.',
    'Jainism__JainaSutras_SBE22.txt': 'Residual: 2 note numbers left at line ends in a verse list '
        '("humpbackedness, 1"); Jacobi\'s cross-references for abbreviated repetitions '
        '("&c. (see II, 1, 1, § 5)") kept inside the text, about 2.9k chars (0.7%).',
    'Jainism__JainaSutras_SBE45.txt': 'Residual: 5 note markers not matched (left as bare digits); Jacobi\'s '
        'cross-references for abbreviated repetitions ("(&c., all as in II, 2, 76, p. 382 ...)") kept, '
        'about 3.9k chars (0.8%).',
    'Judaism__Tanakh_JPS1917.txt': 'Residual: none (only whitespace normalised).',
    'Mesopotamian__EnumaElish.txt': 'Residual: none found; one line number ("15 Tutu ...") kept.',
    'Mesopotamian__Gilgamesh.txt': 'Residual: 4 note markers glued to a lowercase word ("he 3slack\'d") '
        'not removed; Thompson\'s 52 parenthesised section titles kept as headings (about 2k chars, 2%); '
        'his brackets and parentheses for restored and supplied words are part of the rendering (about '
        '20% of characters).',
    'Norse-Germanic__PoeticEdda.txt': 'Residual: none found; part/volume heading lines ("PART I", "VOLUME I") '
        'kept as headings.',
    'Roman__Aeneid.txt': 'Residual: none found (bracketed Latin line numbers are glued to the next word, '
        'e.g. "[20-53]Troy", as in the source).',
    'Shinto__Kojiki.txt': 'Residual: 9 note entries not matched, 5 bare note numbers left in the text '
        '(e.g. "Brave-Sun 9 Direction-Youth") and one unbracketed original page number ("hanging on 303 the"); '
        'Chamberlain\'s section titles "[SECT. ...]" kept as headings (about 12k chars, 4%).',
    'Zoroastrianism__Avesta_SBE04_Vendidad.txt': 'Residual: none found; Darmesteter\'s section numerals '
        '("I.", "II a.") and short Fargard titles kept as headings.',
    'Zoroastrianism__Avesta_SBE23_Yashts.txt': 'Residual: 1 note marker not matched; formula abbreviations '
        '". . . ." are the translator\'s and kept.',
    'Zoroastrianism__Avesta_SBE31_Yasna.txt': 'Residual: Mills\'s capitalised chapter titles (about 4k '
        'chars, 1.3%) and speaker labels ("Ahura speaks.", about 0.3k chars) kept as headings; his '
        'parenthesised interpretive supplements are heavy in the Gathas (about 13% of characters are in '
        'parentheses) and are kept as the translator\'s supplied words; a few "(See Y. ...)" pointers '
        'inside verse lines kept.',
}


def main(only=None):
    os.makedirs(DST, exist_ok=True)
    os.makedirs(AUDIT, exist_ok=True)
    rows = []
    for name, fn in FILES:
        if only and name not in only:
            continue
        c = Cleaner(name)
        fn(c)
        if name in RESIDUAL:
            c.note(RESIDUAL[name])
        if getattr(c, 'dup_markers', 0):
            c.note('%d further copies of a note number repeated on the same printed page (source prints '
                   'e.g. "Phäng Mäng 1, Thien Phien 1") removed; list in audit file as "[marker dup ...]".'
                   % c.dup_markers)
        row = c.finish()
        rows.append(row)
        print('%-45s %9d -> %9d  %s' % (name, row['chars_before'], row['chars_after'], row['rules_applied']))
    if not only:
        with open(os.path.join(DST, 'cleaning_log.csv'), 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['file', 'chars_before', 'chars_after', 'first_retained_line',
                                              'last_retained_line', 'rules_applied', 'notes'])
            w.writeheader()
            w.writerows(rows)


if __name__ == '__main__':
    main(sys.argv[1:] or None)
