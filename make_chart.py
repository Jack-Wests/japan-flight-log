#!/usr/bin/env python3
"""Regenerate the price charts from the full prices.csv log.

Outputs:
  chart.png        - full-size chart for the repo
  chart-email.png  - small (~<10 KB) version for embedding in the daily email
  chart-email.b64  - the exact, complete base64 of chart-email.png; paste this
                     whole string as the email's cid attachment content

Decision bands shown on the chart (group-facing):
  green  BUY zone  <= $1,000
  amber  WATCH     $1,000 - $1,200
(The private $800 target is deliberately NOT drawn - it goes in the
 push notification only, never in anything the group sees.)
"""
import base64
import csv
import os
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


def draw(figsize, dpi, out, compact=False):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfbfd")

    # Y range gives headroom around the data and always shows the bands.
    ymax = max(max(best), max(fastest), WATCH) * 1.08
    ymin = max(0, min(min(best), BUY) - 120)

    # Shaded decision bands.
    ax.axhspan(0, BUY, color="#2e7d32", alpha=0.14, zorder=0)
    ax.axhspan(BUY, WATCH, color="#f9a825", alpha=0.16, zorder=0)
    ax.axhline(BUY, color="#2e7d32", lw=1.2, ls="--", alpha=0.8)
    ax.axhline(WATCH, color="#f9a825", lw=1.2, ls="--", alpha=0.8)
    fs = 8 if compact else 9
    ax.text(0.012, BUY - 8, "  BUY zone  ≤ $1,000", transform=ax.get_yaxis_transform(),
            va="top", ha="left", fontsize=fs, color="#1b5e20", fontweight="bold")
    ax.text(0.012, WATCH - 8, "  WATCH  $1,000–$1,200", transform=ax.get_yaxis_transform(),
            va="top", ha="left", fontsize=fs, color="#8d6e00", fontweight="bold")

    # Fastest-sensible reference line (lighter), then the hero line.
    ax.plot(dates, fastest, "-o", color="#90a4ae", lw=1.6, ms=4,
            label="Fastest sensible pp", zorder=3)
    ax.plot(dates, best, "-o", color="#1565c0", lw=2.6, ms=6,
            label="Best total pp", zorder=4)

    # Highlight today's / latest point.
    ax.scatter([dates[-1]], [best[-1]], s=150, facecolor="#1565c0",
               edgecolor="white", linewidth=2, zorder=6)
    ax.annotate(f"${best[-1]:,.0f}", (dates[-1], best[-1]),
                textcoords="offset points", xytext=(0, 13), ha="center",
                fontsize=10 if compact else 11, fontweight="bold", color="#0d47a1")

    ax.set_ylim(ymin, ymax)
    ax.set_title("Brisbane → Japan snow trip — best price per person (Feb 2027)",
                 fontsize=11 if compact else 14, fontweight="bold", pad=12)
    ax.set_ylabel("AUD per person (all-in, incl. bags)", fontsize=9 if compact else 11)
    ax.set_xlabel("Date checked", fontsize=9 if compact else 11)

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
    ax.legend(loc="upper right", framealpha=0.9, fontsize=8 if compact else 9)

    fig.tight_layout()
    fig.savefig(out, dpi=dpi)
    plt.close(fig)


draw((10, 5.6), 130, "chart.png")
draw((6.6, 3.4), 72, "chart-email.png", compact=True)

# Shrink the email chart to a small palette PNG so its base64 stays short
# enough to paste whole into the email attachment (target <= ~10 KB).
from PIL import Image
im = Image.open("chart-email.png").convert("RGB")
im = im.resize((480, int(im.size[1] * 480 / im.size[0])), Image.LANCZOS)
im.convert("P", palette=Image.ADAPTIVE, colors=16).save("chart-email.png", optimize=True)

b64 = base64.b64encode(open("chart-email.png", "rb").read()).decode()
with open("chart-email.b64", "w") as f:
    f.write(b64)
print(f"wrote chart.png ({len(dates)} point(s)), chart-email.png "
      f"({os.path.getsize('chart-email.png')} B), chart-email.b64 ({len(b64)} chars)")
