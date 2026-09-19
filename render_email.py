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
    # Set to a one-line string to show the red banner; leave "" for a normal day.
    "action": "🚨 ACTION NEEDED TODAY: Qantas's snow-season sale ends Monday (21 Sep). "
              "It advertises Sapporo return from Brisbane (via Sydney) from <b>$1,349pp</b> — "
              "below our $1,430 buy target — for Feb 2027 travel. Kiwi and Skyscanner don't "
              "show it, so check <b>qantas.com</b> for BNE⇄Sapporo/Tokyo, travel early Feb 2027, "
              "TODAY. I couldn't load Qantas's own page from here, but four travel-news outlets "
              "all report the same sale.",
    "verdict_headline": "🔴 HOLD — everyday fares are dear (but read the red bit)",
    "best_pp": "$1,612",
    "best_all4": "$6,448",
    "target_distance": "$182 above",
    "snapshot": [
        "On the normal, bookable fares today it's a <b>HOLD</b>: the cheapest way to get all "
        "four of you to Hokkaido and home is <b>$1,612 per person</b> — <b>$6,448 for the four</b>, "
        "or <b>$4,836 for three</b> if Hugh sits it out. That routes Brisbane→Tokyo and back "
        "through Seoul, with the two Sapporo hops folded in.",
        "That's <b>$185 dearer than yesterday</b> ($1,427, which briefly dipped into buy "
        "territory) and <b>$182 above our $1,430 target</b> — so the everyday market is firmly "
        "in wait-and-see mode. Across all 59 checks the best fare has run <b>$1,333–$1,709</b>.",
        "<b>But</b> — and this is the bit that matters — Qantas has a snow-season sale that "
        "<b>ends Monday</b>, advertising Sapporo return from Brisbane from <b>$1,349pp</b>, "
        "under our target. The flight-search tools we use can't see sale fares, so this needs "
        "a human to check qantas.com directly (details in the red bar above).",
        "We're about <b>4½ months</b> from departure (Feb 2), and the mid-October "
        "book-by-deadline is roughly <b>four weeks</b> away — still time, but the free run is "
        "shortening.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, all3, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 2 Feb 8:40am → 🛬 lands Tokyo (HND) Mon 2 Feb 10:50pm "
         "<i>(Korean Air via Seoul)</i>, then next-morning hop to Sapporo (CTS) Tue 3 Feb",
         "🛫 Dep Tokyo (NRT) Wed 17 Feb 2:00pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 6:20am "
         "<i>(Korean Air via Seoul)</i>",
         "$1,612", "$6,448", "$4,836",
         "Cheapest, but two Seoul stops + an overnight in Tokyo before Sapporo (~14h in, ~15h home)"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Mon 2 Feb 11:05am → 🛬 lands Sapporo (CTS) Tue 3 Feb 8:20am "
         "<i>(one ticket via Seoul + Tokyo)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,624", "$6,496", "$4,872",
         "Only $12pp more, and one ticket lands you straight on the snow — no Tokyo backtrack (long haul: ~22h in)"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Thu 4 Feb 10:30am → 🛬 lands Tokyo (NRT) Thu 4 Feb 6:25pm "
         "<i>(Jetstar direct, 7h55)</i>, then hop to Sapporo (CTS)",
         "🛫 Dep Tokyo (NRT) Thu 18 Feb 8:55pm → 🛬 lands Brisbane (BNE) Fri 19 Feb 6:50am "
         "<i>(Jetstar direct, 9h55)</i>",
         "$1,770", "$7,080", "$5,310",
         "Jetstar direct both ways — no long layovers. $158pp more; but flying out Feb 4 trims the Sapporo start"),
    ],
    "options_footnote":
        "The Qantas QF107 Sydney→Sapporo direct (with a Brisbane→Sydney feeder) prices at "
        "<b>$1,794pp one-way</b> on Kiwi today — about $7,176 for four just to get there — so at "
        "standard fares it's roughly double the cheapest and gets no row. That same QF107 is the "
        "backbone of the live sale, where it's advertised from ~$1,349pp <i>return</i>, which is "
        "exactly why the sale is worth chasing. No date shift within ±3 days saved $100+ pp, so "
        "the options stay on the planned dates.",
    "itin_title": "Option A itinerary — Furano base",
    "itin_subtitle": "Cheapest option's dates · ~13 nights on the snow &amp; in Tokyo · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Mon 2 Feb", "Brisbane → Tokyo", "Fly out 8:40am, land Tokyo 10:50pm (via Seoul); overnight near the airport"),
        ("Tue 3 Feb", "Tokyo → Sapporo", "Morning hop to Sapporo (CTS), pick up the hire car, settle in"),
        ("Wed 4 Feb", "Sapporo", "Snow Festival day 1 at Odori Park (festival opens today)"),
        ("Thu 5 Feb", "Sapporo", "Snow Festival day 2; night out in Susukino"),
        ("Fri 6 Feb", "→ Furano", "Drive ~2.5h to Furano, settle into the lodge, easy afternoon"),
        ("Sat 7 Feb", "Furano", "Ski day 1 — Isaac's AM beginner lesson, lads ride powder"),
        ("Sun 8 Feb", "Furano", "Ski day 2 — Isaac's AM lesson, then all ride together"),
        ("Mon 9 Feb", "Furano / Biei", "Rest day — Biei &amp; the Blue Pond, or Asahikawa Zoo penguin parade"),
        ("Tue 10 Feb", "Furano", "Ski day 3 — best snow day, tree runs"),
        ("Wed 11 Feb", "Furano", "Ski day 4 (or a lodge chill day if legs are cooked)"),
        ("Thu 12 Feb", "Furano", "Spare day — last laps, onsen, pack up"),
        ("Fri 13 Feb", "→ Otaru → Sapporo", "Drive back; Jozankei day-use onsen soak, then Otaru Snow Light Path (last evening); night in Sapporo"),
        ("Sat 14 Feb", "Sapporo → Tokyo", "Drop the hire car, fly CTS→Tokyo; afternoon in Shibuya"),
        ("Sun 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab"),
        ("Mon 16 Feb", "Tokyo", "Tsukiji breakfast, shopping, last night out"),
        ("Tue 17 Feb", "Tokyo → home", "Depart Tokyo (NRT) 2:00pm"),
        ("Wed 18 Feb", "→ Brisbane", "Land Brisbane 6:20am"),
    ],
    "itin_footnote":
        "<b>Best value</b> runs the same trip on the ground but flies you straight into Sapporo "
        "on one ticket (no overnight in Tokyo at the start). <b>Fastest sensible</b> is the same "
        "trip flown Jetstar-direct both ways — quicker, but its Feb 4 outbound trims a day off "
        "the Sapporo start. All three keep 7 nights at Furano, 2 Snow Festival days, the Otaru "
        "Snow Light Path on its final evening (13 Feb), and the Jozankei onsen stop.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 59. Bands: 🟢 BUY ≤ $1,430 · "
        "🟡 WATCH $1,430–$1,500 · 🔴 HOLD above $1,500. Yesterday's $1,427 was the first "
        "buy-territory day in a while; today has bounced back to a HOLD.",
    "footer":
        "Auto-sent daily flight watch · everyday fares from Kiwi.com, AUD incl. 1 checked bag "
        "each way · a live Qantas snow-season sale is flagged in the red bar (verify on qantas.com).",
}
# ─────────────────────────────────────────────────────────────────────────────

TH_TD = "padding:9px 10px;font-size:12.5px;color:#3d4757;line-height:1.5;border-bottom:1px solid #eef0f3;vertical-align:top;"


def options_rows():
    out = []
    for label, there, home, pp, all4, all3, note in RUN["options"]:
        out.append(
            f'<tr>'
            f'<td style="{TH_TD}font-weight:700;color:#1a202c;">{label}</td>'
            f'<td style="{TH_TD}">{there}</td>'
            f'<td style="{TH_TD}">{home}</td>'
            f'<td style="{TH_TD}text-align:center;font-weight:700;color:#1a202c;white-space:nowrap;">{pp}</td>'
            f'<td style="{TH_TD}text-align:center;white-space:nowrap;">{all4}</td>'
            f'<td style="{TH_TD}text-align:center;white-space:nowrap;">{all3}</td>'
            f'<td style="{TH_TD}">{note}</td>'
            f'</tr>')
    return "".join(out)


def action_banner():
    """Red call-to-action bar, or nothing on a normal day."""
    msg = RUN.get("action", "").strip()
    if not msg:
        return ""
    return (
        '<tr><td style="background:#b91c1c;border-radius:12px;padding:16px 22px;">'
        '<p style="margin:0;color:#ffffff;font-size:14.5px;font-weight:600;line-height:1.55;">'
        f'{msg}</p></td></tr>'
        '<tr><td style="height:14px;line-height:14px;font-size:0;">&nbsp;</td></tr>')


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
    "ACTION_BANNER": action_banner(),
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
    if RUN.get("action", "").strip():
        L += ["*** " + strip(RUN["action"]) + " ***", ""]
    L += [strip(p) for p in RUN["snapshot"]] + [""]
    d1l, d1v, d2l, d2v = deltas()
    L += [f'{d1l}: {d1v}',
          f'{d2l}: {d2v}',
          f'Distance from buy target (${BUY_TARGET:,}): {RUN["target_distance"]}',
          "", "TRIP OPTIONS", ""]
    for label, there, home, pp, all4, all3, note in RUN["options"]:
        L += [f'{label} - {pp} pp / {all4} for four / {all3} for three',
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
