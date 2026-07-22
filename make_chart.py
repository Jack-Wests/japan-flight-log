#!/usr/bin/env python3
"""Regenerate chart.png (and the email copies) from the full prices.csv log.

Best-total-per-person line over time, with a green BUY zone (<=$1,000),
amber WATCH band ($1,000-$1,200), and a marker on today's (latest) point.

PUBLIC targets only — the private $800 target must never appear here.
Outputs:
  chart.png        — repo / report / desktop copy
  chart-email.png  — email-sized copy (narrower, embeds nicely on phones)
  chart-email.b64  — complete base64 of chart-email.png (for cid embedding)
"""
import base64
import csv
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BUY = 1000        # public buy target
WATCH = 1200      # public watch ceiling

dates, best, fastest = [], [], []
with open("prices.csv") as f:
    for row in csv.DictReader(f):
        dates.append(datetime.strptime(row["date"], "%Y-%m-%d"))
        best.append(float(row["best_total_pp"]))
        fastest.append(float(row["fastest_sensible_pp"]))


def render(path, figsize, dpi, title_size=13):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfbfd")

    ymax = max(max(best), max(fastest), WATCH) * 1.08
    ymin = min(min(best), BUY) - 160
    ymin = max(0, ymin)

    # Shaded decision bands (public).
    ax.axhspan(0, BUY, color="#2e7d32", alpha=0.14, zorder=0)
    ax.axhspan(BUY, WATCH, color="#f9a825", alpha=0.16, zorder=0)
    ax.axhline(BUY, color="#2e7d32", lw=1.2, ls="--", alpha=0.8)
    ax.axhline(WATCH, color="#f9a825", lw=1.2, ls="--", alpha=0.8)
    ax.text(0.012, BUY - 8, "  BUY zone  ≤ $1,000", transform=ax.get_yaxis_transform(),
            va="top", ha="left", fontsize=9, color="#1b5e20", fontweight="bold")
    ax.text(0.012, WATCH - 8, "  WATCH  $1,000–$1,200", transform=ax.get_yaxis_transform(),
            va="top", ha="left", fontsize=9, color="#8d6e00", fontweight="bold")

    # Fastest-sensible reference line (lighter).
    ax.plot(dates, fastest, "-o", color="#90a4ae", lw=1.6, ms=4,
            label="Fastest sensible pp", zorder=3)

    # Best-total line (hero).
    ax.plot(dates, best, "-o", color="#1565c0", lw=2.6, ms=6,
            label="Best total pp", zorder=4)

    # Highlight today's / latest point.
    ax.scatter([dates[-1]], [best[-1]], s=170, facecolor="#1565c0",
               edgecolor="white", linewidth=2, zorder=6)
    ax.annotate(f"${best[-1]:,.0f}", (dates[-1], best[-1]),
                textcoords="offset points", xytext=(0, 14), ha="center",
                fontsize=11, fontweight="bold", color="#0d47a1")

    ax.set_ylim(ymin, ymax)
    ax.set_title("Brisbane → Japan snow trip — best price per person (Feb 2027)",
                 fontsize=title_size, fontweight="bold", pad=14)
    ax.set_ylabel("AUD per person (all-in, incl. bags)", fontsize=10)
    ax.set_xlabel("Date checked", fontsize=10)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    if len(dates) == 1:
        ax.margins(x=0.5)
        ax.set_xticks(dates)
    elif len(dates) <= 8:
        # Few points: label the actual dates, no repeated auto ticks.
        ax.set_xticks(dates)
        ax.margins(x=0.06)
    else:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=0, ha="center")

    ax.grid(True, axis="y", color="#e0e0e0", lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


# Repo / report / desktop chart.
render("chart.png", (10, 5.6), 130)

# Email copy — narrower / lighter so it embeds cleanly on phones and keeps the
# base64 payload small.
render("chart-email.png", (5.6, 3.3), 74, title_size=9)

# Complete base64 of the email chart, for cid embedding.
with open("chart-email.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("ascii")
with open("chart-email.b64", "w") as f:
    f.write(b64)

print(f"wrote chart.png, chart-email.png, chart-email.b64 ({len(dates)} point(s), b64 len {len(b64)})")
