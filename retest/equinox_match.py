"""Match Equinox 2020 polity codes to current Seshat polities (retest plan, Section 3.1).
Uses only names, regions (NGA) and dates; no ideology value or outcome is read.
Rule (fixed before running): for each current polity P (frame, 864) and each Equinox polity E listed in P's home NGA,
overlap = years shared / years of P. Candidates are E with overlap >= 0.5. If exactly one candidate, or the best candidate
has overlap >= 0.8 and the next best < 0.3, the match is 'unique'. Otherwise 'ambiguous' (sent to a blind AI matcher that
sees names, NGA and dates only). No candidate: 'none'.
Equinox dates: from the moralizing-gods polities.csv list (Start, End) where present, else parsed from the Equinox
'Duration' variable."""
import pandas as pd, numpy as np, re, io, json
EQ = '/root/data/seshat_polaris/build_polaris_dataset/Equinox2020.05.2023.xlsx'
OUT = '/root/analysis/retest/'
e = pd.read_excel(EQ)
e['code'] = e.Polity.str.replace('*', '', regex=False).str.strip()

def parse_dur(s):
    s = str(s).replace('–', '-').replace('—', '-')
    m = re.findall(r'(\d+)\s*(BCE|BC|CE|AD)?', s)
    if len(m) < 2:
        return (np.nan, np.nan)
    (a, ea), (b, eb) = m[0], m[1]
    eb = eb or 'CE'; ea = ea or eb
    sign = lambda era: -1 if era in ('BCE', 'BC') else 1
    return (sign(ea) * int(a), sign(eb) * int(b))

raw = open('/root/data/moralizing-gods/polities.csv', 'rb').read().decode('latin1').replace('\r\n', '\n').replace('\r', '\n')
mg = pd.read_csv(io.StringIO(raw)); mg['code'] = mg.PolID.str.replace('*', '', regex=False).str.strip()
mgd = mg.groupby('code').agg(start=('Start', 'min'), end=('End', 'max'))
dur = e[e.Variable == 'Duration'].groupby('code')['Value.From'].first().map(parse_dur)
eqp = e.groupby(['NGA', 'code']).size().reset_index()[['NGA', 'code']]
eqp['start'] = eqp.code.map(mgd.start); eqp['end'] = eqp.code.map(mgd.end)
miss = eqp.start.isna()
eqp.loc[miss, 'start'] = eqp.loc[miss, 'code'].map(lambda c: dur.get(c, (np.nan, np.nan))[0])
eqp.loc[miss, 'end'] = eqp.loc[miss, 'code'].map(lambda c: dur.get(c, (np.nan, np.nan))[1])
eqp['date_source'] = np.where(miss, 'Duration', 'polities.csv')
f = pd.read_csv('/root/analysis/frame/polities_frame.csv')
rows = []
for _, p in f.iterrows():
    c = eqp[(eqp.NGA == p.nga_name) & eqp.start.notna()].copy()
    span = max(p.end_year - p.start_year, 1)
    c['ov'] = ((np.minimum(c.end, p.end_year) - np.maximum(c.start, p.start_year)).clip(lower=0)) / span
    c = c[c.ov >= 0.5].sort_values('ov', ascending=False)
    if len(c) == 0:
        status = 'none'; best = None
    elif len(c) == 1 or (c.ov.iloc[0] >= 0.8 and c.ov.iloc[1] < 0.3):
        status = 'unique'; best = c.iloc[0]
    else:
        status = 'ambiguous'; best = c.iloc[0]
    rows.append(dict(name=p['name'], long_name=p.long_name, nga=p.nga_name, start=p.start_year, end=p.end_year, status=status,
                     equinox_code=None if best is None else best.code, overlap=None if best is None else round(best.ov, 3),
                     candidates=';'.join(f'{r.code}({int(r.start)}..{int(r.end)},{r.ov:.2f})' for r in c.itertuples())))
m = pd.DataFrame(rows)
m.to_csv(OUT + 'equinox_match_auto.csv', index=False)
eqp.to_csv(OUT + 'equinox_polities_dates.csv', index=False)
print(m.status.value_counts().to_dict())
print('Equinox polities without dates:', int(eqp.start.isna().sum()))
