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
    "date_iso": "2026-08-19",
    "date_human": "Wed 19 Aug 2026",
    "verdict_headline": "🔴 HOLD — third day running with no price",
    "best_pp": "$1,421",
    "best_all4": "$5,684",
    "target_distance": "$421 above (as at 16 Aug)",
    "snapshot": [
        "<b>Still no price — that's three days now.</b> The flight search connector "
        "didn't load again today, and every flight and airline website was blocked "
        "before a page could open. Monday's check failed the same way, and on Tuesday "
        "the check doesn't appear to have run at all. As on Monday, <b>nothing was "
        "added to the price log</b> rather than a guessed number.",
        "The last real reading is still <b>Sun 16 Aug: $1,421 per person — $5,684 for "
        "the four</b>, flying Jetstar to Osaka, a night near the airport, a short hop up "
        "to Sapporo in the morning, then home out of Tokyo with Singapore Airlines. "
        "That is what the table below shows; it is three days old, not today's.",
        "The gap costs us nothing yet. Across <b>28 days of checks</b> the price has "
        "bounced between <b>$1,333 and $1,688</b> with no trend either way, and it has "
        "never once come near the $1,000 we're waiting for — so there is no sign we've "
        "missed a bargain. It was HOLD on Sunday and it stays HOLD.",
        "No verified airline sale is running — the sale pages couldn't be read again. "
        "<b>Nothing for you to do today.</b> The thing that does need doing is a look at "
        "the checker itself: three days blind is no longer a glitch, and if it keeps up, "
        "we'd have no warning when a cheap fare finally shows up.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 11:45am → 🛬 lands Sapporo (CTS) Tue 2 Feb 9:55am "
         "<i>(Jetstar to Osaka, overnight, Peach up to Sapporo)</i>",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 4:40pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 10:45am "
         "<i>(Singapore Airlines via Singapore)</i>",
         "$1,421", "$5,684",
         "23h10 out · 17h05 home. Long haul: the 12h stop in Osaka is overnight, so it's a "
         "cheap airport hotel rather than a look around town. Quick 1h30 change in Singapore "
         "on the way back"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 11:45am → 🛬 lands Sapporo (CTS) Tue 2 Feb 9:55am "
         "<i>(same as above)</i>",
         "🛫 Dep Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am "
         "<i>(Air Niugini via Port Moresby)</i>",
         "$1,456", "$5,824",
         "23h10 out · 11h00 home. $35pp buys 6 hours off the trip home — overnight flight, "
         "1h stop in Port Moresby at dawn, land 9:40am. Costs one extra night away"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 10:35pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 11:00am "
         "<i>(EVA Air via Taipei)</i>",
         "🛫 Dep Tokyo (HND) Tue 16 Feb 4:40pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 10:45am "
         "<i>(Singapore Airlines via Singapore)</i>",
         "$1,828", "$7,312",
         "13h25 out · 17h05 home. On the mountain half a day earlier with no overnight "
         "anywhere — but $407pp over the cheapest, past what this trip can carry"),
    ],
    "options_footnote":
        "<b>These three are Sunday's prices (16 Aug), now three days old and carried over "
        "unchanged — nothing could be priced today.</b> The <b>Qantas QF107 Sydney–Sapporo "
        "direct</b> couldn't be priced either; its last reading was <b>$1,664pp</b> for the "
        "flight in, plus a $200pp Brisbane→Sydney hop and $746pp home from Tokyo — "
        "<b>$2,610pp all-in ($10,440 for four)</b>. Nicest way to travel, nearly double the "
        "cheapest, so it stays a footnote rather than a row. Date shifts of ±3 days couldn't "
        "be tested today either, so the dates stay put.",
    "itin_title": "Option A — Cheapest",
    "itin_subtitle": "Rusutsu base · 14 nights · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Mon 1 Feb", "Brisbane → Osaka", "Fly out 11:45am, land Osaka (KIX) 7:45pm; cheap airport hotel"),
        ("Tue 2 Feb", "Osaka → Sapporo", "8:00am hop, land Sapporo (CTS) 9:55am; pick up the hire car, check in"),
        ("Wed 3 Feb", "Sapporo", "Shake off the flight — Susukino, ramen alley, Sapporo Beer Museum"),
        ("Thu 4 Feb", "Sapporo", "Snow Festival day 1 — the big Odori Park sculptures"),
        ("Fri 5 Feb", "Sapporo / Otaru", "Snow Festival day 2; evening in Otaru — canal lights, sushi"),
        ("Sat 6 Feb", "→ Rusutsu", "Drive ~2h to Rusutsu, check in, afternoon warm-up laps"),
        ("Sun 7 Feb", "Rusutsu", "Ski day 1 — Isaac AM lesson, lads ride powder"),
        ("Mon 8 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride Mt Isola together"),
        ("Tue 9 Feb", "Rusutsu / Niseko", "Ski day 3 — day-trip to Niseko (45 min each way)"),
        ("Wed 10 Feb", "Rusutsu", "Ski day 4 — tree runs, last big powder day"),
        ("Thu 11 Feb", "→ Sapporo", "Drive back, drop the car at Sapporo (CTS); night out in Susukino"),
        ("Fri 12 Feb", "Sapporo → Tokyo", "Fly 9:30am → 11:20am; afternoon in Shibuya"),
        ("Sat 13 Feb", "Tokyo", "Asakusa, Akihabara, teamLab Planets"),
        ("Sun 14 Feb", "Tokyo", "Day trip to Hakone — the droppable day if you'd rather ski another"),
        ("Mon 15 Feb", "Tokyo", "Tsukiji breakfast, shopping, last night out"),
        ("Tue 16 Feb", "Tokyo → home", "Depart Haneda (HND) 4:40pm"),
        ("Wed 17 Feb", "→ Brisbane", "Land Brisbane 10:45am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the same trip on the ground — same flights over, same Snow "
        "Festival days, same four ski days at Rusutsu. It only changes at the end: one extra "
        "Tokyo day, then a shorter overnight run home. <b>Fastest sensible</b> is also the same "
        "trip; it just flies in through Taipei overnight instead of stopping in Osaka, so you "
        "skip a hotel and reach Sapporo before lunch.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 28. The log stops at Sun 16 Aug — "
        "there are no bars for Mon, Tue or today, because no price could be read on any of them "
        "and nothing was logged. Everything on record still sits in the red HOLD band; the "
        "cheapest day yet was $1,333 on 31 Jul.",
    "footer":
        "Auto-sent daily flight watch · prices normally from Kiwi.com, AUD incl. 1 checked bag "
        "each way · today's check failed — figures shown are Sun 16 Aug · no verified sale live.",
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


# Normally None: the chart is served from whatever branch this run pushes to.
# Set it to a branch name when this run CANNOT push (see 19 Aug 2026 — the
# GitHub token had read-only access), and point it at a pushed branch whose
# chart-email.png is byte-identical to the one just generated. Verify that with
# md5sum before setting it; otherwise the email ships a chart that disagrees
# with its own text.
CHART_BRANCH_OVERRIDE = None


def chart_branch():
    """Branch the chart image is served from — read it from git rather than
    hardcoding, so the URL still resolves whichever branch the run pushes to."""
    if CHART_BRANCH_OVERRIDE:
        return CHART_BRANCH_OVERRIDE
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

    # A run that couldn't price anything appends no row, so the last row is not
    # today's. Say so rather than calling an older reading "yesterday".
    run_day = datetime.strptime(RUN["date_iso"], "%Y-%m-%d")
    stale = today != run_day

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
    elif stale:
        gap = (run_day - today).days
        when = "yesterday" if gap == 1 else f"{gap} days ago"
        l1 = f"No reading today — last check was {when} ({fmt(today)}), when it moved"
        v1 = move(float(prior[-1]["best_total_pp"]))
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
        l2 = f"{label} ({fmt(pdt)})" + (f", measured to {fmt(today)}" if stale else "")
        v2 = move(float(pick["best_total_pp"]))
    else:
        l2, v2 = "Longer trend", "not enough history yet"

    return l1, v1, l2, v2


_d1l, _d1v, _d2l, _d2v = deltas()

P = "margin:0 0 11px;font-size:14.5px;line-height:1.65;color:#2d3748;"

def header_bg():
    """Banner colour follows the verdict. It used to be hardcoded green, which
    put a 'go' colour above a HOLD headline on every email we've ever sent."""
    h = RUN["verdict_headline"]
    if "🔴" in h:
        return "#991b1b"      # HOLD  — red
    if "🟡" in h:
        return "#a16207"      # WATCH — amber
    return "#166534"          # BUY   — green


VALUES = {
    "HEADER_BG": header_bg(),
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
