#!/usr/bin/env python3
"""Every search a daily run must do, and a log proving it did them.

Added 29 Sep 2026 after a run skipped several required searches (Brisbane ⇄
Tokyo return, date shifts, Gold Coast/Cairns, via-China) and missed a cheaper
fare as a result. render_email.py refuses to build the email until every item
below has a row in search-log.csv for today's date, so a skipped search stops
the run instead of slipping through.

    python3 search_checklist.py                 # today's checklist: done / missing
    python3 search_checklist.py log ID STATUS "what it found"

STATUS is one of:
  done     searched; the result says what came back (cheapest price, or "nothing")
  blocked  the source refused (e.g. Skyscanner BannedWithCaptcha) after one retry
  failed   the tool errored after one retry

"blocked"/"failed" still count as done — the point is that every search was
attempted and its outcome written down, never silently skipped.
"""
import csv
import os
import sys
from datetime import date

LOG = "search-log.csv"
HEADER = ["date", "id", "status", "result"]
STATUSES = {"done", "blocked", "failed"}

# (id, what to search). Dates are Feb 2027 unless stated. Kiwi searches are for
# 4 adults with 1 checked bag each (adults_hold_bags=[1,1,1,1]), currency AUD.
REQUIRED = [
    # A) Kiwi — fly into Sapporo, home from Tokyo
    ("kiwi-bne-cts", "Kiwi: Brisbane → Sapporo (CTS), any routing, leaving 1–4 Feb"),
    ("kiwi-bne-kix", "Kiwi: Brisbane → Osaka (KIX), leaving 1–3 Feb (for Osaka → Sapporo combos)"),
    ("kiwi-tyo-bne", "Kiwi: Tokyo (NRT/HND) → Brisbane, leaving 14–18 Feb"),
    ("kiwi-qf107", "Kiwi: Qantas Sydney → Sapporo (QF107), 1–4 Feb (select_airlines=QF)"),
    # A) Kiwi — Brisbane ⇄ Tokyo + Hokkaido flights
    ("kiwi-bne-tyo-return", "Kiwi: Brisbane ⇄ Tokyo return, out 1–3 Feb, back 14–18 Feb"),
    ("kiwi-tyo-cts", "Kiwi: Tokyo → Sapporo, 2 Feb evening to 5 Feb"),
    ("kiwi-cts-tyo", "Kiwi: Sapporo → Tokyo, 13–14 Feb"),
    # A) date shifts (±3 days, only reported if they save $100+pp)
    ("kiwi-shift-out", "Kiwi: Brisbane → Sapporo leaving 29–31 Jan"),
    ("kiwi-shift-home", "Kiwi: Tokyo → Brisbane leaving 19–21 Feb"),
    # A) carriers and origins the prompt names
    ("kiwi-singapore", "Kiwi: Singapore Airlines + Scoot via Singapore, both directions (select_airlines=SQ,TR)"),
    ("kiwi-china", "Kiwi: China Southern / China Eastern, both directions (select_airlines=CZ,MU)"),
    ("kiwi-cns-ool", "Kiwi: Cairns and Gold Coast → Japan, leaving 1–3 Feb"),
    # A2) Skyscanner cross-check (4 adults) — retry each once; 'blocked' if captcha
    ("sky-bne-cts", "Skyscanner: Brisbane → Sapporo"),
    ("sky-nrt-bne", "Skyscanner: Tokyo Narita → Brisbane"),
    ("sky-hnd-bne", "Skyscanner: Tokyo Haneda → Brisbane"),
    ("sky-bne-nrt-return", "Skyscanner: Brisbane ⇄ Narita return"),
    ("sky-bne-hnd-return", "Skyscanner: Brisbane ⇄ Haneda return"),
    ("sky-tyo-cts", "Skyscanner: Tokyo → Sapporo"),
    ("sky-cts-tyo", "Skyscanner: Sapporo → Tokyo"),
    # 1b) Google Flights via SerpApi
    ("serpapi", "Google Flights (serp_check.py) on the cheapest option's flights"),
    # B) budget carrier web searches
    ("web-jetstar", "Web: Jetstar Brisbane/Cairns/Gold Coast → Tokyo, Feb 2027"),
    ("web-scoot", "Web: Scoot Brisbane → Tokyo, Feb 2027"),
    ("web-airasia", "Web: AirAsia Brisbane → Tokyo, Feb 2027"),
    ("web-china-southern", "Web: China Southern Brisbane → Japan, Feb 2027"),
    # Sale check
    ("sale-ozb-jetstar", "Web: OzBargain Jetstar Japan"),
    ("sale-ozb-qantas", "Web: OzBargain Qantas Japan"),
    ("sale-ozb-general", "Web: OzBargain flight sale Japan"),
    ("sale-jetstar", "Web: Jetstar sale"),
    ("sale-qantas", "Web: Qantas sale Japan"),
]
IDS = [i for i, _ in REQUIRED]


def rows_for(day):
    if not os.path.exists(LOG):
        return {}
    out = {}
    for r in csv.DictReader(open(LOG)):
        if r["date"] == day and r["status"] in STATUSES and len(r["result"].strip()) >= 8:
            out[r["id"]] = r
    return out


def missing(day):
    """Required search ids with no proper log row for `day`."""
    have = rows_for(day)
    return [i for i in IDS if i not in have]


def require(day):
    """Stop the run if any required search has no log row for `day`."""
    gone = missing(day)
    if gone:
        desc = dict(REQUIRED)
        lines = "\n".join(f"  - {i}: {desc[i]}" for i in gone)
        raise SystemExit(
            f"STOP: {len(gone)} required search(es) not logged for {day}.\n{lines}\n"
            f"Do each search, then: python3 search_checklist.py log ID STATUS \"what it found\"")


def log(id_, status, result, day=None):
    if id_ not in IDS:
        raise SystemExit(f"unknown search id {id_!r}; see REQUIRED in search_checklist.py")
    if status not in STATUSES:
        raise SystemExit(f"status must be one of {sorted(STATUSES)}")
    if len(result.strip()) < 8:
        raise SystemExit("say what the search found (price, or why it was blocked)")
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(HEADER)
        w.writerow([day or date.today().isoformat(), id_, status, result.strip()])


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "log":
        log(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
    else:
        day = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
        have = rows_for(day)
        for i, d in REQUIRED:
            mark = f"[{have[i]['status']}]" if i in have else "[MISSING]"
            print(f"{mark:<10} {i:<20} {d}")
        print(f"\n{len(IDS) - len(missing(day))}/{len(IDS)} logged for {day}")
