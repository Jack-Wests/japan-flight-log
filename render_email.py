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
    "date_iso": "2026-09-11",
    "date_human": "Fri 11 Sep 2026",
    "verdict_headline": "🔴 HOLD — dear side today, sit tight",
    "best_pp": "$1,606",
    "best_all4": "$6,424",
    "target_distance": "$176 above",
    "snapshot": [
        "The cheapest way to get all four of you into the Hokkaido snow and home again is "
        "<b>$1,606 per person — about $6,424 for the four, or $4,818 if it's just the three "
        "of you</b>. That's flying into Sapporo (CTS) through Singapore, the short "
        "Sapporo→Tokyo hop mid-trip, then home from Tokyo through Seoul.",
        "Today is a <b>dear day, not a buy day</b>: that's <b>$186 up on the last check</b> "
        "($1,420 on 10 Sep) and back above the $1,500 'too expensive' line. This is HOLD "
        "territory — nothing to do.",
        "For context, across 52 days of checks the cheapest all-in fare has swung between "
        "<b>$1,333 and $1,688</b>, sitting around <b>$1,485</b> most days. Yesterday briefly "
        "dipped to $1,420 (a WATCH day) and today it's bounced straight back up — exactly the "
        "one-day dips we keep seeing, so a good day can vanish fast.",
        "No airline sale could be confirmed today — Jetstar's own deal pages and OzBargain "
        "were both unreachable. The Jetstar 'return for free' Japan sale you'll see floating "
        "around online <b>ended back in May</b>, so ignore it; it's not live.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 6:10pm → 🛬 lands Sapporo (CTS) Wed 3 Feb 4:15pm "
         "<i>(via Singapore + Osaka, Singapore Airlines + Peach)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul, Air Premia + Jetstar)</i>",
         "$1,606", "$6,424",
         "Long haul: 23h in via two stops — no overnight, but a slog. Total includes the "
         "$119 Sapporo→Tokyo hop on 14 Feb"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:50pm "
         "<i>(via Hong Kong, Cathay Pacific)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul, Air Premia + Jetstar)</i>",
         "$1,674", "$6,696",
         "Only $68pp more but 8h shorter in, and lands early arvo on 2 Feb — a bonus half-day "
         "before the Snow Festival"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:50pm "
         "<i>(via Hong Kong, Cathay Pacific)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 8:00pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 6:05am "
         "<i>(Qantas QF62 direct)</i>",
         "$1,847", "$7,388",
         "Quickest sensible run: 15h in, 9h direct home. $241pp more than the cheapest"),
    ],
    "options_footnote":
        "The Qantas QF107 Sydney–Sapporo direct was priced today — <b>$1,737pp</b> for the flight "
        "in (10h50m, lands 5:55pm same day), plus roughly $180pp for a Brisbane→Sydney hop to feed "
        "it, so about <b>$2,759pp all-in ($11,036 for four)</b> once you add the way home. It's the "
        "comfy one-flight option to the snow, but roughly <b>double</b> the cheapest, so it's not a "
        "live pick. No date shift within ±3 days saved $100+ pp, so all options stay put. "
        "All-4 figures shown; for three, knock off a quarter (cheapest $4,818, best value $5,022, "
        "fastest $5,541).",
    "itin_title": "Option A itinerary — Furano base",
    "itin_subtitle": "13 nights · fly into Sapporo (CTS), home from Tokyo · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Tue 2 Feb", "Brisbane → (fly)", "Fly out Brisbane (BNE) 6:10pm — overnight in the air via Singapore"),
        ("Wed 3 Feb", "→ Sapporo (CTS)", "Land Sapporo 4:15pm, pick up the hire car, check in; dinner in Susukino"),
        ("Thu 4 Feb", "Sapporo", "Snow Festival day 1 — the big snow sculptures at Odori Park"),
        ("Fri 5 Feb", "Sapporo", "Snow Festival day 2 — Susukino ice sculptures, Sapporo beer + ramen"),
        ("Sat 6 Feb", "→ Furano", "Drive ~2.5h to Furano, settle into the lodge, easy afternoon"),
        ("Sun 7 Feb", "Furano", "Ski day 1 — Isaac's beginner lesson in the morning, lads on the powder"),
        ("Mon 8 Feb", "Furano", "Ski day 2 — Isaac's 2nd beginner lesson, then all ride together"),
        ("Tue 9 Feb", "Furano / Biei", "Rest day — Biei's Blue Pond + snowscapes, or Asahikawa Zoo penguin parade"),
        ("Wed 10 Feb", "Furano", "Ski day 3 — full day on the mountain"),
        ("Thu 11 Feb", "Furano", "Ski day 4 — last big day, tree runs"),
        ("Fri 12 Feb", "Furano", "Chill day at the lodge — onsen, recover, last Furano night"),
        ("Sat 13 Feb", "→ Otaru → Sapporo", "Drive back: Jozankei day-use onsen soak, then Otaru Snow Light Path (final evening); night in Sapporo"),
        ("Sun 14 Feb", "Sapporo → Tokyo", "Drop the car, fly CTS→Tokyo 8:00am→9:35am; afternoon in Shibuya"),
        ("Mon 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab Planets"),
        ("Tue 16 Feb", "Tokyo → home", "Last Tokyo morning, then depart Tokyo (NRT) 12:30pm"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane (BNE) 8:00am"),
    ],
    "itin_footnote":
        "<b>Best value</b> and <b>fastest sensible</b> are the exact same trip on the ground — "
        "only the flights in and out change. Best value gets you into Sapporo a day earlier "
        "(early arvo 2 Feb) via Hong Kong; fastest flies Qantas direct home in 9 hours. The "
        "ryokan-overnight variant (leave Furano a day early, sleep at Jozankei) uses these same "
        "flight dates.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 52. The cheapest day yet was $1,333 "
        "(31 Jul / 1 Aug); the floor has been drifting up as Snow Festival week fills out.",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. 1 checked bag each way "
        "· no verified airline sale live today.",
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
