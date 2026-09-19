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
    "date_iso": "2026-09-19",
    "date_human": "Sat 19 Sep 2026",
    "verdict_headline": "🔴 HOLD — but a live sale ends in 2 days",
    "best_pp": "$1,612",
    "best_all4": "$6,447",
    "target_distance": "$182 above",
    # Action banner: red box above the header. Empty string "" on non-action days.
    "action_banner":
        '<tr><td style="background:#b91c1c;border-radius:12px;padding:16px 20px;">'
        '<p style="margin:0;color:#ffffff;font-size:15px;font-weight:800;line-height:1.4;">'
        '🚨 ACTION TODAY: Qantas Japan sale ends Monday 21 Sep — 2 days away</p>'
        '<p style="margin:7px 0 0;color:#fee2e2;font-size:13px;line-height:1.55;">'
        'It’s advertising <b style="color:#fff;">Sydney→Sapporo direct and Brisbane→Tokyo from '
        '$1,349 return</b> — that’s <b style="color:#fff;">under</b> our $1,430 buy target. '
        'The search engines can’t see these fares (Kiwi shows the same Qantas flights at '
        '$1,600–2,200), so the sale price only shows up on '
        '<b style="color:#fff;">qantas.com</b> itself. Worth a look <b style="color:#fff;">today</b>: '
        'search Brisbane or Sydney to Tokyo/Sapporo, travelling Feb 2027. If it lands under '
        '$1,430 all-in, that’s a book-on-the-spot.</p>'
        '</td></tr>'
        '<tr><td style="height:14px;line-height:14px;font-size:0;">&nbsp;</td></tr>',
    "action_text":
        "*** ACTION TODAY: Qantas Japan sale ends Monday 21 Sep (2 days away). It's advertising "
        "Sydney->Sapporo direct and Brisbane->Tokyo from $1,349 return - under our $1,430 buy "
        "target. The search engines can't see these fares (Kiwi shows the same Qantas flights at "
        "$1,600-2,200), so check qantas.com directly today: Brisbane or Sydney to Tokyo/Sapporo, "
        "travelling Feb 2027. If it lands under $1,430 all-in, book on the spot. ***",
    "snapshot": [
        "The cheapest way the search engines can find to get all four of you into the Hokkaido "
        "snow and home from Tokyo is <b>$1,612 per person</b> — about <b>$6,447 for the four</b>, "
        "or <b>$4,835 if it ends up being just the three of you</b>. That’s a "
        "<b>🔴 HOLD</b>: it’s above the $1,500 line, so on the normal booking sites today is a "
        "dear day.",
        "<b>But there’s a real opportunity the search sites can’t see.</b> Qantas has a Japan "
        "sale on that <b>ends this Monday (21 Sep) — 2 days away</b>, advertising "
        "Sydney→Sapporo direct and Brisbane→Tokyo from <b>$1,349 return</b>, which is below our "
        "$1,430 buy target. Kiwi still prices those same Qantas flights at $1,600–2,200, so the "
        "only place to get the sale fare is <b>qantas.com directly</b> — worth a look today.",
        "On the searchable price, yesterday’s <b>$1,427</b> (a rare BUY day) has already bounced "
        "<b>$185 back into the red</b> — exactly how the last few sub-$1,430 dips behaved, gone "
        "in a day. Across 59 days of checks the cheapest fare has run <b>$1,333–$1,709</b>.",
        "We’re about <b>4½ months</b> out, and roughly <b>4 weeks</b> from the mid-October "
        "book-by deadline. Nothing forces a booking on the search-engine price today — but if "
        "the Qantas sale genuinely lands under $1,430 all-in, don’t wait.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 8:40am → 🛬 lands Tokyo (HND) Tue 2 Feb 10:50pm "
         "<i>(via Seoul, Korean Air)</i>, then next day Tokyo→Sapporo (CTS), lands Wed 3 Feb 10:05pm",
         "🛫 Sapporo (CTS)→Tokyo Sat 14 Feb 8:00am, then 🛫 Dep Tokyo (NRT) Tue 16 Feb 6:50pm → "
         "🛬 lands Brisbane (BNE) Wed 17 Feb 4:55pm <i>(via Singapore)</i>",
         "$1,612", "$6,447",
         "Cheapest, but you lose day one to Tokyo + a domestic hop each end. Long haul: ~21h in"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Wed 3 Feb 12:50am → 🛬 lands Sapporo (CTS) Wed 3 Feb 2:50pm "
         "<i>(one stop in Hong Kong, Cathay)</i>",
         "🛫 Sapporo (CTS)→Tokyo Sat 14 Feb 8:00am, then 🛫 Dep Tokyo (NRT) Tue 16 Feb 6:50pm → "
         "🛬 lands Brisbane (BNE) Wed 17 Feb 4:55pm <i>(via Singapore)</i>",
         "$1,702", "$6,809",
         "Straight to the snow — lands Sapporo mid-afternoon day one, only one domestic hop. $90pp more"),
    ],
    "options_footnote":
        "<b>Fastest sensible</b> today is ~<b>$1,930pp ($7,720 for four)</b> — Brisbane→Sapporo "
        "via Hong Kong (~15h) in and Tokyo→Brisbane via Hong Kong (~15½h) home, both Cathay, so "
        "about 15–16h each way instead of 21h+. It’s $318pp above the cheapest, so it "
        "doesn’t earn its own row. The <b>Qantas QF107 Sydney→Sapporo direct</b> prices at "
        "<b>$1,668pp one-way</b> on Kiwi (plus a ~$180 Brisbane→Sydney hop) — but the current "
        "Qantas sale advertises that same route at <b>$1,349 return</b>, so the sale is the only "
        "place the direct flight is affordable. No date shift within ±3 days saved $100+pp.",
    "itin_title": "Option A — Best value (fly into Sapporo, home from Tokyo)",
    "itin_subtitle": "Furano base · ~13 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Wed 3 Feb", "Brisbane → Sapporo", "Fly out 12:50am, land Sapporo (CTS) 2:50pm; pick up the hire car, check into Sapporo"),
        ("Thu 4 Feb", "Sapporo", "Snow Festival day 1 — Odori Park (festival runs 4–11 Feb)"),
        ("Fri 5 Feb", "Sapporo", "Snow Festival day 2; evening bar-hop through Susukino"),
        ("Sat 6 Feb", "→ Furano", "Drive ~2.5h to Furano, settle into the lodge"),
        ("Sun 7 Feb", "Furano", "Ski day 1 — Isaac's beginner lesson in the morning, lads on the powder"),
        ("Mon 8 Feb", "Furano", "Ski day 2 — Isaac's beginner lesson AM, then all ride together"),
        ("Tue 9 Feb", "Biei / Blue Pond", "Rest day — Blue Pond and the Biei snow country"),
        ("Wed 10 Feb", "Furano", "Ski day 3"),
        ("Thu 11 Feb", "Asahikawa", "Rest day — Asahikawa Zoo penguin parade"),
        ("Fri 12 Feb", "Furano", "Ski day 4 — last big powder day"),
        ("Sat 13 Feb", "Furano → Otaru → Sapporo", "Drive back; Jozankei day-use onsen soak, then Otaru Snow Light Path (its last night, runs 6–13 Feb); sleep in Sapporo"),
        ("Sun 14 Feb", "Sapporo → Tokyo", "Drop the car at Sapporo (CTS); fly CTS→Tokyo 8:00am; afternoon in Tokyo"),
        ("Mon 15 Feb", "Tokyo", "Shibuya, Asakusa, teamLab — full day in the city"),
        ("Tue 16 Feb", "Tokyo → home", "Last morning in Tokyo; depart Tokyo (NRT) 6:50pm"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane (BNE) 4:55pm"),
    ],
    "itin_footnote":
        "<b>Cheapest ($1,612pp)</b> is the same trip on the ground — it just flies into Tokyo and "
        "hops up to Sapporo the next day (so you lose your first day to travel) and comes home the "
        "same way, for $90pp less. The <b>ryokan overnight variant</b> (leave Furano a day earlier "
        "and sleep at Jozankei) uses the same flight dates.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 59. Yesterday’s $1,427 was only the "
        "second BUY day we’ve ever logged and it lasted a single day. Cheapest ever was $1,333 "
        "(31 Jul).",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. 1 checked bag each way "
        "· LIVE Qantas Japan sale ends Mon 21 Sep — check qantas.com.",
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
    "ACTION_BANNER": RUN.get("action_banner", ""),
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
    L = [f'JAPAN SNOW TRIP - DAILY CHECK - {RUN["date_human"]}', ""]
    if RUN.get("action_text"):
        L += [strip(RUN["action_text"]), ""]
    L += [strip(RUN["verdict_headline"]),
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
