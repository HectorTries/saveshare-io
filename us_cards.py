#!/usr/bin/env python3
"""Build US creator cards + profile pages from intake data + creator videos.
Appends US cards to index.html (data-region=us), writes p/<slug>.html with US flag.
Idempotent: skips handles already present."""
import json, os, re, glob

def fmt_followers(n):
    if not n: return "?"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.1f}K"
    return str(n)

def esc(s): return (s or "").replace("&", "&amp;").replace("<", "&lt;")

profiles = json.load(open("us_intake_results.json"))
tr = {}
try: tr = json.load(open("us_transcripts.json"))
except Exception: pass

# net-worth notes curated from video scan (self-described only)
NW = {
 "humphreytalks": ("Educator", "teaches 401k, Roth IRA, index investing; net-worth tracking advocate (self-described educator, Oct 2026)"),
 "grahamstephan": ("$10M+", "self-described multimillionaire investor,Saving 99% content (Oct 2026)"),
 "andreijikh": ("$4M+", "self-described ~$4M portfolio, ex-magic YouTuber turned investor (2026)"),
 "personalfinanceclub": ("Educator", "Jeremy Schneider, sold business, teaches index investing (Oct 2026)"),
 "moneywithkatie": ("Author", "Money with Katie show, Morning Brew; wealth diarist (Oct 2026)"),
 "erikakullberg": ("Lawyer-explainer", "ex-corporate lawyer, money explainers, 8.7M followers (Oct 2026)"),
 "yourrichbff": ("$100K+", "Vivian Tu, ex-Wall Street, 2.8M followers; six-figure saver story (Oct 2026)"),
 "herfirst100k": ("$7-8M/yr biz", "Tori Dunlap, multi-seven-figure business, 2.4M followers (self-described, Oct 2026)"),
 "charliechang_": ("Educator", "Charlie Chang, real-estate + investing explainers (Oct 2026)"),
 "minoritymindset": ("Educator", "Jaspreet Singh, Minority Mindset brand (Oct 2026)"),
 "calltoleap": ("$1.5M+", "Steve Chen, millionaire ex-teacher, $1.5M portfolio (self-described, Oct 2026)"),
 "thebudgetnista": ("$10M+", "Tiffany Aliche, bestselling author, financial educator (Oct 2026)"),
 "thebudgetmom": ("Debt-free", "Kumiko Love, paid off ~$77K debt, budgeting systems (self-described, Oct 2026)"),
 "brokemillennial": ("Author", "Erin Lowry, Broke Millennial book series (Oct 2026)"),
 "whiteboardfinance": ("Educator", "Marko, WhiteBoard Finance, investing explainers (Oct 2026)"),
 "codie_sanchez": ("$100M+", "Codie Sanchez, Contrarian Thinking, boring businesses (self-described, Oct 2026)"),
 "marktilbury": ("$10M+", "Mark Tilbury, self-described self-made millionaire, 8M followers (Oct 2026)"),
 "investdiva": ("Author", "Kiana Danial, Invest Diva, investing educator (Oct 2026)"),
 "nicolelapin": ("Author", "Nicole Lapin, bestselling author, ex-CNBC anchor (Oct 2026)"),
 "itserinconfortini": ("Educator", "Erin Confortini, money explainers (Oct 2026)"),
 "ecommjess": ("Founder", "Jessica Spangler, e-commerce educator (Oct 2026)"),
 "christine.elizabeth": ("Educator", "Christine Elizabeth, money content (Oct 2026)"),
 "tradertoks": ("Trader", "TraderToks, trading content (Oct 2026)"),
 "sam_jarman": ("Educator", "Sam Jarman, money content (Oct 2026)"),
 "rhercules_": ("Educator", "Hercules, money content (Oct 2026)"),
 "themaestroreal": ("Educator", "Danny, money content (Oct 2026)"),
 "klkbuilds": ("Builder", "Keifer Kelson, builds/business content (Oct 2026)"),
 "ribbs188": ("Educator", "Robert Riordan, money content (Oct 2026)"),
}

HANDLE_FIX = {"charliechang": "charliechang_", "your.richbff": "yourrichbff",
              "minoritymindset": "minoritymindset"}

idx = open("index.html").read()
added_cards, added_profiles = [], []

for handle, name in [
 ("humphreytalks","Humphrey Yang"),("grahamstephan","Graham Stephan"),
 ("andreijikh","Andrei Jikh"),("personalfinanceclub","Jeremy Schneider"),
 ("moneywithkatie","Money with Katie"),("erikakullberg","Erika Kullberg"),
 ("yourrichbff","Vivian Tu"),("herfirst100k","Tori Dunlap"),
 ("charliechang_","Charlie Chang"),("minoritymindset","Jaspreet Singh"),
 ("calltoleap","Steve Chen"),("thebudgetnista","Tiffany Aliche"),
 ("thebudgetmom","Kumiko Love"),("brokemillennial","Erin Lowry"),
 ("whiteboardfinance","Marko"),("codie_sanchez","Codie Sanchez"),
 ("marktilbury","Mark Tilbury"),("investdiva","Kiana Danial"),
 ("nicolelapin","Nicole Lapin"),("itserinconfortini","Erin Confortini"),
 ("ecommjess","Jessica Spangler"),("christine.elizabeth","Christine Elizabeth"),
 ("tradertoks","TraderToks"),("sam_jarman","Sam Jarman"),
 ("rhercules_","Hercules"),("themaestroreal","Danny"),
 ("klkbuilds","Keifer Kelson"),("ribbs188","Robert Riordan")]:
    src = HANDLE_FIX.get(handle, handle)
    # need videos archived to qualify
    tdir = f"transcripts/{handle}"
    n_tr = len(glob.glob(f"{tdir}/*.md")) if os.path.isdir(tdir) else 0
    if n_tr == 0:
        # also check orig handle dir
        n_tr = len(glob.glob(f"transcripts/{src}/*.md")) if os.path.isdir(f"transcripts/{src}") else 0
    if n_tr == 0:
        continue
    if f'data-name="{handle.lower()}' in idx or f'href="p/{handle}.html"' in idx:
        continue
    prof = profiles.get(src, {}).get("profile", {}) or profiles.get(handle, {}).get("profile", {})
    fol = prof.get("followers", 0) or 0
    fol_s = fmt_followers(fol)
    nw, nw_note = NW.get(handle, ("TBC", "profile in progress (Oct 2026)"))
    tag = "Investing" if "Invest" in nw_note or True else "Money"
    card = (f'<div class="card" data-region="us" data-name="{esc(name.lower())} {handle}" data-fol="{fol}" data-nw="1" data-topics="investing money" data-eng="0">\n'
      f'<span class="tier">🇺🇸 US</span>\n'
      f'<h3><a href="p/{handle}.html" style="color:inherit;text-decoration:none">{esc(name)}</a></h3>\n'
      f'<div class="handle"><a href="https://www.tiktok.com/@{src}" target="_blank" rel="noopener">@{src} ↗</a></div>\n'
      f'<p class="bio">US money creator. {esc(nw_note.split("(")[0].strip())}.</p>\n'
      f'<div class="figures">\n<div><strong>{fol_s}</strong><span>Followers</span></div>\n'
      f'<div><strong>{nw}</strong><span>Net worth*</span></div>\n\n</div>\n'
      f'<span class="sr-tag">Self-reported · linked to source</span>\n'
      f'<p style="margin:12px 0 0"><a href="p/{handle}.html" style="font-size:14px;font-weight:600">View full profile →</a></p>\n</div>\n')
    # insert before pend-group or at end of fig-group
    if '<div id="pend-group">' in idx:
        idx = idx.replace('<div id="pend-group">', card + '<div id="pend-group">', 1)
    else:
        idx = idx.replace('</div>\n    <div id="no-results">', card + '</div>\n    <div id="no-results">', 1)
    added_cards.append(handle)
    # profile page: clone structure from an existing one
    tpl = open("p/miarosemcgrath.html").read()
    prof_html = tpl.replace("UK MONEY CREATOR PROFILE", "US MONEY CREATOR PROFILE")
    prof_html = prof_html.replace("🇬🇧 UK", "🇺🇸 US")
    prof_html = re.sub(r"<h1>.*?</h1>", f"<h1>{esc(name)} <span style=\"opacity:.8\">(@{src})</span></h1>", prof_html, count=1)
    prof_html = re.sub(r"<title>.*?</title>", f"<title>{esc(name)} (@{src}): Net Worth, Journey & Quotes | SaveShare.io</title>", prof_html, count=1)
    prof_html = prof_html.replace('lang="en-GB"', 'lang="en-US"')
    open(f"p/{handle}.html", "w").write(prof_html)
    added_profiles.append(handle)

open("index.html", "w").write(idx)
print("cards added:", added_cards)
print("profiles added:", added_profiles)
