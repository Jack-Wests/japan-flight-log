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

- **Buy target is $1,500 (comfortable routing). One set of bands, no private
  target.** The old $1,000/$800 targets were based on a 2024 anomaly that won't
  repeat. The bands are set against the cheapest *comfortable* option — no
  forced-overnight costs hidden from the fare; a Singapore overnight counts as
  free. $1,500 is a genuine dip; below that = book on the spot.
  $1,500–$1,600 = WATCH. Above $1,600 = HOLD.
- **Keep the old $1,430 line on the chart.** Isaac asked (23 Sep 2026) for the
  retired $1,430 buy target to stay visible as a purple dotted line, so the
  goalposts can't quietly move. It's a record, not a second target: no shading,
  no verdict based on it. `make_chart.py` draws it — don't remove it.
- **The "How long each trip takes" bars are settled (25 Sep 2026).** One bar per
  leg, There/Home in bold black, hours inside **every** piece (short pieces get
  a minimum width and a smaller font rather than a blank), one line of detail
  underneath in each piece's colour starting with each piece's **local** start
  time and ending "lands <local time>", 🛏️ on overnight layovers. (Times and
  every-piece labels added at Isaac's request, 25 Sep evening.) Isaac rejected
  one-row-per-piece, numbered pieces, stacked labels and AEST timestamps. Don't
  redesign it unless he asks.
- **The way over is settled (21 Oct 2026): short Singapore change, then Osaka.**
  Isaac wants Singapore Airlines Brisbane → Singapore → Osaka (KIX) with a
  *short* change in Singapore (~1–2h, e.g. 6:10pm → 12:05am, 1:30am → 8:35am)
  so everyone sleeps on both flights. Then 1–2 days in Osaka, then a separately
  booked Osaka (KIX/ITM/UKB) → Sapporo (CTS) flight on 3 Feb (4 Feb at the
  latest), in time for Snow Festival days on 4–5 Feb. This **overrides** the
  routine prompt's "prefer a Singapore overnight / long layover" rule: never
  pick a Singapore overnight over a short change unless it's actually cheaper,
  and don't sell it as a perk. Osaka hotel nights replace Sapporo nights, so add
  nothing for them. This plan is the "Cheapest" row, the "There" journey bar
  ends at Osaka, and its total is `best_comfortable_pp` and the verdict price.
  Other routings can still fill the other rows. If this plan is **$1,633pp or
  under** (Mon 19 Oct's price), open the email with "🚨 ACTION NEEDED TODAY:
  back to $1,633 or under".
- **Subject line is always `Japan trip <emoji> <date> — best $<X>pp`.** Isaac's
  Gmail sorts on it. Two off-format emails on 21 Oct got sorted away and looked
  like they never arrived.
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
