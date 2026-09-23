#!/usr/bin/env python3
"""Regenerate chart.png (and the email copy) from the full prices.csv price log.

Comfortable-price-per-person line over time (the number the verdict is based
on), with a green BUY zone (<=$1,500), amber WATCH band ($1,500-$1,600), and a
marker on today's (latest) point. The absolute-cheapest (any-routing) total is
drawn as a lighter dotted reference so the gap to comfortable is visible — for
rows logged before comfortable was tracked separately the two lines overlap.

One set of targets — no private target. The retired $1,430 buy target is drawn
as a plain dotted reference line on Isaac's request (23 Sep 2026), so the chart
shows how far the goalposts have moved. It is history, not a band: never shade
it, and never base a verdict on it. Also writes chart-email.png and its
base64 (chart-email.b64) for embedding in the daily email.
"""
import base64
import csv
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BUY = 1500    # buy target — CALL THE LADS at or below this
WATCH = 1600  # watch ceiling — HOLD above this
OLD_BUY = 1430  # retired buy target (Sep 2026) — reference line only, keep it
# White backing so band labels stay readable where the price line crosses them.
LABEL_BOX = dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85)

dates, total, comfortable = [], [], []
with open("prices.csv") as f:
    for row in csv.DictReader(f):
        dates.append(datetime.strptime(row["date"], "%Y-%m-%d"))
        t = float(row["best_total_pp"])
        # best_comfortable_pp was added in v3; fall back to the total for any
        # older row (or a blank cell) so the chart never crashes on a hand edit.
        c = row.get("best_comfortable_pp") or ""
        comfortable.append(float(c) if c.strip() else t)
        total.append(t)


def build(path, figsize=(10, 5.6), dpi=130):
    # Font sizes are tuned for the 10in wide chart; scale them down for the
    # narrower email copy so the title doesn't get clipped.
    s = min(1.0, figsize[0] / 10.0)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfbfd")

    # Y range gives headroom around the data and always shows the buy/watch bands.
    ymax = max(max(total), max(comfortable), WATCH) * 1.06
    ymin = min(min(comfortable), min(total), BUY, OLD_BUY) - 120
    ymin = max(0, ymin)

    # Shaded decision bands.
    ax.axhspan(0, BUY, color="#2e7d32", alpha=0.14, zorder=0)
    ax.axhspan(BUY, WATCH, color="#f9a825", alpha=0.16, zorder=0)
    ax.axhline(BUY, color="#2e7d32", lw=1.2, ls="--", alpha=0.8)
    ax.axhline(WATCH, color="#f9a825", lw=1.2, ls="--", alpha=0.8)
    ax.text(0.012, BUY - 8, "  BUY zone  ≤ $1,500", transform=ax.get_yaxis_transform(),
            va="top", ha="left", fontsize=9*s, color="#1b5e20", fontweight="bold", bbox=LABEL_BOX, zorder=7)
    ax.text(0.012, WATCH - 8, "  WATCH  $1,500–$1,600", transform=ax.get_yaxis_transform(),
            va="top", ha="left", fontsize=9*s, color="#8d6e00", fontweight="bold", bbox=LABEL_BOX, zorder=7)

    # Retired target — kept visible on purpose so the old goalpost stays on record.
    ax.axhline(OLD_BUY, color="#6a1b9a", lw=1.3, ls=":", alpha=0.9, zorder=2)
    ax.text(0.012, OLD_BUY + 6, "  Old buy target $1,430 (retired 23 Sep)",
            transform=ax.get_yaxis_transform(), va="bottom", ha="left",
            fontsize=8.5*s, color="#6a1b9a", fontweight="bold", bbox=LABEL_BOX, zorder=7)

    # Cheapest any-routing total — lighter dotted reference (may include
    # forced-overnight fares). Overlaps the comfortable line where they're equal.
    ax.plot(dates, total, "--o", color="#90a4ae", lw=1.5, ms=3.5,
            label="Cheapest any-routing pp", zorder=3)

    # Best-comfortable line (hero) — the number the verdict is based on.
    ax.plot(dates, comfortable, "-o", color="#1565c0", lw=2.6, ms=6,
            label="Best comfortable pp", zorder=4)

    # Highlight today's / latest comfortable point.
    ax.scatter([dates[-1]], [comfortable[-1]], s=170*s, facecolor="#1565c0",
               edgecolor="white", linewidth=2, zorder=6)
    ax.annotate(f"${comfortable[-1]:,.0f}", (dates[-1], comfortable[-1]),
                textcoords="offset points", xytext=(0, 14), ha="center",
                fontsize=11*s, fontweight="bold", color="#0d47a1")

    ax.set_ylim(ymin, ymax)
    ax.set_title("Brisbane → Japan snow trip — best price per person (Feb 2027)",
                 fontsize=14*s, fontweight="bold", pad=14*s)
    ax.set_ylabel("AUD per person (all-in, incl. bags)", fontsize=11*s)
    ax.set_xlabel("Date checked", fontsize=11*s)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    if len(dates) == 1:
        ax.margins(x=0.5)
        ax.set_xticks(dates)  # avoid repeated identical month ticks on a 1-point log
    elif len(dates) <= 8:
        ax.set_xticks(dates)  # one tick per check; AutoDateLocator overlaps them
    else:
        # Cap the tick count — the default packs them in tight enough to collide
        # once the log runs to a couple of weeks.
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=7))
    ax.tick_params(labelsize=9.5*s)
    fig.autofmt_xdate(rotation=0, ha="center")

    ax.grid(True, axis="y", color="#e0e0e0", lw=0.8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9*s)

    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


build("chart.png")

# Email copy: full readable size, then palette-quantised. A line chart is mostly
# flat colour, so quantising cuts the bytes far more than shrinking the image
# does — and keeps it legible instead of a postage stamp.
build("chart-email.png", figsize=(6.4, 3.6), dpi=100)

from PIL import Image

img = Image.open("chart-email.png").convert("RGB")
img.quantize(colors=24, method=Image.MEDIANCUT).save(
    "chart-email.png", optimize=True)

with open("chart-email.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("ascii")
with open("chart-email.b64", "w") as f:
    f.write(b64)

print("wrote chart.png + chart-email.png with", len(dates), "point(s);",
      "b64 length", len(b64))
