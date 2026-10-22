"""
Independent verification, step A: score Berezkin motifs with the MAC-D dictionaries.

Written from scratch. Steps:
  1. Read each .dic file: header (between the two '%' lines) maps numbers to names,
     each later line is 'term<TAB>cat<TAB>cat...'.
  2. Build each motif's text = lowercase(title_english + '. ' + desc_eng).
  3. Tokenize the text into words (several tokenizer variants, to see what matters).
  4. A dictionary term is tokenized with the same tokenizer, then matched
     as a contiguous phrase; a trailing '*' makes the last word a prefix match.
  5. Flag motif x domain for virtue and vice; save flags and summary shares.
"""
import json
import re
import sys

import pandas as pd

DIC_DIR = "/root/data/ext/eMACDscore/emacscore/dictionaries/"
MOTIFS = "/root/data/mx_folklore/Motif_Master.dta"
OUT = "/root/analysis/verify2/"

DOMAINS = ["Family", "Group", "Reciprocity", "Heroism", "Deference", "Fairness", "Property"]


# ---------- 1. dictionary reader ----------
def read_dic(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    pct = [i for i, l in enumerate(lines) if l.strip() == "%"]
    assert len(pct) >= 2, "expected two % lines"
    cats = {}
    for l in lines[pct[0] + 1:pct[1]]:
        num, name = l.split("\t")
        cats[int(num)] = name.strip()
    terms = []
    for l in lines[pct[1] + 1:]:
        if not l.strip():
            continue
        parts = l.split("\t")
        term = parts[0].strip().lower()
        nums = [int(p) for p in parts[1:] if p.strip()]
        terms.append((term, nums))
    return cats, terms


# ---------- 2/3. tokenizers ----------
def normalize(text):
    text = text.lower()
    text = text.replace("’", "'").replace("‘", "'")   # curly apostrophes
    text = text.replace("\xad", "")                             # soft hyphen
    return text


TOKENIZERS = {
    # words; internal apostrophes kept ("mother's"), hyphens split words
    "alpha_apos": lambda t: re.findall(r"[a-z]+(?:'[a-z]+)*", normalize(t)),
    # letters only, apostrophes and hyphens both split
    "alpha_only": lambda t: re.findall(r"[a-z]+", normalize(t)),
    # internal apostrophes and hyphens kept ("father-in-law" one token)
    "alpha_apos_hyph": lambda t: re.findall(r"[a-z]+(?:['\-][a-z]+)*", normalize(t)),
    # python \w+ without curly-quote normalisation (a naive tokenizer)
    "naive_w": lambda t: re.findall(r"\w+", t.lower()),
}


def term_tokens(term, tok):
    """Tokenize a dictionary term; keep a trailing '*' as a prefix marker on the last token."""
    wild = term.endswith("*")
    core = term[:-1] if wild else term
    toks = tok(core)
    return tuple(toks), wild


def build_matcher(terms, tok):
    exact_single = {}      # token -> set(cats)
    prefix_single = []     # (prefix, cats)
    phrases = []           # (tuple tokens, wild_last, cats)
    for term, nums in terms:
        toks, wild = term_tokens(term, tok)
        if not toks:
            continue
        if len(toks) == 1 and not wild:
            exact_single.setdefault(toks[0], set()).update(nums)
        elif len(toks) == 1 and wild:
            prefix_single.append((toks[0], set(nums)))
        else:
            phrases.append((toks, wild, set(nums)))
    return exact_single, prefix_single, phrases


def match_text(tokens, matcher):
    exact_single, prefix_single, phrases = matcher
    cats = set()
    hits = []
    for w in tokens:
        if w in exact_single:
            cats |= exact_single[w]
            hits.append(w)
        for p, c in prefix_single:
            if w.startswith(p):
                cats |= c
                hits.append(p + "*")
    n = len(tokens)
    for toks, wild, c in phrases:
        k = len(toks)
        for i in range(n - k + 1):
            ok = all(tokens[i + j] == toks[j] for j in range(k - 1))
            last = tokens[i + k - 1]
            ok = ok and (last.startswith(toks[-1]) if wild else last == toks[-1])
            if ok:
                cats |= c
                hits.append(" ".join(toks))
                break
    return cats, hits


def score(variant):
    tok = TOKENIZERS[variant]
    m = pd.read_stata(MOTIFS)
    text = m["title_english"].fillna("") + ". " + m["desc_eng"].fillna("")
    out = pd.DataFrame({"motif_id": m["motif_id"]})
    for kind in ["virtue", "vice"]:
        cats, terms = read_dic(DIC_DIR + f"macd{kind}.dic")
        # sanity: category names
        names = [cats[i].replace("Virtue", "").replace("Vice", "") for i in range(1, 8)]
        assert names == DOMAINS, names
        matcher = build_matcher(terms, tok)
        flags = {d: [] for d in DOMAINS}
        hitlist = []
        for t in text:
            c, hits = match_text(tok(t), matcher)
            for i, d in enumerate(DOMAINS, start=1):
                flags[d].append(int(i in c))
            hitlist.append("|".join(sorted(set(hits))))
        for d in DOMAINS:
            out[f"{kind}_{d}"] = flags[d]
        out[f"{kind}_any"] = out[[f"{kind}_{d}" for d in DOMAINS]].max(axis=1)
        out[f"{kind}_hits"] = hitlist
    return out


if __name__ == "__main__":
    summary = {}
    for v in TOKENIZERS:
        f = score(v)
        f.to_csv(OUT + f"flags_{v}.csv", index=False)
        s = {"n_motifs": int(len(f)),
             "virtue_any_pct": round(100 * f["virtue_any"].mean(), 2),
             "vice_any_pct": round(100 * f["vice_any"].mean(), 2)}
        for d in DOMAINS:
            s[f"virtue_{d}_pct"] = round(100 * f[f"virtue_{d}"].mean(), 2)
        for d in DOMAINS:
            s[f"vice_{d}_pct"] = round(100 * f[f"vice_{d}"].mean(), 2)
        summary[v] = s
        print(v, json.dumps(s))
    json.dump(summary, open(OUT + "motif_scoring_summary.json", "w"), indent=1)
