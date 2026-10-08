#!/usr/bin/env python3
"""Build p/*.html, blog/index.html, patch index.html cards, update creators.md."""
import os

CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
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
.stat-row{{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}}
.stat{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 20px;flex:1;min-width:140px}}
.stat strong{{display:block;font-size:22px}}
.stat span{{font-size:13px;color:var(--muted)}}
blockquote{{border-left:4px solid var(--teal);margin:20px 0;padding:12px 20px;background:#fff;border-radius:0 12px 12px 0;font-style:italic}}
blockquote cite{{display:block;font-style:normal;font-size:13px;color:var(--muted);margin-top:8px}}
blockquote cite a{{color:var(--teal)}}
.card{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:28px;margin:20px 0}}
.card h2{{font-size:22px;margin-bottom:10px}}
.tag{{display:inline-block;background:var(--teal-soft);color:var(--teal-dark);font-size:12px;font-weight:600;padding:3px 12px;border-radius:9999px;margin:2px 6px 2px 0}}
a{{color:var(--teal)}}
footer{{background:#fff;border-top:1px solid var(--line);padding:32px 0;font-size:13px;color:var(--muted);margin-top:48px}}
.src{{font-size:13px;color:var(--muted)}}
ul.tick{{list-style:none;padding:0}}
ul.tick li::before{{content:"✓ ";color:#0F766E;font-weight:700}}"""

NAV = """<nav><div class="wrap"><a class="logo" href="../index.html">SaveShare<span>.io</span></a>
<div class="nav-links"><a href="../index.html#creators">Creators</a><a href="index.html">Money Advice</a></div></div></nav>"""
NAV_HOME = NAV.replace("../", "").replace('href="index.html#creators"', 'href="../index.html#creators"').replace('href="index.html">Money', 'href="blog/index.html">Money')
# simpler: build nav per location explicitly below

def page(title, desc, nav, hero_badge, hero_h1, hero_sub, body):
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3T9QS61KD0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-3T9QS61KD0');
</script>
<style>{CSS}</style>
</head>
<body>
{nav}
<header class="hero"><div class="wrap">
<div style="display:inline-block;background:rgba(255,255,255,.15);font-size:13px;font-weight:600;padding:6px 18px;border-radius:9999px;margin-bottom:16px">{hero_badge}</div>
<h1>{hero_h1}</h1>
<p>{hero_sub}</p>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap" style="max-width:1100px">
<p>Net worth figures are self-reported by each creator in their own TikTok content and have not been independently verified. Nothing on this site constitutes financial advice. © 2026 SaveShare.io</p>
</div></footer>
</body>
</html>"""

NAV_P = """<nav><div class="wrap"><a class="logo" href="../index.html">SaveShare<span>.io</span></a>
<div class="nav-links"><a href="../index.html#creators">Creators</a><a href="../blog/index.html">Money Advice</a></div></div></nav>"""
NAV_BLOG = """<nav><div class="wrap"><a class="logo" href="../index.html">SaveShare<span>.io</span></a>
<div class="nav-links"><a href="../index.html#creators">Creators</a><a href="index.html">Money Advice</a></div></div></nav>"""

TT = "https://www.tiktok.com"
TT_HANDLE_PY = {"seansmoney": "seans.money", "drjubairsfinance": "dr.jubairsfinance", "iainmoneyinsights": "iainjgeddes"}
NW_DATE_PY = {"miarosemcgrath": "Oct 2026", "itssophieblank": "Sep 2026", "seansmoney": "Aug 2026", "neilinvests": "Sep 2026", "hannahbevington": "Sep 2026", "drjubairsfinance": "2025", "iainmoneyinsights": "late 2025", "ollieinvests": "2026"}

CREATORS = [
 dict(handle="miarosemcgrath", name="Mia Rose", tagline="Frugal Chic® — build wealth, stylishly",
      followers="668.3K", nw="£200K+", nw_note="multiple six-figure net worth, £100K invested (self-described, Oct 2026)",
      nw_vid="7693085657937218838", eng="7.16%", n_tr=20,
      who=("Mia Rose McGrath is the UK money creator behind <strong>Frugal Chic®</strong> — a brand built around "
            "building wealth stylishly, without jargon or deprivation. Featured in Vogue and The Times, she is also the "
            "author of the book <em>Frugal Chic</em> and, at 25, describes herself as having a multiple six-figure net worth."),
      journey=("Mia says she did not grow up financially literate, never worked in finance, and does not have financially "
            "literate parents. Everything she knows comes from seven years of self-directed research driven by genuine interest. "
            "She spent her early twenties increasing her income and reducing her expenses with the goal of financial freedom, "
            "and spent over seven years saving her first £100,000. She now has £100,000 invested and teaches investing "
            "step-by-step for beginners — including a series where she and her 21-year-old sister each start investing with £100 to see who ends up with more."),
      quotes=[
        ("I spent over seven years saving £100,000. And that's why people have a gravitation towards my content, because it comes from lived experience.", "7693085657937218838"),
        ("I built a multiple six figure net worth in my 20s. I have 100K invested and I didn't grow up financially literate.", "7684543907404958979"),
        ("Have 3 months worth of living expenses saved… when I left my 9 to 5 to pursue self employment, I had 12 months saved.", "7684166553079778582"),
      ],
      stats=[("668.3K", "Followers"), ("£200K+", "Net worth*"), ("7.16%", "Avg engagement"), ("20", "Videos archived")]),
 dict(handle="itssophieblank", name="Sophie Blank", tagline="Wealth, career, life in her 30s — London",
      followers="28.9K", nw="£230K", nw_note="self-described net worth, aiming for £250K by end of 2026 (Sep 2026)",
      nw_vid="7691210896189771030", eng="4.88%", n_tr=12,
      who=("Sophie Blank is a London-based creator in her 30s who documents her journey from zero financial literacy to a "
            "£230,000 net worth. A first-generation university student who moved to the UK 14 years ago, she now works as an AI "
            "strategist at a big tech company, earning six figures, and shares her goal of reaching Coast FI of £1 million by age 40."),
      journey=("Sophie made her first £100 investment in July 2018 with what she describes as zero investing knowledge. Her net worth "
            "progression, shared year by year: −£28,000 in 2018, −£18,000 in 2019, £10,500 in 2020, £50,000 in 2021, £43,000 in 2022 "
            "(after a sabbatical), £105,000 in assets in 2023, £134,800 in 2024 after paying off her student loan in full, £175,000 in "
            "2025 when she started earning six figures, and £230,000 in 2026. She credits paying off her student loan as the moment her "
            "net worth skyrocketed, invests monthly into 3 simple funds (2 ETFs + 1 ETC), and famously loves renting — her rent "
            "content was featured by the BBC and iPaper."),
      quotes=[
        ("I made my first investment of £100 in July 2018… fast forward 8 years and I have a net worth of £230,000 even though I was raised with zero financial literacy.", "7691210896189771030"),
        ("I don't like to spend time selling and buying stocks, so simple ETFs that I invest in every month are the way forward for me.", "7681352811250076950"),
        ("My sinking funds are the one reason I pay off my credit card every single month and I never go into debt.", "7675026659027815702"),
      ],
      stats=[("28.9K", "Followers"), ("£230K", "Net worth*"), ("4.88%", "Avg engagement"), ("20", "Videos archived")]),
 dict(handle="seansmoney", name="Sean", tagline="Documenting money at 30 — Edinburgh",
      followers="20.6K", nw="~£165K invested", nw_note="£89K pensions + £72K ISAs + £3.5K LISA (self-described, Aug 2026)",
      nw_vid="7675840516411395330", eng="0.97%", n_tr=20,
      who=("Sean is an Edinburgh-based creator in his early 30s documenting what he does with his money while educating "
            "others about personal finance. His content mixes beginner investing explainers, ETF breakdowns and honest personal updates."),
      journey=("Sean started saving money in 2021 from a starting point of nothing saved. After anxiety left him signed off work and "
            "dropping to statutory sick pay, the experience pushed him to take saving seriously — five years later he has around £75,000 "
            "saved. He later detailed his full invested position: around £89,000 in pensions (mostly AJ Bell), about £72,000 in stocks "
            "and shares ISAs (mostly Trading 212), plus a £3,500 lifetime ISA — roughly £165,000 invested in the stock market in total. "
            "He also runs a £10-a-week demo portfolio (£6 global ETF, £3 S&P 500, £1 semiconductor) to show beginners you can start small."),
      quotes=[
        ("I had nothing saved at that point and now five years later I have around £75,000 saved.", "7689003263584193814"),
        ("Overall, I have about £165,000 invested in the stock market.", "7675840516411395330"),
        ("If you're waiting until you have more money to invest, you're doing it wrong. I'm doing it with just £10 a week.", "7669798085471653142"),
      ],
      stats=[("20.6K", "Followers"), ("~£165K", "Invested*"), ("0.97%", "Avg engagement"), ("20", "Videos archived")]),
 dict(handle="neilinvests", name="Neil Invests", tagline="Helping beginners start investing",
      followers="146.5K", nw="£350K", nw_note="investment portfolios (self-described, Sep 2026); ~£700K projected pension at 57",
      nw_vid="7690583705051614497", eng="2.47%", n_tr=11,
      who=("Neil Invests is one of the UK's most-followed beginner-investing creators, aged 43, building toward financial "
            "independence well before the standard retirement age. His content focuses on simple, low-cost index investing and "
            "monthly portfolio updates on Trading 212."),
      journey=("Neil keeps his approach deliberately simple: match the all-world market rather than picking individual businesses. "
            "He states he currently holds £350,000 across his investment portfolios, plus a private pension projected to be worth "
            "around £700,000 kicking in at age 57. His core message is that contributions — not returns — drive portfolio growth for "
            "years: making 10% on £1,000 is just £100, so the priority is increasing income and contributions until compounding can "
            "take over. He was made redundant 18 months ago and calls it the best thing that ever happened to him."),
      quotes=[
        ("Can you retire on 350 grand? That's what I've got in my investment portfolios at the moment.", "7690583705051614497"),
        ("The biggest thing that's gonna impact your portfolio performance for a number of years is your contributions into it, not the returns.", "7690258184518274337"),
        ("I just wanna match the all world. If I do that, I actually will beat most [stock pickers].", "7690258184518274337"),
      ],
      stats=[("146.5K", "Followers"), ("£350K", "Invested*"), ("2.47%", "Avg engagement"), ("20", "Videos archived")]),
 dict(handle="hannahbevington", name="Hannah Bevington", tagline="Tall, blue eyes & talks finance",
      followers="41.0K", nw="£135K", nw_note="at 26, from 0 financial awareness at 21 (self-described, Sep 2026)",
      nw_vid="7685007554212138262", eng="4.68%", n_tr=12,
      who=("Hannah Bevington is a 26-year-old UK finance creator who went from zero financial awareness at 21 to £135,000 by 26. "
            "She shares monthly portfolio breakdowns across four accounts and practical payday systems for beginners."),
      journey=("Hannah saved her first £4,000 between ages 17 and 21, then started investing five years ago and never looked back. "
            "Her Trading 212 stocks and shares ISA passed £27,000 after two years of investing. She runs four investment accounts, each "
            "with its own purpose, and says 57% of her total portfolio comes from her own contributions while 43% — around £57,000 of "
            "'free money' — comes from the government, her employer and market growth. Her only regret: not starting sooner, since her "
            "cash ISA days earned far less than investing."),
      quotes=[
        ("I did, in fact, go from having 0 financial awareness at 21 years old to now having £135K at 26 years old.", "7685007554212138262"),
        ("Building wealth doesn't just happen. You really have to curate it and put certain systems in place.", "7682883142197202198"),
        ("5 years investing & the only regret I have is that I didn't start sooner.", "7692825250110737686"),
      ],
      stats=[("41.0K", "Followers"), ("£135K", "Net worth*"), ("4.68%", "Avg engagement"), ("20", "Videos archived")]),
 dict(handle="drjubairsfinance", name="Dr Jubair", tagline="Doctor-turned-investor documenting daily investing",
      followers="17.5K", nw="~£110K+", nw_note="11,000 shares worth £110,469 in one fund (self-described, 2025)",
      nw_vid="7478749549515902230", eng="2.14%", n_tr=19,
      who=("Dr Jubair holds a doctorate (UCL) and creates investing-education content alongside a successful YouTube channel "
            "(14,000+ subscribers). His signature series: investing £100 every single day into the stock market and reporting the results."),
      journey=("Jubair got his doctorate in his 20s, which he calls a life hack that made his 30s easier. He documents long-form "
            "investing experiments — including a £100-a-day daily investing challenge running 130+ days into an S&P 500 ETF (SPDR, "
            "accumulating), passing his first £100 of profit around day 136. He has shown holdings of 11,000 shares worth £110,469 in "
            "one fund. He also transparently shares creator earnings: £9,248 in a year from YouTube AdSense, £14,853 total, and £10,016 "
            "from 900,000 views."),
      quotes=[
        ("I just made my first £100 by investing into the S&P 500 every single day… up overall by 7.47% or £101.54.", "7553752548314746134"),
        ("My 11,000 shares are now worth £110,469.", "7478749549515902230"),
        ("Being a doctor in your 20s is a life hack.", "7437270529976945953"),
      ],
      stats=[("17.5K", "Followers"), ("~£110K+", "Holdings*"), ("2.14%", "Avg engagement"), ("20", "Videos archived")]),
 dict(handle="iainmoneyinsights", name="Iain Geddes", tagline="Building wealth from £0 & showing it all — Scotland",
      followers="34.1K", nw="£94K", nw_note="S&S ISA portfolio value (self-described, late 2025)",
      nw_vid="7578188989362900255", eng="0.26%", n_tr=20,
      who=("Iain Geddes, 34, from Scotland, shares his real-time ISA portfolio journey under the banner 'building wealth from £0 "
            "and showing it all'. He started investing in April 2020 and posts transparent portfolio updates."),
      journey=("Iain spent his younger years only saving — putting leftover money into bank and savings accounts — and says it never "
            "got him anywhere because inflation kept eating its purchasing power. Since taking investing seriously around 2020 with a "
            "Trading 212 stocks and shares ISA, compounding took over: his portfolio approached £82,000, then £94,102, with nearly "
            "£42,000 of total return (a 224.6% rate of return). His message: saving and investing are two completely different things, "
            "keep a long-term mindset, and don't panic-sell when markets drop."),
      quotes=[
        ("Portfolio value is now £94,102.", "7578188989362900255"),
        ("Saving money was keeping me broke. So I did this instead.", "7578182511159774494"),
        ("Do not panic sell… Remember why you invested in them in the first place. Think of that long-term picture.", "7578185208575315231"),
      ],
      stats=[("34.1K", "Followers"), ("£94K", "Portfolio*"), ("0.26%", "Avg engagement"), ("20", "Videos archived")]),
 dict(handle="ollieinvests", name="Ollie Invests", tagline="23, Engineering Graduate — engineering financial freedom",
      followers="2.2K", nw="Growing", nw_note="early-stage portfolio; shares weekly portfolio updates (2026)",
      nw_vid="7692499806496836886", eng="2.65%", n_tr=11,
      who=("Ollie Invests is a 23-year-old engineering graduate sharing weekly portfolio updates, ISA guides and money-habit content. "
            "His style is educational explainer videos — breaking down market news, ISAs and beginner investing steps."),
      journey=("Ollie is at the start of his wealth-building journey and documents it openly: weekly portfolio check-ins (five holdings, "
            "70% in a FTSE world fund), step-by-step Stocks & Shares ISA setup guides (£20,000 annual allowance), and honest money-habit "
            "content — including how keeping savings in his current account led him to slowly spend £2–3,000 of it. His core investing "
            "advice for beginners: use diversified ETFs, think in decades, and let compounding do the work."),
      quotes=[
        ("70% of my money goes straight into a FTSE world fund… diversify your risk and think long term.", "7691726292114279702"),
        ("Lifestyle creep… as soon as you get a pay rise, it's so easy to just start spending that extra money rather than saving.", "7693093069448613142"),
        ("Your [ISA] allowance is £20,000 a year. Questions? Drop them below.", "7691802357973126422"),
      ],
      stats=[("2.2K", "Followers"), ("Growing", "Portfolio"), ("2.65%", "Avg engagement"), ("20", "Videos archived")]),
]

for c in CREATORS:
    h = c['handle']
    tt = TT_HANDLE_PY.get(h, h)
    srdate = NW_DATE_PY.get(h, 'see source')
    qhtml = ''
    for q, v in c['quotes']:
        qhtml += '<blockquote>' + chr(8220) + q + chr(8221) + '<cite>' + chr(8212) + ' ' + c['name'] + ' (<a href="' + TT + '/@' + tt + '/video/' + v + '" target="_blank" rel="noopener">watch on TikTok ' + chr(8599) + '</a>)</cite></blockquote>' + chr(10)
    shtml = ''
    for v, l in c['stats']:
        shtml += '<div class="stat"><strong>' + v + '</strong><span>' + l + '</span></div>' + chr(10)
    who_html = c['who'] if c['who'] else 'Profile in progress — bio coming soon.'
    journey_html = c['journey'] if c['journey'] else 'Journey details coming soon — check their TikTok for the latest.'
    quotes_section = qhtml if qhtml else '<p>No quotes archived yet.</p>'
    nw_line = c['nw'] if c['nw'] not in ('TBC', 'Growing') else 'Not yet stated'
    _card_open = '<div class="card">' + chr(10) + '<p><span class="tag">' + c['tagline'] + '</span> '
    body = (
        _card_open + '<span class="tag">Self-reported \u00b7 ' + srdate + '</span> ' +
        '<span class="tag">' + str(c['n_tr']) + ' videos archived</span> ' +
        '<span class="tag">Avg engagement ' + c['eng'] + '</span></p>' + chr(10) + '<div class="stat-row">' + chr(10) + shtml + '</div>' + chr(10) +
        '<p class="src">* Self-reported figure — stated by the creator in their own TikTok content, not independently verified. Source video (+ date) linked below.</p></div>' + chr(10) + chr(10) + '<h2 style="margin:32px 0 12px">Who is ' + c['name'] + '?</h2><p>' + who_html + '</p>' +
        '<h2 style="margin:32px 0 12px">How they got there</h2><p>' + journey_html + '</p>' +
        '<h2 style="margin:32px 0 12px">Net worth &amp; source (self-reported)</h2>' +
        '<p><strong>' + nw_line + '</strong> — ' + c['nw_note'] + '.<br>' +
        '<a href="' + TT + '/@' + tt + '/video/' + c['nw_vid'] + '" target="_blank" rel="noopener">Watch the source video on TikTok ↗</a> · ' +
        '<a href="' + TT + '/@' + tt + '" target="_blank" rel="noopener">@' + tt + ' on TikTok ↗</a></p>' +
        '<h2 style="margin:32px 0 12px">Key quotes</h2>' + quotes_section
    )
    html = page(c['name'] + ' (@' + h + ') — Net Worth, Journey & Quotes | SaveShare.io',
                c['name'] + ' (@' + h + '): ' + c['tagline'] + '. Self-reported net worth ' + c['nw'] + ', journey and key quotes with TikTok sources.',
                NAV_P, 'UK MONEY CREATOR PROFILE', c['name'] + ' <span style="opacity:.8">(@' + h + ')</span>', c['tagline'],
                body)
    open('p/' + h + '.html', 'w').write(html)
    print('wrote p/' + h + '.html')
