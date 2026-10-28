# Video script (2:50)

The event asks for a public video under three minutes that shows the project working and how
Token Factory and Nemotron are used. This script runs 2:50. Terminal shots come from the VHS
tapes in [tapes/](tapes/) (or any screen recorder running the same commands); browser shots
come from the demo page, https://sarthak-1111.github.io/stepswitch-nemotron/, and the README.
No music is needed; if you add some, use a track you hold the rights to.

Every number spoken below is in the README's hackathon section or in
`claims/evidence/C-029.json` and `claims/evidence/C-030.json`. If a re-run changes one, read it
from there.

## 0:00 to 0:15: the problem

**Shot:** the README's hackathon section, scrolling from the title to the model table.

**Voice:** "A coding agent makes dozens of model calls for one task. Most of them are small:
find a file, read it, condense a test log. Yet agents send every call to one model, usually
the biggest. Stepswitch picks the model for each step, on Token Factory."

## 0:15 to 0:50: a live run, model by model

**Shot:** `tapes/live-run.tape` (terminal). Each line names the step, the Nemotron model on
Token Factory that ran it, and the task's running tokens and dollars.

**Voice:** "This is a live run on Token Factory. Nemotron 3 Ultra writes the plan. Nemotron 3.5
Lightning, the smallest model, finds and reads the files. Nemotron 3 Super makes the edit and
runs the tests. Every step line shows the model and the dollars so far."

## 0:50 to 1:30: a failed gate escalates to Ultra

**Shot:** the live run continuing, if the take escalated; otherwise the demo page, Replay, the
**Watch an escalation** button (task `temperature-units`, recorded on 2026-10-28). Let the
replay play: two gate results in red, the orange **Escalated** line, then the steps in purple
for Ultra and the green **Gates passed**.

**Voice:** "Here the work starts on Nemotron Nano. Its change fails the project's tests. It
tries again, and the tests fail a second time, so Stepswitch escalates: Ultra takes over the
edit, and its change passes the gates. Then Ultra reviews the change, and gpt-oss-120b, a
model from another family, gives a second opinion on the same diff."

## 1:30 to 2:15: results and the bill

**Shot:** the demo page's results cards (both mini suites), then the README's results table
and the bill line.

**Voice:** "On our two mini suites, 21 tasks, the ladder and Ultra alone both passed all 21.
The ladder spent 81.6% fewer dollars per task: about one cent against five and a half. It
also sent fewer than half the uncached tokens, because Super and Lightning hit the prompt
cache and Ultra rarely did. The second reviewer agreed with Ultra on 20 of 21 changes. We
publish the whole bill: every hosted bench run, failed ones included, came to two dollars
eighteen on our ledger, and two thirty-eight on the Token Factory console for the whole day."

## 2:15 to 2:35: prove it yourself

**Shot:** `tapes/prove.tape` (terminal): `uv run ssw prove --claim C-029 --claim C-030` ends
with both claims passing; `--render-readme` leaves the README unchanged.

**Voice:** "Every number in the README has a test. Clone the repository and run ssw prove: it
re-checks these claims from the recorded runs, with no key and nothing billed."

## 2:35 to 2:50: close

**Shot:** the demo page header with its URL, then the repository page.

**Voice:** "Stepswitch sends each step of a coding task to the right Nemotron model on Token
Factory, verifies every change with your tests and a reviewer from another model family, and
makes every claim re-runnable. Links below."

## Recording notes

- `python hackathon/tapes/setup_demo.py` sets up the toy project for the live run (the
  Nano-first policy, so a gate failure is likely; `--policy ladder` for the C-029 ladder). A
  take costs about US$ 0.05 to 0.30 and stops at 0.30.
- VHS reads the tapes: `vhs hackathon/tapes/live-run.tape` and `vhs hackathon/tapes/prove.tape`,
  with `NEBIUS_API_KEY` set in the shell for the live run only. The key is never typed on screen.
- The demo page plays a replay with **Play**; **Show all steps** shows the whole run at once.
- Upload as public on YouTube, then put the link in the README's hackathon section ("Video")
  and in the submission form.
