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
    "date_iso": "2026-09-14",
    "date_human": "Mon 14 Sep 2026",
    "verdict_headline": "🔴 HOLD — dear side, wait",
    "best_pp": "$1,621",
    "best_all4": "$6,485",
    "target_distance": "$191 above",
    "snapshot": [
        "Cheapest way to get all four of you to the Hokkaido snow and home again is "
        "<b>$1,621 per person</b> — that's <b>$6,485 for the four</b>, or <b>$4,864 for three</b> "
        "if Hugh sits this one out. It flies Brisbane into Sapporo via Seoul &amp; Tokyo, home "
        "from Tokyo via Seoul, and includes the ~$116pp Sapporo→Tokyo hop on 14 Feb.",
        "That's a <b>🔴 HOLD</b>: it's over the <b>$1,500pp</b> line we said we won't cross, so "
        "today's a wait, not a book. It did fall <b>$88 from yesterday's $1,709</b> — but it's "
        "still <b>$116 up on a week ago</b> ($1,505) and <b>$191 above the $1,430 buy target</b>.",
        "The floor's been jumpy, not trending one way: over the last fortnight the cheapest day "
        "was <b>$1,420 (10 Sep)</b> and the dearest <b>$1,709 (yesterday)</b>. Cheap fare classes "
        "keep selling in and out as Snow Festival week fills up.",
        "<b>No verified airline sale today</b> — OzBargain and the airline deal pages were both "
        "blocked, so nothing to act on. We're about <b>4.5 months out</b>, with a month to go "
        "before the mid-October “book under $1,500 anyway” deadline.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "✈️ Dep Brisbane (BNE) Tue 2 Feb 11:05am → 🛬 lands Sapporo (CTS) Wed 3 Feb 8:20am "
         "<i>(via Seoul &amp; Tokyo)</i>",
         "✈️ Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,621", "$6,485",
         "Long haul: ~22h in with a 6h overnight wait at Tokyo (Haneda), ~18h home via Seoul — "
         "cheapest but tiring"),
        ("Best value",
         "✈️ Dep Brisbane (BNE) Tue 2 Feb 12:50am → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:50pm "
         "<i>(Cathay via Hong Kong)</i>",
         "✈️ Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,676", "$6,702",
         "Clean 15h run in, lands mid-arvo the same day — no overnight airport sleep. "
         "Only $55pp more ($5,027 for three)"),
    ],
    "options_footnote":
        "The <b>Qantas QF107 Sydney–Sapporo direct</b> was priced again today — <b>$1,742pp just "
        "for that one leg in</b> ($6,969 for four), before you even add a Brisbane→Sydney hop or "
        "the flight home. Roughly double, so it's not a real pick. The <b>fastest sensible</b> run "
        "(15h in via Hong Kong, then the 9h Jetstar nonstop home) comes to about <b>$1,877pp</b> — "
        "$256pp more than the cheapest, so it doesn't earn its own row. No date shift within ±3 "
        "days saved $100+pp, so the options stay put.",
    "itin_title": "Option A — Furano base",
    "itin_subtitle": "Furano base · 13 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Tue 2 Feb", "In transit", "Fly out Brisbane 11:05am; overnight in transit via Seoul &amp; Tokyo"),
        ("Wed 3 Feb", "Land Sapporo (CTS)", "Land 8:20am, pick up the hire car, check in; ease into Sapporo"),
        ("Thu 4 Feb", "Sapporo", "Snow Festival day 1 (opening day) — Odori Park &amp; Susukino ice sculptures"),
        ("Fri 5 Feb", "Sapporo", "Snow Festival day 2; evening out in Susukino"),
        ("Sat 6 Feb", "→ Furano", "Drive ~2.5h to Furano, settle into the lodge, afternoon chill"),
        ("Sun 7 Feb", "Furano", "Ski day 1 — Isaac's AM beginner lesson, lads ride the powder"),
        ("Mon 8 Feb", "Furano", "Ski day 2 — Isaac's AM lesson, then all ski together"),
        ("Tue 9 Feb", "Biei / Blue Pond", "Rest day — Biei &amp; the frozen Blue Pond, snacks in town"),
        ("Wed 10 Feb", "Furano", "Ski day 3 — tree runs and long groomers"),
        ("Thu 11 Feb", "Asahikawa", "Rest day — Asahiyama Zoo penguin parade"),
        ("Fri 12 Feb", "Furano", "Ski day 4 — last powder day, or chill at the lodge"),
        ("Sat 13 Feb", "Furano → Sapporo", "Drive back; Jozankei day-use onsen soak, then Otaru Snow Light Path (last evening); night in Sapporo"),
        ("Sun 14 Feb", "Sapporo → Tokyo", "Drop the car, fly CTS→Tokyo 8:00am; afternoon in Shibuya"),
        ("Mon 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab"),
        ("Tue 16 Feb", "Tokyo → home", "Last Tokyo morning; depart Narita 12:30pm"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane 8:00am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the same trip on the ground — it just flies in via Hong Kong (a "
        "clean 15-hour daytime run) instead of the cheaper overnight through Seoul and Tokyo, for "
        "about $55pp more. The ryokan variant (leave Furano a day earlier and sleep at Jozankei) "
        "uses the same flight dates.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 53. The cheapest day yet was $1,333 "
        "on 31 Jul; the last dip under the $1,430 buy line was $1,420 on 10 Sep, and it lasted a "
        "single day before bouncing back.",
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
        L.append(f'  {date:<12} {strip(loc):<20} {strip(plan)}')
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
