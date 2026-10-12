# SaveShare.io Pillar-Cluster SEO Map (2026-10-12)

Source data: video-theme counts + Ubersuggest CSVs in
`media/inbound/` (how-to-invest x2, stocks-and-shares-isa, uk-influencers x2)
+ existing keyword shortlist in `SEO_KEYWORDS.md`.

Rule: every post targets ONE primary keyword. High volume + low SEO difficulty first.
Difficulty <= 22 = easy win. 23-30 = medium. 31+ = long-term.

Theme supply (video posts): investing 368, property 262, budgeting 140,
isa 132, tax 100, pension 89, debt 66, side-hustle 44, net-worth 16, crypto 5.

## Pillar 1: ISAs and Tax-Free Saving
FLAGSHIP (pillar): `blog/isa-beginners-guide.html` — primary: **stocks and shares isa** (49.5k, 49, hard, must-have)
- `blog/lifetime-isa-first-home-bonus.html` — lifetime isa / LISA house deposit
- `blog/emergency-funds-uk.html` — emergency fund uk / cash isa buffer
- NEW `blog/isa-transfer-rules.html` — **isa transfer** (880, 21)
- NEW `blog/isa-withdrawal-rules.html` — **isa withdrawal rules** (140, 12)
- NEW `blog/junior-isa-guide.html` — **junior isa** (140, 12)
- NEW `blog/isa-dividend-tax.html` — **dividend uk tax rate** (3600, 7) + dividend allowance (3600, 27)
- NEW `blog/average-isa-return.html` — **average return isa** (1000, 17)

## Pillar 2: Start Investing
FLAGSHIP (pillar): `blog/gen-z-start-investing.html` — primary: **how to invest uk** (320, 43) / how to invest money uk
- `blog/market-dips-etf-lupes.html` — **how to invest etf** (590, 22)
- `blog/money-moves-18-adamjay.html` — **how to invest 100k** (390, 19) angle: first 100k
- `blog/five-monthly-habits-dahlia.html` — monthly investing habits
- NEW `blog/how-to-invest-sp500-uk.html` — **how to invest in s&p 500 uk** (1300, 22)
- NEW `blog/how-to-invest-50k.html` — **how to invest 50k** (170, 17) + 50k uk (50, 18)
- NEW `blog/how-to-invest-200k-passive-income.html` — **how to invest 200k for passive income** (50, 19)
- NEW `blog/how-to-invest-trading212.html` — **how to invest trading 212** (30, 17)
- NEW `blog/how-to-invest-million.html` — **how to invest a million pounds** (70, 15)
- NEW `blog/how-to-invest-recession.html` — **how to invest during recession** (~20, 5)

## Pillar 3: Pensions and Retirement
FLAGSHIP (pillar): `blog/pension-basics-uk.html` — primary: uk pension / how pensions work uk
- `blog/retire-350k-trinity-study.html` — **trinity study / retire on 350k**
- `blog/teacher-to-millionaire.html` — teacher pension millionaire story
- `blog/five-monthly-habits-dahlia.html` — (cross-link) monthly pension contributions
- NEW `blog/sipp-vs-workplace-pension.html` — sipp vs workplace pension
- NEW `blog/pension-contribution-limits-uk.html` — pension annual allowance uk
- NEW `blog/retire-early-uk-fire.html` — FIRE uk / retire early uk

## Pillar 4: Debt, Budgeting and Saving
FLAGSHIP (pillar): `blog/kill-debt-first.html` — primary: how to get out of debt uk
- `blog/emergency-funds-uk.html` — (cross-link) emergency fund before investing
- `blog/women-money-uk.html` — budgeting systems, sinking funds
- NEW `blog/average-uk-personal-debt.html` — **average uk personal debt** (40, 6)
- NEW `blog/sinking-funds-guide.html` — sinking funds uk (creator-proven: Sophie, Mia)
- NEW `blog/lifestyle-creep.html` — lifestyle creep / leaky money habits

## Pillar 5: Property and First Homes
FLAGSHIP (pillar): `blog/lifetime-isa-first-home-bonus.html` — primary: lifetime isa first home
- `blog/teacher-to-millionaire.html` — (cross-link) renting vs buying (Sophie rents, BBC-featured)
- NEW `blog/rent-vs-buy-uk.html` — rent vs buy uk (strong creator supply: Sophie, Mia)
- NEW `blog/how-much-house-deposit-uk.html` — how much deposit for house uk
- NEW `blog/first-time-buyer-schemes-uk.html` — first time buyer schemes (strong adm.jay video supply)

## Pillar 6: Wealth Mindset, Creators and Net Worth
FLAGSHIP (pillar): `blog/400k-net-worth-tatiana.html` — primary: uk personal finance creator stories
- `blog/quant-investing-emmie.html` — quant / ETF investing
- `blog/side-hustles-krish.html` — side hustles uk 2026
- `blog/crypto-without-getting-drained.html` — **how to invest in crypto** (1000, 27)
- NEW `blog/uk-money-influencers.html` — **uk influencers** (880, 34) + famous uk influencers (30, 13)
- NEW `blog/how-much-influencers-earn-uk.html` — **how much do uk influencers earn** (0 vol now, diff 4, zero-competition capture)
- NEW `blog/net-worth-progression-20s.html` — net worth by age uk (net-worth theme: highest engagement 0.094)

## Internal linking rules (wired into build_blog.py + recipe)
1. Every cluster post links UP to its pillar flagship ("Start with the full guide: ...").
2. Every pillar links DOWN to all its cluster posts (Keep-reading block).
3. Sibling cross-links where topics overlap (marked cross-link above).
4. Every post already links creator profiles (`../p/<handle>.html` q-mentions); new posts must cite 4-6 creators per BLOG_RECIPE.md.
5. Blog index (`blog/index.html`) renders a pillar nav section (built by build_blog.py from PILLARS map).
6. Related block markup: `<aside class="related"><h2>Keep reading</h2><ul>...` injected before closing disclaimers.

## Status
- [x] 2026-10-12: map written, related blocks injected into 17 existing posts, pillar nav added to blog index
- [ ] Next: daily-post agents pick NEW keywords top-down (easy wins first: dividend uk tax rate, isa withdrawal rules, junior isa, recession)
