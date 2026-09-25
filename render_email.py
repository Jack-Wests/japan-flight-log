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
from datetime import datetime, timedelta

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
    "date_iso": "2026-09-25",
    "date_human": "Fri 25 Sep 2026 (afternoon re-check)",
    "verdict_headline": "🟡 WATCH — normal range, a dip might come",
    "best_pp": "$1,574",
    "best_all4": "$6,296",
    "target_distance": "$74 above",
    "snapshot": [
        "The cheapest comfortable way to the Hokkaido snow and home again is now "
        "<b>$1,574 per person — $6,296 for all four, or $4,722 for three</b> if Hugh buys "
        "separately. It's a <b>China Airlines return to Tokyo via Taipei</b>, plus a cheap Peach flight up to "
        "Sapporo and an Air Do flight back to Tokyo after the ski. This morning's email said $1,589. This "
        "re-check found the China Airlines return, which comes in $15 cheaper.",
        "The catch: you land in Tokyo at 6:30pm Tue 2 Feb, sleep near Narita airport and fly to Sapporo at "
        "6:50am. That night replaces a Sapporo night, so it costs about the same, but you reach Sapporo the "
        "morning of Wed 3 Feb. <b>For $35pp more, the Best value option</b> (Singapore Airlines over, Air Niugini "
        "home) gets you there 18 hours sooner and home in 11 hours instead of 19. Honestly, it's the better trip.",
        "That's <b>WATCH</b>, $74 above the $1,500 buy price, and $28 down on yesterday's $1,602.",
        "⏳ About 4 months (130 days) until departure. <b>About 3 weeks to the mid-October deadline</b>. "
        "After that, book the first comfortable day under $1,600, and today's $1,574 would already qualify. "
        "No airline sale covers early February from Brisbane right now.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 11:10pm → 🛬 lands Tokyo (NRT) Tue 2 Feb 6:30pm "
         "<i>(China Airlines via Taipei)</i>; night near Narita, then 🛫 Tokyo (NRT) Wed 3 Feb 6:50am → "
         "🛬 lands Sapporo (CTS) 8:40am <i>(Peach)</i>",
         "🛫 Sapporo (CTS) Sun 14 Feb 8:00am → Tokyo (HND) 9:35am <i>(Air Do)</i>, then 🛫 Dep Tokyo (NRT) "
         "Wed 17 Feb 2:35pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 10:45am <i>(China Airlines via Taipei)</i>",
         "$1,574", "$6,296<br><span style=\"color:#8a94a6;\">3 of you: $4,722</span>",
         "34.5h over, including an 8.5h daytime stop in Taipei (long enough to get into the city, no visa "
         "needed) and a night's sleep near Narita that replaces a Sapporo night · 19h home with a 6h "
         "evening stop in Taipei"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:30pm "
         "<i>(Singapore Airlines via Singapore to Osaka (KIX), Peach to Sapporo)</i>",
         "🛫 Sapporo (CTS) Sun 14 Feb 8:00am → Tokyo (HND) 9:35am <i>(Air Do)</i>, then 🛫 Dep Tokyo (NRT) "
         "Wed 17 Feb 9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am <i>(Air Niugini via Port Moresby, 1h change)</i>",
         "$1,609", "$6,436<br><span style=\"color:#8a94a6;\">3 of you: $4,827</span>",
         "$35pp more: in Sapporo 18 hours sooner, 21h over, and home in 11h on an overnight flight "
         "with a 5:30am plane change in Port Moresby (no hotel)"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am (Mon night) → 🛬 lands Sapporo (CTS) Tue 2 Feb "
         "2:50pm <i>(Cathay Pacific via Hong Kong)</i>",
         "Same as Best value: Sapporo → Tokyo Sun 14 Feb, Air Niugini home from Tokyo (NRT) Wed 17 Feb "
         "9:40pm → lands Brisbane Thu 18 Feb 9:40am",
         "$1,737", "$6,948<br><span style=\"color:#8a94a6;\">3 of you: $5,211</span>",
         "15h over with one short Hong Kong change. $163pp more than the cheapest"),
    ],
    "options_footnote":
        "Prices are per person, all-in, with a 20kg checked bag each way and the flights within Japan "
        "(Air Do Sapporo→Tokyo $113 on 14 Feb; Peach Narita→Sapporo $118 on 3 Feb for the Cheapest). "
        "<b>This morning's pick</b> (Singapore Airlines to Osaka, a 30-min ferry to Kobe, Skymark to Sapporo, "
        "landing Tue 2 Feb 7:15pm; Singapore Airlines home Tue 16 Feb) is still there at $1,589. "
        "<b>Singapore overnight option</b>: leave Tue 2 Feb, 12:05–8:25am in Singapore (Isaac sees his partner, "
        "free stay), land Sapporo Wed 3 Feb 7:40pm. That's $1,650, $76 over the cheapest and past the ~$50 "
        "we'd pay extra for a Singapore stop. <b>Cheapest if you'd overnight at Osaka's airport:</b> "
        "$1,610 (Jetstar + Peach). Not recommended: it's ~$1,670 once you add a hotel. "
        "<b>Qantas QF107 Sydney–Sapporo direct:</b> $1,737pp one way from Sydney, before the Brisbane–Sydney "
        "flight. That's just to get there, so it's not a live pick. No date shift saved $100+pp.",
    # Door-to-door timeline per table row, drawn as bars in the email.
    # Each leg is (departure in Brisbane time/AEST "YYYY-MM-DD HH:MM", segments);
    # each segment is (kind, minutes, label). kind: "fly" = in the air,
    # "wait" = stopover/transfer, "sg" = Singapore stop long enough to leave the
    # airport (free stay with Isaac's partner). Minutes must add up to the
    # door-to-door time quoted in the table; clock times are worked out from them.
    "journeys": [
        ("Cheapest", {
            "there": ("2027-02-01 23:10", [
                ("fly", 520, "Brisbane → Taipei"), ("wait", 515, "Taipei, 5:50am–2:25pm"),
                ("fly", 185, "Taipei → Tokyo"),
                ("wait", 740, "night near Narita airport"),
                ("fly", 110, "Tokyo → Sapporo")]),
            "home": ("2027-02-17 15:35", [
                ("fly", 250, "Tokyo → Taipei"), ("wait", 370, "Taipei, 5:45–11:55pm"),
                ("fly", 530, "Taipei → Brisbane")]),
        }),
        ("Best value", {
            "there": ("2027-02-01 18:10", [
                ("fly", 475, "Brisbane → Singapore"), ("wait", 85, "Singapore"),
                ("fly", 365, "Singapore → Osaka"), ("wait", 240, "Osaka"),
                ("fly", 115, "Osaka → Sapporo")]),
            "home": ("2027-02-17 22:40", [
                ("fly", 410, "Tokyo → Port Moresby"), ("wait", 60, "Port Moresby, 5:30–6:30am"),
                ("fly", 190, "Port Moresby → Brisbane")]),
        }),
        ("Fastest sensible", {
            "there": ("2027-02-02 00:50", [
                ("fly", 510, "Brisbane → Hong Kong"), ("wait", 110, "Hong Kong"),
                ("fly", 280, "Hong Kong → Sapporo")]),
            "home": ("2027-02-17 22:40", [
                ("fly", 410, "Tokyo → Port Moresby"), ("wait", 60, "Port Moresby, 5:30–6:30am"),
                ("fly", 190, "Port Moresby → Brisbane")]),
        }),
    ],
    "itin_title": "Option A — Cheapest (Furano base)",
    "itin_subtitle": "15 nights on the ground · hire car picked up &amp; dropped at Sapporo (CTS)",
    "itinerary": [
        ("Mon 1 Feb", "Brisbane → Taipei", "Fly out 11:10pm on China Airlines"),
        ("Tue 2 Feb", "Taipei → Tokyo", "Land Taipei 5:50am, morning in the city (Taipei 101, breakfast), fly 2:25pm, land Narita 6:30pm, sleep near the airport"),
        ("Wed 3 Feb", "Tokyo → Sapporo", "Fly 6:50am, land Sapporo 8:40am, pick up the car; ramen alley, Sapporo Beer Museum"),
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
        ("Sun 14 Feb", "Sapporo → Tokyo", "Drop the car at Sapporo (CTS), fly 8:00am, land Haneda 9:35am; Shibuya"),
        ("Mon 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab"),
        ("Tue 16 Feb", "Tokyo", "Shinjuku, Harajuku, day trip option to Kamakura or Hakone"),
        ("Wed 17 Feb", "Tokyo → Taipei", "Fly out of Narita 2:35pm, 6h evening stop in Taipei (a night market if you're keen), fly 11:55pm"),
        ("Thu 18 Feb", "→ Brisbane", "Land Brisbane 10:45am"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the same trip from Snow Festival day 1 onwards, but you leave Mon 1 Feb at 6:10pm "
        "on Singapore Airlines and land in Sapporo at 2:30pm Tue 2 Feb, a whole extra afternoon and evening in "
        "Sapporo. On the way home you fly out of Narita at 9:40pm Wed 17 Feb and land in Brisbane at 9:40am. "
        "<b>Fastest sensible</b> leaves just after midnight Mon night and lands in Sapporo at 2:50pm Tue 2 Feb, "
        "with the same flight home as Best value.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 65. Today's figure replaces this morning's "
        "$1,589. Since 23 Sep the line tracks the cheapest <i>comfortable</i> price (no hidden forced "
        "overnights). Earlier days logged the cheapest price with any routing. Comfortable range so far: "
        "$1,333–$1,709.",
    "footer":
        "Daily flight watch · prices from Kiwi.com (Skyscanner cross-check unavailable today), AUD "
        "incl. 1 checked bag each way · no verified sale live today.",
}
# ─────────────────────────────────────────────────────────────────────────────

TH_TD = "padding:9px 10px;font-size:12.5px;color:#3d4757;line-height:1.5;border-bottom:1px solid #eef0f3;vertical-align:top;"


def options_rows():
    """One stacked card per option. Cards, not a six-column table: a wide table
    forces the whole email wider than a phone screen."""
    lab = "margin:0 0 2px;font-size:11px;font-weight:700;color:#8a94a6;letter-spacing:0.6px;text-transform:uppercase;"
    body = "margin:0 0 10px;font-size:13px;color:#3d4757;line-height:1.5;"
    out = []
    for label, there, home, pp, all4, note in RUN["options"]:
        out.append(
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="width:100%;border:1px solid #e5e8ec;border-radius:8px;margin:0 0 12px;">'
            f'<tr><td style="background:#f3f5f8;padding:10px 12px;border-bottom:1px solid #e5e8ec;'
            f'border-radius:8px 8px 0 0;font-size:14.5px;font-weight:700;color:#1a202c;">{label}</td>'
            f'<td align="right" style="background:#f3f5f8;padding:10px 12px;border-bottom:1px solid #e5e8ec;'
            f'border-radius:8px 8px 0 0;white-space:nowrap;">'
            f'<span style="font-size:17px;font-weight:800;color:#1a202c;">{pp}</span>'
            f'<span style="font-size:12px;color:#5b6b8c;"> pp</span></td></tr>'
            f'<tr><td colspan="2" style="padding:10px 12px 2px;">'
            f'<p style="{body}font-size:12.5px;color:#5b6b8c;">All 4: <b style="color:#1a202c;">'
            f'{all4.replace("<br>", "</b> · ")}</p>'
            f'<p style="{lab}">Getting there</p><p style="{body}">{there}</p>'
            f'<p style="{lab}">Getting home</p><p style="{body}">{home}</p>'
            f'<p style="{lab}">Worth knowing</p><p style="{body}">{note}</p>'
            f'</td></tr></table>')
    return "".join(out)


# Journey bars: flying / waiting / Singapore stop, hours written inside each
# piece where it fits. Colours checked for colourblind separation; every bar
# also has a written breakdown underneath (in the matching colour), so
# nothing relies on colour alone.
SEG_COLOUR = {"fly": "#1565c0", "wait": "#e0913a", "sg": "#12a37f"}
SEG_TEXT = {"fly": "#1565c0", "wait": "#b8660f", "sg": "#0c8a69"}   # same hues, dark enough to read
SEG_WORD = {"fly": "✈️", "wait": "wait", "sg": "🇸🇬 stop"}
NIGHT = (22, 8)          # 10pm–8am Brisbane time counts as sleep time, for 🛏️


def hm(mins):
    return f"{mins // 60}h{mins % 60:02d}" if mins % 60 else f"{mins // 60}h"


def night_mins(start, mins):
    return sum(5 for i in range(0, mins, 5)
               if not NIGHT[1] <= (start + timedelta(minutes=i)).hour < NIGHT[0])


def segments(leg):
    """(kind, mins, label, start, end, offset_mins) for each part of one leg."""
    t = datetime.strptime(leg[0], "%Y-%m-%d %H:%M")
    off = 0
    for kind, m, label in leg[1]:
        end = t + timedelta(minutes=m)
        yield kind, m, label, t, end, off
        t, off = end, off + m


def overnight(kind, st, m):
    """A layover long enough to sleep through: 4h+ and mostly 10pm–8am."""
    return kind in ("wait", "sg") and m >= 240 and night_mins(st, m) >= m / 2


def journey_block():
    legs = [leg for _, j in RUN["journeys"] for leg in j.values()]
    longest = max(sum(m for _, m, _ in leg[1]) for leg in legs)
    px = 210                               # bar width on a phone, for fitting the hours
    out = []
    for i, (name, j) in enumerate(RUN["journeys"]):
        out.append(f'<p style="margin:{0 if i == 0 else 30}px 0 8px;font-size:14px;font-weight:700;'
                   f'color:#1a202c;">{name}</p>')
        for which, leg in (("There", j["there"]), ("Home", j["home"])):
            segs = list(segments(leg))
            total = sum(s[1] for s in segs)
            cells, detail = [], []
            for kind, m, label, st, en, off in segs:
                w = max(1, round(m / longest * 100, 1))
                bed = " 🛏️" if overnight(kind, st, m) else ""
                txt = hm(m) + bed
                if w / 100 * px < 7 * len(hm(m)) + (18 if bed else 6):
                    txt = hm(m) if w / 100 * px >= 7 * len(hm(m)) + 6 else "&nbsp;"
                cells.append(f'<td align="center" style="width:{w}%;background:{SEG_COLOUR[kind]};height:20px;'
                             f'line-height:20px;font-size:10.5px;font-weight:700;color:#ffffff;white-space:nowrap;'
                             f'overflow:hidden;border-right:2px solid #ffffff;">{txt}</td>')
                detail.append(f'<span style="color:{SEG_TEXT[kind]};">{SEG_WORD[kind]} {hm(m)} {label}{bed}</span>')
            rest = round(100 - total / longest * 100, 1)
            if rest > 0.5:
                cells.append(f'<td style="width:{rest}%;font-size:0;">&nbsp;</td>')
            out.append(
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                f'<td style="width:44px;font-size:13px;font-weight:700;color:#1a202c;padding:0 8px 0 0;'
                f'white-space:nowrap;">{which}</td>'
                f'<td style="padding:0;"><table width="100%" cellpadding="0" cellspacing="0" border="0" '
                f'style="border-radius:4px;overflow:hidden;table-layout:fixed;"><tr>{"".join(cells)}</tr></table></td>'
                f'<td style="width:52px;font-size:12.5px;font-weight:700;color:#1a202c;text-align:right;'
                f'padding:0 0 0 8px;white-space:nowrap;">{hm(total)}</td></tr></table>'
                f'<p style="margin:4px 0 16px 52px;font-size:11.5px;line-height:1.45;color:#5b6b8c;">'
                + ' <span style="color:#8a94a6;">·</span> '.join(detail) + '</p>')
    legend = " &nbsp; ".join(
        f'<span style="display:inline-block;width:10px;height:10px;background:{SEG_COLOUR[k]};'
        f'border-radius:2px;vertical-align:middle;"></span>&nbsp;{t}'
        for k, t in (("fly", "In the air"), ("wait", "Waiting / changing planes"),
                     ("sg", "Singapore stop, can leave the airport")))
    return (f'<p style="margin:0 0 18px;font-size:12px;color:#3d4757;">{legend} &nbsp; 🛏️&nbsp;Overnight stop</p>'
            + "".join(out))


def journey_text():
    L = []
    for name, j in RUN["journeys"]:
        L.append(name)
        for which, leg in (("There", j["there"]), ("Home", j["home"])):
            segs = list(segments(leg))
            total = sum(s[1] for s in segs)
            parts = " | ".join(
                f'{"flying" if k == "fly" else "waiting"} {hm(m)} {label}'
                f'{" (overnight stop)" if overnight(k, st, m) else ""}'
                for k, m, label, st, en, off in segs)
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
        L += [f'{label} - {pp} pp / all 4: {strip(all4.replace("<br>", " · "))}',
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
