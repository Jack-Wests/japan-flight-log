#!/usr/bin/env python3
"""Second price source: Google Flights, via SerpApi.

Skyscanner blocks the cloud machine the routine runs on, so this is the
automatic cross-check against Kiwi. Each argument is one flight to check:

    python3 serp_check.py BNE-KIX-2027-02-01 CTS-HND-2027-02-14 NRT-BNE-2027-02-16

It prints Google's cheapest few options for each flight (per person, AUD,
1 adult). Google's prices usually do NOT include a checked bag on budget
airlines (Jetstar, Peach, Scoot, Parata...), so add the bag before comparing
with Kiwi's all-in price.

Needs the SERPAPI_KEY environment variable (set in the Claude cloud
environment settings, never in this public repo). Without it, it says so and
exits cleanly so the rest of the daily run carries on. Every flight costs one
search from the monthly allowance; SERPAPI_MAX_PER_RUN (default 4) caps it,
and it stops early if the account is nearly out of searches.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://serpapi.com/search.json"
ACCOUNT = "https://serpapi.com/account.json"   # free to call, doesn't use a search
KEEP_SPARE = 5                                  # leave a few for a manual re-run


def get(url, params):
    with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=60) as r:
        return json.load(r)


def hhmm(t):
    """'2027-02-16 13:25' -> '1:25pm'."""
    h, m = map(int, t.split(" ")[1].split(":"))
    return f"{(h - 1) % 12 + 1}:{m:02d}{'am' if h < 12 else 'pm'}"


def describe(opt):
    legs = opt["flights"]
    airlines = " + ".join(dict.fromkeys(f["airline"] for f in legs))
    route = " → ".join([legs[0]["departure_airport"]["id"]] + [f["arrival_airport"]["id"] for f in legs])
    dep, arr = legs[0]["departure_airport"]["time"], legs[-1]["arrival_airport"]["time"]
    mins = opt.get("total_duration", 0)
    bags = "; ".join(e for f in legs for e in f.get("extensions", []) if "bag" in e.lower())
    return (f"${opt.get('price', '?')} pp  {airlines}  {route}  "
            f"dep {hhmm(dep)} {dep[5:10]} → arr {hhmm(arr)} {arr[5:10]}  ({mins // 60}h{mins % 60:02d})"
            + (f"  [{bags}]" if bags else ""))


def main(args):
    key = os.environ.get("SERPAPI_KEY", "").strip()
    if not key:
        print("SerpApi: SERPAPI_KEY not set, Google Flights cross-check skipped.")
        return
    if not args:
        sys.exit(__doc__)
    cap = int(os.environ.get("SERPAPI_MAX_PER_RUN", "4"))

    try:
        left = get(ACCOUNT, {"api_key": key}).get("total_searches_left")
    except Exception as e:                      # account check is a nicety, not a blocker
        left = None
        print(f"SerpApi: couldn't read the account balance ({e}); carrying on.")
    if left is not None:
        print(f"SerpApi: {left} searches left this month.")
        cap = min(cap, max(0, left - KEEP_SPARE))

    if len(args) > cap:
        print(f"SerpApi: only checking the first {cap} of {len(args)} flights (monthly allowance).")
    for spec in args[:cap]:
        frm, to, date = spec.split("-", 2)
        try:
            data = get(API, {"engine": "google_flights", "departure_id": frm, "arrival_id": to,
                             "outbound_date": date, "type": 2, "adults": 1, "currency": "AUD",
                             "hl": "en", "gl": "au", "api_key": key})
        except Exception as e:
            print(f"\n{frm}→{to} {date}: request failed ({e})")
            continue
        if data.get("error"):
            print(f"\n{frm}→{to} {date}: {data['error']}")
            continue
        opts = sorted(data.get("best_flights", []) + data.get("other_flights", []),
                      key=lambda o: o.get("price", 1e9))
        print(f"\n{frm}→{to} {date}: {len(opts)} options on Google Flights")
        for o in opts[:5]:
            print("  " + describe(o))


if __name__ == "__main__":
    main(sys.argv[1:])
