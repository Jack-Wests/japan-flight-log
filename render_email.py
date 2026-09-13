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
    "date_iso": "2026-09-13",
    "date_human": "Sun 13 Sep 2026",
    "verdict_headline": "🔴 HOLD — dear side, sit tight",
    "best_pp": "$1,709",
    "best_all4": "$6,836",
    "target_distance": "$279 above",
    "snapshot": [
        "The cheapest sensible way to get all four of you into the Hokkaido snow and home "
        "again is <b>$1,709 per person</b> today — that's <b>$6,836 for the four</b>, or "
        "<b>$5,127 if it's just the three of you</b> and Hugh sits it out. It flies you "
        "straight into Sapporo (CTS) via Hong Kong, and home from Tokyo via Singapore.",
        "That's a <b>bad day</b>: up <b>$103</b> on the last check (Fri 11 Sep, $1,606) and up "
        "<b>$279</b> on a week ago (Sun 6 Sep, $1,430). In fact it's the <b>dearest we've ever "
        "logged</b> — the old high was $1,688 back on 10 Aug. The floor really is lifting as "
        "Snow Festival fare classes sell out.",
        "So we're <b>$279 above the $1,430 book-on-the-spot mark</b> and well over the $1,500 "
        "line. Nothing to do but wait — there's no dip here to jump on.",
        "Still plenty of runway: departure is <b>~5 months</b> off and the mid-October deadline "
        "is a month away, so a normal-priced day will almost certainly come back around before "
        "we're forced to act.",
        "No verified airline sale today. Search results hint at a Jetstar \"Return for Free\" "
        "Japan run, but both Jetstar's and OzBargain's own pages are blocked from here, so I "
        "can't confirm it's live or that it covers our dates — not treating it as real.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:50pm "
         "<i>(Cathay Pacific via Hong Kong, ~14h)</i>",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 8:30am → 🛬 lands Brisbane (BNE) Wed 17 Feb 7:15am "
         "<i>(Singapore Airlines via Singapore)</i>",
         "$1,709", "$6,836",
         "Long haul home: ~22h — but the 11h Singapore layover is long enough to get into town. "
         "Includes the $119 Sapporo→Tokyo hop on 14 Feb."),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:50pm "
         "<i>(Cathay Pacific via Hong Kong, ~14h)</i>",
         "🛫 Dep Tokyo (NRT) Mon 15 Feb 7:20pm → 🛬 lands Brisbane (BNE) Tue 16 Feb 10:35am "
         "<i>(Qantas via Melbourne, ~14¼h)</i>",
         "$1,831", "$7,324",
         "Full-service Qantas the whole way home, one stop, bag included — comfiest, $122pp over "
         "the cheapest."),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:50pm "
         "<i>(Cathay Pacific via Hong Kong, ~14h)</i>",
         "🛫 Dep Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am "
         "<i>(Air Niugini via Port Moresby, ~11h)</i>",
         "$1,745", "$6,980",
         "Half the travel time home for only $36pp more — quick 1h stop, no overnight. Home lands "
         "Thu 18 Feb, so you get a bonus Tokyo day."),
    ],
    "options_footnote":
        "The Qantas QF107 Sydney–Sapporo direct was priced today at <b>$1,737pp</b> for the "
        "flight in — add a ~$180pp Brisbane→Sydney hop and it's ~$1,917pp just to reach the snow, "
        "against $833pp via Hong Kong. All-in that routing lands around <b>$2,790pp</b>, so it's "
        "not shown as a live pick. No date shift within ±3 days saved $100+ pp, so the options "
        "stay put. All three still fly you straight into Sapporo and home from Tokyo.",
    "itin_title": "Option A — Cheapest (Furano base)",
    "itin_subtitle": "~13 nights · fly into Sapporo (CTS), home from Tokyo · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Tue 2 Feb", "Brisbane → Sapporo", "Fly out 12:50am, land New Chitose 2:50pm (via Hong Kong); pick up the car, into Sapporo"),
        ("Wed 3 Feb", "Sapporo", "Settle in — Susukino, ramen, scope out Odori Park before the crowds"),
        ("Thu 4 Feb", "Sapporo", "Snow Festival day 1 — Odori Park ice sculptures (festival opens today)"),
        ("Fri 5 Feb", "Sapporo", "Snow Festival day 2 — Susukino ice bar + Tsudome family site"),
        ("Sat 6 Feb", "→ Furano", "Drive ~2½h to Furano, settle into the lodge, afternoon warm-up laps"),
        ("Sun 7 Feb", "Furano", "Ski day 1 — Isaac's AM beginner lesson, lads ride the powder"),
        ("Mon 8 Feb", "Furano", "Ski day 2 — Isaac's AM lesson, then all ski together"),
        ("Tue 9 Feb", "Furano / Biei", "Rest day — Blue Pond + Biei snowscapes, onsen evening"),
        ("Wed 10 Feb", "Furano", "Ski day 3 — full day on the mountain"),
        ("Thu 11 Feb", "Furano / Asahikawa", "Asahiyama Zoo penguin parade, or a 4th ski day if legs allow"),
        ("Fri 12 Feb", "Furano", "Ski day 4 / chill — last full day at the lodge"),
        ("Sat 13 Feb", "Furano → Sapporo", "Drive back; Jozankei day-use onsen soak, then Otaru Snow Light Path (last night); sleep Sapporo"),
        ("Sun 14 Feb", "Sapporo → Tokyo", "Drop the car, fly CTS→Tokyo 8:00am→9:35am; afternoon Shibuya/Shinjuku"),
        ("Mon 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab — last full day"),
        ("Tue 16 Feb", "Tokyo → home", "Depart Haneda 8:30am (via Singapore)"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane 7:15am"),
    ],
    "itin_footnote":
        "Same trip on the ground for all three options — only the flight home changes. "
        "<b>Best value</b> flies Qantas home via Melbourne (lands Tue 16 Feb, ~14¼h). "
        "<b>Fastest sensible</b> flies Air Niugini home via Port Moresby (~11h) but leaves a day "
        "later, so Tokyo stretches to three days and you land Thu 18 Feb.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 53. Today ($1,709) is a fresh high — "
        "the cheapest day on record is still $1,333 (31 Jul).",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. 1 checked 20kg bag each way "
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
