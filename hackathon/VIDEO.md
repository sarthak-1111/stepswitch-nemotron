# Video script (2:58)

The event asks for a public video under three minutes that shows the project working and how
Token Factory and Nemotron are used. The cut runs 2:58; the timecodes below are the cut's.
Terminal shots come from the VHS tapes in [tapes/](tapes/) (or any screen recorder running the
same commands); browser shots come from the demo page,
https://sarthak-1111.github.io/stepswitch-nemotron/, and the README. The cut's music is a score
generated for it and released as CC0; if you add other music, use a track you hold the rights
to.

Every number spoken below is in the README's hackathon section, in
`claims/evidence/C-029.json` and `claims/evidence/C-030.json`, in `hackathon/bill.json`, or in
the recorded run the live scene replays. If a re-run changes one, read it from there.

## 0:00 to 0:20: the story in twenty seconds

**Shot:** two cards side by side, "Nemotron 3 Ultra alone" and "Stepswitch, the Nemotron
ladder", 21 check marks each. The left card's marks fill and its total counts up to $1.16; then
the right card's fill and it counts up to $0.21. Then the wordmark and "The right Nemotron for
every step."

**Voice:** "Give a coding agent 21 small tasks, and run every step on Nemotron's largest model.
All 21 pass, for $1.16. With Stepswitch, all 21 still pass, for $0.21."

## 0:20 to 0:38: the problem

**Shot:** the step types of the recorded task as chips. Every chip but plan and review turns
green ("a smaller model will do"), plan and review turn dark, then every chip flies into one
big model.

**Voice:** "Most of those calls don't need the largest model: find a file, read it, make a small
edit, run the tests. Only a few are hard, like planning a change or reviewing it. Yet many
agents send every call to the same big model."

## 0:38 to 0:53: the ladder

**Shot:** the model ladder on Token Factory: Nemotron 3.5 Lightning, Nemotron 3 Super,
Nemotron 3 Ultra and `gpt-oss-120b`, with the steps each takes and its list prices.

**Voice:** "Stepswitch picks the model for each step, on Token Factory. Small Nemotron models
read and summarize. Bigger ones plan, edit and review."

## 0:53 to 1:41: a recorded run that escalates

**Shot:** `tapes/live-run.tape` (terminal), recorded with the Nano-first policy and replayed
sped up (the badge says so). Each line names the step, the Nemotron model that ran it, and the
task's running tokens and dollars. The demo page replays the same kind of run: Replay, the
**Watch an escalation** button (task `temperature-units`, recorded on 2026-10-28).

**Voice:** "This is a real run on Token Factory, sped up. Nemotron 3 Ultra writes the plan, and
Nemotron 3.5 Lightning reads the files. For this demo, Nemotron 3 Nano, a small model, tries the
edit first. Its change fails the project's tests. It tries again, and fails a second time. So
Stepswitch escalates. Ultra takes over the edit, and now the tests pass. Ultra reviews the
change, and a model from another family gives a second opinion. Every step line shows the model
and the running bill. This task cost 11 cents."

## 1:41 to 2:09: results

**Shot:** the ladder against Ultra alone on the 21 task runs: passes, dollars per task run,
uncached tokens and the reviewers' agreement.

**Voice:** "The full comparison, on 21 coding and science tasks. Both passed all 21. Stepswitch
spent 81.6% fewer dollars per task. About 1 cent, against 5.5 cents. It also sent fewer than
half the uncached tokens. A reviewer from another model family agreed with Ultra on 20 of 21
changes."

## 2:09 to 2:29: the bill

**Shot:** the bill as the README states it, then the replication line under the table.

**Voice:** "We publish the whole bill: every hosted bench run, failed ones included, cost $5.65.
We ran it again, registered in advance: the same 18% of Ultra's dollars, but it missed its
bound on one task, so we withdrew that claim."

## 2:29 to 2:44: prove it yourself

**Shot:** `tapes/prove.tape` (terminal), at its real speed: `uv run ssw prove --claim C-029
--claim C-030` ends with both claims passing.

**Voice:** "Every number in the README has a test. Clone the repository and run ssw prove: it
re-checks these claims from the recorded runs. No key needed, and it costs nothing."

## 2:44 to 2:58: close

**Shot:** the wordmark, the code and replay links, and the demo page playing **Watch a failed
gate escalate**.

**Voice:** "Stepswitch: the right Nemotron for every step, checked by your tests and a second
reviewer. The code and the replay are linked below."

## Recording notes

- `python hackathon/tapes/setup_demo.py` sets up the toy project for the live run (the
  Nano-first policy, so a gate failure is likely; `--policy ladder` for the C-029 ladder). A
  take costs about US$ 0.05 to 0.30 and stops at 0.30.
- VHS reads the tapes: `vhs hackathon/tapes/live-run.tape` and `vhs hackathon/tapes/prove.tape`,
  with `NEBIUS_API_KEY` set in the shell for the live run only. The key is never typed on screen.
- The demo page plays a replay with **Play**; **Show all steps** shows the whole run at once.
- Upload as public on YouTube, then put the link in the README's hackathon section ("Video")
  and in the submission form.
