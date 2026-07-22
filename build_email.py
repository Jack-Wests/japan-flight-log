#!/usr/bin/env python3
"""Fill email-template.html placeholders -> email-final.html. No restructuring."""

DATE_LONG = "22 Jul 2026"
VERDICT_EMOJI = "🔴"
VERDICT_WORD = "HOLD"
BEST_PP = "1,364"
BEST_ALL4 = "5,456"

# Quiet day (HOLD) -> calm green header, no action banner.
ACTION_BANNER = ""
HEADER_BG = "#2e7d32"

SNAPSHOT = (
    "The cheapest all-in way to get all four lads to the Hokkaido snow and home again is "
    "<strong>$1,364 per person (about $5,456 for the four of you)</strong> — still above our "
    "$1,000 buy target, and up only ~$17pp since the last check on 20 Jul, so basically flat. "
    "No verified sale is running today (the Jetstar, Qantas and Virgin sale pages all blocked us "
    "again), so there's nothing to jump on. Sit tight — two readings isn't a trend yet."
)
SINCE_YDAY = "↑ $17 (vs 20 Jul)"
SINCE_WEEK = "no week of history yet"
DISTANCE = "$364 above"

OPTIONS_ROWS = """
<tr>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;font-weight:700;">Cheapest</td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;">🛫 Brisbane (BNE) Tue 2 Feb 2:40pm → 🛬 Tokyo (NRT) Wed 3 Feb 8:00pm <span style="color:#889;">(via Port Moresby, overnight; hop to Sapporo next morning)</span></td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;">🛫 Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 Brisbane (BNE) Thu 18 Feb 9:40am <span style="color:#889;">(via Port Moresby)</span></td>
  <td align="right" style="padding:10px 8px;border-bottom:1px solid #eef1f4;font-weight:800;">$1,364</td>
  <td align="right" style="padding:10px 8px;border-bottom:1px solid #eef1f4;">$5,456</td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;color:#b23;">long haul: 30h out via Port Moresby — brutal</td>
</tr>
<tr style="background:#f6fbf6;">
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;font-weight:700;">Best value</td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;">🛫 Brisbane (BNE) Tue 2 Feb 10:30am → 🛬 Tokyo (NRT) Tue 2 Feb 6:25pm <span style="color:#889;">(nonstop, 9h; hop to Sapporo next morning)</span></td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;">🛫 Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 Brisbane (BNE) Thu 18 Feb 9:40am <span style="color:#889;">(via Port Moresby)</span></td>
  <td align="right" style="padding:10px 8px;border-bottom:1px solid #eef1f4;font-weight:800;">$1,573</td>
  <td align="right" style="padding:10px 8px;border-bottom:1px solid #eef1f4;">$6,292</td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;color:#2e7d32;">nonstop 9h out, lands 6:25pm — easy; +$209pp to skip the slog</td>
</tr>
<tr>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;font-weight:700;">Fastest sensible</td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;">🛫 Brisbane (BNE) Wed 3 Feb 5:00am → 🛬 Sapporo (CTS) Wed 3 Feb 6:00pm <span style="color:#889;">(via Sydney on Qantas QF107, same day)</span></td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;">🛫 Tokyo (NRT) Wed 17 Feb 9:40pm → 🛬 Brisbane (BNE) Thu 18 Feb 9:40am <span style="color:#889;">(via Port Moresby)</span></td>
  <td align="right" style="padding:10px 8px;border-bottom:1px solid #eef1f4;font-weight:800;">$2,474</td>
  <td align="right" style="padding:10px 8px;border-bottom:1px solid #eef1f4;">$9,896</td>
  <td style="padding:10px 8px;border-bottom:1px solid #eef1f4;">straight to the snow same day, no overnight — lands 6pm</td>
</tr>
"""

ITIN_A = [
    ("1", "Tue 2 Feb", "Brisbane → transit", "Depart Brisbane (BNE) 2:40pm; overnight in Port Moresby"),
    ("2", "Wed 3 Feb", "→ Tokyo", "Land Tokyo (NRT) 8:00pm; overnight near airport"),
    ("3", "Thu 4 Feb", "Tokyo → Sapporo → Rusutsu", "Morning hop to Sapporo (CTS), pick up hire car, drive to Rusutsu (~2h)"),
    ("4", "Fri 5 Feb", "Rusutsu", "Ski day 1 — Isaac AM beginner lesson, lads ride powder"),
    ("5", "Sat 6 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride together"),
    ("6", "Sun 7 Feb", "Rusutsu → Sapporo", "Snow Festival day 1 (Odori Park); evening in Otaru"),
    ("7", "Mon 8 Feb", "Sapporo", "Snow Festival day 2 — full day"),
    ("8", "Tue 9 Feb", "Rusutsu", "Ski day 3 — powder day (Niseko day-trip option)"),
    ("9", "Wed 10 Feb", "Rusutsu", "Ski day 4 — last runs"),
    ("10", "Thu 11 Feb", "Hokkaido", "Rest day — Noboribetsu onsen / Jigokudani"),
    ("11", "Fri 12 Feb", "Sapporo → Tokyo", "Drop hire car (CTS), fly to Tokyo, check in"),
    ("12", "Sat 13 Feb", "Tokyo", "Shibuya, Shinjuku, ramen"),
    ("13", "Sun 14 Feb", "Tokyo", "Day trip — Nikko or teamLab (droppable)"),
    ("14", "Mon 15 Feb", "Tokyo", "Shopping, final feed"),
    ("15", "Tue 16 Feb", "Tokyo", "Last full day — spare / day trip"),
    ("16", "Wed 17 Feb", "Tokyo → home", "Depart Tokyo (NRT) 9:40pm"),
    ("17", "Thu 18 Feb", "→ Brisbane", "Land Brisbane (BNE) 9:40am"),
]
ITIN_B = [
    ("1", "Tue 2 Feb", "Brisbane → Tokyo", "Nonstop Brisbane (BNE) 10:30am → Tokyo (NRT) 6:25pm; overnight near airport"),
    ("2", "Wed 3 Feb", "Tokyo → Sapporo → Rusutsu", "Morning hop to Sapporo (CTS), pick up hire car, drive to Rusutsu (~2h)"),
    ("3", "Thu 4 Feb", "Rusutsu", "Ski day 1 — Isaac AM beginner lesson, lads ride powder"),
    ("4", "Fri 5 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride together"),
    ("5", "Sat 6 Feb", "Rusutsu", "Free ride / warm-up laps, relax"),
    ("6", "Sun 7 Feb", "Rusutsu → Sapporo", "Snow Festival day 1 (Odori Park); evening in Otaru"),
    ("7", "Mon 8 Feb", "Sapporo", "Snow Festival day 2 — full day"),
    ("8", "Tue 9 Feb", "Rusutsu", "Ski day 3 — powder day (Niseko day-trip option)"),
    ("9", "Wed 10 Feb", "Rusutsu", "Ski day 4 — last runs"),
    ("10", "Thu 11 Feb", "Hokkaido", "Rest day — Noboribetsu onsen / Jigokudani"),
    ("11", "Fri 12 Feb", "Sapporo → Tokyo", "Drop hire car (CTS), fly to Tokyo, check in"),
    ("12", "Sat 13 Feb", "Tokyo", "Shibuya, Shinjuku, ramen"),
    ("13", "Sun 14 Feb", "Tokyo", "Day trip — Nikko or teamLab (droppable)"),
    ("14", "Mon 15 Feb", "Tokyo", "Shopping, final feed"),
    ("15", "Tue 16 Feb", "Tokyo", "Last full day — spare / day trip"),
    ("16", "Wed 17 Feb", "Tokyo → home", "Depart Tokyo (NRT) 9:40pm"),
    ("17", "Thu 18 Feb", "→ Brisbane", "Land Brisbane (BNE) 9:40am"),
]
ITIN_C = [
    ("1", "Wed 3 Feb", "Brisbane → Sapporo", "Brisbane (BNE) 5:00am → Sydney → Sapporo (CTS) direct QF107, land 6:00pm; overnight Sapporo"),
    ("2", "Thu 4 Feb", "Sapporo → Rusutsu", "Pick up hire car, drive to Rusutsu (~2h), settle in"),
    ("3", "Fri 5 Feb", "Rusutsu", "Ski day 1 — Isaac AM beginner lesson, lads ride powder"),
    ("4", "Sat 6 Feb", "Rusutsu", "Ski day 2 — Isaac AM lesson, then all ride together"),
    ("5", "Sun 7 Feb", "Rusutsu → Sapporo", "Snow Festival day 1 (Odori Park); evening in Otaru"),
    ("6", "Mon 8 Feb", "Sapporo", "Snow Festival day 2 — full day"),
    ("7", "Tue 9 Feb", "Rusutsu", "Ski day 3 — powder day (Niseko day-trip option)"),
    ("8", "Wed 10 Feb", "Rusutsu", "Ski day 4 — last runs"),
    ("9", "Thu 11 Feb", "Hokkaido", "Rest day — Noboribetsu onsen / Jigokudani"),
    ("10", "Fri 12 Feb", "Sapporo → Tokyo", "Drop hire car (CTS), fly to Tokyo, check in"),
    ("11", "Sat 13 Feb", "Tokyo", "Shibuya, Shinjuku, ramen"),
    ("12", "Sun 14 Feb", "Tokyo", "Day trip — Nikko or teamLab (droppable)"),
    ("13", "Mon 15 Feb", "Tokyo", "Shopping, final feed"),
    ("14", "Tue 16 Feb", "Tokyo", "Last full day — spare / day trip"),
    ("15", "Wed 17 Feb", "Tokyo → home", "Depart Tokyo (NRT) 9:40pm"),
    ("16", "Thu 18 Feb", "→ Brisbane", "Land Brisbane (BNE) 9:40am"),
]


def itin_block(title, subtitle, rows):
    body = ""
    for d, date, loc, plan in rows:
        body += (
            f'<tr><td style="padding:7px 8px;border-bottom:1px solid #f0f3f6;color:#889;">{d}</td>'
            f'<td style="padding:7px 8px;border-bottom:1px solid #f0f3f6;white-space:nowrap;">{date}</td>'
            f'<td style="padding:7px 8px;border-bottom:1px solid #f0f3f6;font-weight:600;">{loc}</td>'
            f'<td style="padding:7px 8px;border-bottom:1px solid #f0f3f6;">{plan}</td></tr>\n'
        )
    return f"""
    <div style="background:#ffffff;padding:20px 24px;border:1px solid #e6eaee;border-top:none;">
      <h2 style="font-size:16px;margin:0 0 4px;color:#0d47a1;">🗓️ {title}</h2>
      <p style="font-size:12px;color:#889;margin:0 0 12px;">{subtitle}</p>
      <div style="overflow-x:auto;">
      <table role="presentation" width="100%" style="border-collapse:collapse;font-size:13px;min-width:460px;">
        <thead><tr style="background:#f0f4f8;">
          <th align="left" style="padding:8px;border-bottom:2px solid #d6dde4;">Day</th>
          <th align="left" style="padding:8px;border-bottom:2px solid #d6dde4;">Date</th>
          <th align="left" style="padding:8px;border-bottom:2px solid #d6dde4;">Location</th>
          <th align="left" style="padding:8px;border-bottom:2px solid #d6dde4;">Plan</th>
        </tr></thead>
        <tbody>{body}</tbody>
      </table>
      </div>
    </div>"""


ITINERARIES = itin_block(
    "Itinerary — shared plan (Rusutsu base, ~14 nights, hire car pickup/drop Sapporo CTS)",
    "Hokkaido first, Tokyo last · 4 ski days at Rusutsu · Isaac's lessons the first 2 ski mornings · "
    "2 full Snow Festival days + an Otaru evening. All three options run this same plan — only the "
    "flight in differs (see the note under the table).",
    ITIN_A,
) + """
    <div style="background:#ffffff;padding:0 24px 20px;border:1px solid #e6eaee;border-top:none;">
      <table role="presentation" width="100%" style="border-collapse:collapse;font-size:13px;background:#f6f8fa;border-radius:8px;">
        <tr><td style="padding:12px 14px;line-height:1.6;">
          <strong>How the flight in changes the first days:</strong><br>
          • <strong>Cheapest</strong> — as shown above (via Port Moresby, land Tokyo Wed 3 Feb 8:00pm, hop to Sapporo Thu 4 Feb).<br>
          • <strong>Best value</strong> — identical plan, but a nonstop in: Brisbane Tue 2 Feb 10:30am → Tokyo 6:25pm, hop to Sapporo Wed 3 Feb (a day earlier on the snow).<br>
          • <strong>Fastest sensible</strong> — fly straight into Sapporo on Qantas QF107 (Brisbane Wed 3 Feb 5:00am → Sapporo 6:00pm), skip the Tokyo-on-the-way-in night; Tokyo section at the end is unchanged.
        </td></tr>
      </table>
    </div>"""

TREND_BLOCK = """
<p style="font-size:13px;color:#556;margin:0 0 12px;">Where each daily reading lands against the buy bands (scale $0–$1,500pp):</p>
<table role="presentation" width="100%" style="border-collapse:collapse;">
  <tr>
    <td style="width:64px;"></td>
    <td>
      <table role="presentation" width="100%" style="border-collapse:collapse;height:14px;border-radius:4px;overflow:hidden;">
        <tr>
          <td style="width:66.7%;background:#c8e6c9;font-size:1px;line-height:14px;">&nbsp;</td>
          <td style="width:13.3%;background:#ffe0b2;font-size:1px;line-height:14px;">&nbsp;</td>
          <td style="width:20%;background:#ffcdd2;font-size:1px;line-height:14px;">&nbsp;</td>
        </tr>
      </table>
    </td>
    <td style="width:64px;"></td>
  </tr>
  <tr>
    <td></td>
    <td style="font-size:11px;color:#889;padding-top:2px;">
      <span style="color:#2e7d32;">◀ BUY ≤$1,000</span> &nbsp;·&nbsp; <span style="color:#8d6e00;">WATCH</span> &nbsp;·&nbsp; <span style="color:#b23;">HOLD &gt;$1,200 ▶</span>
    </td>
    <td></td>
  </tr>
</table>

<table role="presentation" width="100%" style="border-collapse:collapse;margin-top:14px;font-size:13px;">
  <tr>
    <td style="width:64px;color:#556;white-space:nowrap;">20 Jul</td>
    <td>
      <table role="presentation" width="100%" style="border-collapse:collapse;background:#eef1f4;border-radius:4px;">
        <tr><td style="width:89.8%;background:#c62828;height:16px;border-radius:4px;font-size:1px;line-height:16px;">&nbsp;</td><td style="font-size:1px;">&nbsp;</td></tr>
      </table>
    </td>
    <td style="width:64px;text-align:right;font-weight:700;white-space:nowrap;">$1,347</td>
  </tr>
  <tr>
    <td style="width:64px;color:#556;white-space:nowrap;padding-top:8px;">22 Jul</td>
    <td style="padding-top:8px;">
      <table role="presentation" width="100%" style="border-collapse:collapse;background:#eef1f4;border-radius:4px;">
        <tr><td style="width:90.9%;background:#c62828;height:16px;border-radius:4px;font-size:1px;line-height:16px;">&nbsp;</td><td style="font-size:1px;">&nbsp;</td></tr>
      </table>
    </td>
    <td style="width:64px;text-align:right;font-weight:700;white-space:nowrap;padding-top:8px;">$1,364</td>
  </tr>
</table>
<p style="font-size:12px;color:#889;margin:12px 0 0;">Both readings sit deep in the red HOLD zone — best price is $364 above the $1,000 buy target and has barely moved (↑$17 in two days). Full dated chart (chart.png) is saved in the trip repo.</p>
"""

NERD_NOTES = """
<li>Prices via the Kiwi.com connector, AUD, incl. 1 checked bag each way. Cheapest = Brisbane⇄Tokyo return via Port Moresby + two Tokyo↔Sapporo hops.</li>
<li>Sale check couldn't be verified — Jetstar, Qantas &amp; Virgin sale pages all returned 403 today; no live sale reported.</li>
<li>Via-China carriers priced but uncompetitive ($3,133+pp return).</li>
<li>Only two readings so far (20 &amp; 22 Jul) — not a trend yet.</li>
<li>Chart shown as a lightweight HTML trend so it renders on every device; the full dated chart.png is in the repo (couldn't embed the PNG this run — the repo is private so it can't be pulled by URL).</li>
"""

repl = {
    "{{ACTION_BANNER}}": ACTION_BANNER,
    "{{HEADER_BG}}": HEADER_BG,
    "{{VERDICT_EMOJI}}": VERDICT_EMOJI,
    "{{VERDICT_WORD}}": VERDICT_WORD,
    "{{BEST_PP}}": BEST_PP,
    "{{BEST_ALL4}}": BEST_ALL4,
    "{{DATE_LONG}}": DATE_LONG,
    "{{SNAPSHOT}}": SNAPSHOT,
    "{{SINCE_YDAY}}": SINCE_YDAY,
    "{{SINCE_WEEK}}": SINCE_WEEK,
    "{{DISTANCE}}": DISTANCE,
    "{{OPTIONS_ROWS}}": OPTIONS_ROWS,
    "{{ITINERARIES}}": ITINERARIES,
    "{{TREND_BLOCK}}": TREND_BLOCK,
    "{{NERD_NOTES}}": NERD_NOTES,
}

with open("email-template.html") as f:
    html = f.read()
for k, v in repl.items():
    html = html.replace(k, v)

if "{{" in html:
    import re
    leftover = re.findall(r"\{\{[^}]+\}\}", html)
    raise SystemExit(f"Unfilled placeholders: {leftover}")

with open("email-final.html", "w") as f:
    f.write(html)
print(f"wrote email-final.html ({len(html)} chars)")
