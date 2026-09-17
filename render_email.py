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

# One target: $1,430. No private target.
BUY_TARGET = 1430

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS BLOCK EACH RUN
# ─────────────────────────────────────────────────────────────────────────────
RUN = {
    "date_iso": "2026-09-17",
    "date_human": "Thu 17 Sep 2026",
    "verdict_headline": "🔴 HOLD — dear side, sit tight",
    "best_pp": "$1,609",
    "best_all4": "$6,437",
    "target_distance": "$179 above",
    "snapshot": [
        "The cheapest all-in way to get all four of you into the snow at Sapporo (CTS) and "
        "home from Tokyo is <b>$1,609 per person — about $6,437 for the four, or $4,828 if it's "
        "just the three of you</b> (fly in via Seoul and Tokyo, ski, then a short hop back to "
        "Tokyo and home). Our buy line is $1,430, so today sits <b>$179 above it</b> — a clear HOLD.",
        "It's jumped hard: <b>up $175 since yesterday</b> ($1,434) and <b>up $189 on a week ago</b> "
        "($1,420). The cheap Seoul/Tokyo routings that were floating around all week have thinned "
        "out, pushing the floor back up towards Snow Festival peak. Across all 56 earlier checks the "
        "price has run <b>$1,333 to $1,709</b>, so today isn't the top — but it's well above the "
        "~$1,485 middle.",
        "Nothing to do today — no genuine dip, and <b>no verified airline sale</b>: the Jetstar and "
        "Qantas deal chatter online is all old 2026-travel stuff, nothing live for Feb 2027. We're "
        "about <b>4½ months out</b>, still comfortably before the mid-October book-by deadline. A "
        "WATCH-band dip has turned up most weeks lately, so one likely will again — sit tight.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "✈️ Dep Brisbane (BNE) Tue 2 Feb 11:05am → 🛬 lands Sapporo (CTS) Wed 3 Feb 8:20am "
         "<i>(via Seoul + Tokyo; ~6h overnight wait at Tokyo-Haneda)</i>",
         "✈️ Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,609", "$6,437",
         "Long haul: ~22h in with an overnight airport wait, ~18h home — cheapest, but the roughest"),
        ("Best value",
         "✈️ Dep Brisbane (BNE) Wed 3 Feb 12:50am → 🛬 lands Sapporo (CTS) Wed 3 Feb 2:50pm "
         "<i>(Cathay via Hong Kong, one stop)</i>",
         "✈️ Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,664", "$6,654",
         "Only $55pp more, but ~14h in and lands mid-afternoon — no overnight in an airport. Best comfort-for-money"),
        ("Fastest sensible",
         "✈️ Dep Brisbane (BNE) Wed 3 Feb 12:50am → 🛬 lands Sapporo (CTS) Wed 3 Feb 2:50pm "
         "<i>(Cathay via Hong Kong)</i>",
         "✈️ Dep Tokyo (NRT) Thu 18 Feb 8:55pm → 🛬 lands Brisbane (BNE) Fri 19 Feb 6:50am "
         "<i>(Jetstar direct — nonstop)</i>",
         "$1,806", "$7,223",
         "Fastest overall — 14h in, ~10h nonstop home. But +$197pp, and the nonstop home only flies 18 Feb (two extra Tokyo nights)"),
    ],
    "options_footnote":
        "The Qantas QF107 Sydney→Sapporo seasonal direct was priced again today: <b>$1,742pp for that "
        "leg alone</b> (10h50m, lands 5:55pm the same day), before you even add the Brisbane→Sydney "
        "hop or the flight home — so it's roughly double the cheapest and stays a footnote, not a "
        "pick. No date shift within ±3 days saved $100pp, so the options stay on our dates. Flying "
        "into Tokyo on 4 Feb instead (Jetstar direct, $628pp) would shave about $65pp, but you'd lose "
        "the early Sapporo and Snow Festival days — not worth it.",
    "itin_title": "Option A — Cheapest ($1,609pp)",
    "itin_subtitle": "Furano base · ~13 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Mon 2 Feb", "✈️ Brisbane → (Seoul)", "Fly out Brisbane 11:05am; overnight in transit via Seoul and Tokyo"),
        ("Tue 3 Feb", "🛬 Sapporo (CTS)", "Land 8:20am, pick up the hire car, check in; ease in around Susukino (festival opens tomorrow)"),
        ("Wed 4 Feb", "Sapporo", "Snow Festival day 1 — Odori Park ice sculptures"),
        ("Thu 5 Feb", "Sapporo", "Snow Festival day 2, then Susukino for the illuminations"),
        ("Fri 6 Feb", "→ Furano", "Drive ~2.5h to Furano, settle into the lodge"),
        ("Sat 7 Feb", "Furano", "Ski day 1 — Isaac's beginner lesson in the morning"),
        ("Sun 8 Feb", "Furano", "Ski day 2 — Isaac's beginner lesson in the morning"),
        ("Mon 9 Feb", "Furano", "Ski day 3 — full day on the mountain"),
        ("Tue 10 Feb", "Furano / Biei", "Rest day — Biei Blue Pond or the Asahikawa Zoo penguin parade"),
        ("Wed 11 Feb", "Furano", "Ski day 4 — last big powder day"),
        ("Thu 12 Feb", "Furano", "Chill day — onsen, town, easy laps"),
        ("Fri 13 Feb", "→ Jozankei → Otaru", "Drive back; Jozankei day-use onsen soak, then Otaru Snow Light Path (last evening); night in Sapporo"),
        ("Sat 14 Feb", "✈️ Sapporo → Tokyo", "Drop the hire car, fly CTS→Tokyo 8:00am→9:35am; afternoon in Shibuya"),
        ("Sun 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab — full day"),
        ("Mon 16 Feb", "✈️ Tokyo → home", "Last Tokyo morning, then fly out Narita 12:30pm"),
        ("Tue 17 Feb", "🛬 Brisbane", "Land Brisbane 8:00am"),
    ],
    "itin_footnote":
        "<b>Best value</b> and <b>fastest</b> run the exact same trip on the ground — only the "
        "flights in and out change (best value flies in via Hong Kong and lands mid-afternoon "
        "instead of the overnight; fastest also flies straight home nonstop, but on 18 Feb, adding "
        "two Tokyo nights). The ryokan-overnight variant — leave Furano a day earlier and sleep at "
        "Jozankei — uses these same flight dates.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 57. Everything since late July has sat "
        "in the amber/red zone — the cheapest day was $1,333 on 31 Jul, and sub-$1,430 hasn't held "
        "for more than a day since.",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. one 20kg checked bag each way "
        "· no verified airline sale live today · buy line $1,430.",
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
        colour = "#1565c0" if latest else ("#c0392b" if v > 1500 else
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
open(OUT, "w").write(html)
print(f"wrote {OUT} ({len(html):,} chars) — placeholders filled")

text = build_text()
open("email.txt", "w").write(text)
print(f"wrote email.txt ({len(text):,} chars)")
