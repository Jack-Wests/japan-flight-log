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

# Public target only. The real target lives in the push notification, nowhere else.
BUY_TARGET = 1000

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS BLOCK EACH RUN
# ─────────────────────────────────────────────────────────────────────────────
RUN = {
    "date_iso": "2026-08-30",
    "date_human": "Sun 30 Aug 2026",
    "verdict_headline": "🔴 HOLD — nothing worth booking today",
    "best_pp": "$1,516",
    "best_all4": "$6,063",
    "target_distance": "$516 above",
    "snapshot": [
        "The cheapest way to get all four of you to the Hokkaido snow and home again is "
        "<b>$1,516 per person — $6,063 for the four</b>: Brisbane out to Sapporo via Singapore "
        "and Osaka, the internal hop down to Tokyo, and home through Manila.",
        "It's a mild improvement — <b>down $13 on yesterday</b> ($1,529), the third straight day "
        "off the recent peak. But zoom out and it's flat, not falling: <b>up $19 on a week ago</b> "
        "($1,497 on 23 Aug), and mid-pack across the 40 checks we now have, which have run "
        "between <b>$1,333</b> (31 Jul) and <b>$1,688</b> (10 Aug).",
        "The one genuinely useful change: the quick options have come back to earth. The fastest "
        "sensible trip is <b>$1,539pp</b> — only $23pp more than the cheapest. For most of August "
        "that gap was $200–$1,300, so if the price ever does drop you won't have to pick between "
        "cheap and bearable.",
        "No airline sale could be verified — Jetstar, Qantas and Virgin's deal pages were all "
        "blocked today, so we're reporting nothing rather than guessing. Nothing to do; sit tight.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:30pm "
         "<i>(via Singapore + Osaka)</i>",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 3:25pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 10:15am "
         "<i>(via Manila)</i>",
         "$1,516", "$6,063",
         "Long haul: 21h20m in — the Singapore connection is a 1:30am boarding call, brutal. "
         "Lands Sapporo mid-afternoon though, easy first day. Home is 17h50m"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:30pm "
         "<i>(via Singapore + Osaka)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 10:00am → 🛬 lands Brisbane (BNE) Wed 17 Feb 7:15am "
         "<i>(Singapore Airlines the whole way)</i>",
         "$1,549", "$6,198",
         "$33pp more buys a real airline home, bags checked through, and a 5h evening in Changi "
         "instead of a midnight scramble in Manila. 21h20m in, 20h15m home"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 1:45pm "
         "<i>(via Singapore + Osaka)</i>",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 3:25pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 10:15am "
         "<i>(via Manila)</i>",
         "$1,539", "$6,157",
         "20h35m in — but only 45 min quicker, and you change Osaka airports (Kansai → Itami) "
         "with your bags to get it. Honestly not worth $23pp"),
    ],
    "options_footnote":
        "Every price is all-in per person: the flight over, the internal Sapporo→Tokyo hop on "
        "Fri 12 Feb ($116pp), the flight home, and one 20kg checked bag each way. "
        "The Qantas QF107 Sydney–Sapporo nonstop was priced again today at <b>$1,742pp</b> for the "
        "flight in alone; add a ~$180pp Brisbane→Sydney hop and the trip home and it's about "
        "<b>$2,621pp ($10,484 for four)</b> — the nicest way in by a mile (8h50m nonstop, lands "
        "5:55pm) and more than the entire trip budget, so it doesn't get a row. "
        "No date shift within ±3 days saved $100+ pp, so all three stay on their natural dates.",
    "itin_title": "Option A — Cheapest",
    "itin_subtitle": "Rusutsu base · 14 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Mon 1 Feb", "Brisbane → in the air", "Fly out 6:10pm; connect Singapore, then Osaka"),
        ("Tue 2 Feb", "→ Sapporo", "Land Sapporo (CTS) 2:30pm, pick up the hire car, check in, easy first night"),
        ("Wed 3 Feb", "Sapporo", "Nijo Market breakfast, Mt Moiwa ropeway at dusk, Susukino for dinner"),
        ("Thu 4 Feb", "Sapporo", "Snow Festival day 1 — Odori Park, full day"),
        ("Fri 5 Feb", "Sapporo / Otaru", "Snow Festival day 2; evening in Otaru — canal illuminations, sushi"),
        ("Sat 6 Feb", "→ Rusutsu", "Drive ~2h to Rusutsu, check in, afternoon warm-up laps"),
        ("Sun 7 Feb", "Rusutsu", "Ski day 1 — Isaac AM lesson, lads ride powder"),
        ("Mon 8 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride Mt Isola together"),
        ("Tue 9 Feb", "Rusutsu / Niseko", "Ski day 3 — day trip to Niseko, 45 min down the road"),
        ("Wed 10 Feb", "Rusutsu", "Ski day 4 — tree runs, last big powder day"),
        ("Thu 11 Feb", "→ Sapporo", "Drive back, drop the car at Sapporo (CTS); night out in Susukino"),
        ("Fri 12 Feb", "Sapporo → Tokyo", "Fly Sapporo (CTS) 10:35am → Tokyo (HND) 12:20pm; afternoon in Shibuya"),
        ("Sat 13 Feb", "Tokyo", "Asakusa, Akihabara, teamLab Planets"),
        ("Sun 14 Feb", "Tokyo", "Day trip to Hakone — the droppable day if you'd rather add a Rusutsu ski"),
        ("Mon 15 Feb", "Tokyo", "Tsukiji breakfast, shopping, last night out"),
        ("Tue 16 Feb", "Tokyo → home", "Depart Tokyo (HND) 3:25pm"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane (BNE) 10:15am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is exactly the same trip on the ground — same 14 nights, same Rusutsu "
        "base, same festival and ski days. The only change is the flight home: out of Narita at "
        "10:00am instead of Haneda at 3:25pm, and you land Brisbane three hours earlier. "
        "<b>Fastest sensible</b> is also the same trip; it just lands Sapporo 45 minutes earlier "
        "at the cost of shifting yourselves and four bags between Osaka's two airports. "
        "For later: the genuinely quick ways home — Jetstar's 8h55m nonstop and Air Niugini's 11h "
        "run through Port Moresby — only fly on 17 Feb, which means an extra night in Japan and "
        "pushes the total past $1,700pp. Not live today.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 40. Every check so far sits in the "
        "red HOLD band — the cheapest day yet was $1,333 on 31 Jul.",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com, AUD incl. 1 checked bag each way "
        "· no verified sale live today (all three airline deal pages blocked).",
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
