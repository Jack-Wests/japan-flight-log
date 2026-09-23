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

# One target: $1,500. No private target.
BUY_TARGET = 1500


def cpp(row):
    """Comfortable price for a log row — the number the verdict is based on.
    Falls back to best_total_pp for rows logged before v3 added the column."""
    c = (row.get("best_comfortable_pp") or "").strip()
    return float(c) if c else float(row["best_total_pp"])

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS BLOCK EACH RUN
# ─────────────────────────────────────────────────────────────────────────────
RUN = {
    "date_iso": "2026-09-23",
    "date_human": "Wed 23 Sep 2026",
    "verdict_headline": "🟡 WATCH — normal range, a dip might come",
    "best_pp": "$1,587",
    "best_all4": "$6,348",
    "target_distance": "$87 above",
    "snapshot": [
        "The cheapest comfortable way to get you to the Hokkaido snow and home again is "
        "<b>$1,587 per person — $6,348 for all four, or $4,761 for three</b> if Hugh buys "
        "separately. That's Singapore Airlines into Osaka, a cheap Skymark hop up to Sapporo, a "
        "hop back to Tokyo after the ski, and Singapore Airlines home from Tokyo.",
        "That's <b>WATCH</b>: normal range, not a buy. It's $23 up on yesterday's $1,564 and $87 "
        "above the $1,500 buy price. Singapore Airlines has turned up cheap today — every "
        "option in the table flies it at least one way.",
        "If you'd put up with a forced overnight in Port Moresby, it's ~$1,455 before the hotel, "
        "but ~$1,655 once you add it. Not recommended.",
        "⏳ About 4 months (131 days) until departure. <b>About 3 weeks to the mid-October "
        "deadline</b> — after that, book the first comfortable day under $1,600, and today's "
        "$1,587 would already qualify. No airline sale is live: Qantas's Asia sale ended on 21 Sep.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 7:15pm "
         "<i>(Singapore Airlines via Singapore to Osaka (KIX), ferry to Kobe (UKB), Skymark to Sapporo)</i>",
         "🛫 Sapporo (CTS) Sun 14 Feb 8:10am → Tokyo (HND) 9:55am, then Dep Tokyo (NRT) Tue 16 Feb "
         "6:50pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 4:55pm <i>(Singapore Airlines via Singapore)</i>",
         "$1,587", "$6,348<br><span style=\"color:#8a94a6;\">3 of you: $4,761</span>",
         "~26h over (9h daytime stop in Osaka, bags and 30-min ferry, ~$19 included) · ~21h home, "
         "1:20–7:05am wait in Singapore"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 6:10pm → 🛬 lands Sapporo (CTS) Wed 3 Feb 7:40pm "
         "<i>(Singapore Airlines via Singapore to Osaka (KIX), Peach to Sapporo)</i>",
         "Same as Cheapest: Sapporo → Tokyo Sun 14 Feb, home from Tokyo (NRT) Tue 16 Feb 6:50pm "
         "→ lands Brisbane Wed 17 Feb 4:55pm",
         "$1,641", "$6,564<br><span style=\"color:#8a94a6;\">3 of you: $4,923</span>",
         "Overnight in Singapore (12:05–8:25am): Isaac sees his partner, free stay. $54pp more"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am (Mon night) → 🛬 lands Sapporo (CTS) Tue 2 Feb "
         "2:50pm <i>(Cathay Pacific via Hong Kong)</i>",
         "Same as Cheapest: Sapporo → Tokyo Sun 14 Feb, home from Tokyo (NRT) Tue 16 Feb 6:50pm "
         "→ lands Brisbane Wed 17 Feb 4:55pm",
         "$1,729", "$6,916<br><span style=\"color:#8a94a6;\">3 of you: $5,187</span>",
         "15h over with one short Hong Kong change. $142pp more than the cheapest"),
    ],
    "options_footnote":
        "Prices are per person, all-in, with a 20kg checked bag each way and the $125 Sapporo→Tokyo hop "
        "on 14 Feb. <b>In between:</b> $1,599pp for the Cheapest routing but with a direct Peach hop "
        "from Osaka (KIX) instead of the Kobe ferry: 20h over and no airport change, $12pp more. "
        "<b>Cheapest if you'd overnight in Port Moresby:</b> ~$1,455pp. Not recommended: "
        "it's ~$1,655 once you add a hotel and transfers. <b>Qantas QF107 Sydney–Sapporo direct:</b> "
        "$1,737pp one way from Sydney, about $1,900pp with the Brisbane–Sydney flight. That's just to "
        "get there, so it's not a live pick. <b>Fastest both ways</b> (Cathay over, Singapore Airlines "
        "from Haneda home in 17h) is $1,890pp, $303 over the cheapest. No date shift saved $100+pp.",
    # Door-to-door timeline per table row, drawn as bars in the email.
    # Each leg is a list of (kind, minutes, label). kind: "fly" = in the air,
    # "wait" = stopover/transfer, "sg" = Singapore stop long enough to leave the
    # airport (free stay with Isaac's partner). Minutes must add up to the
    # door-to-door time quoted in the table.
    "journeys": [
        ("Cheapest", {
            "there": [("fly", 475, "Brisbane → Singapore"), ("wait", 85, "Singapore"),
                      ("fly", 365, "Singapore → Osaka"),
                      ("wait", 530, "Osaka, ferry to Kobe airport"),
                      ("fly", 110, "Kobe → Sapporo")],
            "home": [("fly", 450, "Tokyo → Singapore"), ("wait", 345, "Singapore, 1:20–7:05am"),
                     ("fly", 470, "Singapore → Brisbane")],
        }),
        ("Best value", {
            "there": [("fly", 475, "Brisbane → Singapore"),
                      ("sg", 500, "Singapore overnight, 12:05–8:25am"),
                      ("fly", 365, "Singapore → Osaka"), ("wait", 135, "Osaka"),
                      ("fly", 115, "Osaka → Sapporo")],
            "home": [("fly", 450, "Tokyo → Singapore"), ("wait", 345, "Singapore, 1:20–7:05am"),
                     ("fly", 470, "Singapore → Brisbane")],
        }),
        ("Fastest sensible", {
            "there": [("fly", 510, "Brisbane → Hong Kong"), ("wait", 110, "Hong Kong"),
                      ("fly", 280, "Hong Kong → Sapporo")],
            "home": [("fly", 450, "Tokyo → Singapore"), ("wait", 345, "Singapore, 1:20–7:05am"),
                     ("fly", 470, "Singapore → Brisbane")],
        }),
    ],
    "itin_title": "Option A — Cheapest (Furano base)",
    "itin_subtitle": "15 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Mon 1 Feb", "Brisbane → Singapore", "Fly out 6:10pm, change planes in Singapore around midnight"),
        ("Tue 2 Feb", "Osaka → Sapporo", "Land Osaka 8:35am, day in Osaka, ferry to Kobe, land Sapporo 7:15pm, pick up the car"),
        ("Wed 3 Feb", "Sapporo", "Recovery day: ramen alley, Sapporo Beer Museum, Tanukikoji arcade"),
        ("Thu 4 Feb", "Sapporo", "<b>Snow Festival day 1</b>: Odori Park on opening day"),
        ("Fri 5 Feb", "Sapporo", "<b>Snow Festival day 2</b>: Susukino ice sculptures + Tsudome; night out"),
        ("Sat 6 Feb", "→ Furano", "Drive ~2h to Furano, check into the lodge, easy afternoon"),
        ("Sun 7 Feb", "Furano", "<b>Ski day 1</b>: Isaac's beginner lesson in the morning, the others ride"),
        ("Mon 8 Feb", "Furano", "<b>Ski day 2</b>: Isaac's second lesson, then everyone skis together"),
        ("Tue 9 Feb", "Furano / Biei", "Rest day: Blue Pond and Biei's snowy hills"),
        ("Wed 10 Feb", "Furano", "<b>Ski day 3</b>"),
        ("Thu 11 Feb", "Furano / Asahikawa", "Asahikawa Zoo penguin parade, or a chill lodge day"),
        ("Fri 12 Feb", "Furano", "<b>Ski day 4</b>, last night at the lodge"),
        ("Sat 13 Feb", "→ Jozankei → Otaru → Sapporo", "Day-use onsen at Jozankei, then the <b>Otaru Snow Light Path</b> on its last evening; sleep in Sapporo"),
        ("Sun 14 Feb", "Sapporo → Tokyo", "Drop the car at Sapporo (CTS), fly 8:10am, land Haneda 9:55am; Shibuya"),
        ("Mon 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab"),
        ("Tue 16 Feb", "Tokyo → home", "Last morning in Tokyo, fly out of Narita 6:50pm"),
        ("Wed 17 Feb", "→ Brisbane", "Change planes in Singapore 1:20–7:05am, land Brisbane 4:55pm"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the same trip, but you leave Tue 2 Feb and spend the night in "
        "Singapore (Isaac with his partner, the others in town). You land in Sapporo Wed 3 Feb at 7:40pm, "
        "so there's one less Sapporo night and you still make the first Snow Festival day. "
        "<b>Fastest sensible</b> leaves just after midnight Mon night and lands in Sapporo at 2:50pm Tue 2 Feb, "
        "an afternoon earlier than the cheapest. Everything after that is the same.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 63. From today the line tracks the "
        "cheapest <i>comfortable</i> price (no hidden forced overnights). Earlier days logged the "
        "cheapest price with any routing. Comfortable range so far: $1,333–$1,709.",
    "footer":
        "Auto-sent daily flight watch · prices from Kiwi.com (Skyscanner cross-check failed today), AUD "
        "incl. 1 checked bag each way · no verified sale live today.",
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


# Journey bars: flying / waiting / Singapore stop. Colours checked for
# colourblind separation; every bar also has a written breakdown underneath, so
# nothing relies on colour alone.
SEG_COLOUR = {"fly": "#1565c0", "wait": "#e0913a", "sg": "#12a37f"}
SEG_WORD = {"fly": "✈️", "wait": "wait", "sg": "🇸🇬 stop"}


def hm(mins):
    return f"{mins // 60}h{mins % 60:02d}" if mins % 60 else f"{mins // 60}h"


def journey_block():
    legs = [leg for _, j in RUN["journeys"] for leg in j.values()]
    longest = max(sum(m for _, m, _ in leg) for leg in legs)
    out = []
    for name, j in RUN["journeys"]:
        out.append(f'<p style="margin:16px 0 6px;font-size:13.5px;font-weight:700;color:#1a202c;">{name}</p>')
        for which, leg in (("There", j["there"]), ("Home", j["home"])):
            total = sum(m for _, m, _ in leg)
            cells = []
            for kind, m, _ in leg:
                w = max(1, round(m / longest * 100, 1))
                cells.append(f'<td style="width:{w}%;background:{SEG_COLOUR[kind]};height:18px;'
                             f'line-height:18px;font-size:0;border-right:2px solid #ffffff;">&nbsp;</td>')
            rest = round(100 - total / longest * 100, 1)
            if rest > 0.5:
                cells.append(f'<td style="width:{rest}%;font-size:0;">&nbsp;</td>')
            detail = " · ".join(
                f'{SEG_WORD[k]} {hm(m)} {label}' for k, m, label in leg)
            out.append(
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                f'<td style="width:44px;font-size:12px;color:#5b6b8c;padding:0 8px 0 0;white-space:nowrap;">{which}</td>'
                f'<td style="padding:0;"><table width="100%" cellpadding="0" cellspacing="0" border="0" '
                f'style="border-radius:4px;overflow:hidden;"><tr>{"".join(cells)}</tr></table></td>'
                f'<td style="width:52px;font-size:12.5px;font-weight:700;color:#1a202c;text-align:right;'
                f'padding:0 0 0 8px;white-space:nowrap;">{hm(total)}</td></tr></table>'
                f'<p style="margin:3px 0 8px 52px;font-size:11.5px;color:#5b6b8c;line-height:1.45;">{detail}</p>')
    legend = " &nbsp; ".join(
        f'<span style="display:inline-block;width:10px;height:10px;background:{SEG_COLOUR[k]};'
        f'border-radius:2px;vertical-align:middle;"></span>&nbsp;{t}'
        for k, t in (("fly", "In the air"), ("wait", "Waiting / changing planes"),
                     ("sg", "Singapore stop, can leave the airport")))
    return (f'<p style="margin:0 0 4px;font-size:12px;color:#3d4757;">{legend}</p>'
            + "".join(out))


def journey_text():
    L = []
    for name, j in RUN["journeys"]:
        L.append(name)
        for which, leg in (("There", j["there"]), ("Home", j["home"])):
            total = sum(m for _, m, _ in leg)
            parts = " | ".join(
                f'{"flying" if k == "fly" else "waiting"} {hm(m)} {label}' for k, m, label in leg)
            L.append(f"  {which} {hm(total)}: {parts}")
    return L



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
    vals = [cpp(r) for r in allrows]
    top = max(vals) * 1.06
    out = []
    for i, r in enumerate(rows):
        latest = i == len(rows) - 1
        v = cpp(r)
        pct = max(4, round(v / top * 100))
        colour = "#1565c0" if latest else ("#c0392b" if v > 1600 else
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
    now = cpp(rows[-1])
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
        v1 = move(cpp(prev))

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
        v2 = move(cpp(pick))
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
    "JOURNEY_BLOCK": journey_block(),
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
        L += [f'{label} - {pp} pp / {strip(all4.replace("<br>", " · "))} for four',
              f'  There: {strip(there)}',
              f'  Home:  {strip(home)}',
              f'  {note}', ""]
    L += [strip(RUN["options_footnote"]), "", "HOW LONG EACH TRIP TAKES", ""] + journey_text() + [""]
    L += [
          RUN["itin_title"].upper(), strip(RUN["itin_subtitle"]), ""]
    for date, loc, plan in RUN["itinerary"]:
        L.append(f'  {date:<12} {strip(loc):<20} {strip(plan)}')
    L += ["", strip(RUN["itin_footnote"]), "", "PRICE LOG", ""]
    for r in csv.DictReader(open("prices.csv")):
        d = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%a %-d %b")
        L.append(f'  {d:<12} ${cpp(r):,.0f}')
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
