# japan-flight-log

Daily flight + itinerary watch for the Brisbane → Hokkaido snow trip, Feb 2027.

- **[CLAUDE.md](CLAUDE.md)** — context for Claude: who it's talking to, house rules
- **[RUNBOOK.md](RUNBOOK.md)** — the daily run, in order. Start here.
- `prices.csv` — append-only price log
- `make_chart.py` — builds `chart.png` (full) and `chart-email.png` (email copy)
- `email-template.html` — the email layout; edit this, never rebuild HTML per-run
- `render_email.py` — fills the template, writes `email.html` / `email.txt`
- `latest-report.md` — the most recent full write-up

Public buy target: **$1,000 pp**. Bands: 🟢 ≤ $1,000 BUY · 🟡 $1,000–$1,200 WATCH · 🔴 > $1,200 HOLD.
