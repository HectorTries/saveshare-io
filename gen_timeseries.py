#!/usr/bin/env python3
"""Build net worth over time sections from snapshots table. No em dashes. Figures only, each with quote + source."""
import sqlite3, os, html
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("SS_DB", os.path.join(BASE, "transcript_db.sqlite"))
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
snaps = [dict(r) for r in con.execute("SELECT * FROM snapshots ORDER BY creator, snap_date")]
con.close()
def esc(s): return html.escape(s or "")
def sym(c): return "\u00a3" if c == "GBP" else "$"

def spark(pts, w=220, h=56):
    vals = [p["net_worth"] for p in pts]
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    n = len(pts)
    coords = []
    for i, v in enumerate(vals):
        x = 8 + (w-16) * (i/(n-1) if n > 1 else 0.5)
        y = h-10 - (h-24) * ((v-lo)/rng)
        coords.append(f"{x:.0f},{y:.0f}")
    first, last = pts[0], pts[-1]
    base = first["net_worth"]
    pct = round((last["net_worth"]-base)/max(1,abs(base))*100) if base != 0 else (0 if last["net_worth"] == 0 else 100)
    arrow = "up" if pct >= 0 else "down"
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="trend {arrow} {pct}%">'
            f'<polyline points="{" ".join(coords)}" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>'
            + "".join(f'<circle cx="{c.split(",")[0]}" cy="{c.split(",")[1]}" r="3" fill="currentColor"/>' for c in coords)
            + "</svg>", pct)

by_creator = {}
for s in snaps:
    by_creator.setdefault((s["creator"], s.get("kind") or "net_worth"), []).append(s)
multi = {k: v for k, v in by_creator.items() if len(v) >= 2}
KIND_LABEL = {"net_worth": "net worth", "debt_balance": "debt balance", "portfolio": "portfolio"}
cards = []
for (handle, kind), pts in sorted(multi.items()):
    svg, pct = spark(pts)
    kind_label = KIND_LABEL.get(kind, kind)
    rows = "".join(
        f'<li><a href="{esc(p["video_url"])}" target="_blank" rel="noopener">{esc(p["snap_date"])}: <b>{sym(p["currency"])}{p["net_worth"]:,}</b></a>'
        f'<span class="q">&ldquo;{esc(p["quote"][:140])}&rdquo;</span></li>' for p in pts)
    cards.append(f'<div class="ts-card"><h3>@{esc(handle)} <span class="ts-kind">({esc(kind_label)})</span></h3><div class="ts-trend">{"+" if pct>=0 else ""}{pct}% stated change</div>{svg}<ul class="ts-points">{rows}</ul></div>')
spark_section = ('<section id="overtime"><div class="panel reveal"><div class="eyebrow">Over time</div>'
    '<h2>Net worth over time, per creator</h2>'
    '<p class="sub">Only creators with 2 or more stated points. Every point links to the video where it was said.</p>'
    f'<div class="ts-grid">{"".join(cards)}</div></div></section>')

# aggregate: median per quarter per region (native currency)
from collections import defaultdict
import statistics
q = defaultdict(lambda: defaultdict(list))
for s in snaps:
    d = s["snap_date"][:7]
    ym = d.split("-"); quarter = f"{ym[0]}-Q{(int(ym[1])-1)//3+1}"
    q[s["region"].lower()][quarter].append(s["net_worth"])
quarters = sorted({qq for r in q.values() for qq in r})
def med_line(region, color):
    vals = []
    for qq in quarters:
        v = q[region].get(qq)
        vals.append(statistics.median(v) if v else None)
    known = [v for v in vals if v is not None]
    if not known: return "", []
    lo, hi = min(known), max(known); rng = (hi-lo) or 1
    W, H = 560, 220
    pts = []
    for i, v in enumerate(vals):
        if v is None: continue
        x = 40 + (W-60) * (i/(len(vals)-1) if len(vals) > 1 else 0.5)
        y = H-30 - (H-60) * ((v-lo)/rng)
        pts.append((x, y, v, quarters[i]))
    line = " ".join(f"{x:.0f},{y:.0f}" for x, y, _, _ in pts)
    dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="{color}"><title>{qq}: {v:,}</title></circle>' for x, y, v, qq in pts)
    labels = "".join(f'<text x="{x:.0f}" y="{H-10}" font-size="10" text-anchor="middle">{qq}</text>' for x, y, v, qq in pts)
    return (f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="3"/>'+dots+labels, pts)

uk_svg, _ = med_line("uk", "#0f766e")
us_svg, _ = med_line("us", "#1d4ed8")
agg = ('<section id="aggregate"><div class="panel reveal"><div class="eyebrow">Aggregate</div>'
    '<h2>Median stated net worth by quarter</h2>'
    '<p class="sub">Median of stated snapshot points per quarter. UK in pounds, US in dollars. Small sample, shown as stated.</p>'
    '<h3>UK (GBP)</h3><svg class="agg" viewBox="0 0 560 220" width="100%" role="img">' + uk_svg + '</svg>'
    '<h3>US (USD)</h3><svg class="agg" viewBox="0 0 560 220" width="100%" role="img">' + us_svg + '</svg>'
    '</div></section>')
print(spark_section + "\n" + agg)
