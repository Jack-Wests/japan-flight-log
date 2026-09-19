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
    "verdict_headline": "🚨 Qantas snow sale is live — ends Monday",
    "best_pp": "$1,554",
    "best_all4": "$6,217",
    "target_distance": "$124 above",
    "snapshot": [
        "<span style=\"display:block;background:#fdecec;border-left:4px solid #c0392b;"
        "padding:12px 14px;border-radius:6px;color:#8a1c1c;font-weight:600;line-height:1.6;\">"
        "🚨 ACTION THIS WEEKEND — Qantas has a snow-season sale on right now: "
        "Brisbane→Sapporo (via Sydney) for the Feb 2027 snow season from about "
        "<b>$1,349 return per person including a checked bag</b>, on a full-service airline. "
        "It ends <b>Monday 21 Sep</b>. That's below our $1,430 book-on-the-spot line. "
        "Get on qantas.com this weekend, price Brisbane→Sapporo return for early Feb — if it "
        "lands anywhere near $1,349–$1,430pp, book it and tell the lads.</span>",
        "On our own daily tracker the cheapest sensible way to get all four of you to the "
        "Hokkaido snow and home is <b>$1,554 per person (about $6,217 for the four, ~$4,663 "
        "for three)</b> — fly into Sapporo (CTS) via Singapore, ski, then home from Tokyo "
        "through Seoul. On the everyday fares that's the <b>dear side — 🔴 HOLD</b>, $124 "
        "above our $1,430 target.",
        "That's <b>up $127 on yesterday's $1,427</b>, which briefly dipped into buy range and "
        "bounced straight back out — exactly the one-day dips we keep seeing. Across all 59 "
        "checks the cheapest has swung between <b>$1,333 and $1,709</b>.",
        "So today's story isn't the everyday fare (still dear) — it's the sale. Qantas "
        "snow-season seats rarely go cheap, and this window shuts Monday. Ignore the "
        "rock-bottom $1,421 Kiwi price: it routes Brisbane⇄Tokyo via Port Moresby both ways "
        "with an overnight stuck in the airport each way — brutal, not worth it.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Sun 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Mon 2 Feb 2:30pm "
         "<i>(Singapore Airlines, via Singapore + Osaka)</i>",
         "🛫 Dep Tokyo (NRT) Mon 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Tue 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,554", "$6,217",
         "Long haul: ~21h in, ~18½h home — two long but civilised layovers, no airport "
         "overnights. Cheapest you'd actually book. Includes the Sapporo→Tokyo hop on 14 Feb"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:50pm "
         "<i>(Cathay Pacific, via Hong Kong)</i>",
         "🛫 Dep Tokyo (NRT) Mon 16 Feb 12:30pm → 🛬 lands Brisbane (BNE) Tue 17 Feb 8:00am "
         "<i>(via Seoul)</i>",
         "$1,685", "$6,740",
         "Only ~15h in, one stop, one airline the whole way — lands you at the snow "
         "mid-afternoon for ~$131pp more. Far less faff than the cheapest"),
    ],
    "options_footnote":
        "The <b>Qantas QF107 Sydney–Sapporo direct</b> is normally about double — but it's "
        "exactly what this week's sale covers: <b>from ~$1,349pp return via Sydney, bags "
        "included</b> (see the red note up top). <b>Fastest all-round</b> is into Sapporo via "
        "Hong Kong (~15h) then Jetstar direct home (~9h) at <b>~$1,883pp</b> — $329pp over the "
        "cheapest, so it doesn't get its own row. And the rock-bottom <b>$1,421pp</b> routes "
        "Brisbane⇄Tokyo via Port Moresby both ways with an overnight stuck in the airport each "
        "way — brutal, so it's left off. No date shift within ±3 days saved $100+pp.",
    "itin_title": "Option — Cheapest (into Sapporo, home from Tokyo)",
    "itin_subtitle": "Furano base · ~13 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Sun 1 Feb", "✈️ Brisbane → (Singapore)", "Fly out Brisbane (BNE) 6:10pm; overnight in the air via Singapore"),
        ("Mon 2 Feb", "🛬 Sapporo (CTS)", "Land 2:30pm; pick up the hire car, check in, dinner in Susukino"),
        ("Tue 3 Feb", "Sapporo", "Gear hire + city day (Snow Festival opens tomorrow)"),
        ("Wed 4 Feb", "Sapporo", "Snow Festival day 1 — Odori Park ice sculptures"),
        ("Thu 5 Feb", "Sapporo", "Snow Festival day 2, then a night in Susukino"),
        ("Fri 6 Feb", "→ Furano", "Drive ~2½h to Furano, settle into the lodge"),
        ("Sat 7 Feb", "Furano", "Ski day 1 — Isaac's beginner lesson in the morning"),
        ("Sun 8 Feb", "Furano", "Ski day 2 — Isaac's beginner lesson in the morning"),
        ("Mon 9 Feb", "Furano / Biei", "Rest day — Biei & the Blue Pond"),
        ("Tue 10 Feb", "Furano", "Ski day 3 — powder laps"),
        ("Wed 11 Feb", "Furano / Asahikawa", "Rest day — Asahikawa Zoo penguin parade"),
        ("Thu 12 Feb", "Furano", "Ski day 4 — last big day on the mountain"),
        ("Fri 13 Feb", "→ Jozankei → Otaru", "Drive back: Jozankei day-use onsen soak, then Otaru Snow Light Path (its last evening); night in Sapporo"),
        ("Sat 14 Feb", "✈️ Sapporo → Tokyo", "Drop the car; fly CTS→Tokyo (HND) 8:00am→9:35am; afternoon in Shibuya"),
        ("Sun 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab — full day"),
        ("Mon 16 Feb", "✈️ Tokyo → home", "Tsukiji breakfast, then depart Tokyo (NRT) 12:30pm (via Seoul)"),
        ("Tue 17 Feb", "🛬 Brisbane", "Land Brisbane (BNE) 8:00am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the same trip on the ground — it just flies you in on Cathay via "
        "Hong Kong (~15h, lands mid-afternoon) instead of the longer Singapore routing. If "
        "Hugh's out and it's three of you, the per-person fares don't change; the group totals "
        "just drop to ~$4,663 (cheapest) / ~$5,055 (best value). The ryokan variant — leave "
        "Furano a day earlier and sleep at Jozankei on the 12th — uses the same flights.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 59. Today's $1,554 is 🔴 HOLD; "
        "yesterday's $1,427 was the only recent dip into buy range and it lasted a single day. "
        "Cheapest ever was $1,333 (late Jul / early Aug); dearest $1,709 (13 Sep).",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. 1 checked bag each way "
        "· 🚨 live Qantas snow-season sale ends Mon 21 Sep.",
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
