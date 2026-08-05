#!/usr/bin/env python3
"""Rebuild prices.csv from every logged row on every branch.

Each scheduled run gets its own fresh branch off main, appends one row, and
pushes to that branch — nothing merges back. So the daily rows exist, but they
are scattered across ~20 abandoned branches and no single checkout sees more
than a couple of them.

Run this at the START of a run (RUNBOOK step 0) to pull the full history back
together before appending today's row. It walks every commit that touched
prices.csv across all refs in chronological order, so if a date was logged
twice, the later run wins.

Safe to run repeatedly: it only ever adds rows it can find, and it refuses to
write a file with fewer rows than the one already on disk.
"""
import csv
import io
import os
import subprocess
import sys

HEADER = "date,best_total_pp,fastest_sensible_pp,verdict"
PATH = "prices.csv"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def main(write=True):
    subprocess.run(["git", "fetch", "--all", "--quiet"], capture_output=True)

    # Oldest commit first, so later observations of the same date overwrite.
    commits = git("log", "--all", "--reverse", "--format=%H", "--", PATH).split()

    rows = {}
    for c in commits:
        blob = subprocess.run(["git", "show", f"{c}:{PATH}"],
                              capture_output=True, text=True)
        if blob.returncode:
            continue
        for row in csv.DictReader(io.StringIO(blob.stdout)):
            if row.get("date"):
                rows[row["date"]] = row

    # Whatever is on disk right now counts too — today's row may not be committed.
    if os.path.exists(PATH):
        with open(PATH) as f:
            for row in csv.DictReader(f):
                if row.get("date"):
                    rows.setdefault(row["date"], row)

    existing = 0
    if os.path.exists(PATH):
        with open(PATH) as f:
            existing = sum(1 for _ in csv.DictReader(f))

    if len(rows) < existing:
        sys.exit(f"refusing to shrink {PATH}: rebuilt {len(rows)} < existing {existing}")

    out = [HEADER] + [
        f'{r["date"]},{r["best_total_pp"]},{r["fastest_sensible_pp"]},{r["verdict"]}'
        for _, r in sorted(rows.items())
    ]
    if write:
        with open(PATH, "w") as f:
            f.write("\n".join(out) + "\n")
    print(f"{PATH}: {existing} row(s) before, {len(rows)} after "
          f"({len(rows) - existing} recovered)")
    return len(rows)


if __name__ == "__main__":
    main(write="--dry-run" not in sys.argv)
