#!/usr/bin/env python3
"""Fill email-template.html with today's run and write email.html.

Edit RUN below each day, run this, then send email.html. Do NOT hand-write the
email HTML on a run — that is what made every daily email look different.

The price-log bars are generated from prices.csv so they can't drift from the
logged numbers. The private buy target must never appear here; a check at the
bottom fails the render if it does.
"""
import csv
import os
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
    "date_iso": "2026-08-19",
    "date_human": "Wed 19 Aug 2026",
    # Anything that went wrong on this run and makes the numbers below less than
    # trustworthy — a dead flight search, a connector that wouldn't answer, prices
    # carried over from a previous day. Each string becomes a bullet in a banner at
    # the top of the email. Leave [] on a clean run and no banner is drawn.
    # Jack does not read the session chat: if it isn't in here, he never finds out.
    "warnings": [],
    "verdict_headline": "🔴 HOLD — one of the dearer days we've seen",
    "best_pp": "$1,612",
    "best_all4": "$6,448",
    "target_distance": "$612 above",
    "snapshot": [
        "The cheapest way to get all four of you to the Hokkaido snow and home again is "
        "<b>$1,612 per person ($6,448 for the four)</b> — Jetstar to Osaka, a night in town, "
        "up to Sapporo the next day, and home from Tokyo with Singapore Airlines.",
        "Today is a <b>bad day to book</b>: that's <b>$191 dearer than the last check on "
        "16 Aug</b> ($1,421), and the fourth-dearest of the 29 days we've logged. A normal "
        "day is around <b>$1,421</b>; the best we've ever seen was <b>$1,333</b> on 31 July.",
        "Every quoted price includes a 20kg checked bag each way <i>and</i> the "
        "Sapporo→Tokyo hop on 12 Feb, so these are the real all-in numbers.",
        "No airline sale could be verified today — Jetstar, Qantas and Virgin's deal pages "
        "were all blocked before they loaded, so treat any sale talk as unconfirmed. "
        "Nothing to do today except wait.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Wed 3 Feb 11:45am → 🛬 lands Osaka (KIX) Wed 3 Feb 7:45pm "
         "<i>(Jetstar)</i>, night in Osaka, then 🛫 Osaka (ITM) Thu 4 Feb 1:05pm → "
         "🛬 lands Sapporo (CTS) Thu 4 Feb 2:50pm",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 4:40pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 10:45am "
         "<i>(Singapore Airlines via Singapore)</i>",
         "$1,612", "$6,448",
         "Long haul: 28h out — but 17h of it is a night and a morning in Osaka, "
         "not an airport sleep. 17h home"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Wed 3 Feb 11:45am → 🛬 lands Osaka (KIX) Wed 3 Feb 7:45pm "
         "<i>(Jetstar)</i>, night in Osaka, then 🛫 Osaka (ITM) Thu 4 Feb 7:35am → "
         "🛬 lands Sapporo (CTS) Thu 4 Feb 9:25am",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 4:40pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 10:45am "
         "<i>(Singapore Airlines via Singapore)</i>",
         "$1,632", "$6,528",
         "23h out, 17h home. $20pp more buys a whole extra day on the ground — "
         "lands 9:25am, on the snow by lunch"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Wed 3 Feb 11:45am → 🛬 lands Osaka (KIX) Wed 3 Feb 7:45pm "
         "<i>(Jetstar)</i>, night in Osaka, then 🛫 Osaka (ITM) Thu 4 Feb 7:35am → "
         "🛬 lands Sapporo (CTS) Thu 4 Feb 9:25am",
         "🛫 Dep Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am "
         "<i>(Air Niugini via Port Moresby)</i>",
         "$1,666", "$6,664",
         "23h out, 12h home — quickest trip back by 5 hours, for $54pp more than the cheapest"),
    ],
    "options_footnote":
        "The Qantas Sydney–Sapporo direct (QF107) was priced again today: <b>$1,664pp</b> for that "
        "flight, plus $115pp Brisbane→Sydney, the $134pp Sapporo→Tokyo hop and $743pp home = "
        "<b>$2,656pp all-in ($10,624 for four)</b>. On the snow at 5:55pm the same day with no "
        "overnight anywhere, but over $1,000pp more than the cheapest, so it doesn't get a row. "
        "Leaving a day earlier (Brisbane Mon 1 Feb, into Sapporo Tue 2 Feb 9:55am) comes to "
        "<b>$1,571pp</b> — $41pp cheaper, but it adds a 15th night away, and the extra night's "
        "beds and food costs the four of you more than the $164 it saves. No other date shift "
        "within ±3 days saved $100pp or more.",
    "itin_title": "Option A — Cheapest",
    "itin_subtitle": "Rusutsu base · 13 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Wed 3 Feb", "Brisbane → Osaka", "Fly out 11:45am, land Kansai 7:45pm; train into Osaka, night in town"),
        ("Thu 4 Feb", "Osaka → Sapporo", "Morning in Osaka, fly Itami 1:05pm → Sapporo 2:50pm; pick up the car; Snow Festival lights at Odori Park"),
        ("Fri 5 Feb", "Sapporo", "Snow Festival day 1 — full day, Odori and Susukino ice sculptures"),
        ("Sat 6 Feb", "Sapporo / Otaru", "Snow Festival day 2; evening in Otaru — canal illuminations and sushi"),
        ("Sun 7 Feb", "→ Rusutsu", "Drive ~2h to Rusutsu, check in, afternoon warm-up laps"),
        ("Mon 8 Feb", "Rusutsu", "Ski day 1 — Isaac AM lesson, lads ride powder"),
        ("Tue 9 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride Mt Isola together"),
        ("Wed 10 Feb", "Rusutsu / Niseko", "Ski day 3 — day trip to Niseko, 45 min up the road"),
        ("Thu 11 Feb", "Rusutsu → Sapporo", "Ski day 4 — tree runs; drive back late arvo, drop the car at Sapporo (CTS); night in Susukino"),
        ("Fri 12 Feb", "Sapporo → Tokyo", "Fly 9:30am → Narita 11:20am; afternoon in Shibuya"),
        ("Sat 13 Feb", "Tokyo", "Asakusa, Akihabara, teamLab Planets"),
        ("Sun 14 Feb", "Tokyo", "Day trip to Hakone — the droppable day if you'd rather have another Rusutsu ski"),
        ("Mon 15 Feb", "Tokyo", "Tsukiji breakfast, shopping, last night out"),
        ("Tue 16 Feb", "Tokyo → home", "Depart Haneda 4:40pm"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane 10:45am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the identical trip on the ground — it just takes the 7:35am flight "
        "out of Osaka instead of the 1:05pm one, so you land in Sapporo at 9:25am and get most "
        "of 4 Feb back. <b>Fastest sensible</b> is also the same trip, one day longer at the "
        "Tokyo end, flying home overnight through Port Moresby: 12 hours door-to-door instead of 17.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 29. Everything logged so far sits "
        "in the red HOLD band — the cheapest day yet was $1,333 on 31 Jul, the dearest $1,688 "
        "on 10 Aug.",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. 1 checked bag each way "
        "and the Sapporo→Tokyo hop · no verified sale live today.",
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


def auto_warnings():
    """Spot a broken run from its own output, without being told.

    A run that can't reach the flight search has, more than once, quietly written
    the previous day's number into the log and sent a confident red headline on top
    of it. Four identical days went out before anyone noticed. These checks read the
    files the run just produced and say so in the email instead.
    """
    out = []
    rows = list(csv.DictReader(open("prices.csv")))

    # 1. Today's row missing, or logged under someone else's date.
    if not rows:
        out.append("The price log is empty — today's check never got written down.")
    elif rows[-1]["date"] != RUN["date_iso"]:
        out.append(
            f'The newest row in the price log is <b>{rows[-1]["date"]}</b>, not today. '
            "Today's check may not have been logged, so the trend numbers below are "
            "comparing against the wrong days.")

    # 2. The same price several days running. Real fares move by a few dollars a day;
    #    an exact repeat across three checks means a failed search reusing old numbers.
    same = 1
    for a, b in zip(reversed(rows), reversed(rows[:-1])):
        if a["best_total_pp"] == b["best_total_pp"]:
            same += 1
        else:
            break
    if same >= 3:
        out.append(
            f'The best price has been <b>exactly the same for {same} checks running</b>. '
            "Real fares move most days, so this usually means the flight search failed "
            "and an old number was copied forward. <b>Worth a reply telling me to look.</b>")

    # 3. Chart older than the log it's meant to be drawing.
    try:
        if os.path.getmtime("chart-email.png") < os.path.getmtime("prices.csv"):
            out.append(
                "The chart image is older than the price log — it was not rebuilt this "
                "run, so the graph below is missing the newest days.")
    except OSError:
        out.append("The chart image is missing — the graph below will not load.")

    return out


def warnings_block():
    """The banner. Empty string on a clean run, so nothing is drawn."""
    items = auto_warnings() + list(RUN.get("warnings", []))
    if not items:
        return ""
    bullets = "".join(
        f'<tr><td style="padding:3px 0 3px 0;font-size:13.5px;line-height:1.6;'
        f'color:#7c2d12;">• {w}</td></tr>' for w in items)
    return (
        '<tr><td style="background:#fef3c7;border-radius:12px;border-left:5px solid #d97706;'
        'padding:16px 20px 16px 18px;">'
        '<p style="margin:0 0 8px;font-size:15px;font-weight:800;color:#7c2d12;">'
        '⚠️ Don\'t trust today\'s numbers yet</p>'
        '<p style="margin:0 0 8px;font-size:13.5px;line-height:1.6;color:#7c2d12;">'
        'Something went wrong on this run, so the prices below may be stale or plain '
        'wrong — read the headline with that in mind:</p>'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">{bullets}</table>'
        '</td></tr>'
        '<tr><td style="height:14px;line-height:14px;font-size:0;">&nbsp;</td></tr>')


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
    "WARNINGS_BLOCK": warnings_block(),
}

def build_text():
    """Plain-text twin of the email — required alongside the HTML part."""
    strip = lambda s: re.sub(r"<[^>]+>", "", s).replace("&amp;", "&")
    L = [f'JAPAN SNOW TRIP - DAILY CHECK - {RUN["date_human"]}', "",
         strip(RUN["verdict_headline"]),
         f'Best all-in {RUN["best_pp"]} pp - {RUN["best_all4"]} for the four lads', ""]
    problems = auto_warnings() + list(RUN.get("warnings", []))
    if problems:
        L += ["*** DON'T TRUST TODAY'S NUMBERS YET ***",
              "Something went wrong on this run, so the prices below may be stale:"]
        L += [f'  - {strip(w)}' for w in problems] + [""]
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
