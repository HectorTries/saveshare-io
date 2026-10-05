#!/usr/bin/env python3
"""Build blog/index.html + patch index.html cards."""
from build_pages import page, NAV_BLOG, CSS, TT

ADVICE = [
 ("Start small — £10 a week still counts", "Start investing", [
   ("If you're waiting until you have more money to invest, you're doing it wrong. I'm doing it with just £10 a week.",
    "seansmoney", "Sean", "7669798085471653142"),
   ("I made my first investment of £100 in the summer of 2018.",
    "itssophieblank", "Sophie Blank", "7681352811250076950"),
   ("Me and my sister start investing with £100! Who ends up with more?",
    "miarosemcgrath", "Mia Rose", "7689461153717636374"),
 ]),
 ("Pay yourself first with systems, not willpower", "Saving", [
   ("Building wealth doesn't just happen. You really have to curate it and put certain systems in place.",
    "hannahbevington", "Hannah Bevington", "7682883142197202198"),
   ("My sinking funds are the one reason I pay off my credit card every single month and I never go into debt.",
    "itssophieblank", "Sophie Blank", "7675026659027815702"),
   ("There's these things in personal finance called sinking funds — pots of money so you can set aside money beforehand for an event.",
    "miarosemcgrath", "Mia Rose", "7689476178129849622"),
 ]),
 ("Kill high-interest debt before anything else", "Saving", [
   ("Get rid of high interest debt. I'm talking credit cards, Klarna.",
    "miarosemcgrath", "Mia Rose", "7684166553079778582"),
   ("Once I paid [my student loan] off, my net worth skyrocketed.",
    "itssophieblank", "Sophie Blank", "7681352811250076950"),
   ("The second thing I do [on payday] is I pay off any high interest debts.",
    "hannahbevington", "Hannah Bevington", "7682883142197202198"),
 ]),
 ("Keep an emergency fund — 3 months minimum", "Saving", [
   ("Have 3 months worth of living expenses saved… when I left my 9 to 5, I had 12 months saved.",
    "miarosemcgrath", "Mia Rose", "7684166553079778582"),
   ("Put away [money] in your emergency fund in a high yield savings account.",
    "ollieinvests", "Ollie Invests", "7692763293726805270"),
   ("I had no savings… despite being in the workforce for four years. [Now I have] around £75,000 saved.",
    "seansmoney", "Sean", "7689003263584193814"),
 ]),
 ("Buy the market — don't pick stocks", "Investing", [
   ("Rich girls don't panic and pick stocks, they buy the market and move on. Every month, I buy exactly 3 funds.",
    "itssophieblank", "Sophie Blank", "7679903080535657750"),
   ("I just wanna match the all world. If I do that, I actually will beat most [stock pickers].",
    "neilinvests", "Neil Invests", "7690258184518274337"),
   ("Use ETFs, diversify your investments and think long term… 70% of my money goes straight into a FTSE world fund.",
    "ollieinvests", "Ollie Invests", "7691726292114279702"),
 ]),
 ("Contributions matter more than returns (at first)", "Investing", [
   ("The biggest thing that's gonna impact your portfolio performance for a number of years is your contributions into it, not the returns.",
    "neilinvests", "Neil Invests", "7690258184518274337"),
   ("It's important to build the habits of investing early… so that when you do have more money, you understand how the stock market works.",
    "seansmoney", "Sean", "7669798085471653142"),
   ("I invest whatever I can. Sometimes it's £50 a month, other times it's two, three, four thousand.",
    "hannahbevington", "Hannah Bevington", "7682883142197202198"),
 ]),
 ("Use your £20,000 ISA allowance every year", "ISAs", [
   ("You get an ISA allowance, which is £20,000 every tax year.",
    "miarosemcgrath", "Mia Rose", "7689476178129849622"),
   ("Here's how to open a Stocks & Shares ISA in under 10 minutes… Your allowance is £20,000 a year.",
    "ollieinvests", "Ollie Invests", "7691802357973126422"),
   ("If you're wanting to build sustainable long term wealth… respectfully, your cash ISA isn't [enough].",
    "hannahbevington", "Hannah Bevington", "7692825250110737686"),
 ]),
 ("Saving alone keeps you broke — invest to beat inflation", "Mindset", [
   ("Saving money was keeping me broke… inflation [is] constantly eating away at the purchasing power of your money.",
    "iainmoneyinsights", "Iain Geddes", "7578188154323127583"),
   ("Inflation erodes the buying power of our money. £10,000 today is not worth the same as £10,000 will be in the future.",
    "miarosemcgrath", "Mia Rose", "7684543907404958979"),
   ("I was putting the effort in, but I was getting nowhere fast… saving and investing are two completely different things.",
    "iainmoneyinsights", "Iain Geddes", "7578188154323127583"),
 ]),
 ("Don't panic-sell — think in decades", "Mindset", [
   ("Do not panic sell… Remember why you invested in them in the first place. Think of that long-term picture.",
    "iainmoneyinsights", "Iain Geddes", "7578185208575315231"),
   ("Keep that longterm mindset!",
    "iainmoneyinsights", "Iain Geddes", "7578183020323032351"),
   ("18% up in 2 weeks is a phenomenal gain… It's easy to show you just one snapshot. I am building my financial future.",
    "neilinvests", "Neil Invests", "7690122191622409504"),
 ]),
 ("Watch out for lifestyle creep & leaky habits", "Mindset", [
   ("As soon as you get a pay rise, it's so easy to just start spending that extra money rather than saving.",
    "ollieinvests", "Ollie Invests", "7693093069448613142"),
   ("Check for cashback before you buy anything, and check for a referral or welcome offer before you sign up for anything.",
    "seansmoney", "Sean", "7680952036262792470"),
   ("I treat myself to a £100 gift every month… I want to enjoy my income. I'm not sorry about that.",
    "hannahbevington", "Hannah Bevington", "7681347693221793046"),
 ]),
]

THEMES = ["Start investing", "Saving", "Investing", "ISAs", "Mindset"]
sections = []
for theme in THEMES:
    items = [(t, qs) for t, th, qs in ADVICE if th == theme]
    cards = []
    for title, qs in items:
        qs_html = "\n".join(
            f'<blockquote>“{q}”<cite>— <a href="../p/{h}.html">{name}</a> (<a href="{TT}/@{h}/video/{v}" target="_blank" rel="noopener">TikTok ↗</a>)</cite></blockquote>'
            for q, h, name, v in qs)
        cards.append(f'<div class="card"><h2>{title}</h2>\n{qs_html}</div>')
    sections.append(f'<h2 style="margin:36px 0 8px">{theme}</h2>\n' + "\n".join(cards))

body = f"""<p>Actionable money advice quoted word-for-word from UK creators' own TikTok videos. Every quote links to the creator's profile and the original video — check the source yourself.</p>
<p><span class="tag">{len(ADVICE)} advice entries</span> <span class="tag">8 creators</span> <span class="tag">Updated 5 Oct 2026</span></p>
""" + "\n".join(sections) + """
<p style="margin-top:32px"><a href="../index.html#creators">← Browse all creators</a></p>"""

html = page("Money Advice from UK Creators — Quotes with Sources | SaveShare.io",
            "Real money advice quoted from UK TikTok creators: saving, investing, ISAs and mindset. Every quote attributed with links to creator profiles and source videos.",
            NAV_BLOG, "MONEY ADVICE HUB", "Money advice, straight from creators",
            "Quoted from their own videos — attributed, linked, verifiable.",
            body)
open("blog/index.html", "w").write(html)
print(f"wrote blog/index.html ({len(ADVICE)} entries)")
