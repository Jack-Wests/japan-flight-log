#!/usr/bin/env python3
"""Regenerate the price-log chart from prices.csv.

Writes three files:
  - chart.png        : the public chart (shared with the lads / email / report)
  - chart-email.png  : the same chart sized for embedding in the email
  - chart-email.b64  : the complete base64 of chart-email.png (for the cid attach)

Public decision bands (these are what everyone sees):
  green  BUY   <= $1,000
  amber  WATCH  $1,000 - $1,200
  red    HOLD  > $1,200
"""
import base64
import csv
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BUY = 1000
WATCH = 1200

dates, best, fastest = [], [], []
with open("prices.csv") as f:
    for row in csv.DictReader(f):
        dates.append(datetime.strptime(row["date"], "%Y-%m-%d"))
        best.append(float(row["best_total_pp"]))
        fastest.append(float(row["fastest_sensible_pp"]))


def build_figure(compact=False):
    # Compact mode makes a lighter PNG small enough to inline-embed in the email.
    figsize = (6.4, 3.5) if compact else (10, 5.6)
    dpi = 58 if compact else 130
    fs = 0.72 if compact else 1.0  # font-scale
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfbfd")

    ymax = max(max(best), max(fastest), WATCH) * 1.08
    ymin = min(min(best), BUY) - 160
    ymin = max(0, ymin)

    # Shaded decision bands.
    ax.axhspan(0, BUY, color="#2e7d32", alpha=0.14, zorder=0)
    ax.axhspan(BUY, WATCH, color="#f9a825", alpha=0.16, zorder=0)
    ax.axhspan(WATCH, ymax, color="#c62828", alpha=0.08, zorder=0)
    ax.axhline(BUY, color="#2e7d32", lw=1.2, ls="--", alpha=0.8)
    ax.axhline(WATCH, color="#f9a825", lw=1.2, ls="--", alpha=0.8)
    ax.text(0.012, BUY - 6, "  BUY zone  ≤ $1,000", transform=ax.get_yaxis_transform(),
            va="top", ha="left", fontsize=9 * fs, color="#1b5e20", fontweight="bold")
    ax.text(0.012, WATCH - 6, "  WATCH  $1,000–$1,200", transform=ax.get_yaxis_transform(),
            va="top", ha="left", fontsize=9 * fs, color="#8d6e00", fontweight="bold")

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
                fontsize=11 * fs, fontweight="bold", color="#0d47a1")

    ax.set_ylim(ymin, ymax)
    ax.set_title("Brisbane → Japan snow trip — best price per person (Feb 2027)",
                 fontsize=14 * fs, fontweight="bold", pad=14)
    ax.set_ylabel("AUD per person (all-in, incl. bags)", fontsize=11 * fs)
    ax.set_xlabel("Date checked", fontsize=11 * fs)
    ax.tick_params(labelsize=10 * fs)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    if len(dates) == 1:
        ax.margins(x=0.5)
        ax.set_xticks(dates)
    elif len(dates) <= 8:
        # Few points: label each actual check date, no repeated ticks.
        ax.set_xticks(dates)
    else:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=0, ha="center")

    ax.grid(True, axis="y", color="#e0e0e0", lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9 * fs)
    fig.tight_layout()
    return fig


fig = build_figure()
fig.savefig("chart.png", dpi=130)

fig_email = build_figure(compact=True)
fig_email.savefig("chart-email.png", dpi=58)

with open("chart-email.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("ascii")
with open("chart-email.b64", "w") as f:
    f.write(b64)

print("wrote chart.png, chart-email.png, chart-email.b64 with", len(dates), "point(s);",
      "b64 length", len(b64))
