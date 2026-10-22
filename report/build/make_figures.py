"""README figures (light and dark PNGs). Palette and chrome from the dataviz reference palette: series blue #2a78d6 / #3987e5."""
import json, re
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
OUT = '/root/analysis/report/figures/'
import os; os.makedirs(OUT, exist_ok=True)
THEME = {'light': dict(surface='#fcfcfb', ink='#0b0b0b', ink2='#52514e', muted='#898781', grid='#e1e0d9', base='#c3c2b7', series='#2a78d6'),
         'dark': dict(surface='#1a1a19', ink='#f0efec', ink2='#c3c2b7', muted='#898781', grid='#2c2c2a', base='#383835', series='#3987e5')}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})

# ---------- data for figure 1: violent internal end by cooperation quartile (same construction as h8r_analysis.py B2) ----------
src = open('/root/analysis/h8r/h8r_analysis.py').read()
prep = src.split('# ---------------- Part A')[0]
exec(prep)
b2 = src[src.index('# ---------------- Part B2/B3'):src.index('def logit(')]
exec(b2)
d = G.dropna(subset=['viol']).copy()
d['q'] = pd.qcut(d.Sz, 4, labels=['Least\ncooperative', 'Second', 'Third', 'Most\ncooperative'])
shares = d.groupby('q', observed=True).viol.agg(['mean', 'size'])
json.dump({str(k): dict(share=float(v['mean']), n=int(v['size'])) for k, v in shares.iterrows()}, open(OUT + 'fig1_data.json', 'w'), indent=1)
# ---------- data for figure 2: religious legitimation profile (region fixed effects) ----------
R = json.load(open('/root/analysis/h8r/h8r_results.json'))['A_RL']
rows = [('Freedom of religion for others', 'religious_freedom'), ('Public goods instead of favours', 'public_goods'),
        ('Courts constrain the ruler', 'judicial_constraints'), ('Legislature constrains the ruler', 'legislative_constraints'),
        ('Ruler respects the constitution', 'exec_respects_constitution'), ('Repression of civil society', 'CSO_repression'),
        ('Political killings', 'political_killings'), ('Torture', 'torture'), ('Leader portrayed as extraordinary', 'personalist_legitimation')]

def style(ax, t):
    ax.set_facecolor(t['surface'])
    for s in ['top', 'right', 'left']: ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(t['base'])
    ax.tick_params(colors=t['muted'], length=0)
    for lab in ax.get_xticklabels() + ax.get_yticklabels(): lab.set_color(t['ink2'])

for mode, t in THEME.items():
    # Figure 1: columns
    fig, ax = plt.subplots(figsize=(8, 5.0), dpi=200); fig.patch.set_facecolor(t['surface']); style(ax, t)
    x = np.arange(len(shares)); vals = shares['mean'].values * 100
    ax.yaxis.grid(True, color=t['grid'], linewidth=1); ax.set_axisbelow(True)
    ax.bar(x, vals, width=0.34, color=t['series'], linewidth=0)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 1.8, f'{v:.0f}%', ha='center', va='bottom', color=t['ink'], fontsize=12, fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(shares.index.astype(str)); ax.set_ylim(0, 80); ax.set_xlim(-0.6, len(x) - 0.4)
    ax.set_yticks([0, 20, 40, 60, 80]); ax.set_yticklabels(['0%', '20%', '40%', '60%', '80%'])
    fig.text(0.06, 0.95, 'Share of autocratic regimes that ended violently from within', color=t['ink'], fontsize=14, fontweight='bold', ha='left', va='top')
    fig.text(0.06, 0.89, 'By how cooperatively they ruled: quarters of the cooperation-minus-dominance score.\nV-Dem expert ratings, 1,099 autocratic regimes, 1789 to 2025.',
             color=t['ink2'], fontsize=9.5, ha='left', va='top')
    fig.text(0.06, 0.02, 'Violent internal end: coup, assassination, civil-war defeat or uprising.\nCompared with orderly ends: natural death of the ruler, or a guided or electoral transition.',
             color=t['muted'], fontsize=8, ha='left', va='bottom')
    fig.subplots_adjust(left=0.08, right=0.98, top=0.76, bottom=0.2)
    fig.savefig(OUT + f'fig1_violent_end_by_strategy_{mode}.png', facecolor=t['surface']); plt.close(fig)
    # Figure 2: dot plot with 95% intervals
    fig, ax = plt.subplots(figsize=(8, 5.2), dpi=200); fig.patch.set_facecolor(t['surface']); style(ax, t)
    ys = np.arange(len(rows))[::-1]
    ax.axvline(0, color=t['base'], linewidth=1)
    ax.xaxis.grid(True, color=t['grid'], linewidth=1); ax.set_axisbelow(True)
    for y, (lab, k) in zip(ys, rows):
        r = R[k]['region_fe']
        ax.plot([r['lo95'], r['hi95']], [y, y], color=t['series'], linewidth=2, solid_capstyle='round')
        ax.scatter([r['coef']], [y], s=70, color=t['series'], edgecolor=t['surface'], linewidth=2, zorder=3)
    ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows]); ax.set_xlim(-3, 2)
    ax.set_xlabel('Difference in standard deviations, no religious legitimation to full (95% interval)', color=t['muted'], fontsize=9)
    fig.text(0.02, 0.96, 'What autocracies that rule in the name of religion actually do', color=t['ink'], fontsize=14, fontweight='bold', ha='left', va='top')
    fig.text(0.02, 0.905, 'V-Dem expert ratings, autocracies 1900 to 2023, with income, population, year and region held constant.',
             color=t['ink2'], fontsize=9.5, ha='left', va='top')
    fig.subplots_adjust(left=0.38, right=0.97, top=0.84, bottom=0.12)
    fig.savefig(OUT + f'fig2_religious_legitimation_{mode}.png', facecolor=t['surface']); plt.close(fig)
print(shares)
