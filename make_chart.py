#!/usr/bin/env python3
"""Regenerate chart.png (and the email copy) from the full prices.csv price log.

Best-total-per-person line over time, with a green BUY zone (<=$1,000),
amber WATCH band ($1,000-$1,200), and a marker on today's (latest) point.

Public targets only — the mates see this chart, so the private target never
appears here. Also writes chart-email.png and its base64 (chart-email.b64)
for embedding in the daily email.
"""
import base64
import csv
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BUY = 1000    # public buy target — CALL THE LADS at or below this
WATCH = 1200  # public watch ceiling — HOLD above this

dates, best, fastest = [], [], []
with open("prices.csv") as f:
    for row in csv.DictReader(f):
        dates.append(datetime.strptime(row["date"], "%Y-%m-%d"))
        best.append(float(row["best_total_pp"]))
        fastest.append(float(row["fastest_sensible_pp"]))


def build(path, figsize=(10, 5.6), dpi=130):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfbfd")

    # Y range gives headroom around the data and always shows the buy/watch bands.
    ymax = max(max(best), max(fastest), WATCH) * 1.08
    ymin = min(min(best), BUY) - 150
    ymin = max(0, ymin)

    # Shaded decision bands.
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
                 fontsize=14, fontweight="bold", pad=14)
    ax.set_ylabel("AUD per person (all-in, incl. bags)", fontsize=11)
    ax.set_xlabel("Date checked", fontsize=11)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    if len(dates) == 1:
        ax.margins(x=0.5)
        ax.set_xticks(dates)  # avoid repeated identical month ticks on a 1-point log
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
    return path


# Public chart (repo + report): full quality.
build("chart.png")
# Email copy: smaller/lighter so its complete base64 is compact enough to
# paste inline as the cid:chart attachment.
build("chart-email.png", figsize=(5.7, 3.3), dpi=50)

with open("chart-email.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("ascii")
with open("chart-email.b64", "w") as f:
    f.write(b64)

print("wrote chart.png + chart-email.png with", len(dates), "point(s);",
      "b64 length", len(b64))
