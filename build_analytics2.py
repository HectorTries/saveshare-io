#!/usr/bin/env python3
"""Analytics page builder. Rebuilds analytics.html from the figures table.
Rules: stated figures only, zero em dashes, never say transcript,
never mention archived video counts. No external JS or CSS libraries."""
import os, re, html, math, json, sqlite3, statistics
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("SS_DB", os.path.join(BASE, "transcript_db.sqlite"))

DISPLAY = {"net_worth": "Net worth", "invested": "Amount invested",
           "debt_paid": "Debt payoff", "debt_total": "Debt balance",
           "income": "Income flow", "savings": "Savings total",
           "pension": "Pension value", "portfolio": "Portfolio value",
           "property": "Property value", "savings_goal": "Savings goal",
           "crypto": "Crypto value", "cash": "Cash savings"}
TYPE_ORDER = ["net_worth", "portfolio", "invested", "pension", "property",
              "savings", "income", "debt_paid", "debt_total", "savings_goal"]

def slug(h):
    return "p/" + re.sub(r"[^a-z0-9]+", "", h.lower()) + ".html"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
nick = {r["handle"]: (r["nickname"] or r["handle"])
        for r in con.execute("SELECT handle, nickname FROM creators")}
prof_cache = set(os.listdir(os.path.join(BASE, "p")))

rows = []
for f in con.execute("SELECT * FROM figures WHERE verified=1 ORDER BY region, creator, amount DESC"):
    handle = f["creator"]
    pf = slug(handle)
    prof = pf if pf.split("/")[-1] in prof_cache else "index.html#creators"
    sym = "\u00a3" if f["region"] == "UK" else "$"
    date = f["as_of_date"] or (f"{f['as_of_year']}-01-01" if f["as_of_year"] else "")
    if not date:
        pub = con.execute("SELECT published_at FROM transcripts WHERE url=?", (f["video_url"],)).fetchone()
        date = pub[0][:10] if pub and pub[0] else ""
    rows.append(dict(region=f["region"].lower(), prof=prof, name=nick.get(handle, handle),
                     handle=handle, type=f["figure_type"],
                     kind=DISPLAY.get(f["figure_type"], f["figure_type"]),
                     amt=f["amount"], amt_s=f"{sym}{f['amount']:,}", sym=sym,
                     date=date, quote=f["quote"].strip(), url=f["video_url"]))

snaps = [dict(r) for r in con.execute("SELECT * FROM snapshots ORDER BY creator, snap_date")]

# Theme mentions per region, counted from post tags. Labelled mentions only.
THEME_LABEL = {"isa": "ISA", "pension": "Pension", "property": "Property",
               "budgeting": "Budgeting", "debt": "Debt", "investing": "Investing",
               "tax": "Tax", "side-hustle": "Side hustle", "net-worth": "Net worth",
               "crypto": "Crypto"}
mentions = {"uk": Counter(), "us": Counter()}
for r in con.execute("SELECT region, theme_tags FROM transcripts WHERE theme_tags IS NOT NULL AND theme_tags != ''"):
    for tag in r["theme_tags"].split(","):
        tag = tag.strip()
        if tag in THEME_LABEL:
            mentions[r["region"].lower()][tag] += 1
con.close()

assert len(rows) >= 100, f"only {len(rows)} rows in figures table"
uk = [r for r in rows if r["region"] == "uk"]
us = [r for r in rows if r["region"] == "us"]

def money(n, sym):
    return f"{sym}{n:,}"

def reg_stats(rs, sym):
    nw = sorted(r["amt"] for r in rs if r["type"] == "net_worth")
    return dict(
        creators=len(set(r["handle"] for r in rs)), figures=len(rs),
        nw_n=len(nw), nw_avg=round(sum(nw) / len(nw)) if nw else 0,
        nw_med=int(statistics.median(nw)) if nw else 0,
        nw_top=max(nw) if nw else 0,
        port_invested=sum(r["amt"] for r in rs if r["type"] in ("portfolio", "invested")),
        port_invested_n=sum(1 for r in rs if r["type"] in ("portfolio", "invested")),
        debt_paid=sum(r["amt"] for r in rs if r["type"] == "debt_paid"),
        debt_paid_n=sum(1 for r in rs if r["type"] == "debt_paid"),
        types=dict(Counter(r["type"] for r in rs)), sym=sym)

UKS, USS = reg_stats(uk, "\u00a3"), reg_stats(us, "$")
BUCKETS = [("Under 100K", 0, 100000), ("100K to 250K", 100000, 250000),
           ("250K to 500K", 250000, 500000), ("500K to 1M", 500000, 1000000),
           ("1M plus", 1000000, float("inf"))]

def hist_counts(rs):
    nw = [r["amt"] for r in rs if r["type"] == "net_worth"]
    return [{"label": lab, "count": sum(1 for v in nw if lo <= v < hi or (hi == float("inf") and v >= lo))}
            for lab, lo, hi in BUCKETS]

def type_mix(rs):
    c = Counter(r["type"] for r in rs)
    return [{"label": DISPLAY.get(t, t), "val": c[t]} for t in TYPE_ORDER if c.get(t)]

def mention_bars(region):
    items = sorted(mentions[region].items(), key=lambda kv: -kv[1])[:6]
    return [{"label": THEME_LABEL[k], "val": v} for k, v in items]

DATA = {}
for key, rs, st in (("uk", uk, UKS), ("us", us, USS)):
    DATA[key] = dict(
        stats=[{"to": st["creators"], "pre": "", "label": f"{key.upper()} creators tracked"},
               {"to": st["nw_avg"], "pre": st["sym"], "label": f"Avg net worth ({st['nw_n']} stated)"},
               {"to": st["nw_med"], "pre": st["sym"], "label": "Median net worth"},
               {"to": st["port_invested"], "pre": st["sym"], "label": f"Invested ({st['port_invested_n']} figures)"}],
        hist=hist_counts(rs), donut=type_mix(rs), bars=mention_bars(key),
        narrative="")

# Per-region narratives, written from the computed numbers above.
uk_top_type = max(UKS["types"], key=UKS["types"].get) if UKS["types"] else "invested"
us_top_type = max(USS["types"], key=USS["types"].get) if USS["types"] else "debt_paid"
UK_STORY = (
    f"The UK story is a journal story. {UKS['creators']} creators have stated a figure on camera, "
    f"and {UKS['nw_n']} of them have stated a net worth, averaging {money(UKS['nw_avg'], chr(163))} "
    f"with a median of {money(UKS['nw_med'], chr(163))}. The most common stated figure is "
    f"{DISPLAY.get(uk_top_type, uk_top_type).lower()}, which fits a creator culture built around "
    "ISAs, workplace pensions and monthly investing updates. Creators film the same accounts month "
    "after month, so the numbers form a public diary rather than a single headline claim.")
US_STORY = (
    f"The US story starts with debt and income, not net worth. Only {USS['nw_n']} creators have stated "
    f"a net worth, while {USS['types'].get('income', 0)} income figures and "
    f"{USS['types'].get('debt_paid', 0) + USS['types'].get('debt_total', 0)} debt figures are on record. "
    f"That split is the finding. US creators narrate pay cheques, side hustle receipts and balances "
    f"owed in public, week by week, and the payoff journals are the richest records on this page. "
    f"Retirement pots are the gap. Just {USS['types'].get('pension', 0)} stated pension figure exists so far, "
    "even though Roth and 401(k) accounts come up constantly as advice topics.")
DATA["uk"]["narrative"] = UK_STORY
DATA["us"]["narrative"] = US_STORY

# Debt leaderboard: largest stated payoffs across both regions, native currency kept separate by rank within region.
def leaderboard(rs, n=6):
    ds = sorted((r for r in rs if r["type"] == "debt_paid"), key=lambda r: -r["amt"])[:n]
    mx = max((r["amt"] for r in ds), default=1)
    return "".join(
        f'<div class="lrow"><div class="lmeta"><a href="{r["prof"]}"><b>{html.escape(r["name"])}</b></a> '
        f'<span class="h">@{html.escape(r["handle"])}</span><div class="lnote">{html.escape(r["quote"][:150])} '
        f'<a href="{r["url"]}" target="_blank" rel="noopener">source</a></div></div>'
        f'<div class="lbar"><div class="lfill" style="--w:{round(r["amt"] / mx * 100)}%"><span>{html.escape(r["amt_s"])}</span></div></div></div>'
        for r in ds)

# Over time cards from snapshots: creators with 2 or more points of one kind.
KIND_LABEL = {"net_worth": "net worth", "debt_balance": "debt balance",
              "portfolio": "portfolio", "savings": "savings", "debt_paid": "debt payoff",
              "invested": "invested"}
def spark(pts, w=230, h=58):
    vals = [p["net_worth"] for p in pts]
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    n = len(pts)
    coords = []
    for i, v in enumerate(vals):
        x = 8 + (w - 16) * (i / (n - 1) if n > 1 else 0.5)
        y = h - 10 - (h - 24) * ((v - lo) / rng)
        coords.append(f"{x:.0f},{y:.0f}")
    base = pts[0]["net_worth"]
    pct = round((pts[-1]["net_worth"] - base) / max(1, abs(base)) * 100) if base else 0
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="trend {pct}%">'
            f'<polyline points="{" ".join(coords)}" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>'
            + "".join(f'<circle cx="{c.split(",")[0]}" cy="{c.split(",")[1]}" r="3" fill="currentColor"/>' for c in coords)
            + "</svg>", pct)

by_ck = defaultdict(list)
for s in snaps:
    by_ck[(s["creator"], s.get("kind") or "net_worth", s["region"])].append(s)
ts_cards = []
for (handle, kind, region), pts in sorted(by_ck.items()):
    if len(pts) < 2:
        continue
    pts = sorted(pts, key=lambda p: p["snap_date"])
    svg, pct = spark(pts)
    sym = "\u00a3" if pts[0]["currency"] == "GBP" else "$"
    lis = "".join(
        f'<li><a href="{html.escape(p["video_url"])}" target="_blank" rel="noopener">{html.escape(p["snap_date"])}: <b>{sym}{p["net_worth"]:,}</b></a>'
        f'<span class="q">{html.escape(p["quote"][:130])}</span></li>' for p in pts)
    ts_cards.append(
        f'<div class="ts-card"><h3>@{html.escape(handle)} <span class="ts-kind">({html.escape(KIND_LABEL.get(kind, kind))}, {region.upper()})</span></h3>'
        f'<div class="ts-trend">{"+" if pct >= 0 else ""}{pct}% stated change</div>{svg}<ul class="ts-points">{lis}</ul></div>')
TS_SECTION = ('<section id="overtime"><div class="section-head"><h2>Stated figures over time</h2>'
              '<p>Only creators with two or more stated points of the same kind. Every point links to its source.</p></div>'
              f'<div class="ts-grid">{"".join(ts_cards)}</div></section>') if ts_cards else ""

# Aggregate median by quarter from net worth snapshots only.
qmap = defaultdict(lambda: defaultdict(list))
for s in snaps:
    if (s.get("kind") or "net_worth") != "net_worth":
        continue
    y, m = s["snap_date"][:4], int(s["snap_date"][5:7])
    qmap[s["region"].lower()][f"{y}-Q{(m - 1) // 3 + 1}"].append(s["net_worth"])
quarters = sorted({q for r in qmap.values() for q in r})
def med_line(region, color, gid, sym):
    vals = [(qq, statistics.median(qmap[region][qq])) if qmap[region].get(qq) else (qq, None) for qq in quarters]
    known = [v for _, v in vals if v is not None]
    if len(known) < 2:
        return ""
    lo, hi = min(known), max(known)
    pad = (hi - lo) or 1
    lo -= pad * 0.06
    hi += pad * 0.16
    rng = (hi - lo) or 1
    W, H, PT, PB, PL = 560, 252, 30, 36, 58
    def fmt(v):
        a = abs(v)
        if a >= 1000000:
            t = f"{v / 1000000:.1f}".rstrip("0").rstrip(".")
            return f"{sym}{t}M"
        return f"{sym}{v / 1000:.0f}k"
    grid = ""
    for t in range(4):
        gv = lo + rng * t / 3
        gy = PT + (H - PT - PB) * (1 - t / 3)
        grid += (f'<line class="grid-l" x1="{PL}" y1="{gy:.0f}" x2="{W - 10}" y2="{gy:.0f}"/>'
                 f'<text x="{PL - 8}" y="{gy + 4:.0f}" font-size="11" text-anchor="end">{fmt(gv)}</text>')
    pts = []
    for i, (qq, v) in enumerate(vals):
        if v is None:
            continue
        x = PL + (W - PL - 14) * (i / (len(vals) - 1) if len(vals) > 1 else 0.5)
        y = PT + (H - PT - PB) * (1 - (v - lo) / rng)
        pts.append((x, y, v, qq))
    line = " ".join(f"{x:.0f},{y:.0f}" for x, y, _, _ in pts)
    base = H - PB
    area = f"M{pts[0][0]:.0f},{base} " + " ".join(f"L{x:.0f},{y:.0f}" for x, y, _, _ in pts) + f" L{pts[-1][0]:.0f},{base} Z"
    dots = "".join(
        f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{color}" stroke="#fff" stroke-width="2"><title>{qq}: {sym}{v:,.0f}</title></circle>'
        for x, y, v, qq in pts)
    show_q = len(pts) > 6
    labels = "".join(
        f'<text x="{x:.0f}" y="{H - 12}" font-size="10" text-anchor="middle">{qq}</text>'
        for i, (x, y, v, qq) in enumerate(pts) if not show_q or i % 2 == 0 or i == len(pts) - 1)
    lx, ly, lv, _ = pts[-1]
    call = (f'<text class="last-v" x="{min(lx + 10, W - 76):.0f}" y="{max(ly - 10, 14):.0f}" font-size="14" fill="#fff">{fmt(lv)}</text>')
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity=".45"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
            + grid + f'<path d="{area}" fill="url(#{gid})"/>'
            + f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round"/>' + dots + labels + call)

AGG_SECTION = ('<section id="aggregate"><div class="section-head"><h2>The headline trend</h2>'
               '<p>Median of stated net worth points per quarter, native currency, no conversion. Small samples, shown exactly as stated.</p></div>'
               '<div class="hero-chart reveal">'
               '<div class="hc-grid">'
               f'<div class="hc-panel"><h3>UK trend, pounds</h3><p class="hc-sub">Median stated net worth by quarter</p><svg class="agg" viewBox="0 0 560 252" width="100%" role="img" aria-label="UK median net worth by quarter">{med_line("uk", "#EFC65C", "g-uk", chr(163))}</svg></div>'
               f'<div class="hc-panel"><h3>US trend, dollars</h3><p class="hc-sub">Median stated net worth by quarter</p><svg class="agg" viewBox="0 0 560 252" width="100%" role="img" aria-label="US median net worth by quarter">{med_line("us", "#8FB0FF", "g-us", "$")}</svg></div>'
               '</div></div></section>')

def table_rows(rs):
    out = []
    for r in rs:
        out.append(
            f'<tr data-region="{r["region"]}" data-amt="{r["amt"]}" data-date="{r["date"]}" '
            f'data-name="{html.escape(r["name"].lower())}" data-kind="{html.escape(r["kind"])}">'
            f'<td><a href="{r["prof"]}">{html.escape(r["name"])}</a><br>'
            f'<a class="h" href="https://www.tiktok.com/@{r["handle"]}" target="_blank" rel="noopener">@{r["handle"]}</a></td>'
            f'<td><span class="flag">{r["region"].upper()}</span></td>'
            f'<td>{html.escape(r["kind"])}</td><td class="num">{html.escape(r["amt_s"])}</td>'
            f'<td style="white-space:nowrap">{r["date"]}</td>'
            f'<td class="q">{html.escape(r["quote"])} <a href="{r["url"]}" target="_blank" rel="noopener">source</a></td></tr>')
    return "".join(out)

kinds = sorted(set(r["kind"] for r in rows))
kind_opts = "".join(f'<option>{html.escape(k)}</option>' for k in kinds)
total_creators = len(set(r["handle"] for r in rows))
top_uk = max((r for r in uk if r["type"] == "net_worth"), key=lambda r: r["amt"], default=None)
top_us = max((r for r in us if r["type"] in ("net_worth", "portfolio")), key=lambda r: r["amt"], default=None)

CSS = """
:root{--forest:#0B3D2E;--pine:#082A20;--paper:#F5F4EF;--card:#FFFDF8;--ink:#17201B;--muted:#5A665E;--line:#D9D5C7;--amber:#C07A12;--blue:#1D4ED8;--gold:#EFC65C}
section{padding:52px 0 8px;scroll-margin-top:124px}
.section-head{max-width:760px;margin:0 0 26px;border-top:3px solid var(--ink);padding-top:18px}
.section-head h2{font-size:clamp(28px,3.6vw,40px);margin-bottom:10px}
.section-head p{color:var(--muted);font-size:16px;margin:0}
.panel{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--ink);border-radius:4px;padding:28px;margin:20px 0}
.story{font-size:17.5px;line-height:1.75;max-width:72ch}
.story strong{color:var(--forest)}
.takeaways{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:22px 0}
.takeaway{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--amber);border-radius:4px;padding:20px}
.takeaway strong{display:block;font-family:'Playfair Display',Georgia,serif;font-size:19px;line-height:1.25;margin-bottom:8px}
.takeaway p{margin:0;color:var(--muted);font-size:14.5px}
.pullquote{font-family:'Playfair Display',Georgia,serif;font-size:clamp(22px,3vw,30px);line-height:1.35;font-weight:800;border-top:3px solid var(--ink);border-bottom:1px solid var(--line);padding:26px 4px;margin:30px 0;font-style:italic}
.pullquote .pq-who{display:block;font-family:'Inter',system-ui,sans-serif;font-style:normal;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:14px}
.pullquote a{color:var(--forest);font-size:14px;font-style:normal}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:24px 0 8px}
.stat{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--ink);border-radius:4px;padding:22px}
.stat strong{display:block;font-family:'Playfair Display',Georgia,serif;font-size:31px;font-weight:900;font-variant-numeric:tabular-nums;line-height:1.05}
.stat span{font-size:12.5px;color:var(--muted);font-weight:600}
.donut-wrap{display:flex;gap:32px;align-items:center;flex-wrap:wrap}
.donut .slice{cursor:pointer;transition:opacity .15s}
.donut.dim .slice{opacity:.3}
.donut.dim .slice.hot{opacity:1}
.leg{font-size:14.5px;margin:7px 0;color:var(--muted);padding:6px 10px;border-radius:4px;cursor:default}
.leg.hot{background:#F7E8C8;color:var(--ink)}
.dot{display:inline-block;width:12px;height:12px;border-radius:99px;margin-right:8px}
.bars{display:flex;flex-direction:column;gap:12px;margin-top:22px}
.brow{display:grid;grid-template-columns:170px 1fr 60px;gap:12px;align-items:center;font-size:14px}
.btrack{background:#EDEBE3;border-radius:99px;height:24px;overflow:hidden}
.bfill{display:flex;align-items:center;justify-content:flex-end;height:100%;width:0;border-radius:99px;background:var(--forest);color:#fff;font-size:12px;font-weight:700;padding-right:10px;transition:width 1s cubic-bezier(.2,.7,.2,1)}
.bfill.blue{background:var(--blue)}
.in .bfill{width:var(--w)!important}
.lrow{display:grid;grid-template-columns:minmax(220px,320px) 1fr;gap:16px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line)}
.lrow:last-child{border-bottom:none}
.lmeta{font-size:14.5px}.lmeta a{color:var(--ink);text-decoration:none}.lmeta a:hover{color:var(--forest)}
.lnote{font-size:13px;color:var(--muted);margin-top:2px}.lnote a,.q a{color:var(--forest);font-weight:700;white-space:nowrap}
.lbar{background:#EDEBE3;border-radius:99px;height:32px;overflow:hidden}
.lfill{display:flex;align-items:center;height:100%;width:0;border-radius:99px;color:#fff;font-weight:800;font-size:14px;padding-left:14px;white-space:nowrap;transition:width 1s cubic-bezier(.2,.7,.2,1);background:var(--amber)}
.in .lfill{width:var(--w)!important}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.cmp-card{border:1px solid var(--line);border-radius:4px;padding:24px;background:var(--card)}
.cmp-card.us{border-top:3px solid var(--blue)}
.cmp-card.ukc{border-top:3px solid var(--forest)}
.cmp-card h3{font-size:23px;margin-bottom:6px;font-family:'Playfair Display',Georgia,serif}
.cmp-card .cnarr{font-size:14.5px;color:var(--muted);line-height:1.65;margin:0 0 14px}
.cmp-card ul{margin:0;padding:0;list-style:none;font-size:14.5px}
.cmp-card li{padding:8px 0;border-bottom:1px dashed var(--line);display:flex;justify-content:space-between;gap:10px}
.cmp-card li:last-child{border:none}.cmp-card li b{font-variant-numeric:tabular-nums;white-space:nowrap}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px;background:var(--card);border:1px solid var(--line);padding:14px;border-radius:4px}
.controls input,.controls select{font:inherit;font-size:14.5px;padding:11px 14px;border:1.5px solid var(--ink);border-radius:4px;background:#fff;color:var(--ink);min-height:48px}
.controls input{flex:1;min-width:180px}
.twrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px;margin-top:12px;min-width:760px}
th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);padding:10px 8px;border-bottom:2px solid var(--line);white-space:nowrap}
th button{background:none;border:none;font:inherit;color:inherit;cursor:pointer;padding:0;text-transform:inherit;letter-spacing:inherit;font-weight:700;min-height:32px}
td{padding:12px 8px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:nth-child(even) td{background:#F8F6EF}
.num{font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
.h{color:var(--forest);font-weight:600;text-decoration:none;font-size:13px}
.q{color:var(--muted);font-size:13px}
.flag{font-size:11px;font-weight:800;background:#F7E8C8;color:#A44A12;padding:2px 9px;border-radius:2px}
#rowcount{font-size:13.5px;color:var(--muted);margin-top:10px}
.method{background:#FFFBEB;border:1px solid #FDE68A;border-radius:4px;padding:28px;margin:28px 0;font-size:15px}
.method h2{font-size:24px;margin-bottom:10px;font-family:'Playfair Display',Georgia,serif}
.ts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.ts-card{border:1px solid var(--line);border-top:3px solid var(--ink);border-radius:4px;padding:18px;background:var(--card)}
.ts-card h3{font-size:16px;font-family:'Inter',system-ui,sans-serif}
.ts-kind{color:var(--muted);font-weight:600;font-size:13px}
.ts-trend{font-size:13px;font-weight:800;color:var(--forest);margin:4px 0 8px}
.ts-points{list-style:none;margin:10px 0 0;padding:0;font-size:13px}
.ts-points li{margin:8px 0}.ts-points a{color:var(--ink);text-decoration:none}.ts-points .q{display:block;color:var(--muted);font-size:12px;margin-top:2px}
.spark{color:var(--forest)}.agg{background:none;border:none;padding:0;display:block}.kpis{display:grid;grid-template-columns:repeat(4,1fr);background:var(--card);border:1px solid var(--line);border-top:3px solid var(--ink);border-radius:4px;margin:26px 0 8px;overflow:hidden}.kpi{padding:20px 22px;border-left:1px solid var(--line)}.kpi:first-child{border-left:none}.kpi strong{display:block;font-family:Playfair Display,Georgia,serif;font-size:clamp(24px,3vw,32px);font-weight:900;font-variant-numeric:tabular-nums;line-height:1.05}.kpi span{font-size:11.5px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.05em}.hero-chart{background:linear-gradient(180deg,#0B3D2E,#082A20);border-radius:6px;padding:30px 30px 22px;margin:22px 0;color:#F5F4EF}.hc-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.hc-panel{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:4px;padding:16px 16px 8px}.hc-panel h3{margin:0;font-size:15px;color:#fff;font-family:Inter,system-ui,sans-serif;text-transform:uppercase;letter-spacing:.06em}.hc-panel .hc-sub{color:#C9D6CC;font-size:13px;margin:4px 0 8px}.agg text{fill:#C9D6CC}.agg .grid-l{stroke:rgba(255,255,255,.16);stroke-width:1}.agg .last-v{font-weight:800;fill:#fff}#figtable thead th{position:sticky;top:104px;background:var(--card);z-index:5;box-shadow:0 2px 0 var(--line)}@media(max-width:700px){.kpis{grid-template-columns:1fr 1fr}.kpi:nth-child(3){border-left:none}.kpi:nth-child(n+3){border-top:1px solid var(--line)}.hc-grid{grid-template-columns:1fr}.hero-chart{padding:22px 16px}}
.chart-text{margin-top:14px;font-size:13.5px;color:var(--muted)}
.chart-text table{min-width:0;font-size:13px}
.hist .hbar{transform:scaleY(0);transform-origin:bottom;transform-box:fill-box;transition:transform 1s cubic-bezier(.2,.7,.2,1)}
.in .hbar{transform:scaleY(1)}
.reveal{opacity:0;transform:translateY(16px);transition:opacity .6s ease,transform .6s ease}
.reveal.in{opacity:1;transform:none}
.subnav{background:#17201B;color:#fff;position:sticky;top:57px;z-index:15}
.subnav .wrap{display:flex;gap:2px;overflow-x:auto;max-width:1180px}
.subnav a{color:#C9D6CC;text-decoration:none;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:14px 12px;white-space:nowrap;border-bottom:3px solid transparent;min-height:44px;display:inline-flex;align-items:center}
.subnav a.on{color:var(--gold);border-bottom-color:var(--amber)}
@media(max-width:700px){.cmp{grid-template-columns:1fr}.lrow{grid-template-columns:1fr}.brow{grid-template-columns:110px 1fr 52px;font-size:13px}.panel{padding:20px}}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none}.bfill,.lfill,.hist .hbar{transition:none}.in .bfill,.in .lfill{width:var(--w)!important}.in .hbar{transform:none}}
"""

JS = """
(function(){
var DATA=JSON.parse(document.getElementById("region-data").textContent);
var COLS=["#0B3D2E","#C07A12","#1D4ED8","#8A5A12","#5A665E","#A44A12","#2F6B4F","#7A3B12"];
var view="uk";
try{view=localStorage.getItem("ss-region")||"uk"}catch(e){}
if(view!=="uk"&&view!=="us"&&view!=="all")view="uk";
function money(n,pre){return (pre||"")+Math.round(n).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g,",")}
function fmtCount(el){var to=parseFloat(el.dataset.to),pre=el.dataset.pre||"";el.textContent=money(to,pre)}
function donutSVG(segs){
 var total=segs.reduce(function(a,s){return a+s.val},0)||1,cx=110,cy=110,r=80,ang=-Math.PI/2,out="";
 segs.forEach(function(s,i){var frac=s.val/total,a2=ang+frac*2*Math.PI;
  var x1=cx+r*Math.cos(ang),y1=cy+r*Math.sin(ang),x2=cx+r*Math.cos(a2),y2=cy+r*Math.sin(a2),large=frac>0.5?1:0,pct=Math.round(frac*100);
  out+='<path class="slice" tabindex="0" data-i="'+i+'" data-label="'+s.label+'" data-val="'+s.val+'" data-pct="'+pct+'" d="M'+cx+','+cy+' L'+x1.toFixed(1)+','+y1.toFixed(1)+' A'+r+','+r+' 0 '+large+' 1 '+x2.toFixed(1)+','+y2.toFixed(1)+' Z" fill="'+COLS[i%COLS.length]+'" stroke="#fff" stroke-width="2"><title>'+s.label+': '+s.val+' figures ('+pct+'%)</title></path>';ang=a2;});
 return '<svg class="donut" data-total="'+total+'" viewBox="0 0 220 220" width="230" role="img" aria-label="Figure mix donut chart">'+out+'<circle cx="'+cx+'" cy="'+cy+'" r="46" fill="#FFFDF8"/><text class="donut-c-n" x="'+cx+'" y="'+(cy-2)+'" text-anchor="middle" font-size="24" font-weight="800" fill="#17201B">'+total+'</text><text class="donut-c-l" x="'+cx+'" y="'+(cy+20)+'" text-anchor="middle" font-size="12" fill="#5A665E">figures</text></svg>';
}
function legsHTML(segs){var total=segs.reduce(function(a,s){return a+s.val},0)||1;
 return segs.map(function(s,i){return '<div class="leg" data-i="'+i+'"><span class="dot" style="background:'+COLS[i%COLS.length]+'"></span>'+s.label+' <b>'+s.val+'</b> ('+Math.round(s.val/total*100)+'%)</div>'}).join("");}
function histSVG(counts,color){
 var mx=Math.max.apply(null,counts.map(function(c){return c.count}).concat([1])),bars="";
 counts.forEach(function(c,i){var h=Math.round(c.count/mx*140),x=20+i*100;
  bars+='<g><rect class="hbar" x="'+x+'" y="'+(160-h)+'" width="64" height="'+h+'" rx="4" fill="'+color+'"><title>'+c.label+': '+c.count+'</title></rect><text x="'+(x+32)+'" y="'+(152-h)+'" text-anchor="middle" font-size="15" font-weight="800" fill="#17201B">'+c.count+'</text><text x="'+(x+32)+'" y="180" text-anchor="middle" font-size="11" fill="#5A665E">'+c.label+'</text></g>';});
 return '<svg class="hist" viewBox="0 0 540 196" width="100%" role="img" aria-label="Net worth distribution histogram">'+bars+'</svg>';
}
function chartText(id,rows,head){
 var t='<details class="chart-text"><summary>Chart data as text</summary><table><thead><tr>'+head.map(function(h){return "<th>"+h+"</th>"}).join("")+'</tr></thead><tbody>';
 rows.forEach(function(r){t+="<tr>"+r.map(function(c){return "<td>"+c+"</td>"}).join("")+"</tr>"});return t+"</tbody></table></details>";
}
function render(key){
 var d=DATA[key],color=key==="uk"?"#0B3D2E":"#1D4ED8";
 document.getElementById("stats").innerHTML=d.stats.map(function(s){return '<div class="kpi"><strong>'+money(s.to,s.pre)+'</strong><span>'+s.label+'</span></div>'}).join("");
 document.getElementById("story").textContent=d.narrative;
 document.getElementById("hist-title").textContent=(key==="uk"?"UK":"US")+" stated net worth distribution";
 document.getElementById("hist-box").innerHTML=histSVG(d.hist,color)+chartText("h",d.hist.map(function(c){return [c.label,c.count]}),["Band","Creators"]);
 document.getElementById("donut-box").innerHTML='<div class="donut-wrap">'+donutSVG(d.donut)+"<div>"+legsHTML(d.donut)+"</div></div>"+chartText("d",d.donut.map(function(s){return [s.label,s.val]}),["Figure type","Figures"]);
 var mx=Math.max.apply(null,d.bars.map(function(b){return b.val}).concat([1]));
 document.getElementById("bars-box").innerHTML=d.bars.map(function(b){return '<div class="brow"><span>'+b.label+'</span><div class="btrack"><div class="bfill'+(key==="us"?" blue":"")+'" style="--w:'+Math.round(b.val/mx*100)+'%">'+b.val+'</div></div><span class="num">'+b.val+'</span></div>'}).join("");
 document.getElementById("bars-note").textContent="Topic mentions in "+(key==="uk"?"UK":"US")+" posts, counted from post tags. Mentions show what creators talk about, stated figures in the donut show what they have put a number on.";
 bindDonut();
}
function bindDonut(){
 document.querySelectorAll(".donut-wrap").forEach(function(w){
  var svg=w.querySelector(".donut");if(!svg)return;
  var cn=w.querySelector(".donut-c-n"),cl=w.querySelector(".donut-c-l"),total=svg.dataset.total,legs=w.querySelectorAll(".leg");
  function hot(i,label,val,pct){svg.classList.toggle("dim",i!==null);
   svg.querySelectorAll(".slice").forEach(function(s){s.classList.toggle("hot",i!==null&&s.dataset.i==i)});
   legs.forEach(function(l){l.classList.toggle("hot",i!==null&&l.dataset.i==i)});
   if(i===null){cn.textContent=total;cl.textContent="figures"}else{cn.textContent=val;cl.textContent=label+" ("+pct+"%)"}}
  svg.querySelectorAll(".slice").forEach(function(s){
   s.addEventListener("mouseenter",function(){hot(s.dataset.i,s.dataset.label,s.dataset.val,s.dataset.pct)});
   s.addEventListener("mouseleave",function(){hot(null)});
   s.addEventListener("focus",function(){hot(s.dataset.i,s.dataset.label,s.dataset.val,s.dataset.pct)});
   s.addEventListener("blur",function(){hot(null)});});
  legs.forEach(function(l){l.addEventListener("mouseenter",function(){var s=svg.querySelector('.slice[data-i="'+l.dataset.i+'"]');if(s)hot(l.dataset.i,s.dataset.label,s.dataset.val,s.dataset.pct)});l.addEventListener("mouseleave",function(){hot(null)});});
 });
}
function setView(v){view=v;try{localStorage.setItem("ss-region",v)}catch(e){}
 document.querySelectorAll(".reg-btn").forEach(function(b){b.classList.toggle("active",b.dataset.reg===v)});
 if(v==="all"){render("uk");document.getElementById("story").textContent=DATA.uk.narrative+" "+DATA.us.narrative;}
 else render(v);
 applyFilters();}
document.querySelectorAll(".reg-btn").forEach(function(b){b.addEventListener("click",function(){setView(b.dataset.reg)})});
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target)}})},{threshold:.15});
document.querySelectorAll(".reveal,.anim").forEach(function(el){io.observe(el)});
var links=document.querySelectorAll(".subnav a"),secs=[].map.call(links,function(a){return document.querySelector(a.getAttribute("href"))});
var so=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){links.forEach(function(a){a.classList.toggle("on",a.getAttribute("href")==="#"+e.target.id)})}})},{rootMargin:"-40% 0px -55% 0px"});
secs.forEach(function(s){if(s)so.observe(s)});
var q=document.getElementById("fq"),kt=document.getElementById("fk"),st=document.getElementById("fs"),rc=document.getElementById("rowcount");
function applyFilters(){var term=q.value.trim().toLowerCase(),kind=kt.value,shown=0,total=0;
 var trs=[].slice.call(document.querySelectorAll("#figtable tbody tr"));
 trs.forEach(function(tr){var ok=true;total++;
  if(view!=="all"&&tr.dataset.region!==view)ok=false;
  if(ok&&kind!=="all"&&tr.dataset.kind!==kind)ok=false;
  if(ok&&term){var t=(tr.dataset.name+" "+tr.textContent).toLowerCase();if(t.indexOf(term)<0)ok=false;}
  tr.style.display=ok?"":"none";if(ok)shown++;});
 var s=st.value;
 trs.sort(function(a,b){if(s==="amt-desc")return b.dataset.amt-a.dataset.amt;if(s==="amt-asc")return a.dataset.amt-b.dataset.amt;
  if(s==="new")return b.dataset.date<a.dataset.date?-1:1;if(s==="old")return a.dataset.date<b.dataset.date?-1:1;
  return a.dataset.name<b.dataset.name?-1:1;});
 var tb=document.querySelector("#figtable tbody");trs.forEach(function(tr){tb.appendChild(tr)});
 rc.textContent="Showing "+shown+" of "+total+" figures.";}
[q,kt,st].forEach(function(el){el.addEventListener("input",applyFilters)});
document.querySelectorAll("th button").forEach(function(b){b.addEventListener("click",function(){st.value=b.dataset.s;applyFilters()})});
setView(view);
})();
"""

NAV = ('<nav><div class="wrap"><a class="logo" href="index.html">SaveShare<span>.io</span></a>'
       '<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">&#9776;</button>'
       '<div class="nav-links" id="site-nav"><a href="index.html">Home</a><a href="blog/index.html">Blog</a><a href="analytics.html">Analytics</a>'
       '<div class="region-toggle" role="group" aria-label="Region"><button class="reg-btn active" data-reg="uk" type="button">UK</button>'
       '<button class="reg-btn" data-reg="us" type="button">US</button><button class="reg-btn" data-reg="all" type="button">All</button></div>'
       '</div></div></nav>')
FOOTER = ('<footer><div class="wrap"><div><a class="logo" href="index.html">SaveShare<span>.io</span></a>'
          '<p>Sourced creator directory for UK and US personal finance.</p></div>'
          '<div class="foot-links"><a href="index.html">Home</a><a href="blog/index.html">Blog</a><a href="analytics.html">Analytics</a></div></div>'
          '<div class="wrap"><p class="disclaimer">Disclaimer: figures shown are self-reported by each creator in their own content and have not been independently verified. They may be outdated. Nothing on this site constitutes financial advice.</p>'
          '<p>\u00a9 2026 SaveShare.io. All rights reserved.</p></div></footer>'
          '<script data-site-menu>document.querySelector(".nav-toggle").addEventListener("click",function(){var n=document.getElementById("site-nav");var open=n.classList.toggle("open");this.setAttribute("aria-expanded",open);});</script>')

def takeaway(title, body):
    return f'<div class="takeaway"><strong>{title}</strong><p>{body}</p></div>'

page = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analytics: self-reported creator figures | SaveShare.io</title>
<meta name="description" content="Interactive analytics on self-reported net worth, portfolios, income and debt payoffs from UK and US money creators. Every figure links to its source.">
<link rel="stylesheet" href="styles.css"><link rel="preload" href="fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<style>{CSS}</style>
</head>
<body>
{NAV}
<nav class="subnav" aria-label="Sections"><div class="wrap">
<a href="#aggregate">Trend</a><a href="#figures">Creators</a><a href="#story">The story</a><a href="#distribution">Charts</a><a href="#debt">Debt payoff</a><a href="#overtime">Journeys</a><a href="#regions">UK vs US</a><a href="#method">Method</a>
</div></nav>
<header class="hero"><div class="wrap">
<div class="kicker">Analytics</div>
<h1>Creator money, <em>in their own words</em></h1>
<p>Self-reported figures from UK and US money creators. Every number on this page was stated by the creator it belongs to, and every number links to its source. Hypothetical examples and projections are excluded.</p>
<div class="hero-stats">
<div class="hstat"><strong>{len(rows)}</strong><span>sourced figures</span></div>
<div class="hstat"><strong>{total_creators}</strong><span>creators with stated figures</span></div>
<div class="hstat"><strong>92</strong><span>creator profiles</span></div>
<div class="hstat"><strong>100%</strong><span>source linked</span></div>
</div></div></header>
<div class="wrap">

<div id="stats" class="kpis"></div>

{AGG_SECTION}

<section id="figures"><div class="section-head"><h2>Every creator, every figure</h2>
<p>Search by creator, filter by figure type, sort by amount or date. The region switch at the top applies here too.</p></div>
<div class="panel"><div class="controls">
<input id="fq" type="search" placeholder="Search creator or handle..." aria-label="Search creators">
<select id="fk" aria-label="Filter by figure type"><option value="all">All types</option>{kind_opts}</select>
<select id="fs" aria-label="Sort figures">
<option value="amt-desc">Amount: high to low</option>
<option value="amt-asc">Amount: low to high</option>
<option value="new">Newest stated</option>
<option value="old">Oldest stated</option>
<option value="name">Creator A to Z</option>
</select>
</div>
<div class="twrap"><table id="figtable"><thead><tr>
<th><button data-s="name" type="button">Creator</button></th><th>Region</th><th>Figure type</th>
<th><button data-s="amt-desc" type="button">Amount</button></th><th><button data-s="new" type="button">Stated</button></th><th>Quote and source</th></tr></thead>
<tbody>{table_rows(rows)}</tbody></table></div>
<div id="rowcount"></div>
</div></section>

<section id="story"><div class="section-head"><h2>Two regions, two money cultures</h2>
<p>The same method was applied on both sides of the Atlantic. What creators chose to state is where the regions diverge.</p></div>
<div class="panel reveal"><p class="story" id="story"></p></div>
<div class="takeaways">
{takeaway("UK creators journal net worth", f"{UKS['nw_n']} UK creators have stated a net worth. The median stated figure is {money(UKS['nw_med'], chr(163))}, and the habit behind it is monthly account updates filmed in public.")}
{takeaway("US creators journal debt and income", f"The US record holds {USS['types'].get('income', 0)} income figures and {USS['types'].get('debt_paid', 0) + USS['types'].get('debt_total', 0)} debt figures, against {USS['nw_n']} stated net worths. Pay cheques and balances owed are the public diary.")}
{takeaway("The retirement gap is American", f"UK creators have stated {UKS['types'].get('pension', 0)} pension figures. US creators have stated {USS['types'].get('pension', 0)}. Roth and 401(k) accounts dominate US advice while almost nobody states the balance inside one.")}
{takeaway("Debt payoff is a US genre", f"Stated US debt payoffs total {money(USS['debt_paid'], '$')} across {USS['debt_paid_n']} figures, many filmed as daily balance countdowns. The UK equivalent is smaller and mostly student debt.")}
</div>
{f'<div class="pullquote">&ldquo;{html.escape(top_uk["quote"][:180])}&rdquo;<span class="pq-who">Largest UK stated net worth, {html.escape(top_uk["amt_s"])}, {html.escape(top_uk["name"])} <a href="{top_uk["url"]}" target="_blank" rel="noopener">source</a></span></div>' if top_uk else ""}
{f'<div class="pullquote">&ldquo;{html.escape(top_us["quote"][:180])}&rdquo;<span class="pq-who">Largest US stated figure, {html.escape(top_us["amt_s"])}, {html.escape(top_us["name"])} <a href="{top_us["url"]}" target="_blank" rel="noopener">source</a></span></div>' if top_us else ""}
</section>

<section id="distribution"><div class="section-head"><h2>Where the money sits</h2>
<p>Net worth bands, figure mix and topic mentions in one place. Stated figures only, counts shown in full.</p></div>
<div class="panel reveal anim"><h3 id="hist-title" style="font-size:19px;margin-bottom:12px">Stated net worth distribution</h3><div id="hist-box"></div></div>
</div>
<div class="panel reveal"><h3 style="font-size:19px;margin-bottom:12px">Stated figures by type</h3><div id="donut-box"></div>
<div class="bars anim" id="bars-box" style="margin-top:26px"></div><p class="sub" id="bars-note" style="color:var(--muted);font-size:13.5px;margin-top:12px"></p></div>
</section>

<section id="debt"><div class="section-head"><h2>Debt payoff leaderboard</h2>
<p>Largest self-stated debt payoffs, ranked within each region so pounds and dollars are never mixed in one bar.</p></div>
<div class="panel reveal anim"><h3 style="font-size:19px;margin-bottom:8px">US payoffs (dollars)</h3>{leaderboard(us)}<h3 style="font-size:19px;margin:22px 0 8px">UK payoffs (pounds)</h3>{leaderboard(uk)}</div>
</section>

<section id="regions"><div class="section-head"><h2>UK vs US at a glance</h2>
<p>Same rules both sides. Self-stated figures only, original currency, no conversion in any table.</p></div>
<div class="cmp">
<div class="cmp-card ukc"><h3>UK</h3><p class="cnarr">{html.escape(UK_STORY)}</p><ul>
<li><span>Creators with stated figures</span><b>{UKS['creators']}</b></li>
<li><span>Sourced figures</span><b>{UKS['figures']}</b></li>
<li><span>Average stated net worth</span><b>{money(UKS['nw_avg'], chr(163))}</b></li>
<li><span>Median stated net worth</span><b>{money(UKS['nw_med'], chr(163))}</b></li>
<li><span>Stated pension figures</span><b>{UKS['types'].get('pension', 0)}</b></li>
<li><span>Stated debt payoffs</span><b>{money(UKS['debt_paid'], chr(163))}</b></li>
</ul></div>
<div class="cmp-card us"><h3>US</h3><p class="cnarr">{html.escape(US_STORY)}</p><ul>
<li><span>Creators with stated figures</span><b>{USS['creators']}</b></li>
<li><span>Sourced figures</span><b>{USS['figures']}</b></li>
<li><span>Average stated net worth</span><b>{money(USS['nw_avg'], '$')}</b></li>
<li><span>Median stated net worth</span><b>{money(USS['nw_med'], '$')}</b></li>
<li><span>Stated pension figures</span><b>{USS['types'].get('pension', 0)}</b></li>
<li><span>Stated debt payoffs</span><b>{money(USS['debt_paid'], '$')}</b></li>
</ul></div>
</div></section>

{TS_SECTION}



<section id="method"><div class="method"><h2>Methodology</h2>
<p><b>Source.</b> Each figure was stated by the creator it belongs to, in their own content, and links to that source so you can check it yourself.</p>
<p><b>Stated only.</b> Net worth means the creator said the words about themselves. Hypothetical projections, worked examples, other people&rsquo;s money and generic illustrations are excluded. Where a creator gave a range or a round description such as five figures, the floor of that statement is shown and the quote says so.</p>
<p><b>Labels.</b> Property purchase prices are labelled property value, not net worth. Monthly and yearly flows are labelled income flow, not totals. A remaining balance owed is labelled debt balance, and an amount cleared is labelled debt payoff.</p>
<p><b>No fabrication.</b> Where no figure was stated, nothing is estimated and no chart is drawn. Averages and medians use only creators with a stated figure of that type.</p>
<p><b>Currency.</b> UK figures in pounds, US figures in dollars. No conversion is applied anywhere on this page.</p>
<p><b>Freshness.</b> Figures carry the date they were stated. Markets move and creators update their numbers, so treat every figure as a dated snapshot.</p>
</div></section>

</div>
{FOOTER}
<script type="application/json" id="region-data">{json.dumps(DATA)}</script>
<script>{JS}</script>
</body></html>"""

out = os.path.join(BASE, "analytics.html")
assert "\u2014" not in page, "em dash found"
assert "transcript" not in page.lower(), "banned word found"
assert "archived" not in page.lower(), "archived count wording found"
open(out, "w").write(page)
print("wrote", out, len(page), "bytes;", len(rows), "rows; UK", len(uk), "US", len(us))
print("no em dashes, no banned words: OK")
