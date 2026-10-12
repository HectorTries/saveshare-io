#!/usr/bin/env python3
"""Build saveshare-io/analytics.html from research files + transcript cache.
All figures are self-described by creators. No fabrication: gaps read 'not disclosed'.
No em dashes anywhere in output."""
import os, re, json, statistics, html

BASE = os.path.dirname(os.path.abspath(__file__))
TX = os.path.join(BASE, "transcripts")

# ---- Curated per-creator figures (name, handle, region, kind, amount, ccy, date, quote, url, profile) ----
# kind: net_worth | portfolio | invested | pension | savings | income_flow | property | other
F = [
 ("Tatiana Mamixo","tatianamamixo","UK","net_worth",400000,"GBP","2026-10-03","I have just hit 400,000 pounds net worth. At the start of this year, my net worth was only 282,000 pounds.","https://www.tiktok.com/@tatianamamixo/video/7692357791041719574","p/tatianamamixo.html"),
 ("Tatiana Mamixo","tatianamamixo","UK","pension",140000,"GBP","2026-10-05","As someone who has over 140,000 pounds invested in my pension.","https://www.tiktok.com/@tatianamamixo/video/7693098301448621334","p/tatianamamixo.html"),
 ("James Money Stocker","moneystocker","UK","portfolio",400000,"GBP","2026-10-02","My entire 400,000 pound investment portfolio. Since I started investing 10 years ago, I have grown a portfolio from zero to four hundred thousand pounds.","https://www.tiktok.com/@moneystocker/video/7692114627810872598","p/moneystocker.html"),
 ("James Money Stocker","moneystocker","UK","pension",275000,"GBP","2026-10-02","Workplace pension 182,000 pounds, personal SIPP 37,000 pounds; 3 pensions totalling 275,000 pounds; 3 Stocks and Shares ISAs approx 125,000 pounds.","https://www.tiktok.com/@moneystocker/video/7692114627810872598","p/moneystocker.html"),
 ("Adam Jay","adm.jay","UK","portfolio",290000,"GBP","2026-10-03","Caption: Comment the word ISA and I will send you the full breakdown of my 290k+ portfolio for free.","https://www.tiktok.com/@adm.jay/video/7692411609427348768","p/admjay.html"),
 ("Ben","bensfinance","UK","portfolio",230000,"GBP","2026-10-05","Caption: My portfolio now sitting at 230k in my Stocks and Shares ISA.","https://www.tiktok.com/@bensfinance/video/7693210866501700886","p/bensfinance.html"),
 ("Sophie Blank","itssophieblank","UK","net_worth",230000,"GBP","2026-09-30","I made my first investment of 100 pounds in July 2018. Fast forward 8 years and I have a net worth of 230,000 pounds.","https://www.tiktok.com/@itssophieblank/video/7691210896189771030","p/itssophieblank.html"),
 ("Amy Financially Her","financiallyher_","UK","invested",200000,"GBP","2026-10-02","Caption: How I built 200k+ invested by 26. Started a corporate career on around 30,000 pounds.","https://www.tiktok.com/@financiallyher_/video/7691861996341431585","p/financiallyher.html"),
 ("Mia Rose McGrath","miarosemcgrath","UK","other",100000,"GBP","2026-10-05","I spent over seven years saving 100,000 pounds. (A 200k figure seen in older material is unconfirmed in recent transcripts.)","https://www.tiktok.com/@miarosemcgrath/video/7693085657937218838","p/miarosemcgrath.html"),
 ("Neil Invests","neilinvests","UK","portfolio",194086,"GBP","2026-10-05","On-screen Trading 212 screenshot: account value 194,086.19 pounds, total return 62,185.32 pounds, net deposits 131,900.87 pounds. Caption: New all time high reached in my portfolio.","https://www.tiktok.com/@neilinvests/video/7693266687533092129","p/neilinvests.html"),
 ("Hannah Bevington","hannahbevington","UK","net_worth",135000,"GBP","2026-09-13","I went from having 0 financial awareness at 21 years old to now having 135K at 26 years old. Final breakdown total: 134,706 pounds.","https://www.tiktok.com/@hannahbevington/video/7685007554212138262","p/hannahbevington.html"),
 ("Ciara Curated Wealth","ciara__anne","UK","invested",100000,"GBP","2026-09-17","I went from zero to 100,000 pounds invested in just under five years.","https://www.tiktok.com/@ciara__anne/video/7686551034176589089","p/ciara__anne.html"),
 ("Sean","seansmoney","UK","net_worth",75000,"GBP","2026-09-24","I had nothing saved at that point and now five years later I have around 75,000 pounds saved. That allowed me to build up my overall net worth, my overall invested assets to the 75 thousand pounds.","https://www.tiktok.com/@seansmoney/video/7689003263584193814","p/seansmoney.html"),
 ("Fellas Finance","fellasfinance","UK","pension",70000,"GBP","2026-10-05","A junior pension built from childhood (120 pounds a month plus government top-up), worth 70,000 pounds at age 18.","https://www.tiktok.com/@fellasfinance/video/7693185272552459552","p/fellasfinance.html"),
 ("Fellas Finance","fellasfinance","UK","income_flow",1500,"GBP","2026-10-01","Caption: How I am investing 1,500 pounds in October. (Monthly flow, not a total.)","https://www.tiktok.com/@fellasfinance/video/7691678396190821664","p/fellasfinance.html"),
 ("Krish Kara","krish.kara","UK","pension",37000,"GBP","2026-07-23","I have got 37,000 pounds in my pension, and I am getting it to 100,000 pounds before I turn 30.","https://www.tiktok.com/@krish.kara/video/7665752264383974678","p/krish.kara.html"),
 ("George Tuttle","george_tuttle","UK","invested",30000,"GBP","2026-03-18","I have got over 30,000 pounds invested.","https://www.tiktok.com/@george_tuttle/video/7618649568401444118","p/george_tuttle.html"),
 ("JNO","jno_pwnr","UK","invested",30000,"GBP","2026-09-13","Since then, I have put about 30,000 pounds in the stocks and shares ISA.","https://www.tiktok.com/@jno_pwnr/video/7685090389551844630","p/jno_pwnr.html"),
 ("Rex Everyday Millionaire","theeverydaymillionaire","UK","portfolio",17600,"GBP","2026-09-16","So in total I have got 17,600 pounds. (Was 16,205 pounds on 12 Aug.)","https://www.tiktok.com/@theeverydaymillionaire/video/7686230003293408545","p/theeverydaymillionaire.html"),
 ("Janice Myla","janiice.myla","UK","invested",10000,"GBP","2026-09-20","I left uni with 10,000 pounds in my investment portfolio.","https://www.tiktok.com/@janiice.myla/video/7687687817102740739","p/janiice.myla.html"),
 ("Chris Intentional Finance","intentional.finance","UK","savings",5444,"GBP","2026-10-04","I have 5,444 pounds in savings currently.","https://www.tiktok.com/@intentional.finance/video/7692776884307758358","p/intentional.finance.html"),
 ("Iain Money Insights","iainmoneyinsights","UK","portfolio",94102,"GBP","2024-12-01","Portfolio value is now 94,102 pounds. Portfolio update for November, getting close to that 100k mark. (Older video; newest stated total.)","https://www.tiktok.com/@iainmoneyinsights/video/7578188989362900255","p/iainmoneyinsights.html"),
 ("Ollie Invests","ollieinvests","UK","portfolio",3311,"GBP","2026-10-03","On-screen Trading 212 screenshot: account value 3,310.62 pounds. Holdings: Vanguard FTSE All-World 70%, JPMorgan Global Growth 20%, gold 5%.","https://www.tiktok.com/@ollieinvests/video/7692499806496836886","p/ollieinvests.html"),
 ("Emmie","emmieedit","UK","property",380000,"GBP","2026-10-01","Instead I bought a second hand property for 380,000 pounds. (Property purchase price, not net worth.)","https://www.tiktok.com/@emmieedit/video/7691710068085116182","p/emmieedit.html"),
 # US
 ("Jeremy Schneider Personal Finance Club","personalfinanceclub","US","invested",3000000,"USD","2026-04-01","I have about 3 million dollars invested in the stock market.","https://www.tiktok.com/@personalfinanceclub/video/7499862112387206442","p/personalfinanceclub.html"),
 ("Tori Dunlap Her First 100K","herfirst100k","US","net_worth",2000000,"USD","2026-09-25","I am Tori Dunlap. I am a multi millionaire. (Self-described multi-millionaire; shown as 2M+ floor.)","https://www.tiktok.com/@herfirst100k/video/7690359849581858078","p/herfirst100k.html"),
]

KIND_LABEL = {"net_worth":"Net worth","portfolio":"Portfolio value","invested":"Amount invested","pension":"Pension value","savings":"Cash savings","income_flow":"Monthly investing flow","property":"Property value","other":"Savings milestone"}

def totals(rows, kinds):
    vals = [r[4] for r in rows if r[3] in kinds and r[4] and r[3] != "income_flow"]
    vals = sorted(vals)
    n = len(vals)
    if not n: return dict(n=0)
    med = vals[n//2] if n % 2 else (vals[n//2-1]+vals[n//2])/2
    return dict(n=n, total=sum(vals), avg=sum(vals)/n, med=med, mx=max(vals), mn=min(vals))

uk = [r for r in F if r[2]=="UK"]
us = [r for r in F if r[2]=="US"]
uk_c = sorted(set(r[1] for r in uk)); us_c = sorted(set(r[1] for r in us))
uk_nw = totals(uk, {"net_worth"})
us_nw = totals(us, {"net_worth"})
uk_inv = totals(uk, {"portfolio","invested"})
us_inv = totals(us, {"portfolio","invested"})

# asset mention sweep
import subprocess
pats = [("ETF / index funds","ETF|index fund|S&P 500|FTSE All|all-world|all world|VUAG|VWRP"),
 ("Stocks / shares","Trading 212|Vanguard|dividend|InvestEngine"),
 ("Property","mortgage|buy-to-let|landlord|LISA|help to buy|first.time buyer"),
 ("Crypto","crypto|bitcoin|ethereum|dogecoin"),
 ("Cash / savings","cash ISA|emergency fund|HYSA|high yield savings|premium bonds"),
 ("Pension / 401k","pension|SIPP|401.?k|retirement|Coast FI")]
def sweep(handles):
    out = []
    for name, pat in pats:
        nv = nh = 0
        for h in handles:
            d = os.path.join(TX, h)
            if not os.path.isdir(d): continue
            r = subprocess.run(["grep","-rliE",pat,"--include=*.md",d],capture_output=True,text=True)
            c = len([l for l in r.stdout.splitlines() if l.strip()])
            if c: nh += 1; nv += c
        out.append((name, nv, nh))
    return out

import sqlite3
db = sqlite3.connect(os.path.join(BASE, "..", "saveshare_blog", "transcript_db.sqlite"))
ukh = [r[0] for r in db.execute("SELECT handle FROM creators WHERE region='UK'")]
ush = [r[0] for r in db.execute("SELECT handle FROM creators WHERE region='US'")]
nuk_tx = db.execute("SELECT COUNT(*) FROM transcripts WHERE region='UK'").fetchone()[0]
nus_tx = db.execute("SELECT COUNT(*) FROM transcripts WHERE region='US'").fetchone()[0]
uk_a = sweep(ukh); us_a = sweep(ush)

def fmt(x, ccy="GBP"):
    s = "GBP" if ccy=="GBP" else "USD"
    sym = "\u00a3" if ccy=="GBP" else "$"
    if isinstance(x, float): x = round(x)
    return f"{sym}{x:,}".replace(",", ",")

def bar_svg(items, maxv, color="#0F766E", unit=""):
    rows = []
    y = 0
    for name, v in items:
        w = max(2, round(v/maxv*420)) if maxv else 2
        rows.append(f'<text x="0" y="{y+16}" font-size="13" fill="#0F172A">{html.escape(name)}</text>'
          f'<text x="560" y="{y+16}" font-size="13" font-weight="700" text-anchor="end" fill="#0F172A">{v:,}{unit}</text>'
          f'<rect x="0" y="{y+24}" width="{w}" height="14" rx="7" fill="{color}"/>')
        y += 52
    return f'<svg viewBox="0 0 560 {y}" width="100%" role="img">{"".join(rows)}</svg>'

def donut(segs, total):
    cx, cy, r = 110, 110, 80
    import math
    out, ang = [], -math.pi/2
    leg = []
    cols = ["#0F766E","#0EA5A4","#F59E0B","#8B5CF6","#EC4899","#64748B"]
    for i,(name,v) in enumerate(segs):
        frac = v/total if total else 0
        a2 = ang + frac*2*math.pi
        x1,y1 = cx+r*math.cos(ang), cy+r*math.sin(ang)
        x2,y2 = cx+r*math.cos(a2), cy+r*math.sin(a2)
        large = 1 if frac > .5 else 0
        out.append(f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} Z" fill="{cols[i%6]}" stroke="#fff" stroke-width="2"/>')
        pct = round(frac*100)
        leg.append(f'<div class="leg"><span class="dot" style="background:{cols[i%6]}"></span>{html.escape(name)} <b>{v:,}</b> ({pct}%)</div>')
        ang = a2
    svg = f'<svg viewBox="0 0 220 220" width="220" role="img">{"".join(out)}<circle cx="{cx}" cy="{cy}" r="44" fill="#fff"/><text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="20" font-weight="800" fill="#0F172A">{total:,}</text></svg>'
    return svg, "".join(leg)

def table(rows, ccy):
    trs = []
    for name,handle,region,kind,amt,rccy,date,quote,url,prof in rows:
        if rccy != ccy: continue
        amt_s = fmt(amt, rccy) if amt else "not disclosed"
        trs.append(f'<tr data-region="{region.lower()}"><td><a href="{prof}">{html.escape(name)}</a><br><a class="h" href="https://www.tiktok.com/@{handle}" target="_blank" rel="noopener">@{handle}</a></td>'
          f'<td><span class="flag">{region}</span></td><td>{KIND_LABEL[kind]}</td>'
          f'<td class="num">{amt_s}</td><td>{date}</td>'
          f'<td class="q">{html.escape(quote)} <a href="{url}" target="_blank" rel="noopener">source</a></td></tr>')
    return "".join(trs)

FX = 1.27  # approx USD per GBP, stated in methodology
uk_alloc = [("Pension / retirement",53,24),("Cash / savings",46,23),("ETF / index",61,24),("Stocks",50,23),("Property",39,20),("Crypto",5,5)]
us_alloc = [("Pension / 401k",26,12),("Cash / savings",16,6),("ETF / index",14,6),("Stocks",4,3),("Property",19,11),("Crypto",10,4)]

uk_videos = [(n,v) for n,v,_ in uk_a]; us_videos = [(n,v) for n,v,_ in us_a]
uk_svg = bar_svg(uk_videos, max(v for _,v in uk_videos))
us_svg = bar_svg(us_videos, max(v for _,v in us_videos), "#1D4ED8")
uk_donut_svg, uk_leg = donut([(n,h) for n,_,h in uk_a], sum(h for _,_,h in uk_a))
us_donut_svg, us_leg = donut([(n,h) for n,_,h in us_a], sum(h for _,_,h in us_a))

allkinds = sorted(set(r[3] for r in F))

page = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analytics: self-reported creator figures | SaveShare.io</title>
<meta name="description" content="Aggregated self-reported net worth, invested amounts and asset mentions from UK and US money creators on TikTok. Every figure links to its source.">
<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
:root{{--teal:#0F766E;--teal-dark:#115E59;--teal-soft:#E0F2F1;--ink:#0F172A;--muted:#475569;--line:#E2E8F0;--bg:#F8FAFC;--blue:#1D4ED8}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}}
h1,h2{{font-family:'Playfair Display',Georgia,serif;line-height:1.15;margin:0}}
.wrap{{max-width:1100px;margin:0 auto;padding:0 24px}}
nav{{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}}
nav .wrap{{display:flex;align-items:center;justify-content:space-between;padding-top:14px;padding-bottom:14px}}
.logo{{font-weight:800;font-size:20px;color:var(--teal);text-decoration:none}}
.logo span{{color:var(--ink)}}
.nav-links{{display:flex;gap:24px;align-items:center}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:15px;font-weight:500}}
.nav-links a:hover{{color:var(--teal)}}
.region-toggle{{display:flex;gap:0;border:1px solid var(--line);border-radius:9999px;overflow:hidden}}
.reg-btn{{border:none;background:#fff;color:var(--muted);font-weight:700;font-size:15px;padding:10px 22px;cursor:pointer;font-family:inherit;min-height:44px}}
.reg-btn.active{{background:var(--teal);color:#fff}}
.hero{{background:linear-gradient(135deg,#0F766E 0%,#134E4A 100%);color:#fff;padding:56px 0 64px;text-align:center}}
.hero h1{{font-size:clamp(32px,5vw,52px);max-width:780px;margin:0 auto 16px}}
.hero p{{font-size:18px;opacity:.9;max-width:660px;margin:0 auto}}
section{{padding:56px 0 8px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:28px 0}}
.stat{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;box-shadow:0 10px 15px -3px rgb(15 23 42/.05)}}
.stat strong{{display:block;font-size:30px;font-weight:800;color:var(--teal)}}
.stat span{{font-size:14px;color:var(--muted)}}
.panel{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:28px;margin:20px 0;box-shadow:0 10px 15px -3px rgb(15 23 42/.05)}}
.panel h2{{font-size:26px;margin-bottom:6px}}
.panel .sub{{color:var(--muted);font-size:15px;margin:0 0 20px}}
.donut-wrap{{display:flex;gap:28px;align-items:center;flex-wrap:wrap}}
.leg{{font-size:14px;margin:6px 0;color:var(--muted)}}
.dot{{display:inline-block;width:12px;height:12px;border-radius:99px;margin-right:8px}}
table{{width:100%;border-collapse:collapse;font-size:14px;margin-top:12px}}
th{{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);padding:10px 8px;border-bottom:2px solid var(--line)}}
td{{padding:12px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
tr:nth-child(even) td{{background:#F8FAFC}}
.num{{font-weight:700;white-space:nowrap}}
.h{{color:var(--teal);font-weight:600;text-decoration:none;font-size:13px}}
.q{{color:var(--muted);font-size:13px}}
.q a{{color:var(--teal);font-weight:700;white-space:nowrap}}
.flag{{font-size:11px;font-weight:700;background:var(--teal-soft);color:var(--teal-dark);padding:2px 10px;border-radius:9999px}}
.method{{background:#FFFBEB;border:1px solid #FDE68A;border-radius:16px;padding:28px;margin:28px 0;font-size:15px}}
.method h2{{font-size:24px;margin-bottom:10px}}
footer{{background:#fff;border-top:1px solid var(--line);padding:40px 0;font-size:14px;color:var(--muted);margin-top:48px}}
footer .wrap{{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap}}
[data-rv]{{display:none}}
body[data-view="uk"] [data-rv="uk"]{{display:block}}
body[data-view="us"] [data-rv="us"]{{display:block}}
body[data-view="uk"] tr[data-region="uk"]{{display:table-row}}
body[data-view="us"] tr[data-region="us"]{{display:table-row}}
tr[data-region]{{display:none}}
@media(max-width:640px){{.nav-links a:not(.btn){{display:none}}.donut-wrap{{flex-direction:column}}}}
</style>
</head>
<body data-view="uk">
<nav><div class="wrap"><a class="logo" href="index.html">SaveShare<span>.io</span></a>
<div class="nav-links"><a href="index.html#creators">Directory</a><a href="blog/index.html">Blog</a><a href="analytics.html">Analytics</a>
<div class="region-toggle" role="group" aria-label="Region"><button class="reg-btn active" data-reg="uk" type="button">UK</button><button class="reg-btn" data-reg="us" type="button">US</button></div>
</div></div></nav>
<header class="hero"><div class="wrap">
<h1>Creator money, in their own words</h1>
<p>Aggregated self-reported figures from {len(ukh)} UK and {len(ush)} US money creators, drawn from {nuk_tx + nus_tx} archived TikTok transcripts. Every number links to the video where the creator said it.</p>
</div></header>
<div class="wrap">

<div data-rv="uk">
<section><div class="cards">
<div class="stat"><strong>{len(uk_c)}</strong><span>UK creators with stated figures</span></div>
<div class="stat"><strong>{fmt(round(uk_nw['avg']), 'GBP') if uk_nw.get('n') else 'not disclosed'}</strong><span>Avg self-stated net worth ({uk_nw.get('n',0)} creators)</span></div>
<div class="stat"><strong>{fmt(round(uk_nw['med']), 'GBP') if uk_nw.get('n') else 'not disclosed'}</strong><span>Median self-stated net worth</span></div>
<div class="stat"><strong>{fmt(uk_inv.get('total',0), 'GBP')}</strong><span>Combined stated portfolios + invested ({uk_inv.get('n',0)} figures)</span></div>
</div></section>
<section><div class="panel"><h2>What UK creators talk about</h2><p class="sub">Videos mentioning each asset class across {nuk_tx} archived UK transcripts ({len(ukh)} creators).</p>{uk_svg}</div></section>
<section><div class="panel"><h2>UK asset mix by creator count</h2><p class="sub">Creators with at least one video mentioning each class.</p><div class="donut-wrap">{uk_donut_svg}<div>{uk_leg}</div></div></div></section>
</div>

<div data-rv="us">
<section><div class="cards">
<div class="stat"><strong>{len(us_c)}</strong><span>US creators with stated figures</span></div>
<div class="stat"><strong>{fmt(round(us_nw['avg']), 'USD') if us_nw.get('n') else 'not disclosed'}</strong><span>Avg self-stated net worth ({us_nw.get('n',0)} creators)</span></div>
<div class="stat"><strong>{fmt(round(us_nw['med']), 'USD') if us_nw.get('n') else 'not disclosed'}</strong><span>Median self-stated net worth</span></div>
<div class="stat"><strong>{fmt(us_inv.get('total',0), 'USD')}</strong><span>Combined stated portfolios + invested ({us_inv.get('n',0)} figures)</span></div>
</div></section>
<section><div class="panel"><h2>What US creators talk about</h2><p class="sub">Videos mentioning each asset class across {nus_tx} archived US transcripts ({len(ush)} creators).</p>{us_svg}</div></section>
<section><div class="panel"><h2>US asset mix by creator count</h2><p class="sub">Creators with at least one video mentioning each class.</p><div class="donut-wrap">{us_donut_svg}<div>{us_leg}</div></div></div></section>
</div>

<section><div class="panel"><h2>Every figure, with its source</h2>
<p class="sub">Self-described amounts only. Where a creator has not stated a figure, they are listed as not disclosed. Figures shown in the creator's original currency; cross-region totals are not converted.</p>
<table><thead><tr><th>Creator</th><th>Region</th><th>Figure type</th><th>Amount</th><th>Stated</th><th>Quote + source</th></tr></thead>
<tbody>{table(F, 'GBP')}{table(F, 'USD')}</tbody></table></div></section>

<section><div class="method"><h2>Methodology</h2>
<p><b>Source.</b> Figures come from archived TikTok transcripts ({nuk_tx} UK videos, {nus_tx} US videos) plus on-screen portfolio screenshots verified by OCR, and creator-written captions. Research notes: networth-research.md, networth-verification-2026-10-05.md, networth-deep-2026-10-05.md, networth-ocr-2026-10-05.md.</p>
<p><b>Self-described only.</b> Net worth means the creator said the words about themselves. Hypothetical projections, other people's money, and generic examples are excluded. Property purchase prices are labelled property value, not net worth. Monthly flows are labelled as flows, not totals.</p>
<p><b>No fabrication.</b> Where no figure was stated, the value is not disclosed. Averages and medians use only creators with a stated net worth figure. Combined invested totals sum stated portfolio and invested amounts only, in original currency.</p>
<p><b>Currency.</b> UK figures in pounds, US figures in dollars. No conversion applied in the tables. Reference rate used only for narrative comparison: about {FX} USD per GBP (Oct 2026).</p>
<p><b>Freshness.</b> Figures carry the date stated. Markets move and creators update their numbers, so treat every figure as a snapshot. Last rebuilt 12 Oct 2026.</p>
</div></section>

</div>
<footer><div class="wrap"><div><a class="logo" href="index.html" style="font-size:18px">SaveShare<span>.io</span></a>
<p style="margin:8px 0 0">Sourced creator directory for UK and US personal finance.</p></div>
<div style="font-size:14px"><a href="index.html#creators" style="color:var(--muted);text-decoration:none;margin-right:18px">Directory</a><a href="blog/index.html" style="color:var(--muted);text-decoration:none;margin-right:18px">Blog</a><a href="analytics.html" style="color:var(--muted);text-decoration:none">Analytics</a></div></div></footer>
<script>
(function(){{var k="ss-region";function set(v){{document.body.dataset.view=v;try{{localStorage.setItem(k,v)}}catch(e){{}}document.querySelectorAll(".reg-btn").forEach(function(b){{b.classList.toggle("active",b.dataset.reg===v)}})}}var v="uk";try{{v=localStorage.getItem(k)||"uk"}}catch(e){{}}if(v!=="uk"&&v!=="us")v="uk";set(v);document.querySelectorAll(".reg-btn").forEach(function(b){{b.addEventListener("click",function(){{set(b.dataset.reg)}})}})}})();
</script></script>
</body></html>"""

out = os.path.join(BASE, "analytics.html")
open(out, "w").write(page)
print("wrote", out, len(page), "bytes")
print("UK net_worth:", uk_nw, "UK invested:", uk_inv)
print("US net_worth:", us_nw, "US invested:", us_inv)
assert "\u2014" not in page, "em dash found"
print("no em dashes: OK")
