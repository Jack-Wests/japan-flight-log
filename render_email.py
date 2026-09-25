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
    "date_human": "Fri 25 Sep 2026",
    "verdict_headline": "🟡 WATCH — normal range, a dip might come",
    "best_pp": "$1,589",
    "best_all4": "$6,356",
    "target_distance": "$89 above",
    "snapshot": [
        "The cheapest comfortable way to get you to the Hokkaido snow and home again is "
        "<b>$1,589 per person. That's $6,356 for all four, or $4,767 for three</b> if Hugh buys "
        "separately. You'd fly Singapore Airlines to Osaka (with a day stop in Osaka and a short ferry to "
        "Kobe airport) and hop up to Sapporo. After the ski you hop back to Tokyo, then fly "
        "<b>Singapore Airlines home from Tokyo</b> on Tue 16 Feb.",
        "That's <b>WATCH</b>: $13 down on yesterday's $1,602 and <b>$89 above the $1,500 buy price</b>. "
        "The main change is the flight home. Singapore Airlines from Narita is now $777, $10 less than "
        "Air Niugini, when on 23 Sep it was $55 more. "
        "Compared with a week ago (18 Sep, $1,427) it's up $162. But the 18 Sep figure was logged before we "
        "started leaving out forced overnights, so it isn't a like-for-like comparison.",
        "If you'd put up with a forced overnight in Port Moresby on the way over, it's ~$1,477 "
        "before the hotel, but ~$1,677 once you add it. Not recommended.",
        "⏳ About 4 months (130 days) until departure. <b>Under 3 weeks to the mid-October "
        "deadline.</b> After that, book the first comfortable day under $1,600, and today's "
        "$1,589 would already qualify. No airline sale is live: Qantas's Asia sale ended on 21 Sep and "
        "Scoot's on 20 Sep.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 7:15pm "
         "<i>(Singapore Airlines via Singapore to Osaka (KIX), ferry to Kobe (UKB), Skymark to Sapporo)</i>",
         "🛫 Sapporo (CTS) Sun 14 Feb 8:00am → Tokyo (HND) 9:35am, then Dep Tokyo (NRT) Tue 16 Feb "
         "6:50pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 4:55pm <i>(Singapore Airlines via Singapore)</i>",
         "$1,589", "$6,356<br><span style=\"color:#8a94a6;\">3 of you: $4,767</span>",
         "~26h over (9h daytime stop in Osaka with bags and a 30-min ferry, ~$19 included) · 21h home, "
         "with a 1:20–7:05am wait in Singapore (too short to leave the airport)"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:30pm "
         "<i>(Singapore Airlines via Singapore to Osaka (KIX), Peach to Sapporo from the same airport)</i>",
         "🛫 Sapporo (CTS) Sun 14 Feb 8:00am → Tokyo (HND) 9:35am, then Dep Tokyo (NRT) Wed 17 Feb "
         "9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am <i>(Air Niugini via Port Moresby, 1h change)</i>",
         "$1,609", "$6,436<br><span style=\"color:#8a94a6;\">3 of you: $4,827</span>",
         "$20pp more. No ferry, into Sapporo 5 hours earlier, home in 11h instead of 21h, and an extra Tokyo day"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am (Mon night) → 🛬 lands Sapporo (CTS) Tue 2 Feb "
         "2:50pm <i>(Cathay Pacific via Hong Kong)</i>",
         "Same as Best value: Sapporo → Tokyo Sun 14 Feb, Air Niugini home from Tokyo (NRT) Wed 17 Feb "
         "9:40pm → lands Brisbane Thu 18 Feb 9:40am",
         "$1,737", "$6,948<br><span style=\"color:#8a94a6;\">3 of you: $5,211</span>",
         "15h over with one short Hong Kong change. $148pp more than the cheapest"),
    ],
    "options_footnote":
        "Prices are per person, all-in, with a 20kg checked bag each way and the $113 Sapporo→Tokyo hop "
        "(Air Do, 8:00am Sun 14 Feb). <b>Singapore overnight option:</b> leave Tue 2 Feb 6:10pm, spend 12:05–8:25am "
        "in Singapore (Isaac sees his partner, free stay), land Sapporo Wed 3 Feb 7:40pm. That comes to $1,650pp "
        "with the Singapore Airlines flight home, which is $61 more than the cheapest. That's just over the "
        "~$50 we'd pay extra for a Singapore stop, so it doesn't get its own row. "
        "<b>Cheapest if you'd overnight in Port Moresby:</b> ~$1,477pp (Air Niugini to Tokyo and back, plus both "
        "Hokkaido hops). Not recommended: it's ~$1,677 once you add a hotel and transfers. "
        "<b>Qantas QF107 Sydney–Sapporo direct:</b> $1,776pp one way including the Brisbane–Sydney flight. "
        "That's just to get there, so it's not a live pick. <b>Brisbane ⇄ Tokyo return plus the Hokkaido hops</b> "
        "(Jetstar direct over, Singapore Airlines home) comes to ~$1,723pp, dearer than flying into Sapporo. "
        "No date shift saved $100+pp.",
    # Door-to-door timeline per table row, drawn as bars in the email.
    # Each leg is (departure in Brisbane time/AEST "YYYY-MM-DD HH:MM", segments);
    # each segment is (kind, minutes, label). kind: "fly" = in the air,
    # "wait" = stopover/transfer, "sg" = Singapore stop long enough to leave the
    # airport (free stay with Isaac's partner). Minutes must add up to the
    # door-to-door time quoted in the table; clock times are worked out from them.
    "journeys": [
        ("Cheapest", {
            "there": ("2027-02-01 18:10", [
                ("fly", 475, "Brisbane → Singapore"), ("wait", 85, "Singapore"),
                ("fly", 365, "Singapore → Osaka"),
                ("wait", 530, "Osaka, ferry to Kobe airport"),
                ("fly", 110, "Kobe → Sapporo")]),
            "home": ("2027-02-16 19:50", [
                ("fly", 450, "Tokyo → Singapore"), ("wait", 345, "Singapore"),
                ("fly", 470, "Singapore → Brisbane")]),
        }),
        ("Best value", {
            "there": ("2027-02-01 18:10", [
                ("fly", 475, "Brisbane → Singapore"), ("wait", 85, "Singapore"),
                ("fly", 365, "Singapore → Osaka"), ("wait", 240, "Osaka"),
                ("fly", 115, "Osaka → Sapporo")]),
            "home": ("2027-02-17 22:40", [
                ("fly", 410, "Tokyo → Port Moresby"), ("wait", 60, "Port Moresby"),
                ("fly", 190, "Port Moresby → Brisbane")]),
        }),
        ("Fastest sensible", {
            "there": ("2027-02-02 00:50", [
                ("fly", 510, "Brisbane → Hong Kong"), ("wait", 110, "Hong Kong"),
                ("fly", 280, "Hong Kong → Sapporo")]),
            "home": ("2027-02-17 22:40", [
                ("fly", 410, "Tokyo → Port Moresby"), ("wait", 60, "Port Moresby"),
                ("fly", 190, "Port Moresby → Brisbane")]),
        }),
    ],
    "itin_title": "Option A — Cheapest (Furano base)",
    "itin_subtitle": "14 nights on the ground · hire car picked up &amp; dropped at Sapporo (CTS)",
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
        ("Sun 14 Feb", "Sapporo → Tokyo", "Drop the car at Sapporo (CTS), fly 8:00am, land Haneda 9:35am; Shibuya"),
        ("Mon 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab"),
        ("Tue 16 Feb", "Tokyo → Singapore", "Shinjuku/Harajuku morning, fly out of Narita 6:50pm"),
        ("Wed 17 Feb", "→ Brisbane", "Wait in Singapore 1:20–7:05am (airside), land Brisbane 4:55pm"),
    ],
    "itin_footnote":
        "<b>Best value</b> leaves at the same time but skips the ferry: you land in Sapporo at 2:30pm Tue 2 Feb. "
        "You also get an extra Tokyo day (Wed 17 Feb) and fly Air Niugini home that night at 9:40pm, "
        "landing in Brisbane 9:40am Thu 18 Feb. "
        "<b>Fastest sensible</b> leaves just after midnight Mon night and lands in Sapporo at 2:50pm Tue 2 Feb. "
        "The way home is the same as Best value.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 65. Since 23 Sep the line tracks the "
        "cheapest <i>comfortable</i> price (no hidden forced overnights). Earlier days logged the "
        "cheapest price with any routing. Comfortable range so far: $1,333–$1,709.",
    "footer":
        "Daily flight watch · prices from Kiwi.com (Skyscanner cross-check failed today), AUD "
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


# Journey bars: one row per part of the trip (Gantt style), so each piece of
# text sits directly under its own bar. Times are Brisbane time (AEST) so you
# can see which bits fall in the middle of the night. Colours checked for
# colourblind separation; every row is labelled, so nothing relies on colour.
SEG_COLOUR = {"fly": "#1565c0", "wait": "#e0913a", "sg": "#12a37f"}
SEG_WORD = {"fly": "✈️", "wait": "⏳", "sg": "🇸🇬"}
NIGHT = (22, 6)          # 10pm–6am Brisbane time counts as sleep time


def hm(mins):
    return f"{mins // 60}h{mins % 60:02d}" if mins % 60 else f"{mins // 60}h"


def clock(dt):
    return dt.strftime("%-I:%M%p").lower().replace(":00", "")


def when(dt, prev=None):
    """'Mon 1 Feb 6:10pm', or just '2:05am' when it's the same day as prev."""
    if prev is not None and prev.date() == dt.date():
        return clock(dt)
    return f'{dt.strftime("%a %-d %b")} {clock(dt)}'


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


def journey_block():
    legs = [leg for _, j in RUN["journeys"] for leg in j.values()]
    longest = max(sum(m for _, m, _ in leg[1]) for leg in legs)
    track = "background:#f1f3f6;font-size:0;"
    out = []
    for name, j in RUN["journeys"]:
        out.append(f'<p style="margin:20px 0 2px;font-size:14px;font-weight:700;color:#1a202c;">{name}</p>')
        for which, leg in (("Getting there", j["there"]), ("Getting home", j["home"])):
            segs = list(segments(leg))
            total = sum(s[1] for s in segs)
            out.append(
                f'<p style="margin:16px 0 2px;font-size:12.5px;color:#3d4757;"><b>{which} · {hm(total)}</b>'
                f' <span style="color:#8a94a6;">· {when(segs[0][3])} → {when(segs[-1][4])}</span></p>')
            for kind, m, label, st, en, off in segs:
                lead = round(off / longest * 100, 1)
                w = max(1.5, round(m / longest * 100, 1))
                tail = round(100 - lead - w, 1)
                cells = (f'<td style="width:{lead}%;{track}">&nbsp;</td>' if lead > 0 else "")
                cells += (f'<td style="width:{w}%;background:{SEG_COLOUR[kind]};height:12px;'
                          f'line-height:12px;font-size:0;border-radius:3px;">&nbsp;</td>')
                cells += (f'<td style="width:{tail}%;{track}">&nbsp;</td>' if tail > 0 else "")
                moon = " · 🌙" if night_mins(st, m) >= 60 else ""
                out.append(
                    f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
                    f'style="margin:11px 0 0;border-radius:3px;"><tr>{cells}</tr></table>'
                    f'<p style="margin:2px 0 0;font-size:12px;color:#3d4757;line-height:1.4;">'
                    f'{SEG_WORD[kind]} <b>{label}</b> · {hm(m)}'
                    f' <span style="color:#5b6b8c;">· {when(st)} → {when(en, st)}{moon}</span></p>')
    legend = " &nbsp; ".join(
        f'<span style="display:inline-block;width:10px;height:10px;background:{SEG_COLOUR[k]};'
        f'border-radius:2px;vertical-align:middle;"></span>&nbsp;{t}'
        for k, t in (("fly", "In the air"), ("wait", "Waiting / changing planes"),
                     ("sg", "Singapore stop, can leave the airport")))
    return (f'<p style="margin:0 0 4px;font-size:12px;color:#3d4757;">{legend}</p>'
            f'<p style="margin:0;font-size:12px;color:#5b6b8c;">All times are <b>Brisbane time (AEST)</b>. '
            f'🌙 = at least an hour of it falls between 10pm and 6am Brisbane time.</p>'
            + "".join(out))


def journey_text():
    L = ["All times Brisbane time (AEST). (night) = at least an hour between 10pm and 6am."]
    for name, j in RUN["journeys"]:
        L.append(name)
        for which, leg in (("There", j["there"]), ("Home", j["home"])):
            segs = list(segments(leg))
            total = sum(s[1] for s in segs)
            L.append(f"  {which} {hm(total)}: {when(segs[0][3])} -> {when(segs[-1][4])}")
            for kind, m, label, st, en, _ in segs:
                word = {"fly": "flying", "wait": "waiting", "sg": "Singapore stop"}[kind]
                night = " (night)" if night_mins(st, m) >= 60 else ""
                L.append(f"    {word} {hm(m)} {label}: {when(st)} -> {when(en, st)}{night}")
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
