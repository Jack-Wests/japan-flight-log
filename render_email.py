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
BUY_TARGET = 1350
WATCH_CEILING = 1500

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS BLOCK EACH RUN
# ─────────────────────────────────────────────────────────────────────────────
RUN = {
    "date_iso": "2026-09-09",
    "date_human": "Wed 9 Sep 2026",
    "verdict_headline": "🟡 WATCH — normal range, a dip like this will likely come again",
    "best_pp": "$1,435",
    "best_all4": "$5,741",
    "target_distance": "$85 above",
    "snapshot": [
        "The cheapest way to get all four of you to the Hokkaido snow and home again is "
        "<b>$1,435 per person</b> — about <b>$5,741 for the four</b>, or <b>~$4,305 if it's "
        "just three</b> and Hugh sits it out. That's Brisbane→Tokyo return through Port Moresby, "
        "plus the two short hops up to Sapporo and back.",
        "Good news first: that's <b>$187 cheaper than the last check</b> ($1,622 on Tue) — a "
        "proper drop back into the normal range. But it's not a buy signal: we've twice seen the "
        "low $1,300s this winter, and today still sits <b>$85 above the $1,350 buy line</b>. A dip "
        "like this will very likely come round again, so there's no rush.",
        "The catch with the cheapest fare: the way over routes through <b>Port Moresby with an "
        "overnight stuck at the airport</b> — about 29 hours door-to-door, and not a fun one. For "
        "<b>$200pp more ($1,635)</b> the best-value option flies Singapore Airlines straight into "
        "Sapporo with no Port Moresby night — worth a serious look.",
        "No verified airline sale is running today — the recent Jetstar Japan sale closed on "
        "24 Aug, so it's expired. Nothing to book right now: hold and keep watching.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 2 Feb 2:40pm → 🛬 lands Tokyo (NRT) Tue 3 Feb 8:00pm "
         "<i>(via Port Moresby)</i>, then next-morning hop up to Sapporo (CTS)",
         "🛫 Dep Tokyo (NRT) Tue 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Wed 18 Feb 9:40am "
         "<i>(via Port Moresby)</i>",
         "$1,435", "$5,741",
         "Long haul: ~29h in, overnight stuck at Port Moresby — grim, but the cheapest · ~$4,305 for three"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Mon 2 Feb 6:10pm → 🛬 lands Sapporo (CTS) Wed 3 Feb 4:15pm "
         "<i>(Singapore Airlines via Singapore &amp; Osaka)</i>",
         "🛫 Dep Tokyo (NRT) Tue 16 Feb 6:50pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 4:55pm "
         "<i>(Singapore Airlines via Singapore)</i>",
         "$1,635", "$6,540",
         "23h in / 21h home, no Port Moresby — flies you straight to the snow for $200pp more · ~$4,905 for three"),
    ],
    "options_footnote":
        "The <b>Qantas QF107 Sydney–Sapporo direct couldn't be priced today</b> — Kiwi returned no "
        "Qantas nonstop Sydney→Sapporo for 2–5 Feb (the cheapest Sydney→Sapporo was $767pp via Osaka "
        "on Jetstar, and you'd still need a Brisbane→Sydney add-on). The <b>fastest sensible</b> way "
        "over — Jetstar direct both ways via Tokyo plus the two Sapporo hops — comes to <b>$1,828pp</b> "
        "(about 12h each way), which is $393pp above the cheapest, so it's noted here rather than given "
        "a table row. No date shift within ±3 days saved $100+ pp, so the options stay put.",
    "itin_title": "Option A — Cheapest (Tokyo return via Port Moresby)",
    "itin_subtitle": "Rusutsu base · ~13 nights on the ground · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Mon 2 Feb", "Brisbane → Port Moresby", "Fly out 2:40pm, land 5:50pm; overnight stuck at Port Moresby (grim — you won't leave the airport)"),
        ("Tue 3 Feb", "Port Moresby → Tokyo", "Fly 2:10pm, land Narita 8:00pm; overnight near the airport"),
        ("Wed 4 Feb", "Tokyo → Sapporo", "Morning hop to Sapporo (CTS), pick up the car; Snow Festival day 1 (Odori Park)"),
        ("Thu 5 Feb", "Sapporo / Otaru", "Snow Festival day 2; evening in Otaru — canal illuminations, sushi"),
        ("Fri 6 Feb", "→ Rusutsu", "Drive ~2h to Rusutsu, check in, afternoon warm-up laps"),
        ("Sat 7 Feb", "Rusutsu", "Ski day 1 — Isaac AM lesson, lads ride powder"),
        ("Sun 8 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride Mt Isola together"),
        ("Mon 9 Feb", "Rusutsu / Niseko", "Ski day 3 — day-trip to Niseko (45 min)"),
        ("Tue 10 Feb", "Rusutsu", "Ski day 4 — tree runs, last big powder day"),
        ("Wed 11 Feb", "→ Sapporo", "Drive back, drop the car at Sapporo (CTS); night out in Susukino"),
        ("Thu 12 Feb", "Sapporo", "Easy Sapporo day — markets, ramen, anything Otaru you missed"),
        ("Fri 13 Feb", "Sapporo → Tokyo", "Afternoon hop to Tokyo (CTS→HND); evening in Shibuya"),
        ("Sat 14 Feb", "Tokyo", "Asakusa, Akihabara, teamLab Planets"),
        ("Sun 15 Feb", "Tokyo", "Day trip to Hakone — the droppable day if you want another Rusutsu ski"),
        ("Mon 16 Feb", "Tokyo", "Tsukiji breakfast, shopping, last night out"),
        ("Tue 17 Feb", "Tokyo → home", "Depart Narita 9:40pm (via Port Moresby)"),
        ("Wed 18 Feb", "→ Brisbane", "Land Brisbane 9:40am"),
    ],
    "itin_footnote":
        "<b>Best value</b> ($1,635pp) is the same trip on the ground, but flies Singapore Airlines "
        "straight into Sapporo — you skip both the Port Moresby night and the Tokyo overnight at the "
        "start, landing on the snow a full day sooner. The ski block, the Snow Festival days and the "
        "Tokyo finish are identical; you'd just start the ground plan from the 3 Feb Sapporo landing.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 50. Today's $1,435 is back in the amber "
        "WATCH band after Tuesday's $1,622 — the cheapest we've ever logged was $1,333 (31 Jul &amp; "
        "1 Aug).",
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
        colour = "#1565c0" if latest else ("#c0392b" if v > WATCH_CEILING else
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
# Check the visible text only — CSS like font-weight:800 is not a leak. Strip
# thousands separators first so "$1,200" can't sneak the private target past
# a check that only looks for the bare digits.
visible = re.sub(r"<[^>]+>", " ", html)
visible_digits = re.sub(r"(?<=\d)[,\s](?=\d)", "", visible)
assert not re.search(r"(?<!\d)1200(?!\d)", visible_digits), \
    "private buy target leaked into the email"

open(OUT, "w").write(html)
print(f"wrote {OUT} ({len(html):,} chars) — placeholders filled, private target absent")

text = build_text()
text_digits = re.sub(r"(?<=\d)[,\s](?=\d)", "", text)
assert not re.search(r"(?<!\d)1200(?!\d)", text_digits), "private buy target leaked into the text part"
open("email.txt", "w").write(text)
print(f"wrote email.txt ({len(text):,} chars)")
