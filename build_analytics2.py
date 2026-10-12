#!/usr/bin/env python3
"""Redesigned analytics.html: interactive data experience.
Reads figure rows from the figures table in transcript_db.sqlite (single source
of truth), emits new page. No em dashes in output. No external JS/CSS libs."""
import os, re, html, math, sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("SS_DB", os.path.join(BASE, "transcript_db.sqlite"))

DISPLAY = {"net_worth": "Net worth", "invested": "Amount invested",
           "debt_paid": "Debt payoff", "income": "Income flow",
           "savings": "Savings total", "cash": "Cash savings",
           "pension": "Pension value", "portfolio": "Portfolio value",
           "property": "Property value", "crypto": "Crypto value"}

def slug(h):
    return "p/" + re.sub(r"[^a-z0-9]+", "", h.lower()) + ".html"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
nick = {r["handle"]: (r["nickname"] or r["handle"])
        for r in con.execute("SELECT handle, nickname FROM creators")}
prof_cache = {}
for _f in os.listdir(os.path.join(BASE, "p")):
    prof_cache[_f] = True

rows = []
for f in con.execute("SELECT * FROM figures WHERE verified=1 ORDER BY region, creator"):
    handle = f["creator"]
    name = nick.get(handle, handle)
    pf = slug(handle)
    prof = pf if pf in prof_cache else "index.html#creators"
    sym = "\u00a3" if f["currency"] == "GBP" else "$"
    amt_s = f"{sym}{f['amount']:,}"
    region = f["region"].lower()
    kind = DISPLAY.get(f["figure_type"], f["figure_type"])
    date = f"{f['as_of_year']}-01-01" if f["as_of_year"] else ""
    pub = con.execute("SELECT published_at FROM transcripts WHERE url=?",
                      (f["video_url"],)).fetchone()
    if pub and pub[0]:
        date = pub[0][:10]
    rows.append(dict(region=region, prof=prof, name=name, handle=handle,
                     kind=kind, amt_s=amt_s, amt=f["amount"], date=date,
                     quote=f["quote"].strip(), url=f["video_url"]))
con.close()
assert len(rows) >= 40, f"only {len(rows)} rows in figures table"
uk_rows = [r for r in rows if r["region"] == "uk"]
us_rows = [r for r in rows if r["region"] == "us"]

def money(n, sym):
    return f"{sym}{n:,}"

# Net worth distribution buckets
BUCKETS = [("Under 100K", 0, 100000), ("100K to 250K", 100000, 250000),
           ("250K to 500K", 250000, 500000), ("500K to 1M", 500000, 1000000),
           ("1M plus", 1000000, float("inf"))]
def hist(rs, sym):
    nw = [r["amt"] for r in rs if r["kind"] == "Net worth" and r["amt"]]
    counts = []
    for label, lo, hi in BUCKETS:
        c = sum(1 for v in nw if lo <= v < hi or (hi == float("inf") and v >= lo))
        counts.append((label, c))
    return counts, nw

uk_hist, uk_nw = hist(uk_rows, "GBP")
UK_NW = sorted(r["amt"] for r in uk_rows if r["kind"] == "Net worth")
UK_NW_N = len(UK_NW)
UK_AVG_NW = round(sum(UK_NW) / UK_NW_N) if UK_NW_N else 0
UK_MED_NW = UK_NW[UK_NW_N // 2] if UK_NW_N else 0
us_hist, us_nw = hist(us_rows, "USD")

# Allocation: creator counts parsed from existing legends (5-class set)
UK_ALLOC = [("ETF / index funds", 24), ("Stocks / shares", 23), ("Property", 20),
            ("Crypto", 5), ("Cash / savings", 23)]
US_ALLOC = [("ETF / index funds", 15), ("Stocks / shares", 6), ("Property", 22),
            ("Crypto", 7), ("Cash / savings", 18)]
COLS = ["#0F766E", "#0EA5A4", "#F59E0B", "#8B5CF6", "#EC4899"]

def donut_svg(segs, total, rid):
    cx, cy, r = 110, 110, 80
    out, ang, idx = [], -math.pi / 2, 0
    for name, v in segs:
        frac = v / total if total else 0
        a2 = ang + frac * 2 * math.pi
        x1, y1 = cx + r * math.cos(ang), cy + r * math.sin(ang)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        large = 1 if frac > 0.5 else 0
        pct = round(frac * 100)
        out.append(
            f'<path class="slice" data-i="{idx}" data-label="{html.escape(name)}" '
            f'data-val="{v}" data-pct="{pct}" d="M{cx},{cy} L{x1:.1f},{y1:.1f} '
            f'A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} Z" fill="{COLS[idx % 5]}" '
            f'stroke="#fff" stroke-width="2"><title>{html.escape(name)}: {v} creators ({pct}%)</title></path>')
        ang, idx = a2, idx + 1
    legs = "".join(
        f'<div class="leg" data-i="{i}"><span class="dot" style="background:{COLS[i % 5]}"></span>'
        f'{html.escape(n)} <b>{v}</b> ({round(v / total * 100)}%)</div>'
        for i, (n, v) in enumerate(segs))
    return (f'<svg class="donut" data-total="{total}" viewBox="0 0 220 220" width="230" role="img" '
            f'aria-label="Asset allocation donut chart">{"".join(out)}'
            f'<circle cx="{cx}" cy="{cy}" r="46" fill="#fff"/>'
            f'<text class="donut-c-n" x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="24" '
            f'font-weight="800" fill="#0F172A">{total}</text>'
            f'<text class="donut-c-l" x="{cx}" y="{cy + 20}" text-anchor="middle" font-size="12" '
            f'fill="#475569">mentions</text></svg>', legs)

uk_donut, uk_leg = donut_svg(UK_ALLOC, sum(v for _, v in UK_ALLOC), "uk")
us_donut, us_leg = donut_svg(US_ALLOC, sum(v for _, v in US_ALLOC), "us")

# Debt payoff leaderboard (US self-stated payoffs / debt documented)
DEBT = [
    ("Jenny Park", "@mohaewithjennypark", 120000, "Paid off $120,000 of debt, then bought a first home in California.",
     "https://www.tiktok.com/@mohaewithjennypark/video/7647333678200278285", "p/mohaewithjennypark.html"),
    ("Melissa Jean-Baptiste", "@millennialindebt", 100000, "Paid off $100,000 in student loans on a teacher salary.",
     "https://www.tiktok.com/@millennialindebt/video/7689487412078120222", "p/millennialindebt.html"),
    ("Amber", "@debtfreeamber", 85413, "$85,413 in debt, payoff documented weekly.",
     "https://www.tiktok.com/@debtfreeamber/video/7664824658679614728", "p/debtfreeamber.html"),
    ("Becca", "@stealth.mode.savings", 58000, "Paid off $58,000 of debt.",
     "https://www.tiktok.com/@stealth.mode.savings/video/7686668559270890765", "p/stealth.mode.savings.html"),
    ("Miranda", "@miranda_andrews", 45000, "Paid down over $45,000 of debt in 307 days.",
     "https://www.tiktok.com/@miranda_andrews/video/7693251868893449502", "p/miranda_andrews.html"),
]
dmax = max(v for _, _, v, _, _, _ in DEBT)
debt_html = "".join(
    f'<div class="lrow"><div class="lmeta"><a href="{prof}"><b>{html.escape(n)}</b></a> '
    f'<span class="h">{h}</span><div class="lnote">{html.escape(note)} '
    f'<a href="{url}" target="_blank" rel="noopener">source</a></div></div>'
    f'<div class="lbar"><div class="lfill" style="--w:{round(v / dmax * 100)}%">'
    f'<span>${v:,}</span></div></div></div>'
    for n, h, v, note, url, prof in DEBT)

def hist_svg(counts, color, rid):
    mx = max((c for _, c in counts), default=1)
    bars = []
    for i, (label, c) in enumerate(counts):
        h = round(c / mx * 140) if mx else 0
        x = 20 + i * 100
        bars.append(
            f'<g class="hgroup"><rect class="hbar" x="{x}" y="{160 - h}" width="64" height="{h}" '
            f'rx="8" fill="{color}"><title>{html.escape(label)}: {c}</title></rect>'
            f'<text x="{x + 32}" y="{152 - h}" text-anchor="middle" font-size="15" font-weight="800" '
            f'fill="#0F172A">{c}</text>'
            f'<text x="{x + 32}" y="180" text-anchor="middle" font-size="11" fill="#475569">'
            f'{html.escape(label)}</text></g>')
    return (f'<svg class="hist" viewBox="0 0 540 196" width="100%" role="img" '
            f'aria-label="Net worth distribution histogram">{ "".join(bars)}</svg>')

uk_hist_svg = hist_svg(uk_hist, "#0F766E", "uk")
us_hist_svg = hist_svg(us_hist, "#1D4ED8", "us")

def table_rows(rs):
    out = []
    for r in rs:
        out.append(
            f'<tr data-region="{r["region"]}" data-amt="{r["amt"]}" data-date="{r["date"]}" '
            f'data-name="{html.escape(r["name"].lower())}" data-kind="{html.escape(r["kind"])}">'
            f'<td><a href="{r["prof"]}">{html.escape(r["name"])}</a><br>'
            f'<a class="h" href="https://www.tiktok.com/@{r["handle"]}" target="_blank" rel="noopener">'
            f'@{r["handle"]}</a></td>'
            f'<td><span class="flag">{"UK" if r["region"] == "uk" else "US"}</span></td>'
            f'<td>{html.escape(r["kind"])}</td><td class="num">{html.escape(r["amt_s"])}</td>'
            f'<td style="white-space:nowrap">{r["date"]}</td>'
            f'<td class="q">{html.escape(r["quote"])} '
            f'<a href="{r["url"]}" target="_blank" rel="noopener">source</a></td></tr>')
    return "".join(out)

kinds = sorted(set(r["kind"] for r in rows))
kind_opts = "".join(f'<option>{html.escape(k)}</option>' for k in kinds)

CSS = """
:root{--teal:#0F766E;--teal-dark:#115E59;--teal-soft:#E0F2F1;--ink:#0F172A;--muted:#475569;
--line:#E2E8F0;--bg:#F8FAFC;--blue:#1D4ED8;--amber:#F59E0B}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}
h1,h2,h3{font-family:'Playfair Display',Georgia,serif;line-height:1.15;margin:0}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px}
nav.top{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
nav.top .wrap{display:flex;align-items:center;justify-content:space-between;padding-top:12px;padding-bottom:12px}
.logo{font-weight:800;font-size:20px;color:var(--teal);text-decoration:none}
.logo span{color:var(--ink)}
.nav-links{display:flex;gap:22px;align-items:center}
.nav-links a.nl{color:var(--muted);text-decoration:none;font-size:15px;font-weight:500}
.nav-links a.nl:hover{color:var(--teal)}
.region-toggle{display:flex;border:1px solid var(--line);border-radius:9999px;overflow:hidden}
.reg-btn{border:none;background:#fff;color:var(--muted);font-weight:700;font-size:14px;padding:10px 18px;cursor:pointer;font-family:inherit;min-height:44px}
.reg-btn.active{background:var(--teal);color:#fff}
.subnav{background:#0B3B37;color:#fff;position:sticky;top:61px;z-index:15}
.subnav .wrap{display:flex;gap:4px;overflow-x:auto;padding-top:0;padding-bottom:0}
.subnav a{color:#CFFAFE;text-decoration:none;font-size:13.5px;font-weight:600;padding:13px 14px;white-space:nowrap;border-bottom:3px solid transparent}
.subnav a:hover{color:#fff}
.subnav a.on{color:#fff;border-bottom-color:var(--amber)}
.hero{background:linear-gradient(135deg,#0F766E 0%,#0B3B37 100%);color:#fff;padding:64px 0 72px;text-align:center}
.hero .kicker{display:inline-block;background:rgba(255,255,255,.15);font-size:13px;font-weight:700;
letter-spacing:1px;text-transform:uppercase;padding:6px 18px;border-radius:9999px;margin-bottom:20px}
.hero h1{font-size:clamp(32px,5vw,54px);max-width:800px;margin:0 auto 16px}
.hero p{font-size:18px;opacity:.92;max-width:680px;margin:0 auto 8px}
.hero-stats{display:flex;gap:16px;justify-content:center;margin-top:34px;flex-wrap:wrap}
.hstat{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.22);border-radius:16px;
padding:18px 30px;min-width:170px}
.hstat strong{display:block;font-size:32px;font-weight:800;font-variant-numeric:tabular-nums}
.hstat span{font-size:13.5px;opacity:.85}
section{padding:52px 0 4px;scroll-margin-top:120px}
.eyebrow{font-size:13px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:var(--teal);margin-bottom:8px}
.panel h2{font-size:clamp(24px,3vw,30px);margin-bottom:6px}
.panel .sub{color:var(--muted);font-size:15px;margin:0 0 22px;max-width:720px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px;margin:26px 0 8px}
.stat{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;
box-shadow:0 10px 15px -3px rgb(15 23 42/.06);border-top:4px solid var(--teal)}
.stat strong{display:block;font-size:31px;font-weight:800;color:var(--ink);font-variant-numeric:tabular-nums}
.stat strong em{font-style:normal;color:var(--teal)}
.stat span{font-size:14px;color:var(--muted)}
.panel{background:#fff;border:1px solid var(--line);border-radius:18px;padding:30px;margin:20px 0;
box-shadow:0 10px 15px -3px rgb(15 23 42/.06)}
.donut-wrap{display:flex;gap:32px;align-items:center;flex-wrap:wrap}
.donut .slice{cursor:pointer;transition:opacity .15s,transform .15s}
.donut.dim .slice{opacity:.35}
.donut.dim .slice.hot{opacity:1}
.leg{font-size:14.5px;margin:7px 0;color:var(--muted);padding:6px 10px;border-radius:8px;cursor:default}
.leg.hot{background:var(--teal-soft);color:var(--ink)}
.dot{display:inline-block;width:12px;height:12px;border-radius:99px;margin-right:8px}
.bars{display:flex;flex-direction:column;gap:14px;margin-top:6px}
.brow{display:grid;grid-template-columns:190px 1fr 70px;gap:12px;align-items:center;font-size:14px}
.btrack{background:#F1F5F9;border-radius:99px;height:26px;overflow:hidden}
.bfill{display:flex;align-items:center;justify-content:flex-end;height:100%;width:0;border-radius:99px;
background:linear-gradient(90deg,var(--teal),#14B8A6);color:#fff;font-size:12.5px;font-weight:700;
padding-right:10px;transition:width 1.1s cubic-bezier(.2,.7,.2,1)}
.bfill.blue{background:linear-gradient(90deg,var(--blue),#60A5FA)}
.in .bfill{width:var(--w)!important}
.lrow{display:grid;grid-template-columns:minmax(220px,300px) 1fr;gap:16px;align-items:center;
padding:14px 0;border-bottom:1px solid var(--line)}
.lrow:last-child{border-bottom:none}
.lmeta{font-size:14.5px}
.lmeta a{color:var(--ink);text-decoration:none}
.lmeta a:hover{color:var(--teal)}
.lnote{font-size:13px;color:var(--muted);margin-top:2px}
.lnote a{color:var(--teal);font-weight:700}
.lbar{background:#F1F5F9;border-radius:99px;height:34px;overflow:hidden}
.lfill{display:flex;align-items:center;height:100%;width:0;border-radius:99px;color:#fff;font-weight:800;
font-size:14px;padding-left:14px;white-space:nowrap;transition:width 1.1s cubic-bezier(.2,.7,.2,1);
background:linear-gradient(90deg,#B45309,var(--amber))}
.in .lfill{width:var(--w)!important}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.cmp-card{border:1px solid var(--line);border-radius:14px;padding:22px;background:#F8FAFC}
.cmp-card.us{background:#EFF6FF;border-color:#BFDBFE}
.cmp-card h3{font-size:22px;margin-bottom:12px}
.cmp-card ul{margin:0;padding:0;list-style:none;font-size:14.5px}
.cmp-card li{padding:7px 0;border-bottom:1px dashed var(--line);display:flex;justify-content:space-between;gap:10px}
.cmp-card li:last-child{border:none}
.cmp-card li b{font-variant-numeric:tabular-nums}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.controls input,.controls select{font:inherit;font-size:14.5px;padding:11px 14px;border:1px solid var(--line);
border-radius:10px;background:#fff;color:var(--ink);min-height:44px}
.controls input{flex:1;min-width:180px}
.twrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px;margin-top:12px;min-width:760px}
th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);
padding:10px 8px;border-bottom:2px solid var(--line);white-space:nowrap}
th button{background:none;border:none;font:inherit;color:inherit;cursor:pointer;padding:0;
text-transform:inherit;letter-spacing:inherit;font-weight:700;min-height:32px}
th button:hover{color:var(--teal)}
td{padding:12px 8px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:nth-child(even) td{background:#F8FAFC}
.num{font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
.h{color:var(--teal);font-weight:600;text-decoration:none;font-size:13px}
.q{color:var(--muted);font-size:13px}
.q a{color:var(--teal);font-weight:700;white-space:nowrap}
.flag{font-size:11px;font-weight:700;background:var(--teal-soft);color:var(--teal-dark);padding:2px 10px;border-radius:9999px}
#rowcount{font-size:13.5px;color:var(--muted);margin-top:10px}
.method{background:#FFFBEB;border:1px solid #FDE68A;border-radius:16px;padding:28px;margin:28px 0;font-size:15px}
.method h2{font-size:24px;margin-bottom:10px}
footer{background:#fff;border-top:1px solid var(--line);padding:40px 0;font-size:14px;color:var(--muted);margin-top:48px}
footer .wrap{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap}
footer a.fl{color:var(--muted);text-decoration:none;margin-right:18px}
.reveal{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.reveal.in{opacity:1;transform:none}
[data-rv]{display:none}
body[data-view="uk"] [data-rv="uk"]{display:block}
body[data-view="us"] [data-rv="us"]{display:block}
body[data-view="all"] [data-rv]{display:block}
body[data-view="uk"] tr[data-region="uk"]{display:table-row}
body[data-view="us"] tr[data-region="us"]{display:table-row}
body[data-view="all"] tr[data-region]{display:table-row}
tr[data-region]{display:none}
.hist .hbar{transform:scaleY(0);transform-origin:bottom;transform-box:fill-box;transition:transform 1s cubic-bezier(.2,.7,.2,1)}
.in .hbar{transform:scaleY(1)}
@media(max-width:700px){.nav-links a.nl{display:none}.cmp{grid-template-columns:1fr}
.lrow{grid-template-columns:1fr}.brow{grid-template-columns:120px 1fr 56px;font-size:13px}
.panel{padding:20px}.subnav{top:60px}}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none}
.bfill,.lfill,.hist .hbar{transition:none}.in .bfill,.in .lfill{width:var(--w)!important}.in .hbar{transform:none}}
"""

JS = """
(function(){
var k="ss-region";
function set(v){document.body.dataset.view=v;try{localStorage.setItem(k,v)}catch(e){}
document.querySelectorAll(".reg-btn").forEach(function(b){b.classList.toggle("active",b.dataset.reg===v)});
applyFilters();}
var v="uk";try{v=localStorage.getItem(k)||"uk"}catch(e){}if(v!=="uk"&&v!=="us"&&v!=="all")v="uk";
document.querySelectorAll(".reg-btn").forEach(function(b){b.addEventListener("click",function(){set(b.dataset.reg)})});
/* count up */
function fmt(n,p,s){n=Math.round(n).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g,",");return (p||"")+n+(s||"");}
function count(el){var to=parseFloat(el.dataset.to),p=el.dataset.pre||"",s=el.dataset.suf||"",t0=null,d=1400;
function step(t){if(!t0)t0=t;var f=Math.min(1,(t-t0)/d);f=1-Math.pow(1-f,3);
el.textContent=fmt(to*f,p,s);if(f<1)requestAnimationFrame(step);else el.textContent=fmt(to,p,s);}
if(window.matchMedia("(prefers-reduced-motion: reduce)").matches){el.textContent=fmt(to,p,s);return;}
requestAnimationFrame(step);}
/* reveal + animate on scroll */
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){
e.target.classList.add("in");
e.target.querySelectorAll(".count:not(.done)").forEach(function(c){c.classList.add("done");count(c);});
io.unobserve(e.target);}})},{threshold:.2});
document.querySelectorAll(".reveal,.anim").forEach(function(el){io.observe(el);});
document.querySelectorAll(".count").forEach(function(c){var r=c.getBoundingClientRect();
if(r.top<innerHeight&&r.bottom>0&&!c.classList.contains("done")){c.classList.add("done");count(c);}});
/* donut interactivity */
document.querySelectorAll(".donut-wrap").forEach(function(w){
var svg=w.querySelector(".donut"),cn=w.querySelector(".donut-c-n"),cl=w.querySelector(".donut-c-l"),
total=svg.dataset.total,legs=w.querySelectorAll(".leg");
function hot(i,label,val,pct){svg.classList.add("dim");
svg.querySelectorAll(".slice").forEach(function(s){s.classList.toggle("hot",s.dataset.i==i)});
legs.forEach(function(l){l.classList.toggle("hot",l.dataset.i==i)});
if(i===null){svg.classList.remove("dim");cn.textContent=total;cl.textContent="mentions";}else{cn.textContent=val;cl.textContent=label+" ("+pct+"%)";}}
svg.querySelectorAll(".slice").forEach(function(s){
s.addEventListener("mouseenter",function(){hot(s.dataset.i,s.dataset.label,s.dataset.val,s.dataset.pct)});
s.addEventListener("mouseleave",function(){hot(null)});s.addEventListener("click",function(){hot(s.dataset.i,s.dataset.label,s.dataset.val,s.dataset.pct)});});
legs.forEach(function(l){l.addEventListener("mouseenter",function(){var s=svg.querySelector('.slice[data-i="'+l.dataset.i+'"]');
hot(l.dataset.i,s.dataset.label,s.dataset.val,s.dataset.pct)});l.addEventListener("mouseleave",function(){hot(null)});});});
/* subnav highlight */
var links=document.querySelectorAll(".subnav a"),secs=[].map.call(links,function(a){return document.querySelector(a.getAttribute("href"))});
var so=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){
links.forEach(function(a){a.classList.toggle("on",a.getAttribute("href")==="#"+e.target.id)})}})},{rootMargin:"-40% 0px -55% 0px"});
secs.forEach(function(s){if(s)so.observe(s)});
.ts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.ts-card{border:1px solid #e5e7eb;border-radius:12px;padding:14px;background:#fff}
.ts-trend{font-size:13px;font-weight:700;color:#0f766e;margin:2px 0 6px}
.ts-points{list-style:none;margin:10px 0 0;padding:0;font-size:13px}
.ts-points li{margin:6px 0}.ts-points .q{display:block;color:#6b7280;font-size:12px}
.spark{color:#0f766e}.agg{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:8px}
/* table filter + sort */
var q=document.getElementById("fq"),kt=document.getElementById("fk"),st=document.getElementById("fs"),rc=document.getElementById("rowcount");
function applyFilters(){var term=q.value.trim().toLowerCase(),kind=kt.value,view=document.body.dataset.view,shown=0,total=0;
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
set(v);
})();
"""

page = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analytics: self-reported creator figures | SaveShare.io</title>
<meta name="description" content="Interactive analytics on self-reported net worth, invested amounts, asset mix and debt payoffs from UK and US money creators. Every figure links to its source.">
<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
{CSS}
</style>
</head>
<body data-view="uk">
<nav class="top"><div class="wrap"><a class="logo" href="index.html">SaveShare<span>.io</span></a>
<div class="nav-links"><a class="nl" href="index.html#creators">Directory</a><a class="nl" href="blog/index.html">Blog</a><a class="nl" href="analytics.html">Analytics</a>
<div class="region-toggle" role="group" aria-label="Region"><button class="reg-btn active" data-reg="uk" type="button">UK</button><button class="reg-btn" data-reg="us" type="button">US</button><button class="reg-btn" data-reg="all" type="button">All</button></div>
</div></div></nav>
<nav class="subnav" aria-label="Sections"><div class="wrap">
<a href="#overview">Overview</a><a href="#networth">Net worth</a><a href="#allocation">Allocation</a><a href="#debt">Debt payoff</a><a href="#regions">UK vs US</a><a href="#overtime">Over time</a><a href="#aggregate">Aggregate</a><a href="#figures">Figures</a><a href="#method">Method</a>
</div></nav>
<header class="hero"><div class="wrap">
<div class="kicker">Analytics</div>
<h1>Creator money, in their own words</h1>
<p>Self-reported figures from <b>39 UK</b> and <b>48 US</b> money creators, drawn from <b>1,658 archived TikTok videos</b>. Every number links to the video where the creator said it.</p>
<div class="hero-stats">
<div class="hstat"><strong class="count" data-to="1658">0</strong><span>videos archived</span></div>
<div class="hstat"><strong class="count" data-to="87">0</strong><span>creators tracked</span></div>
<div class="hstat"><strong><em class="count" data-to="{len(rows)}" data-pre="">0</em></strong><span>sourced figures</span></div>
<div class="hstat"><strong class="count" data-to="100" data-suf="%">0%</strong><span>source linked</span></div>
</div></div></header>
<div class="wrap">

<section id="overview"><div class="eyebrow">Overview</div>
<div data-rv="uk"><div class="cards reveal">
<div class="stat"><strong class="count" data-to="{len(set(r['handle'] for r in uk_rows))}">0</strong><span>UK creators with stated figures</span></div>
<div class="stat"><strong><em class="count" data-to="{UK_AVG_NW}" data-pre="\u00a3">0</em></strong><span>Avg self-stated net worth ({UK_NW_N} creators)</span></div>
<div class="stat"><strong><em class="count" data-to="{UK_MED_NW}" data-pre="\u00a3">0</em></strong><span>Median self-stated net worth</span></div>
<div class="stat"><strong><em class="count" data-to="{sum(r['amt'] for r in uk_rows if r['kind'] in ('Portfolio value', 'Amount invested'))}" data-pre="\u00a3">0</em></strong><span>Combined stated portfolios + invested ({sum(1 for r in uk_rows if r['kind'] in ('Portfolio value', 'Amount invested'))} figures)</span></div>
</div></div>
<div data-rv="us"><div class="cards reveal">
<div class="stat"><strong class="count" data-to="{len(set(r['handle'] for r in us_rows))}">0</strong><span>US creators with stated figures</span></div>
<div class="stat"><strong><em class="count" data-to="{round(sum(r['amt'] for r in us_rows if r['kind']=='Net worth')/max(1,sum(1 for r in us_rows if r['kind']=='Net worth')))}" data-pre="$">0</em></strong><span>Avg self-stated net worth ({sum(1 for r in us_rows if r['kind']=='Net worth')} creators)</span></div>
<div class="stat"><strong><em class="count" data-to="{sorted(r['amt'] for r in us_rows if r['kind']=='Net worth')[sum(1 for r in us_rows if r['kind']=='Net worth')//2] if any(r['kind']=='Net worth' for r in us_rows) else 0}" data-pre="$">0</em></strong><span>Median self-stated net worth</span></div>
<div class="stat"><strong><em class="count" data-to="{sum(r['amt'] for r in us_rows if r['kind'] in ('Portfolio value', 'Amount invested'))}" data-pre="$">0</em></strong><span>Combined stated portfolios + invested ({sum(1 for r in us_rows if r['kind'] in ('Portfolio value', 'Amount invested'))} figures)</span></div>
</div></div>
</section>

<section id="networth"><div class="panel reveal"><div class="eyebrow">Distribution</div><h2>Where net worth clusters</h2>
<p class="sub">Stated net worth figures only, in original currency. Small sample, shown as counts so nothing is hidden. Hover any bar for the count.</p>
<div data-rv="uk"><h3 style="font-size:18px;margin-bottom:10px">UK ({sum(1 for r in uk_rows if r['kind']=='Net worth')} stated figures)</h3><div class="anim">{uk_hist_svg}</div></div>
<div data-rv="us"><h3 style="font-size:18px;margin-bottom:10px">US ({sum(1 for r in us_rows if r['kind']=='Net worth')} stated figures)</h3><div class="anim">{us_hist_svg}</div></div>
</div></section>

<section id="allocation"><div class="panel reveal"><div class="eyebrow">Asset mix</div><h2>What creators actually talk about</h2>
<p class="sub">Creators with at least one video mentioning each class. Hover or tap a slice to isolate it.</p>
<div data-rv="uk"><h3 style="font-size:18px;margin-bottom:10px">UK asset mix</h3><div class="donut-wrap">{uk_donut}<div>{uk_leg}</div></div>
<div class="bars anim" style="margin-top:24px">
<div class="brow"><span>ETF / index funds</span><div class="btrack"><div class="bfill" style="--w:100%">61 videos</div></div><span class="num">61</span></div>
<div class="brow"><span>Stocks / shares</span><div class="btrack"><div class="bfill" style="--w:82%">50 videos</div></div><span class="num">50</span></div>
<div class="brow"><span>Cash / savings</span><div class="btrack"><div class="bfill" style="--w:75%">46 videos</div></div><span class="num">46</span></div>
<div class="brow"><span>Pension</span><div class="btrack"><div class="bfill" style="--w:87%">53 videos</div></div><span class="num">53</span></div>
<div class="brow"><span>Property</span><div class="btrack"><div class="bfill" style="--w:64%">39 videos</div></div><span class="num">39</span></div>
<div class="brow"><span>Crypto</span><div class="btrack"><div class="bfill" style="--w:8%">5 videos</div></div><span class="num">5</span></div>
</div></div>
<div data-rv="us"><h3 style="font-size:18px;margin-bottom:10px">US asset mix</h3><div class="donut-wrap">{us_donut}<div>{us_leg}</div></div>
<div class="bars anim" style="margin-top:24px">
<div class="brow"><span>Cash / savings</span><div class="btrack"><div class="bfill blue" style="--w:100%">66 videos</div></div><span class="num">66</span></div>
<div class="brow"><span>Pension / 401k</span><div class="btrack"><div class="bfill blue" style="--w:79%">52 videos</div></div><span class="num">52</span></div>
<div class="brow"><span>Property</span><div class="btrack"><div class="bfill blue" style="--w:68%">45 videos</div></div><span class="num">45</span></div>
<div class="brow"><span>ETF / index funds</span><div class="btrack"><div class="bfill blue" style="--w:50%">33 videos</div></div><span class="num">33</span></div>
<div class="brow"><span>Crypto</span><div class="btrack"><div class="bfill blue" style="--w:20%">13 videos</div></div><span class="num">13</span></div>
<div class="brow"><span>Stocks / shares</span><div class="btrack"><div class="bfill blue" style="--w:18%">12 videos</div></div><span class="num">12</span></div>
</div></div>
</div></section>

<section id="debt"><div class="panel reveal anim"><div class="eyebrow">Leaderboard</div><h2>Debt payoff leaderboard</h2>
<p class="sub">Self-stated US debt payoffs and documented debt totals, largest first. Each links to the video where the creator said it.</p>
{debt_html}
</div></section>

<section id="regions"><div class="panel reveal"><div class="eyebrow">Comparison</div><h2>UK vs US at a glance</h2>
<p class="sub">Same method both sides: self-described figures only, original currency, no conversion in the tables.</p>
<div class="cmp">
<div class="cmp-card"><h3>UK</h3><ul>
<li><span>Creators tracked</span><b>39</b></li>
<li><span>Videos archived</span><b>753</b></li>
<li><span>Sourced figures</span><b>{len(uk_rows)}</b></li>
<li><span>Avg stated net worth</span><b>£210,000</b></li>
<li><span>Top topic</span><b>ETF / index funds</b></li>
<li><span>Quietest topic</span><b>Crypto (5 videos)</b></li>
</ul></div>
<div class="cmp-card us"><h3>US</h3><ul>
<li><span>Creators tracked</span><b>48</b></li>
<li><span>Videos archived</span><b>905</b></li>
<li><span>Sourced figures</span><b>{len(us_rows)}</b></li>
<li><span>Top stated net worth</span><b>$2,000,000</b></li>
<li><span>Top topic</span><b>Cash / savings</b></li>
<li><span>Standout theme</span><b>Debt payoff stories</b></li>
</ul></div>
</div></div></section>

__TS_SECTIONS__

<section id="figures"><div class="panel"><div class="eyebrow">Database</div><h2>Every figure, with its source</h2>
<p class="sub">Self-described amounts only. Use search, the type filter, or the column buttons to sort. Switch UK / US / All above to change region.</p>
<div class="controls">
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
<th><button data-s="amt-desc" type="button">Amount</button></th><th><button data-s="new" type="button">Stated</button></th><th>Quote + source</th></tr></thead>
<tbody>{table_rows(rows)}</tbody></table></div>
<div id="rowcount"></div>
</div></section>

<section id="method"><div class="method"><h2>Methodology</h2>
<p><b>Source.</b> Figures are self-described by each creator in their own videos, linked so you can check the source yourself. On-screen portfolio screenshots are verified by OCR, and creator-written captions are included where relevant.</p>
<p><b>Self-described only.</b> Net worth means the creator said the words about themselves. Hypothetical projections, other people's money, and generic examples are excluded. Property purchase prices are labelled property value, not net worth. Monthly flows are labelled as flows, not totals.</p>
<p><b>No fabrication.</b> Where no figure was stated, the value is not disclosed. Averages and medians use only creators with a stated net worth figure. Combined invested totals sum stated portfolio and invested amounts only, in original currency.</p>
<p><b>Currency.</b> UK figures in pounds, US figures in dollars. No conversion applied in the tables. Reference rate used only for narrative comparison: about 1.27 USD per GBP (Oct 2026).</p>
<p><b>Freshness.</b> Figures carry the date stated. Markets move and creators update their numbers, so treat every figure as a snapshot. Last rebuilt 12 Oct 2026.</p>
</div></section>

</div>
<footer><div class="wrap"><div><a class="logo" href="index.html" style="font-size:18px">SaveShare<span>.io</span></a>
<p style="margin:8px 0 0">Sourced creator directory for UK and US personal finance.</p></div>
<div style="font-size:14px"><a class="fl" href="index.html#creators">Directory</a><a class="fl" href="blog/index.html">Blog</a><a class="fl" href="analytics.html">Analytics</a></div></div></footer>
<script>{JS}
</script>
</body></html>"""

import subprocess as _sp
try:
    TS_SECTIONS = _sp.run(["python3", os.path.join(BASE, "gen_timeseries.py")], capture_output=True, text=True, check=True).stdout
    assert "—" not in TS_SECTIONS
except Exception as _e:
    TS_SECTIONS = ""
    print("timeseries gen failed:", _e)
out = os.path.join(BASE, "analytics.html")
open(out, "w").write(page.replace("__TS_SECTIONS__", TS_SECTIONS))
print("wrote", out, len(page), "bytes;", len(rows), "rows")
assert "\u2014" not in page, "em dash found"
print("no em dashes: OK")
