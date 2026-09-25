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
    "date_human": "Fri 25 Sep 2026 (late re-check)",
    "verdict_headline": "🟡 WATCH — normal range, a dip might come",
    "best_pp": "$1,589",
    "best_all4": "$6,356",
    "target_distance": "$89 above",
    "snapshot": [
        "<b>First, a correction to how I've been counting.</b> Until now the daily price was the fare for "
        "<i>one</i> seat. Tonight I priced the same flights for <b>four seats booked together</b>, and "
        "it costs more: the cheapest seats on some flights run out before you get to four. "
        "One seat would be $1,509 today. Four seats together work out to <b>$1,589 each</b>. "
        "From today the log uses the four-seat price, since that's what you'd actually pay. "
        "The older numbers on the chart were one-seat prices, so they probably looked a bit cheaper "
        "than the real group price.",
        "So the cheapest comfortable trip is <b>$1,589 per person: $6,356 for all four, or $4,767 "
        "for three</b> if Hugh buys separately. You'd fly Singapore Airlines to Osaka, take a 30-minute ferry to "
        "Kobe and fly Skymark up to Sapporo, then hop back to Tokyo after the ski and fly Singapore "
        "Airlines home from Tokyo on one ticket. This evening's cheapest flight home, through Seoul, has gone.",
        "That's <b>WATCH</b>, <b>$89 above the $1,500 buy price</b>. It's $13 under yesterday's "
        "$1,602, though yesterday was counted for one seat. On the same one-seat basis today "
        "is $40 cheaper than this evening's check.",
        "⏳ About 4 months (130 days) until departure. <b>About 3 weeks to the mid-October "
        "deadline</b>. After that, book the first comfortable day under $1,600. Today's $1,589 "
        "would just qualify. No airline sale is live.",
    ],
    "options": [
        # (label, getting there, getting home, pp, all4, worth knowing)
        ("Cheapest",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 7:15pm "
         "<i>(Singapore Airlines via Singapore to Osaka (KIX), ferry to Kobe (UKB), Skymark to Sapporo)</i>",
         "🛫 Sapporo (CTS) Sun 14 Feb 8:00am → Tokyo (HND) 9:35am <i>(Air Do)</i>, then Dep Tokyo (NRT) "
         "Tue 16 Feb 6:50pm → 🛬 lands Brisbane (BNE) Wed 17 Feb 4:55pm <i>(Singapore Airlines via "
         "Singapore, one ticket)</i>",
         "$1,589", "$6,356<br><span style=\"color:#8a94a6;\">3 of you: $4,767</span>",
         "~26h over (9h daytime stop in Osaka, 30-min ferry ~$19 included) · 21h home, with a "
         "1:20–7:05am wait inside Singapore airport (too short to go into town)"),
        ("Best value",
         "🛫 Dep Brisbane (BNE) Mon 1 Feb 6:10pm → 🛬 lands Sapporo (CTS) Tue 2 Feb 2:30pm "
         "<i>(Singapore Airlines via Singapore to Osaka (KIX), Peach to Sapporo)</i>",
         "Same as Cheapest: Sapporo → Tokyo Sun 14 Feb, then Tokyo (NRT) Tue 16 Feb 6:50pm → "
         "lands Brisbane Wed 17 Feb 4:55pm via Singapore",
         "$1,606", "$6,424<br><span style=\"color:#8a94a6;\">3 of you: $4,818</span>",
         "$17pp more, no ferry: in Sapporo nearly 5 hours sooner (21h over)"),
        ("Fastest sensible",
         "🛫 Dep Brisbane (BNE) Tue 2 Feb 12:50am (Mon night) → 🛬 lands Sapporo (CTS) Tue 2 Feb "
         "2:50pm <i>(Cathay Pacific via Hong Kong)</i>",
         "🛫 Sapporo (CTS) Sun 14 Feb 8:00am → Tokyo (HND) 9:35am, then Dep Tokyo (NRT) Wed 17 Feb "
         "9:40pm → 🛬 lands Brisbane (BNE) Thu 18 Feb 9:40am <i>(Air Niugini via Port Moresby, 1h change)</i>",
         "$1,751", "$7,004<br><span style=\"color:#8a94a6;\">3 of you: $5,253</span>",
         "15h over, one short Hong Kong change · 11h home, one ticket. $162pp more than the cheapest"),
    ],
    # Each flight in each option, for the "check it yourself" links:
    # (from, to, "YYYY-MM-DD"), one per separate flight/ticket, in order.
    "check_links": {
        "Cheapest": [("BNE", "KIX", "2027-02-01"), ("UKB", "CTS", "2027-02-02"),
                     ("CTS", "HND", "2027-02-14"), ("NRT", "BNE", "2027-02-16")],
        "Best value": [("BNE", "KIX", "2027-02-01"), ("KIX", "CTS", "2027-02-02"),
                       ("CTS", "HND", "2027-02-14"), ("NRT", "BNE", "2027-02-16")],
        "Fastest sensible": [("BNE", "CTS", "2027-02-02"), ("CTS", "HND", "2027-02-14"),
                             ("NRT", "BNE", "2027-02-17")],
    },
    "options_footnote":
        "Prices are per person for <b>four seats booked together</b>, all-in, with a 20kg checked bag each "
        "way and the $125 Air Do Sapporo→Tokyo hop on 14 Feb. (The links below show one-seat prices, "
        "which can be a little lower.) <b>Singapore overnight on the way over:</b> none for four seats "
        "on 1–2 Feb today. "
        "<b>Cheapest if you'd overnight in Port Moresby:</b> $1,476pp (Air Niugini return to Tokyo, a "
        "night in Port Moresby on the way over, then a night in Tokyo before flying to Sapporo on 4 Feb). "
        "Not recommended: the real cost is ~$1,665 after two hotels and airport transfers. "
        "<b>Qantas QF107 Sydney–Sapporo direct:</b> $1,737pp one way from Sydney, before the "
        "Brisbane–Sydney flight. That's just to get there. <b>Brisbane ⇄ Tokyo return</b> (China Airlines "
        "via Taipei, $1,421pp for four) plus both Hokkaido hops is ~$1,660pp plus a night in Tokyo. "
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
            "home": ("2027-02-16 19:50", [
                ("fly", 450, "Tokyo → Singapore"), ("wait", 345, "Singapore"),
                ("fly", 470, "Singapore → Brisbane")]),
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
        ("Mon 15 Feb", "Tokyo", "Asakusa, Akihabara, teamLab, Shinjuku at night"),
        ("Tue 16 Feb", "Tokyo → Singapore", "Harajuku and a last lunch, fly out of Narita 6:50pm; change planes in Singapore overnight"),
        ("Wed 17 Feb", "→ Brisbane", "Leave Singapore 7:05am, land Brisbane 4:55pm"),
    ],
    "itin_footnote":
        "<b>Best value</b> is the same trip, but you skip the ferry and fly Osaka→Sapporo at 12:35pm, "
        "landing 2:30pm Tue 2 Feb. "
        "<b>Fastest sensible</b> leaves just after midnight Mon night and lands in Sapporo at 2:50pm Tue 2 Feb. "
        "It gets an extra Tokyo day and flies home from Narita at 9:40pm Wed 17 Feb, landing Brisbane "
        "9:40am Thu 18 Feb.",
    "price_log_footnote":
        "Showing the last 10 checks; the chart above has all 65. Since 23 Sep the line tracks the "
        "cheapest <i>comfortable</i> price (no hidden forced overnights). Earlier days logged the "
        "cheapest price with any routing. Up to this evening every day was a one-seat price. From "
        "25 Sep (late check) it's the price for four seats booked together. "
        "Comfortable range so far: $1,333–$1,709.",
    "footer":
        "Daily flight watch · prices from Kiwi.com for 4 seats (Skyscanner blocked us; Google Flights "
        "check not working), AUD incl. 1 checked bag each way · no verified sale live today.",
}
# ─────────────────────────────────────────────────────────────────────────────

TH_TD = "padding:9px 10px;font-size:12.5px;color:#3d4757;line-height:1.5;border-bottom:1px solid #eef0f3;vertical-align:top;"


# Airport codes → names for the check links. Add any new airport here.
AIRPORT = {"BNE": "Brisbane", "OOL": "Gold Coast", "CNS": "Cairns", "SYD": "Sydney",
           "MEL": "Melbourne", "CTS": "Sapporo", "NRT": "Tokyo Narita", "HND": "Tokyo Haneda",
           "KIX": "Osaka Kansai", "ITM": "Osaka Itami", "UKB": "Kobe", "SIN": "Singapore",
           "HKG": "Hong Kong", "TPE": "Taipei", "ICN": "Seoul", "POM": "Port Moresby",
           "MNL": "Manila", "KUL": "Kuala Lumpur", "CAN": "Guangzhou", "PVG": "Shanghai"}


def sky_url(frm, to, date, adults=1):
    """Skyscanner results page for one flight on one day, 1 adult so the prices
    line up with the email's per-person figures."""
    d = datetime.strptime(date, "%Y-%m-%d").strftime("%y%m%d")
    return (f"https://www.skyscanner.com.au/transport/flights/{frm.lower()}/{to.lower()}/{d}/"
            f"?adultsv2={adults}&cabinclass=economy&rtn=0&preferdirects=false")


def gf_url(frm, to, date):
    """Google Flights results for the same flight, in AUD."""
    q = f"Flights from {frm} to {to} on {date} one way economy"
    return "https://www.google.com/travel/flights?hl=en-AU&curr=AUD&q=" + q.replace(" ", "%20")


def flight_name(frm, to, date):
    if frm not in AIRPORT or to not in AIRPORT:
        raise SystemExit(f"check_links: add {frm if frm not in AIRPORT else to} to AIRPORT")
    day = datetime.strptime(date, "%Y-%m-%d")
    return f"{AIRPORT[frm]} → {AIRPORT[to]}, {day.strftime('%a')} {day.day} {day.strftime('%b')}"


def check_links_html(label):
    rows = []
    a = "color:#1565c0;font-weight:600;text-decoration:underline;"
    for frm, to, date in RUN.get("check_links", {}).get(label, []):
        rows.append(f'<p style="margin:0 0 6px;font-size:12.5px;color:#3d4757;line-height:1.5;">'
                    f'{flight_name(frm, to, date)}<br>'
                    f'<a href="{sky_url(frm, to, date)}" style="{a}">Skyscanner</a>'
                    f' &nbsp;·&nbsp; <a href="{gf_url(frm, to, date)}" style="{a}">Google Flights</a></p>')
    return "".join(rows)


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
            + (f'<p style="{lab}">Check each flight yourself</p>{check_links_html(label)}'
               f'<div style="height:6px;line-height:6px;font-size:0;">&nbsp;</div>'
               if RUN.get("check_links", {}).get(label) else "")
            + f'</td></tr></table>')
    return "".join(out)


# Journey bars: flying / waiting / Singapore stop, hours written inside each
# piece where it fits. Colours checked for colourblind separation; every bar
# also has a written breakdown underneath (in the matching colour), so
# nothing relies on colour alone.
SEG_COLOUR = {"fly": "#1565c0", "wait": "#e0913a", "sg": "#12a37f"}
SEG_TEXT = {"fly": "#1565c0", "wait": "#b8660f", "sg": "#0c8a69"}   # same hues, dark enough to read
SEG_WORD = {"fly": "✈️", "wait": "wait", "sg": "🇸🇬 stop"}
NIGHT = (22, 8)          # 10pm–8am Brisbane time counts as sleep time, for 🛏️


# Hours ahead of Brisbane (AEST) in February, for printing each piece's local
# start time. Each journey label starts with the place the piece starts from.
PLACE_TZ = {"Brisbane": 0, "Cairns": 0, "Gold Coast": 0, "Sydney": 1, "Melbourne": 1,
            "Port Moresby": 0, "Singapore": -2, "Kuala Lumpur": -2, "Hong Kong": -2,
            "Taipei": -2, "Manila": -2, "Guangzhou": -2, "Shanghai": -2, "Denpasar": -2,
            "Bangkok": -3, "Seoul": -1, "Tokyo": -1, "Osaka": -1, "Kobe": -1, "Sapporo": -1}


def local_clock(label, t):
    """Local time where this piece starts, e.g. '12:05am' for a Singapore wait."""
    place = next((p for p in sorted(PLACE_TZ, key=len, reverse=True) if label.startswith(p)), None)
    if place is None:
        raise SystemExit(f"journey label {label!r} doesn't start with a place in PLACE_TZ — add it")
    lt = t + timedelta(hours=PLACE_TZ[place])
    return lt.strftime("%I:%M%p").lstrip("0").lower()


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


def min_w(mins, px=210):
    """Narrowest % of the bar that still fits this piece's hours at 9px."""
    return (5.4 * len(hm(mins)) + 5) / px * 100


def leg_end_place(segs):
    """The place a leg lands, from its last flight's label ('Kobe → Sapporo')."""
    return segs[-1][2].split("→")[-1].strip()


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
            leg_w = total / longest * 100
            # Every piece is labelled, so short pieces get a minimum width that
            # fits their hours at the small font; the long pieces give it up.
            need = [min_w(s[1]) for s in segs]
            nat = [s[1] / total * leg_w for s in segs]
            bumped = [max(n, q) for n, q in zip(nat, need)]
            spare = sum(n for n, q in zip(nat, need) if n > q)
            squeeze = (leg_w - sum(q for n, q in zip(nat, need) if n <= q)) / spare if spare else 1
            widths = [q if n <= q else n * squeeze for n, q in zip(nat, need)]
            for (kind, m, label, st, en, off), w in zip(segs, widths):
                w = round(w, 1)
                bed = " 🛏️" if overnight(kind, st, m) else ""
                txt = hm(m) + (bed if w / 100 * px >= 7 * len(hm(m)) + 18 else "")
                fs = "10.5px" if w / 100 * px >= 6.2 * len(hm(m)) + 6 else "9px"
                cells.append(f'<td align="center" style="width:{w}%;background:{SEG_COLOUR[kind]};height:20px;'
                             f'line-height:20px;font-size:{fs};font-weight:700;color:#ffffff;white-space:nowrap;'
                             f'overflow:hidden;letter-spacing:-0.2px;border-right:2px solid #ffffff;">{txt}</td>')
                detail.append(f'<span style="color:{SEG_TEXT[kind]};"><b>{local_clock(label, st)}</b> '
                              f'{SEG_WORD[kind]} {hm(m)} {label}{bed}</span>')
            last = segs[-1]
            detail.append(f'<span style="color:#1a202c;">lands <b>{local_clock(leg_end_place(segs), last[4])}</b></span>')
            rest = round(100 - leg_w, 1)
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
                f'{local_clock(label, st)} {"flying" if k == "fly" else "waiting"} {hm(m)} {label}'
                f'{" (overnight stop)" if overnight(k, st, m) else ""}'
                for k, m, label, st, en, off in segs) + f" | lands {local_clock(leg_end_place(segs), segs[-1][4])}"
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
              f'  {note}']
        for frm, to, date in RUN.get("check_links", {}).get(label, []):
            L += [f'  Check {flight_name(frm, to, date)}:',
                  f'    Skyscanner: {sky_url(frm, to, date)}',
                  f'    Google Flights: {gf_url(frm, to, date)}']
        L += [""]
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
