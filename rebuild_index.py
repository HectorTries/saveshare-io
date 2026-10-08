#!/usr/bin/env python3
"""Rebuild index.html creator directory: sorted w/ figures first, trust wording,
search/sort/filter, tiers, topics, corrected stats, featured hero cards, fixed nav."""
import re, glob

import sys
src = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
index = open(src).read()

# ---------- 1. parse existing cards ----------
parts = index.split('<div class="card">')
head, cards_raw = parts[0], parts[1:]
last = cards_raw[-1]
m = re.search(r'(p/nextgenngpf\.html"[^>]*>View full profile.*?</p>)', last)
assert m, "tail anchor not found"
tail = last[m.end():]
cards_raw[-1] = last[:m.end()]

def parse(p):
    name = re.search(r'<h3><a[^>]*>(.*?)</a></h3>', p).group(1)
    prof = re.search(r'href="(p/[^"]+)" style="color:inherit', p).group(1)
    handle = re.search(r'tiktok\.com/@([^"]+)', p).group(1)
    av = re.search(r'src="(avatars/[^"]+)"', p).group(1)
    figs = dict((l, v) for v, l in re.findall(r'<div><strong>(.*?)</strong><span>(.*?)</span></div>', p))
    eng = re.search(r'<div><strong>([\d.]+%)</strong><span>Engagement</span>', p)
    return dict(name=name, prof=prof, handle=handle, av=av,
                fol=figs.get('Followers', '?'), nw=figs.get('Net worth', 'TBC'),
                eng=eng.group(1) if eng else None)

cards = [parse(p) for p in cards_raw]
assert len(cards) == 40, len(cards)

# ---------- 2. resolved net worths from p/ pages ----------
NW, NWDATE = {}, {}
for f in glob.glob('p/*.html'):
    h = open(f).read()
    stats = dict((l, v) for v, l in re.findall(r'<div class="stat"><strong>(.*?)</strong><span>(.*?)</span></div>', h))
    if 'Net worth*' in stats and stats['Net worth*'] != 'TBC':
        m0 = re.search('Net worth[^<]*</h2><p><strong>[^<]*</strong>(.{0,5})(.{0,120})', h)
        pre_date = ''
        if m0:
            seg = (m0.group(1) + m0.group(2))[:130]
            dm = re.search('((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* 202[56]|late 2025|[A-Z][a-z]+ 202[56])', seg)
            pre_date = dm.group(1) if dm else ''
        key = f.split('/')[1][:-5]
        NW[key] = stats['Net worth*']
        m2 = re.search(r'\((?:self-described,? )?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* 202[56]|20[12][0-9]|late 2025|see source)[^)]*\)', h)
        fixed = {'drjubairsfinance': '2025', 'iainmoneyinsights': 'late 2025',
                 'seansmoney': 'Aug 2026', 'neilinvests': 'Sep 2026'}
        if pre_date:
            NWDATE[key] = pre_date
        elif key in fixed:
            NWDATE[key] = fixed[key]
        elif m2:
            NWDATE[key] = m2.group(1)
        elif '(self-described)' in h:
            NWDATE[key] = 'Oct 2026'
        else:
            NWDATE[key] = ''

TOPICS = {
 'miarosemcgrath': (['Frugal living','Investing'],'Frugal-living author (Vogue, The Times) building wealth stylishly.'),
 'neilinvests': (['Index investing','Retirement'],'Beginner-investing educator focused on low-cost index funds.'),
 'hannahbevington': (['Investing','Payday systems'],'26-year-old sharing monthly portfolio breakdowns and payday systems.'),
 'itssophieblank': (['Coast FI','ETFs'],'London AI strategist documenting her journey to Coast FI by 40.'),
 'seansmoney': (['Beginner investing','ISAs'],'Edinburgh creator documenting his money moves and ETF basics.'),
 'ollieinvests': (['ISAs','Beginner investing'],'23-year-old engineering graduate sharing weekly portfolio updates.'),
 'drjubairsfinance': (['Daily investing','ETFs'],'Doctor-turned-investor documenting a daily investing challenge.'),
 'iainmoneyinsights': (['ISA journey','Long-term investing'],'Scottish creator sharing his real-time ISA portfolio journey.'),
 'intentionalfinance': (['Homeownership','Budgeting'],'22-year-old homeowner building wealth intentionally.'),
 'ciaraanne': (['Intentional spending','Investing'],'Curating a richer life through intentional spending and investing.'),
 'gabrielnussbaum': (['Money news','Tax'],'That Money Guy — UK money news, tax bands and investing explainers.'),
 'getontopwithdahlia': (['Budgeting','Ex-BlackRock'],'Ex-BlackRock educator helping you get on top of your finances.'),
 'theeverydaymillionaire': (['Millionaire journey','Investing'],'Documenting the everyday journey to a million.'),
 'bretandevey': (['Simple investing','Couples money'],'Simple personal finance and investing for everyone.'),
 'fellasfinance': (['Long-term wealth','Index funds'],'Helping people build long-term wealth, month by month.'),
 'tommytalksuk': (['Beginner investing','Saving'],'Ordinary guy talking investing and personal finance.'),
 'moneystocker': (['Pensions','Index funds'],'Personal finance educator breaking down pensions and index funds.'),
 'emmieedit': (['Quant finance','Financial literacy'],'11 years in quantitative finance, teaching financial literacy.'),
 'tatianamamixo': (['Financial freedom','Pensions'],'London creator pursuing financial freedom in her 30s.'),
 'allthingsmoney': (['Budgeting','Beginner'],'All Things Money — levelling up personal finances step by step.'),
 'krishkara': (['Side hustles','Investing'],'Money tips, investing and side hustles for young earners.'),
 'camrusselluk': (['Investing basics','Stocks'],'Making money, investing and the stock market easy to grasp.'),
 'financiallyher': (['Women & money','Career'],'For women who want more — money, career and confidence.'),
 'jnopwnr': (['Emergency funds','Growth'],'London-based creator on money, growth and building a life.'),
 'awrights': (['Intentional living','Saving'],'Building a life she loves — money as a tool, not a goal.'),
 'grayareafinance': (['Better decisions','Investing'],'Better money decisions without the jargon.'),
 'georgetuttle': (['Accounting','Investing'],'London accountant talking personal finance plainly.'),
 'kafilatfinance': (['Systems','Women & money'],'Helping millennial women build systems for money.'),
 'wealthmadeaccessible': (['Budgeting','Saving'],'Helping you budget, save and build wealth — accessibly.'),
 'msellyphant': (['Teacher FI','Millionaire track'],'Primary teacher on track to retire a millionaire.'),
 'amandainvests': (['Mum investors','Investing'],'Mum, investor and author on money and investing.'),
 'didifinance': (['Financial freedom','Community'],'Becoming financially free, together.'),
 'bensfinance': (['Portfolio updates','Index funds'],'UK finance creator sharing honest portfolio updates.'),
 'lupeslively': (['Money & life','Investing'],'Talking money and life, honestly.'),
 'holl005': (['Gen Z money','Learning'],'20-year-old learning money, markets and life in public.'),
 'janiicemyla': (['Student investing','Starting out'],'From student overdraft to a first invested portfolio.'),
 'markonthemoney': (['Pensions','Retirement'],'Helping you retire comfortably — pensions and investing.'),
 'admjay': (['Accountant','Investing'],'London accountant breaking down investing for beginners.'),
 'nextgenngpf': (['Gen Z money','Budgeting'],'Next-gen personal finance for young earners.'),
 'weinvestandrest': (['Early retirement','Investing'],'Invest+Rest creator with £600K+ invested toward early retirement.'),
}
PKEY = {'seans.money':'seansmoney','dr.jubairsfinance':'drjubairsfinance','iainjgeddes':'iainmoneyinsights',
 'gabriel.nussbaum':'gabrielnussbaum','tommytalks.uk':'tommytalksuk','allthingsmoney_':'allthingsmoney',
 'krish.kara':'krishkara','financiallyher_':'financiallyher','jno_pwnr':'jnopwnr','awright.s':'awrights',
 'gray.area.finance':'grayareafinance','george_tuttle':'georgetuttle','kafilat.finance':'kafilatfinance',
 'holl_005':'holl005','janiice.myla':'janiicemyla','adm.jay':'admjay','intentional.finance':'intentionalfinance',
 'ciara__anne':'ciaraanne'}

def fnum(f):
    f = f.strip()
    if f.endswith('M'): return float(f[:-1])*1e6
    if f.endswith('K'): return float(f[:-1])*1e3
    return float(f.replace(',', ''))

def tier(f):
    n = fnum(f)
    if n >= 100000: return 'Mid-tier'
    if n >= 10000: return 'Micro'
    return 'Nano'

for c in cards:
    key = PKEY.get(c['handle'], c['handle'])
    c['key'] = key
    if key in NW:
        c['nw'], c['hasfig'], c['nwdate'] = NW[key], True, NWDATE.get(key, '')
    elif c['nw'] not in ('TBC', '?'):
        c['hasfig'], c['nwdate'] = True, NWDATE.get(key, '')
    else:
        c['hasfig'], c['nwdate'] = False, ''
    c['topics'], c['desc'] = TOPICS.get(key, (['Personal finance'], c['key']))
    c['tier'] = tier(c['fol'])
    c['folnum'] = fnum(c['fol'])

total = sum(c['folnum'] for c in cards)
def fmt(n):
    return f"{n/1e6:.1f}M" if n >= 1e6 else f"{n/1e3:.0f}K"
TOTAL_S, NFIG = fmt(total), sum(1 for c in cards if c['hasfig'])

def card(c):
    ini = ''.join(w[0] for w in c['name'].split()[:2]).upper()
    if c['hasfig']:
        nw_cell = '<div><strong>' + c['nw'] + '</strong><span>Net worth*</span></div>'
        sr = ('<span class="sr-tag">Self-reported \u00b7 ' + c['nwdate'][:45] + '</span>'
              if c.get('nwdate') else '<span class="sr-tag">Self-reported \u00b7 linked to source</span>')
    else:
        nw_cell = '<div><strong class="pending">Not yet stated</strong><span>Net worth</span></div>'
        sr = ''
    eng_cell = ('<div><strong>' + c['eng'] + '</strong><span>Engagement</span></div>' if c['eng']
                else '<div><strong class="pending">\u2014</strong><span>Engagement</span></div>')
    tags = ' '.join('<span class="tag">' + t + '</span>' for t in c['topics'])
    engv = c['eng'].rstrip('%') if c['eng'] else '0'
    fb = ('<div class="fallback-avatar" aria-hidden="true">' + ini + '</div>')
    return ('<div class="card" data-name="' + (c['name'] + ' ' + c['handle']).lower()
        + '" data-fol="' + str(int(c['folnum'])) + '" data-nw="' + ('1' if c['hasfig'] else '0')
        + '" data-topics="' + ' '.join(c['topics']).lower() + '" data-eng="' + engv + '">\n'
        + '<img class="avatar" src="' + c['av'] + '" alt="' + c['name'] + '" width="56" height="56" loading="lazy" '
        + 'onerror="this.outerHTML=' + "'" + fb.replace("'", "\\'") + "'" + '">\n'
        + '<span class="tier">' + c['tier'] + '</span>\n'
        + '<h3><a href="' + c['prof'] + '" style="color:inherit;text-decoration:none">' + c['name'] + '</a></h3>\n'
        + '<div class="handle"><a href="https://www.tiktok.com/@' + c['handle'] + '" target="_blank" rel="noopener">@' + c['handle'] + ' \u2197</a></div>\n'
        + '<p class="bio">' + c['desc'] + '</p>\n'
        + '<p style="margin:0 0 10px">' + tags + '</p>\n'
        + '<div class="figures">\n'
        + '<div><strong>' + c['fol'] + '</strong><span>Followers</span></div>\n'
        + nw_cell + '\n' + eng_cell + '\n</div>\n' + sr + '\n'
        + '<p style="margin:12px 0 0"><a href="' + c['prof'] + '" style="font-size:14px;font-weight:600">View full profile \u2192</a></p>\n'
        + '</div>')

def nwnum(s):
    m = __import__('re').search(r'[\d.]+', s or '')
    v = float(m.group()) if m else 0
    if 'K' in (s or '').upper(): v *= 1e3
    if 'M' in (s or '').upper(): v *= 1e6
    return v
withfig = sorted([c for c in cards if c['hasfig']], key=lambda c: -nwnum(c['nw']))
pending = sorted([c for c in cards if not c['hasfig']], key=lambda c: -c['folnum'])
grid = ('<div id="fig-group">\n' + '\n'.join(card(c) for c in withfig) + '\n</div>\n'
    '<h3 class="pending-head">Figures pending \u2014 educators worth following</h3>\n'
    '<p class="pending-sub">These creators share money education but haven\u2019t stated a personal net worth in archived videos yet.</p>\n'
    '<div id="pend-group">\n' + '\n'.join(card(c) for c in pending) + '\n</div>')
open('/tmp/cards.html', 'w').write(grid)
open('/tmp/rebuild_vars.txt', 'w').write(TOTAL_S + '\n' + str(NFIG) + '\n')
print('cards:', len(withfig), 'with figures,', len(pending), 'pending | combined:', TOTAL_S)
print('featured:', [c['name'] for c in withfig[:4]])
feat = []
for c in withfig[:4]:
    feat.append('<a class="feat-card" href="' + c['prof'] + '"><strong>' + c['name'] + '</strong>'
        '<span>' + c['fol'] + ' followers \u00b7 ' + c['nw'] + ' net worth*</span></a>')
open('/tmp/feat.html', 'w').write('\n'.join(feat))
