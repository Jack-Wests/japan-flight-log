#!/usr/bin/env python3
"""Fill email-template.html with today's run and write email.html.

Edit RUN below each day, run this, then send email.html. Do NOT hand-write the
email HTML on a run — that is what made every daily email look different.

The price-log bars are generated from prices.csv so they can't drift from the
logged numbers. The private buy target must never appear here; a check at the
bottom fails the render if it does.
"""
import csv
import re
import subprocess
from datetime import datetime

TEMPLATE = "email-template.html"
OUT = "email.html"

# Public target only. The real target lives in the push notification, nowhere else.
BUY_TARGET = 1000

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS BLOCK EACH RUN
# ─────────────────────────────────────────────────────────────────────────────
RUN = {
    "date_iso": "2026-08-21",
    "date_human": "Fri 21 Aug 2026",
    "verdict_headline": "🔴 HOLD — dearer again today",
    "best_pp": "$1,554",
    "best_all4": "$6,216",
    "target_distance": "$554 above",
    "snapshot": [
        "The cheapest way to get all four of you to the Hokkaido snow and home again "
        "today is <b>$1,554 per person ($6,216 for the four)</b> — Jetstar to Osaka, a "
        "night by the airport, a morning hop up to Sapporo, then home from Tokyo through "
        "Singapore.",
        "That's <b>$69 dearer than yesterday</b> ($1,485) and <b>$85 dearer than a week "
        "ago</b> ($1,469). Nothing's broken — it's the same restless $1,300–$1,700 band "
        "the price has bounced around in all month — but today is the wrong end of it. "
        "Across 31 days of checks the cheapest we've seen was <b>$1,333</b> (31 Jul) and "
        "the dearest <b>$1,688</b> (10 Aug).",
        "Worth a look further down the table: for <b>$74pp more</b> the fastest option "
        "gets you home in <b>11 hours instead of 20</b>. That's the one real choice on "
        "offer today.",
        "<b>No airline sale could be verified.</b> All three sale pages — Jetstar, Qantas "
        "and Virgin — were blocked outright today, so there's nothing to report as live. "
        "Nothing to do; sit tight.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 11:45am → 🛬 lands Sapporo (CTS) Tue 2 Feb 9:55am "
         "<i>(via Osaka (KIX) — Jetstar, then Peach)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 10:00am → 🛬 lands Brisbane (BNE) Wed 17 Feb 7:15am "
         "<i>(via Singapore — Singapore Airlines)</i>",
         "$1,554", "$6,216",
         "23h out, 20h home. The 12h stop in Osaka is a cheap hotel by the airport, not a "
         "night on the floor. 5h in Singapore coming home — enough for Jewel and a feed, "
         "not enough for town"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 11:45am → 🛬 lands Sapporo (CTS) Tue 2 Feb 9:55am "
         "<i>(via Osaka (KIX) — Jetstar, then Peach)</i>",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 4:40pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 10:45am "
         "<i>(via Singapore — Singapore Airlines)</i>",
         "$1,555", "$6,220",
         "23h out, 17h home. One dollar more than the cheapest, and it buys a last morning "
         "in Tokyo plus 3h less flying. The Singapore connection is a tight 90 min, but "
         "it's the same airline so you're covered if it slips"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 11:05am → 🛬 lands Sapporo (CTS) Wed 3 Feb 10:00am "
         "<i>(via Seoul (ICN) — Jetstar, then Jeju Air)</i>",
         "🛫 Dep Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am "
         "<i>(via Port Moresby — Air Niugini)</i>",
         "$1,628", "$6,512",
         "24h out, but home in 11h — nine hours quicker than the cheapest for $74pp. The "
         "way over is an overnight in Seoul: land 8pm, airport hotel, away again at 7am"),
    ],
    "options_footnote":
        "The <b>Qantas QF107 Sydney–Sapporo direct</b> was priced again today: <b>$1,664pp</b> "
        "for the flight in, plus about $112pp for the Brisbane→Sydney hop, plus the "
        "Sapporo→Tokyo hop and the flight home — <b>$2,655pp all-in ($10,620 for four)</b>. It "
        "puts you on the snow at 5:55pm the same day with no overnight anywhere, but it's "
        "about $1,100pp more than the cheapest, so it doesn't get a row. Two other notes: a "
        "Brisbane⇄Tokyo return via Taipei totalled <b>$1,532pp</b> — $22 less — but its dates "
        "lock you into a 16-night trip, and two extra nights of accommodation wipe that out "
        "several times over. And no date shift of up to ±3 days saved $100pp or more, so all "
        "three options stay on their natural dates.",
    "itin_title": "Option A — Cheapest",
    "itin_subtitle": "Rusutsu base · 14 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Mon 1 Feb", "Brisbane → Osaka", "Fly out 11:45am, land Kansai 7:45pm; hotel by the airport"),
        ("Tue 2 Feb", "Osaka → Sapporo", "Morning flight, land Sapporo (CTS) 9:55am; pick up the hire car, check in"),
        ("Wed 3 Feb", "Sapporo", "Nijo fish market, Mt Moiwa ropeway at dusk — festival opens tomorrow"),
        ("Thu 4 Feb", "Sapporo", "Snow Festival day 1 — the big Odori Park sculptures"),
        ("Fri 5 Feb", "Sapporo / Otaru", "Snow Festival day 2; evening in Otaru — canal illuminations, sushi"),
        ("Sat 6 Feb", "→ Rusutsu", "Drive ~2h to Rusutsu, check in, afternoon warm-up laps"),
        ("Sun 7 Feb", "Rusutsu", "Ski day 1 — Isaac AM lesson, lads ride powder"),
        ("Mon 8 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride Mt Isola together"),
        ("Tue 9 Feb", "Rusutsu / Niseko", "Ski day 3 — day-trip to Niseko (45 min down the road)"),
        ("Wed 10 Feb", "Rusutsu", "Ski day 4 — tree runs, last big powder day"),
        ("Thu 11 Feb", "→ Sapporo", "Drive back to Sapporo; night out in Susukino"),
        ("Fri 12 Feb", "Sapporo → Tokyo", "Drop the car at Sapporo (CTS), fly 9:30am→11:20am; afternoon in Shibuya"),
        ("Sat 13 Feb", "Tokyo", "Asakusa, Akihabara, teamLab Planets"),
        ("Sun 14 Feb", "Tokyo", "Day trip to Hakone — the droppable day if you'd rather ski"),
        ("Mon 15 Feb", "Tokyo", "Tsukiji breakfast, shopping, last night out"),
        ("Tue 16 Feb", "Tokyo → home", "Depart Narita 10:00am"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane 7:15am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is exactly the same trip on the ground — same flights over, same "
        "hire car, same Rusutsu week. Only the last day changes: a free morning in Tokyo, then "
        "out of Haneda at 4:40pm instead of Narita at 10am. <b>Fastest sensible</b> shifts the "
        "whole trip a day later (land Sapporo 3 Feb, home overnight on 17 Feb), which trades "
        "the spare Sapporo city day at the start for a spare Hokkaido day at the end — still "
        "14 nights, still four ski days at Rusutsu, still two full Snow Festival days.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 31. Every day logged so far sits "
        "in the red HOLD band — the cheapest yet was $1,333 on 31 Jul, the dearest $1,688 on "
        "10 Aug.",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. 1 checked bag each way "
        "· no verified sale live today.",
}
# ─────────────────────────────────────────────────────────────────────────────

TH_TD = "padding:9px 10px;font-size:12.5px;color:#3d4757;line-height:1.5;border-bottom:1px solid #eef0f3;vertical-align:top;"


def options_rows():
    out = []
    for label, there, home, pp, all4, note in RUN["options"]:
        out.append(
            f'<tr>'
            f'<td style="{TH_TD}font-weight:700;color:#1a202c;">{label}</td>'
            f'<td style="{TH_TD}">{there}</td>'
            f'<td style="{TH_TD}">{home}</td>'
            f'<td style="{TH_TD}text-align:center;font-weight:700;color:#1a202c;white-space:nowrap;">{pp}</td>'
            f'<td style="{TH_TD}text-align:center;white-space:nowrap;">{all4}</td>'
            f'<td style="{TH_TD}">{note}</td>'
            f'</tr>')
    return "".join(out)


def itin_rows():
    out = []
    for date, loc, plan in RUN["itinerary"]:
        out.append(
            f'<tr>'
            f'<td style="{TH_TD}white-space:nowrap;">{date}</td>'
            f'<td style="{TH_TD}">{loc}</td>'
            f'<td style="{TH_TD}">{plan}</td>'
            f'</tr>')
    return "".join(out)


def price_log_rows():
    """Bars straight from prices.csv, so they can't disagree with the log."""
    allrows = list(csv.DictReader(open("prices.csv")))
    rows = allrows[-10:]                      # the chart above carries the full history
    vals = [float(r["best_total_pp"]) for r in allrows]
    top = max(vals) * 1.06
    out = []
    for i, r in enumerate(rows):
        latest = i == len(rows) - 1
        v = float(r["best_total_pp"])
        pct = max(4, round(v / top * 100))
        colour = "#1565c0" if latest else ("#c0392b" if v > 1200 else
                                           "#f9a825" if v > BUY_TARGET else "#2e7d32")
        label = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%a %-d %b")
        lstyle = ("font-size:12.5px;padding:5px 10px 5px 0;white-space:nowrap;" +
                  ("font-weight:700;color:#1565c0;" if latest else "color:#3d4757;"))
        vstyle = ("font-size:12.5px;padding:5px 0 5px 10px;text-align:right;white-space:nowrap;" +
                  ("font-weight:700;color:#1565c0;" if latest else "font-weight:600;color:#3d4757;"))
        out.append(
            f'<tr><td style="{lstyle}">{label}</td>'
            f'<td style="padding:5px 0;width:100%;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td style="width:{pct}%;background:{colour};height:17px;line-height:17px;'
            f'font-size:0;border-radius:3px 0 0 3px;">&nbsp;</td>'
            f'<td style="background:#eceff3;height:17px;line-height:17px;font-size:0;'
            f'border-radius:0 3px 3px 0;">&nbsp;</td>'
            f'</tr></table></td>'
            f'<td style="{vstyle}">${v:,.0f}</td></tr>')
    return "".join(out)


def chart_branch():
    """Branch the chart image is served from — read it from git rather than
    hardcoding, so the URL still resolves whichever branch the run pushes to."""
    try:
        b = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           capture_output=True, text=True, check=True).stdout.strip()
        return b if b and b != "HEAD" else "main"
    except Exception:
        return "main"


def deltas():
    """Work the two comparison rows out from prices.csv.

    The log is not reliably daily — there was a 9-day gap between 27 Jul and
    5 Aug — so never claim "since yesterday". Say which date is actually being
    compared against, and say so plainly when there's nothing to compare to.
    """
    rows = list(csv.DictReader(open("prices.csv")))
    today = datetime.strptime(rows[-1]["date"], "%Y-%m-%d")
    now = float(rows[-1]["best_total_pp"])
    prior = rows[:-1]

    def move(then):
        d = now - then
        if d == 0:
            return "no change"
        return f'{"↑" if d > 0 else "↓"} ${abs(d):,.0f}'

    def fmt(dt):
        return dt.strftime("%-d %b")

    # Row 1: the previous check, whenever that was.
    if not prior:
        l1, v1 = "Since last check", "first check — no history yet"
    else:
        prev = prior[-1]
        pdt = datetime.strptime(prev["date"], "%Y-%m-%d")
        gap = (today - pdt).days
        when = "yesterday" if gap == 1 else f"{gap} days ago"
        l1 = f"Since last check ({when}, {fmt(pdt)})"
        v1 = move(float(prev["best_total_pp"]))

    # Row 2: a longer view. Prefer the nearest check at least a week back, but if
    # that's the same entry row 1 already used (gappy log), show the first check
    # instead so the two rows never say the same thing twice.
    week = [r for r in prior
            if (today - datetime.strptime(r["date"], "%Y-%m-%d")).days >= 7]
    pick, label = None, None
    if week and (not prior or week[-1]["date"] != prior[-1]["date"]):
        pick, label = week[-1], "Since a week back"
    elif len(prior) > 1:
        pick, label = prior[0], "Since the first check"

    if pick:
        pdt = datetime.strptime(pick["date"], "%Y-%m-%d")
        l2 = f"{label} ({fmt(pdt)})"
        v2 = move(float(pick["best_total_pp"]))
    else:
        l2, v2 = "Longer trend", "not enough history yet"

    return l1, v1, l2, v2


_d1l, _d1v, _d2l, _d2v = deltas()

P = "margin:0 0 11px;font-size:14.5px;line-height:1.65;color:#2d3748;"

VALUES = {
    "DATE_HUMAN": RUN["date_human"],
    "DATE_ISO": RUN["date_iso"],
    "CHART_BRANCH": chart_branch(),
    "VERDICT_HEADLINE": RUN["verdict_headline"],
    "BEST_PP": RUN["best_pp"],
    "BEST_ALL4": RUN["best_all4"],
    "BUY_TARGET": f"${BUY_TARGET:,}",
    "DELTA_1_LABEL": _d1l, "DELTA_1_VALUE": _d1v,
    "DELTA_2_LABEL": _d2l, "DELTA_2_VALUE": _d2v,
    "TARGET_DISTANCE": RUN["target_distance"],
    "SNAPSHOT_PARA": "".join(f'<p style="{P}">{p}</p>' for p in RUN["snapshot"]),
    "OPTIONS_ROWS": options_rows(),
    "OPTIONS_FOOTNOTE": RUN["options_footnote"],
    "ITIN_TITLE": RUN["itin_title"],
    "ITIN_SUBTITLE": RUN["itin_subtitle"],
    "ITIN_ROWS": itin_rows(),
    "ITIN_FOOTNOTE": RUN["itin_footnote"],
    "PRICE_LOG_ROWS": price_log_rows(),
    "PRICE_LOG_FOOTNOTE": RUN["price_log_footnote"],
    "FOOTER_LINE": RUN["footer"],
}

def build_text():
    """Plain-text twin of the email — required alongside the HTML part."""
    strip = lambda s: re.sub(r"<[^>]+>", "", s).replace("&amp;", "&")
    L = [f'JAPAN SNOW TRIP - DAILY CHECK - {RUN["date_human"]}', "",
         strip(RUN["verdict_headline"]),
         f'Best all-in {RUN["best_pp"]} pp - {RUN["best_all4"]} for the four lads', ""]
    L += [strip(p) for p in RUN["snapshot"]] + [""]
    d1l, d1v, d2l, d2v = deltas()
    L += [f'{d1l}: {d1v}',
          f'{d2l}: {d2v}',
          f'Distance from buy target (${BUY_TARGET:,}): {RUN["target_distance"]}',
          "", "TRIP OPTIONS", ""]
    for label, there, home, pp, all4, note in RUN["options"]:
        L += [f'{label} - {pp} pp / {all4} for four',
              f'  There: {strip(there)}',
              f'  Home:  {strip(home)}',
              f'  {note}', ""]
    L += [strip(RUN["options_footnote"]), "",
          RUN["itin_title"].upper(), strip(RUN["itin_subtitle"]), ""]
    for date, loc, plan in RUN["itinerary"]:
        L.append(f'  {date:<12} {loc:<20} {plan}')
    L += ["", strip(RUN["itin_footnote"]), "", "PRICE LOG", ""]
    for r in csv.DictReader(open("prices.csv")):
        d = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%a %-d %b")
        L.append(f'  {d:<12} ${float(r["best_total_pp"]):,.0f}')
    L += ["", strip(RUN["price_log_footnote"]), "", strip(RUN["footer"])]
    return "\n".join(L)


html = open(TEMPLATE).read()
# Drop the template's own documentation comments — they're for whoever edits the
# template, not for the inbox, and they'd otherwise ship in every email.
html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
for k, v in VALUES.items():
    html = html.replace("{{%s}}" % k, v)

left = set(re.findall(r"\{\{(\w+)\}\}", html))
assert not left, f"unfilled placeholders: {sorted(left)}"
# Check the visible text only — CSS like font-weight:800 is not a leak.
visible = re.sub(r"<[^>]+>", " ", html)
assert not re.search(r"(?<![\d,])800(?![\d,])", visible), \
    "private buy target leaked into the email"

open(OUT, "w").write(html)
print(f"wrote {OUT} ({len(html):,} chars) — placeholders filled, private target absent")

text = build_text()
assert not re.search(r"(?<![\d,])800(?![\d,])", text), "private buy target leaked into the text part"
open("email.txt", "w").write(text)
print(f"wrote email.txt ({len(text):,} chars)")
