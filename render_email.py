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
    "date_iso": "2026-08-20",
    "date_human": "Thu 20 Aug 2026",
    "verdict_headline": "🔴 HOLD — cheaper than yesterday, still not close",
    "best_pp": "$1,485",
    "best_all4": "$5,941",
    "target_distance": "$485 above",
    "snapshot": [
        "The cheapest way to get all four of you to the Hokkaido snow and home again is "
        "<b>$1,485 per person (~$5,941 for the four)</b> — flying Brisbane→Tokyo return with "
        "Air Niugini through Port Moresby, plus the two hops up to Sapporo and back.",
        "That's <b>down $127 on yesterday</b> ($1,612), which is a decent one-day move, but it's "
        "still nearly $500 clear of the target. Across 30 days of checks the price has run "
        "between <b>$1,333 and $1,688</b>, so today sits mid-pack — better than the last week, "
        "nowhere near a low.",
        "The catch on the cheapest option is a <b>20-hour overnight stuck in Port Moresby</b> on the "
        "way over — 30h20m door to door. Paying $165pp more swaps that for a 12-hour daytime stop "
        "in Ho Chi Minh City you can actually leave the airport for.",
        "No airline sale could be verified today — the Jetstar, Qantas and Virgin deal pages all "
        "refused to load. Nothing time-sensitive. Sit tight.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 2:40pm → 🛬 lands Tokyo (NRT) Wed 3 Feb 8:00pm "
         "<i>(Air Niugini, overnight in Port Moresby)</i>, then Tokyo (HND) → Sapporo (CTS) "
         "Thu 4 Feb 3:50pm–5:20pm",
         "🛫 Dep Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am "
         "<i>(Air Niugini via Port Moresby)</i>",
         "$1,485", "$5,941",
         "Long haul: 30h20m there, 20h of it stuck overnight in Port Moresby — brutal. "
         "The 11h flight home is the fastest of the lot"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Wed 3 Feb 11:40pm → 🛬 lands Tokyo (HND) Fri 5 Feb 1:00am "
         "<i>(VietJet via Ho Chi Minh City)</i>, then Tokyo (HND) → Sapporo (CTS) Fri 5 Feb",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 10:00am → 🛬 lands Brisbane (BNE) Wed 17 Feb 7:15am "
         "<i>(Singapore Airlines via Singapore)</i>",
         "$1,650", "$6,602",
         "26h20m there — but 12h15m of it is daytime in Ho Chi Minh City, easily long enough "
         "to get into town. Downside: lands Tokyo at 1am, so you wait out the night at the airport"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 8:40am → 🛬 lands Tokyo (HND) Tue 2 Feb 10:50pm "
         "<i>(Korean Air via Seoul)</i>, then Tokyo (HND) → Sapporo (CTS) Wed 3 Feb 8:00am–9:30am",
         "🛫 Dep Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am "
         "<i>(Air Niugini via Port Moresby)</i>",
         "$1,780", "$7,121",
         "14h10m there, 11h home — half the travel time of the cheapest, and you're on the "
         "snow a day earlier. $295pp more"),
    ],
    "options_footnote":
        "The Qantas Sydney–Sapporo direct (QF107, dep Sydney 9:05am, lands Sapporo 5:55pm the same "
        "day) prices at <b>$1,670pp for that one leg</b>, plus $132pp to get Brisbane→Sydney first, "
        "plus $746pp home from Tokyo and the $135pp Sapporo→Tokyo hop — <b>$2,683pp all-in "
        "($10,731 for the four)</b>. Nearly double the cheapest, so it doesn't get a row. No date "
        "shift within ±3 days of the windows saved $100pp or more, so all three options stay put.",
    "itin_title": "Option A — Cheapest",
    "itin_subtitle": "Rusutsu base · 14 nights in Japan · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Tue 2 Feb", "Brisbane → Port Moresby", "Fly out 2:40pm, land 5:50pm; overnight at the airport hotel"),
        ("Wed 3 Feb", "Port Moresby → Tokyo", "Depart 2:10pm, land Narita 8:00pm; overnight near the airport"),
        ("Thu 4 Feb", "Tokyo → Sapporo", "Morning in Tokyo, afternoon hop to Sapporo (CTS), pick up the car; Snow Festival by night at Odori Park"),
        ("Fri 5 Feb", "Sapporo / Otaru", "Snow Festival day 2 — ice sculptures at Susukino; evening in Otaru, canal lights and sushi"),
        ("Sat 6 Feb", "→ Rusutsu", "Drive ~2h to Rusutsu, check in, afternoon warm-up laps"),
        ("Sun 7 Feb", "Rusutsu", "Ski day 1 — Isaac AM lesson, lads ride powder"),
        ("Mon 8 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride Mt Isola together"),
        ("Tue 9 Feb", "Rusutsu / Niseko", "Ski day 3 — day-trip to Niseko (45 min up the road)"),
        ("Wed 10 Feb", "Rusutsu", "Ski day 4 — tree runs, last big powder day"),
        ("Thu 11 Feb", "→ Sapporo", "Drive back, drop the car at Sapporo (CTS); night out in Susukino"),
        ("Fri 12 Feb", "Sapporo", "Nijo market breakfast, Sapporo Beer Museum, Mt Moiwa ropeway at dusk"),
        ("Sat 13 Feb", "Sapporo → Tokyo", "Fly 8:30am → Haneda 10:10am; afternoon in Shibuya"),
        ("Sun 14 Feb", "Tokyo", "Asakusa, Akihabara, teamLab Planets"),
        ("Mon 15 Feb", "Tokyo", "Day trip to Hakone — the droppable day if you'd rather have another Rusutsu ski"),
        ("Tue 16 Feb", "Tokyo", "Tsukiji breakfast, shopping, last night out in Shinjuku"),
        ("Wed 17 Feb", "Tokyo → home", "Last morning, depart Narita 9:40pm"),
        ("Thu 18 Feb", "→ Brisbane", "Land Brisbane 9:40am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the same Rusutsu trip on the ground — it just starts a day later, "
        "swaps the Port Moresby overnight for a day in Ho Chi Minh City, and comes home a day "
        "earlier via Singapore. <b>Fastest sensible</b> is the same trip again, leaving a day "
        "sooner so you're skiing earlier and cutting the trip over from 30 hours to 14.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 30. Everything logged so far sits in "
        "the red HOLD band — the cheapest day yet was $1,333 on 31 Jul and again on 1 Aug.",
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
