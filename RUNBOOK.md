# Daily run — do it in this order

The scheduled routine should follow these steps exactly. Most of the past
breakage came from improvising instead of using the files already in here.

## 1. Get the prices

Kiwi.com connector. Brisbane → Hokkaido and home, Feb 2027, 4 people, one
20 kg checked bag per person each way, all-in AUD, per person.

Record two numbers:

- `best_total_pp` — cheapest sensible combination, whatever the routing
- `fastest_sensible_pp` — quickest routing that isn't silly money

> These two are **not** the same as the three options in the email. The email's
> "Fastest (Qantas)" row is the QF107 Sydney–Sapporo routing, which is usually far
> dearer than `fastest_sensible_pp`. Don't conflate them.

## 2. Check for live airline sales

Jetstar / Qantas / Virgin deal pages. They frequently return **HTTP 403** — if a
page can't be read, report **no verified sale**. Never report a sale found only
via search snippets, and always check the travel window actually covers Feb 2027.

## 3. Log it

Append one row to `prices.csv`:

```
date,best_total_pp,fastest_sensible_pp,verdict
2026-08-05,1527,1859,HOLD
```

Verdict bands (public): 🟢 ≤ $1,000 BUY · 🟡 $1,000–$1,200 WATCH · 🔴 > $1,200 HOLD.

## 4. Rebuild the charts

```bash
python3 make_chart.py     # writes chart.png + chart-email.png
```

Never hand-tune sizes here. The email chart is deliberately 640×360 and
palette-quantised — big enough to read, small enough to serve.

## 5. Render the email

Edit the `RUN` block at the top of `render_email.py`, then:

```bash
python3 render_email.py   # writes email.html + email.txt
```

The delta rows, the price-log bars and the leak check are all computed — don't
hand-write them. In particular **never write "since yesterday"**: the log is not
reliably daily (there was a 9-day gap between 27 Jul and 5 Aug) and the script
labels the comparison with what actually happened.

Do **not** rebuild the HTML from scratch. Rebuilding is why every email used to
look different. If the layout needs changing, change `email-template.html`.

## 6. Commit and push — BEFORE sending

```bash
git add -A && git commit -m "log: YYYY-MM-DD \$NNNN" && git push -u origin <branch>
```

**This step is load-bearing.** The email's chart is a hosted image pointing at
`chart-email.png` on this branch. Send before pushing and the chart 404s in the
inbox.

## 7. Send the email

Resend, one email per run, no correction emails.

- from `onboarding@resend.dev`, to `isaacdique1@gmail.com`
- Resend is in sandbox mode: it will **only** deliver to that address
- body = `email.html`, plain-text part = `email.txt`

## 8. Push notification

This is the only place the **private** buy target may appear. Never in the
email, the report, `prices.csv`, the chart, or any file in this repo.

## 9. Update `latest-report.md`

Full write-up for the record.

---

## Things that have bitten us

| Symptom | Cause | Fix |
|---|---|---|
| Chart missing in Gmail | `data:` URI images are blocked by Gmail | hosted image + `cid:` fallback; never `data:` |
| Chart is yesterday's | Gmail proxy caches by URL | `?v={date}` cache-buster, already in the template |
| Chart 404s | email sent before the push | push first (step 6) |
| Every email looks different | no template; HTML rebuilt each run | `email-template.html` + `render_email.py` |
| Chart illegible | shrunk to 135×78 chasing payload size | quantise, don't shrink |
| "Since yesterday" wrong | hardcoded label on a gappy log | computed in `render_email.py` |
