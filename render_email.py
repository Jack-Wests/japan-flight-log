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

# The real target must never reach the inbox. Matches it with or without the
# thousands comma; the lookarounds stop a longer number tripping the check.
LEAK = re.compile(r"(?<![\d,])1,?200(?![\d,])")

# Public target only. The real target lives in the push notification, nowhere else.
BUY_TARGET = 1350
WATCH_CEILING = 1500

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS BLOCK EACH RUN
# ─────────────────────────────────────────────────────────────────────────────
RUN = {
    "date_iso": "2026-09-04",
    "date_human": "Fri 4 Sep 2026",
    "verdict_headline": "\U0001F7E1 WATCH — normal range, and heading the right way",
    "best_pp": "$1,463",
    "best_all4": "$5,852",
    "target_distance": "$113 above",
    "snapshot": [
        "Cheapest way to get all four of you to the Hokkaido snow and home again today is "
        "<b>$1,463 per person &mdash; $5,852 for the four</b>, or <b>$4,389 if Hugh can&rsquo;t come</b>. "
        "That&rsquo;s Brisbane to Tokyo and back through Port Moresby, with both Japanese domestic "
        "hops and a 20kg checked bag each way already in the price.",
        "It&rsquo;s moving the right way: <b>down $91 since yesterday</b> and <b>down $60 on a week ago</b>. "
        "The last three days went $1,597, $1,554, $1,463 &mdash; so we&rsquo;re out of the dear patch and back "
        "in the normal band. Across 45 checks the price has run between <b>$1,333 and $1,688</b>.",
        "One thing to be straight about on the cheapest option: getting there means "
        "<b>an overnight stuck in Port Moresby</b> &mdash; land 5:50pm, don&rsquo;t leave until 2:10pm the next "
        "day. That&rsquo;s ~20 hours where wandering off to look around is genuinely not advisable, and "
        "30 hours door to door. The best-value option is $67pp more, flies straight into Sapporo and "
        "skips Port Moresby altogether.",
        "No verified airline sale today &mdash; the sale pages were unreachable again. "
        "Nothing to do right now: this is a watch, not a buy.",
    ],
    "options": [
        ("Cheapest",
         "\U0001F6EB Dep Brisbane (BNE) Tue 2 Feb 2:40pm &rarr; \U0001F6EC lands Tokyo (NRT) Wed 3 Feb 8:00pm "
         "<i>(Air Niugini via Port Moresby)</i>, then Thu 4 Feb 2:05pm &rarr; Sapporo (CTS) 3:40pm",
         "\U0001F6EB Dep Tokyo (NRT) Wed 17 Feb 9:40pm &rarr; \U0001F6EC lands Brisbane (BNE) Thu 18 Feb 9:40am "
         "<i>(Air Niugini via Port Moresby)</i>",
         "$1,463", "$5,852 &middot; 3: $4,389",
         "Long haul: 30h out, 11h home. 20h overnight in Port Moresby &mdash; airport hotel, not sightseeing"),
        ("Best value",
         "\U0001F6EB Dep Brisbane (BNE) Mon 1 Feb 6:10pm &rarr; \U0001F6EC lands Sapporo (CTS) Tue 2 Feb 7:15pm "
         "<i>(Singapore Airlines via Singapore &amp; Osaka, then Skymark from Kobe)</i>",
         "\U0001F6EB Dep Tokyo (HND) Tue 16 Feb 8:30am &rarr; \U0001F6EC lands Brisbane (BNE) Wed 17 Feb 7:15am "
         "<i>(Singapore Airlines via Singapore)</i>",
         "$1,530", "$6,120 &middot; 3: $4,590",
         "Long haul: 26h out, 22h home. Straight to the snow, no Port Moresby. ~7h spare in Osaka &mdash; "
         "long enough to get into town for lunch, but a 30-min ferry to Kobe airport for the last leg"),
    ],
    "options_footnote":
        "<b>Fastest sensible</b> &mdash; Brisbane &rarr; Hong Kong &rarr; Sapporo (15h, lands 2:50pm) and Tokyo &rarr; "
        "Port Moresby &rarr; Brisbane (11h home) &mdash; comes to <b>$1,733pp, $6,932 for four</b>. That&rsquo;s $270pp more "
        "than the cheapest so it doesn&rsquo;t get a row, but it&rsquo;s half the travel time of everything else. "
        "<b>Qantas QF107 Sydney&ndash;Sapporo direct</b> was priced again today: <b>$1,737pp</b> for the flight in "
        "(dep Sydney 9:05am, lands Sapporo 5:55pm same day), plus $170pp Brisbane&rarr;Sydney, $124pp for the "
        "Sapporo&rarr;Tokyo hop and $733pp home from Tokyo &mdash; <b>$2,757pp all-in, $11,028 for four</b>. Nearly "
        "double the cheapest. No date shift within &plusmn;3 days saved $100pp or more, so all options stay put.",
    "itin_title": "Option A — Cheapest",
    "itin_subtitle": "Rusutsu base &middot; 14 nights in Japan &middot; hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Tue 2 Feb", "Brisbane &rarr; Port Moresby", "Fly out 2:40pm, land 5:50pm; airport hotel, stay put"),
        ("Wed 3 Feb", "Port Moresby &rarr; Tokyo", "Depart 2:10pm, land Narita 8:00pm; overnight near the airport"),
        ("Thu 4 Feb", "Tokyo &rarr; Sapporo", "Cross to Haneda, fly 2:05pm, land Sapporo 3:40pm; pick up the car; Snow Festival lit up at night"),
        ("Fri 5 Feb", "Sapporo", "Snow Festival day 1 &mdash; full day, Susukino ice sculptures after dark"),
        ("Sat 6 Feb", "Sapporo / Otaru", "Snow Festival day 2 (Tsudome site); evening in Otaru &mdash; canal illuminations, sushi"),
        ("Sun 7 Feb", "&rarr; Rusutsu", "Drive ~2h, check in, afternoon warm-up laps"),
        ("Mon 8 Feb", "Rusutsu", "Ski day 1 &mdash; Isaac AM beginner lesson, lads ride powder"),
        ("Tue 9 Feb", "Rusutsu", "Ski day 2 &mdash; Isaac AM lesson, then all ride Mt Isola together"),
        ("Wed 10 Feb", "Rusutsu / Niseko", "Ski day 3 &mdash; day trip to Niseko (45 min)"),
        ("Thu 11 Feb", "Rusutsu", "Ski day 4 &mdash; tree runs, last big powder day"),
        ("Fri 12 Feb", "Sapporo &rarr; Tokyo", "Drive back, drop the car at Sapporo (CTS); fly down 9:00pm, land 10:40pm"),
        ("Sat 13 Feb", "Tokyo", "Shibuya, Asakusa, Shinjuku at night"),
        ("Sun 14 Feb", "Tokyo", "Akihabara, teamLab Planets"),
        ("Mon 15 Feb", "Tokyo", "Day trip to Hakone &mdash; the droppable day if you want more"),
        ("Tue 16 Feb", "Tokyo", "Tsukiji breakfast, shopping, last night out"),
        ("Wed 17 Feb", "Tokyo &rarr; home", "Depart Narita 9:40pm"),
        ("Thu 18 Feb", "&rarr; Brisbane", "Land Brisbane 9:40am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the same trip on the ground, one day earlier at each end: you land straight "
        "into Sapporo on 2 Feb with a spare day before the festival opens, ski Rusutsu 7&ndash;10 Feb, and fly "
        "home from Haneda on the morning of 16 Feb. Same four ski days, same two full Snow Festival days, "
        "same Otaru evening, same droppable Hakone day &mdash; it just costs $67pp more and skips the Port "
        "Moresby overnight.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 45. Today is the first check to land in the "
        "amber WATCH band since the targets moved &mdash; the cheapest day yet was $1,333 on 31 Jul.",
    "footer":
        "Auto-sent daily flight watch \u00b7 prices from Kiwi.com, AUD incl. 1 checked bag each way and all "
        "Japanese domestic hops \u00b7 no verified sale live today.",
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
        colour = "#1565c0" if latest else ("#c0392b" if v > WATCH_CEILING else
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
    "WATCH_CEILING": f"${WATCH_CEILING:,}",
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
assert not LEAK.search(visible), \
    "private buy target leaked into the email"

open(OUT, "w").write(html)
print(f"wrote {OUT} ({len(html):,} chars) — placeholders filled, private target absent")

text = build_text()
assert not LEAK.search(text), "private buy target leaked into the text part"
open("email.txt", "w").write(text)
print(f"wrote email.txt ({len(text):,} chars)")
