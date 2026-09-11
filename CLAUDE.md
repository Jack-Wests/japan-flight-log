# Working on this repo

## Who you're talking to

Isaac — a uni student, not a programmer. Assume no knowledge of git, Python,
HTML or email plumbing, and don't assume a question is technical just because
the answer is.

- **Explain in plain English.** "Git keeps every old version of a file, so the
  old number is still readable in the history" — not "it's in the reflog."
- **Don't hand over instructions to run.** Do the work, then say what you did.
  If something genuinely needs doing outside this session (changing the
  scheduled task, a GitHub setting), say exactly what to click or paste.
- **Say plainly when something's broken.** Don't soften it into "you may wish
  to consider". If a number is wrong or a claim of mine turned out wrong, lead
  with that.
- **A question is not a complaint.** "why is it doing X" usually means they
  want to understand X, not that they want it changed.
- **Don't ask permission for ordinary work.** Reading, fixing, testing,
  committing to the working branch — just do it. Ask only for things that are
  hard to undo: pushing to `main`, rewriting history, force-pushing, sending an
  extra email, anything the four mates would see.

## The trip (context for judgement calls)

Four uni students, Brisbane → Hokkaido, Feb 2027. The whole-trip budget is about
**$3,000pp including flights** (stretched from $2,500 once non-flight costs were
properly estimated). Flights realistically cap at **~$1,500pp**.

51 days of price data (Jul–Sep 2026) show the cheapest all-in fare has ranged
from $1,333 to $1,688, with a median of ~$1,485 and a trend of +$18/week. The
floor is rising as cheap fare classes sell out into Snow Festival peak week.

**Itinerary shape:** fly into Sapporo (CTS) Feb 2–3, Sapporo Snow Festival
2 days, drive to Furano for 7 nights (ski + chill), drive back via Jozankei
onsen + Otaru Snow Light Path on Feb 13, fly CTS→TYO Feb 14, Tokyo 2–3 days,
fly home from TYO Feb 16–17. ~13 nights total.

## Non-negotiable

- **Buy target is $1,430. One set of bands, no private target.** The old
  $1,000/$800 targets were based on a 2024 anomaly that won't repeat. 51 days
  of data establish the realistic floor at ~$1,350. $1,430 is a genuine dip;
  below that = book on the spot. $1,430–$1,500 = WATCH. Above $1,500 = HOLD.
- **This repo is public.** Anything committed is readable by anyone, including
  every past version in the history.
- **One email per run. Never a "corrected" follow-up.** Fix it before sending
  or note it in Nerd Notes.

## Before changing anything

Read **`RUNBOOK.md`** — it has the daily run order and a table of every failure
mode already hit. The short version of the expensive ones:

- **Never rebuild the email HTML from scratch.** Edit `render_email.py`'s `RUN`
  block and run it. Improvising the HTML each run is why every email used to
  look different.
- **Run `sync_prices.py` before reading `prices.csv`.** Each scheduled run gets
  its own branch and nothing merges back, so an unsynced checkout sees a stale
  log and every trend number comes out wrong.
- **Never embed the chart as base64 / a `data:` URI.** Gmail blocks them. It's a
  hosted image; push before sending or it 404s.
- **Check a trend against the whole log before describing it.** A "down $65"
  claim once came from comparing against the single highest point in the series,
  because that was the only other row the stale log had.

## Token cost

A past run burned ~7× the usual budget on retry loops. Before iterating on
something more than twice, stop and check the assumption underneath it.

Preview an email by rendering `email.html` with headless Chromium and looking at
the screenshot — much cheaper than sending and finding out.
