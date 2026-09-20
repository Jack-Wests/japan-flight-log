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
    "date_iso": "2026-09-20",
    "date_human": "Sun 20 Sep 2026",
    "verdict_headline": "🔴 HOLD — the dear side, sit tight",
    "best_pp": "$1,526",
    "best_all4": "$6,104",
    "target_distance": "$96 above",
    "snapshot": [
        "Cheapest way to get all four of you to the Hokkaido snow and home again is "
        "<b>$1,526 per person</b> — about <b>$6,104 for the four</b>, or <b>$4,578 for three</b> "
        "if Hugh sits it out. That flies you into Sapporo (CTS), a cheap hop down to Tokyo "
        "mid-trip, and home from Tokyo.",
        "It's a <b>HOLD day</b>: $1,526 is <b>$96 over our $1,430 buy line</b>. It has eased a "
        "touch though — <b>down $34 since yesterday</b> ($1,560) and <b>down $183 on a week ago</b> "
        "($1,709).",
        "Nothing to do today. Over the last fortnight the price has bounced between $1,427 and "
        "$1,709 with no real direction — jumpy, not trending down — so we hold out for a genuine "
        "dip under $1,430 (last seen 18 Sep, and gone the very next day).",
        "We're about <b>4½ months out</b> and roughly <b>four weeks short of the mid-October "
        "deadline</b>, so there's still room to wait. <b>No verified airline sale</b> covers our "
        "Feb 2027 dates — Jetstar's deals page was down today, and the sale posts doing the rounds "
        "are all months old and end in 2026.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 11:05am → 🛬 lands Sapporo (CTS) Wed 3 Feb 8:20am "
         "<i>(via Seoul + Tokyo)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,526", "$6,104",
         "Long haul: 22h in, with a ~6h middle-of-the-night wait at Tokyo Haneda — cheap but rough"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 0:50am → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:50pm "
         "<i>(Cathay via Hong Kong)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,657", "$6,628",
         "15h in, one stop, Cathay full-service — lands mid-arvo, no overnight airport. $131pp more"),
    ],
    "options_footnote":
        "Both totals include the <b>$113pp Sapporo→Tokyo hop on 14 Feb</b> (Air Do, nonstop, bag "
        "included) — that leg is needed either way. The <b>Qantas QF107 Sydney→Sapporo direct</b> "
        "(10h50m nonstop, lands 5:55pm) priced at <b>$1,737pp</b> for that leg; add a "
        "Brisbane→Sydney hop (~$180pp) and it's ~$1,917pp just to reach the snow, before the Tokyo "
        "legs — roughly double the cheapest, so it stays a footnote. The genuinely fast way home, "
        "the nonstop Jetstar Narita→Brisbane (~10h), only shows on 18 Feb at $913pp, which pushes a "
        "fast build to about <b>$1,860pp all-in</b> ($334pp over the cheapest) — so it doesn't earn "
        "a table row. No date shift within ±3 days saved $100+pp, so everything stays on the "
        "planned dates.",
    "itin_title": "Option A — Cheapest (Furano base)",
    "itin_subtitle": "Furano base · 13 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Tue 2 Feb", "Brisbane → (air)", "Fly out of Brisbane 11:05am, overnight in transit via Seoul + Tokyo"),
        ("Wed 3 Feb", "→ Sapporo", "Land Sapporo (CTS) 8:20am, pick up the hire car; Snow Festival warm-up, night Sapporo"),
        ("Thu 4 Feb", "Sapporo", "Snow Festival day 1 — Odori Park ice sculptures (festival runs 4–11 Feb)"),
        ("Fri 5 Feb", "Sapporo", "Snow Festival day 2 + Susukino ice bar; night Sapporo"),
        ("Sat 6 Feb", "→ Furano", "Drive ~2.5h to Furano, settle into the lodge, afternoon warm-up laps"),
        ("Sun 7 Feb", "Furano", "Ski day 1 — Isaac's beginner lesson AM, lads on the main runs"),
        ("Mon 8 Feb", "Furano", "Ski day 2 — Isaac's beginner lesson AM, all ski together after"),
        ("Tue 9 Feb", "Furano", "Ski day 3 — full day on the mountain"),
        ("Wed 10 Feb", "Furano / Biei", "Rest day — Biei Blue Pond + Asahikawa Zoo penguin parade"),
        ("Thu 11 Feb", "Furano", "Ski day 4 — last big day, or chill at the lodge"),
        ("Fri 12 Feb", "Furano", "Easy day — onsen, town, pack up (7 nights at Furano)"),
        ("Sat 13 Feb", "→ Otaru → Sapporo", "Drive back, Jozankei day-use onsen soak, Otaru Snow Light Path (last night); night Sapporo"),
        ("Sun 14 Feb", "Sapporo → Tokyo", "Drop the car at CTS; fly to Tokyo 8:00am→9:35am; afternoon Shibuya"),
        ("Mon 15 Feb", "Tokyo", "Asakusa, teamLab, Akihabara; last night out"),
        ("Tue 16 Feb", "Tokyo → home", "Morning in Tokyo, fly out of Narita 12:30pm"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane 8:00am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the exact same trip on the ground — it just flies in via Hong Kong on "
        "Cathay (15h, one stop, lands mid-afternoon) instead of the 22-hour cheapest route with its "
        "6-hour overnight wait at Tokyo, for $131pp more. The ryokan variant (leave Furano a day "
        "earlier and sleep at Jozankei) uses the same flight dates.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 60. Across every check the price has "
        "run $1,333–$1,709; the cheapest day yet was $1,333 (31 Jul / 1 Aug), and a genuine buy "
        "(≤$1,430) has shown only a handful of times, most recently 18 Sep.",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. 1 checked bag each way "
        "· no verified sale live today · Skyscanner cross-check unavailable today.",
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
