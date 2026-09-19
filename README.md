# japan-flight-log

Daily flight + itinerary watch for the Brisbane → Hokkaido snow trip, Feb 2027.

- **[CLAUDE.md](CLAUDE.md)** — context for Claude: who it's talking to, house rules
- **[RUNBOOK.md](RUNBOOK.md)** — the daily run, in order. Start here.
- **[SKYSCANNER-MCP.md](SKYSCANNER-MCP.md)** — Skyscanner MCP setup, network requirements, testing and failure handling
- `.mcp.json` — project-scoped Claude Code MCP configuration
- `tools/start_skyscanner_mcp.sh` — launches the pinned local Skyscanner MCP copy
- `prices.csv` — append-only price log
- `make_chart.py` — builds `chart.png` (full) and `chart-email.png` (email copy)
- `email-template.html` — the email layout; edit this, never rebuild HTML per-run
- `render_email.py` — fills the template, writes `email.html` / `email.txt`
- `latest-report.md` — the most recent full write-up

Public buy target: **$1,430 pp**. Bands: 🟢 ≤ $1,430 BUY · 🟡 $1,430–$1,500 WATCH · 🔴 > $1,500 HOLD.
