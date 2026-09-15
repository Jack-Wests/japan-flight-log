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
    "date_iso": "2026-09-15",
    "date_human": "Tue 15 Sep 2026",
    "verdict_headline": "🟡 WATCH — back in range, $12 short of a buy",
    "best_pp": "$1,442",
    "best_all4": "$5,768",
    "target_distance": "$12 above",
    "snapshot": [
        "The cheapest way to get all four of you to the Hokkaido snow and home again is "
        "<b>$1,442 per person</b> — about <b>$5,768 for the four</b>, or <b>$4,326 if it's just "
        "the three</b> (should Hugh sit it out). That's a return Brisbane→Tokyo on Air Niugini "
        "via Port Moresby, plus the short hops up to Sapporo and back.",
        "Good news after a dear week: that's <b>down $179 on yesterday</b> ($1,621) and "
        "<b>$180 below a week ago</b> ($1,622 on 8 Sep). It drops us out of the red and back "
        "into the amber <b>WATCH</b> band.",
        "But it's not quite a buy. At $1,442 we're <b>only $12 above the $1,430 "
        "book-on-the-spot price</b> — tantalisingly close, but still the wrong side of it, and "
        "the cheapest fare leans on a brutal ~30-hour trip over with a night in Port Moresby. "
        "Across all 54 checks the price has run <b>$1,333–$1,709</b>; today sits in the lower half.",
        "No verified airline sale is live (the big Jetstar Japan sale ended 24 Aug and nothing "
        "new has surfaced). Nothing to do today but keep watching — if it slips another $12 we "
        "call the lads.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 2 Feb 2:40pm → 🛬 lands Tokyo (NRT) Tue 3 Feb 8:00pm "
         "<i>(Air Niugini via Port Moresby — overnight in Port Moresby)</i>, then overnight near "
         "Tokyo and hop to Sapporo (CTS) Wed 4 Feb",
         "🛫 Dep Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am "
         "<i>(Air Niugini via Port Moresby)</i>",
         "$1,442", "$5,768",
         "Long haul: ~30h over with a night in Port Moresby — brutal · 11h home"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Tue 3 Feb 12:50am → 🛬 lands Sapporo (CTS) Tue 3 Feb 2:50pm "
         "<i>(Cathay Pacific via Hong Kong)</i>",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 8:30am → 🛬 lands Brisbane (BNE) Wed 17 Feb 7:15am "
         "<i>(Singapore Airlines via Singapore — 6½h layover, long enough to nip into town)</i>",
         "$1,746", "$6,984",
         "Lands straight on the snow, 15h in · home ~22h · $304pp more but no Port Moresby"),
    ],
    "options_footnote":
        "The Qantas QF107 Sydney→Sapporo direct was priced again — <b>$1,737pp</b> for the flight "
        "in (8h50, lands Sapporo 5:55pm the same day) — but that's before a Brisbane→Sydney feeder "
        "and the whole trip home, so it lands well over budget and isn't a live pick. A genuinely "
        "quick trip — the Hong Kong flight in (15h) with an 11-hour Port Moresby red-eye home — "
        "comes to <b>$1,747pp</b>, $305 more than the cheapest, so it doesn't earn its own row. "
        "No date shift within ±3 days saved $100+ pp.",
    "itin_title": "Option A — Furano base (13 nights)",
    "itin_subtitle": "Fly into Sapporo (CTS), home from Tokyo · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Tue 3 Feb", "🛫 Brisbane → Sapporo", "Fly BNE 12:50am → land Sapporo (CTS) 2:50pm via Hong Kong; pick up the hire car, check in, night in Susukino"),
        ("Wed 4 Feb", "Sapporo", "Snow Festival day 1 — Odori Park ice sculptures"),
        ("Thu 5 Feb", "Sapporo", "Snow Festival day 2; evening bite in Susukino"),
        ("Fri 6 Feb", "→ Furano", "Drive ~2.5h to the Furano lodge, settle in, afternoon warm-up laps"),
        ("Sat 7 Feb", "Furano", "Ski day 1 — Isaac's AM beginner lesson, lads ride the powder"),
        ("Sun 8 Feb", "Furano", "Ski day 2 — Isaac's AM lesson, then all ride together"),
        ("Mon 9 Feb", "Furano / Biei", "Rest day — Biei Blue Pond & Asahikawa Zoo penguin parade"),
        ("Tue 10 Feb", "Furano", "Ski day 3 — tree runs"),
        ("Wed 11 Feb", "Furano", "Ski day 4 — last big powder day"),
        ("Thu 12 Feb", "Furano", "Chill day at the lodge / easy laps, pack up"),
        ("Fri 13 Feb", "→ Jozankei → Otaru → Sapporo", "Drive back; Jozankei day-use onsen soak; Otaru Snow Light Path (final evening); night in Sapporo"),
        ("Sat 14 Feb", "Sapporo → Tokyo", "Drop the car at Sapporo (CTS), fly CTS→Tokyo morning; afternoon in Shibuya"),
        ("Sun 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab Planets"),
        ("Mon 16 Feb", "🛬 Tokyo → home", "Morning at Tsukiji, then fly home from Tokyo (lands Brisbane next morning)"),
    ],
    "itin_footnote":
        "The days on the ground are the same whichever fare you pick — only the flights in and out "
        "change. <b>Best value</b> lands you straight in Sapporo on Tue 3 Feb (no Tokyo faff). The "
        "<b>cheapest</b> comes in via Port Moresby and Tokyo, so you'd overnight near Tokyo and hop "
        "up to Sapporo on the Wednesday, and fly home a day later (Thu 18 Feb) — same snow, rougher "
        "travel.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above carries all 54. Today's $1,442 is the first "
        "dip back into the amber WATCH band after four dear HOLD days — the cheapest day on record "
        "is still $1,333 (31 Jul).",
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
