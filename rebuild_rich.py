#!/usr/bin/env python3
"""Shared chrome + helpers for SaveShare blog richness rebuild (2026-10-12).
Standard: 1500-2000 words in <main>, 4-6 creators, full quotes, no lists,
no em/en dashes, third person. See ../saveshare_blog/BLOG_RECIPE.md.
"""
import re

CSS_EXTRA = """.quote-unit{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:20px 0}
.q-head{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.q-head img{width:48px;height:48px;border-radius:50%;object-fit:cover;flex-shrink:0}
.q-fol{color:var(--muted);font-weight:400;font-size:13px;margin-left:8px}
.q-text{font-size:16px;margin:0 0 10px}
.q-src{font-size:13px;color:var(--muted);margin:0}
.q-mention{display:inline-flex;align-items:center;gap:6px;font-weight:600;white-space:nowrap}
.q-mention img{width:24px;height:24px;border-radius:50%;object-fit:cover}"""

C = {
 "admjay": ("Adam Jay", "adm.jay", "admjay", "admjay"),
 "didi": ("DiDi", "didifinance", "didifinance", "didifinance"),
 "sophie": ("Sophie Blank", "itssophieblank", "itssophieblank", "itssophieblank"),
 "janice": ("Janice", "janiice.myla", "janiicemyla", "janiicemyla"),
 "bret": ("Bret and Evey", "bretandevey", "bretandevey", "bretandevey"),
 "lupes": ("Lupes", "lupeslively", "lupeslively", "lupeslively"),
 "mark": ("Mark", "markonthemoney", "markonthemoney", "markonthemoney"),
 "dahlia": ("Dahlia", "getontopwithdahlia", "getontopwithdahlia", "getontopwithdahlia"),
 "tatiana": ("Tatiana", "tatianamamixo", "tatianamamixo", "tatianamamixo"),
 "hannah": ("Hannah Bevington", "hannahbevington", "hannahbevington", "hannahbevington"),
 "mia": ("Mia Rose", "miarosemcgrath", "miarosemcgrath", "miarosemcgrath"),
 "ollie": ("Ollie Invests", "ollieinvests", "ollieinvests", "ollieinvests"),
 "sean": ("Sean", "seansmoney", "seansmoney", "seansmoney"),
 "neil": ("Neil Invests", "neilinvests", "neilinvests", "neilinvests"),
 "emmie": ("Emmie", "emmieedit", "emmieedit", "emmieedit"),
 "krish": ("Krish Kara", "krish.kara", "krishkara", "krish.kara"),
 "james": ("James", "moneystocker", "moneystocker", "moneystocker"),
 "elly": ("Elly", "msellyphant", "msellyphant", "msellyphant"),
 "jubair": ("Dr Jubair", "drjubairsfinance", "drjubairsfinance", "drjubairsfinance"),
 "holly": ("Holly", "holl_005", "holl005", "holl005"),
 "ciara": ("Ciara", "ciara__anne", "ciaraanne", "ciara__anne"),
 "kafilat": ("Kafilat", "kafilat.finance", "kafilatfinance", "kafilat.finance"),
 "amy": ("Amy", "financiallyher_", "financiallyher", "financiallyher_"),
 "iain": ("Iain", "iainmoneyinsights", "iainmoneyinsights", "iainmoneyinsights"),
 "fellas": ("Fellas Finance", "fellasfinance", "fellasfinance", "fellasfinance"),
 "cam": ("Cam", "camrusselluk", "camrusselluk", "camrusselluk"),
 "gabriel": ("Gabriel", "gabriel.nussbaum", "gabrielnussbaum", "gabrielnussbaum"),
 "chris": ("Chris", "intentional.finance", "intentionalfinance", "intentional.finance"),
 "rex": ("Rex", "theeverydaymillionaire", "theeverydaymillionaire", "theeverydaymillionaire"),
 "tommy": ("Tommy", "tommytalks.uk", "tommytalksuk", "tommytalksu"),
 "charlie": ("Charlie", "wealthmadeaccessible", "wealthmadeaccessible", "wealthmadeaccessible"),
 "jno": ("JNO", "jno_pwnr", "jnopwnr", "jno_pwnr"),
 "daniel": ("Daniel", "gray.area.finance", "grayareafinance", "gray.area.finance"),
 "george": ("George", "george_tuttle", "georgetuttle", "george_tuttle"),
 "ola": ("Ola", "allthingsmoney_", "allthingsmoney", "allthingsmoney"),
 "amanda": ("Amanda", "amandainvests", "amandainvests", "amandainvests"),
 "will": ("Will", "nextgenngpf", "nextgenngpf", "nextgenngpf"),
}

def qm(key):
    name, handle, pfile, av = C[key]
    return (f'<span class="q-mention"><img src="../avatars/{av}.jpg" alt="{name}" loading="lazy">'
            f'<a href="../p/{pfile}.html">{name}</a></span>')

def qu(key, quote, url, stat, ctx=""):
    name, handle, pfile, av = C[key]
    tail = f" {ctx}" if ctx else ""
    return (f'<div class="quote-unit"><div class="q-head"><img src="../avatars/{av}.jpg" alt="{name}" loading="lazy">'
            f'<strong><a href="../p/{pfile}.html">{name}</a><span class="q-fol">@{handle}</span></strong></div>'
            f'<p class="q-text">{quote}</p>'
            f'<p class="q-src"><a href="{url}">Watch on TikTok</a> ({stat}).{tail}</p></div>')

def bq(key, quote, url):
    name, handle, pfile, av = C[key]
    return (f'<blockquote>{quote}<cite>{qm(key)}, '
            f'<a href="{url}">on TikTok</a></cite></blockquote>')

DISC1 = ("<p><em>Nothing on this page constitutes financial advice. Figures quoted are "
         "self-described by each creator in their own TikTok videos, linked so you can check "
         "the source yourself.</em></p>")
DISC2 = ("<p>Net worth figures are self-described by each creator in their own TikTok content "
         "and have not been independently verified. Nothing on this site constitutes financial "
         "advice. \u00a9 2026 SaveShare.io</p>")

def page(fname, title, desc, badge, h1, sub, tags, body):
    taghtml = " ".join(f'<span class="tag">{t}</span>' for t in tags)
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3T9QS61KD0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-3T9QS61KD0');
</script>
<title>{title}</title>
<link rel="canonical" href="https://saveshare.io/blog/{fname}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SaveShare.io">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://saveshare.io/blog/{fname}">
<meta name="twitter:card" content="summary_large_image">
<meta name="description" content="{desc}">
<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
:root{{--teal:#0F766E;--teal-dark:#115E59;--teal-soft:#E0F2F1;--ink:#0F172A;--muted:#475569;--line:#E2E8F0;--bg:#F8FAFC}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.7}}
h1,h2,h3{{font-family:'Playfair Display',Georgia,serif;line-height:1.2;margin:0}}
.wrap{{max-width:780px;margin:0 auto;padding:0 24px}}
nav{{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}}
nav .wrap{{max-width:1100px;display:flex;align-items:center;justify-content:space-between;padding-top:14px;padding-bottom:14px}}
.logo{{font-weight:800;font-size:20px;color:var(--teal);text-decoration:none}}
.logo span{{color:var(--ink)}}
.nav-links{{display:flex;gap:24px;align-items:center}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:15px;font-weight:500}}
.nav-links a:hover{{color:var(--teal)}}
.hero{{background:linear-gradient(135deg,#0F766E 0%,#134E4A 100%);color:#fff;padding:56px 0;text-align:center}}
.hero h1{{font-size:clamp(30px,4vw,44px);margin-bottom:10px}}
.hero p{{opacity:.9;font-size:17px;margin:0}}
main{{padding:48px 0}}
blockquote{{border-left:4px solid var(--teal);margin:20px 0;padding:12px 20px;background:#fff;border-radius:0 12px 12px 0;font-style:italic}}
blockquote cite{{display:block;font-style:normal;font-size:13px;color:var(--muted);margin-top:8px}}
blockquote cite a{{color:var(--teal)}}
.tag{{display:inline-block;background:var(--teal-soft);color:var(--teal-dark);font-size:12px;font-weight:600;padding:3px 12px;border-radius:9999px;margin:2px 6px 2px 0}}
a{{color:var(--teal)}}
footer{{background:#fff;border-top:1px solid var(--line);padding:32px 0;font-size:13px;color:var(--muted);margin-top:48px}}
{CSS_EXTRA}</style>
</head>
<body>
<nav><div class="wrap"><a class="logo" href="../index.html">SaveShare<span>.io</span></a>
<div class="nav-links"><a href="../index.html#creators">Creators</a><a href="index.html">Blog</a></div></div></nav>
<header class="hero"><div class="wrap">
<div style="display:inline-block;background:rgba(255,255,255,.15);font-size:13px;font-weight:600;padding:6px 18px;border-radius:9999px;margin-bottom:16px">{badge}</div>
<h1>{h1}</h1>
<p>{sub}</p>
</div></header>
<main><div class="wrap">
<p>{sub}</p>
<p><a href="index.html">\u2190 Blog</a> {taghtml}</p>
{body}
{DISC1}
{DISC2}
</div></main>
<footer><div class="wrap" style="max-width:1100px">
<p>Net worth figures are self-described by each creator in their own TikTok content and have not been independently verified. Nothing on this site constitutes financial advice. \u00a9 2026 SaveShare.io</p>
</div></footer>
<script src="../guard.js"></script>
</body>
</html>
"""

def check_no_dashes(s):
    assert "\u2014" not in s and "\u2013" not in s, "em/en dash found"
    assert "<ul" not in s and "<ol" not in s, "list found"
