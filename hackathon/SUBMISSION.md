# Stepswitch

**Each step of a coding task on the right Nemotron model, checked by your tests and a reviewer
from another model family, with every claim re-runnable.**

- Track: **Coding and Agentic Engineering**
- Repository: https://github.com/sarthak-1111/stepswitch-nemotron (MIT)
- Demo: https://sarthak-1111.github.io/stepswitch-nemotron/ (read-only replays, no login)
- Video: link added at upload
- Feedback on Token Factory, Sandboxes and Nemotron: [FEEDBACK.md](FEEDBACK.md)

Stepswitch sends each step of a coding task to the right Nemotron model on Token Factory,
verifies every change with your tests and a reviewer from another model family, and makes every
claim re-runnable with `ssw prove`.

## The numbers

On the two mini bench suites (21 tasks: small bug fixes, features, refactors and numerical tasks
in Python), the Nemotron ladder and Nemotron 3 Ultra alone ran interleaved on Token Factory, one
task run per task, with the same gates. From the evidence of claim C-029
([claims/evidence/C-029.json](../claims/evidence/C-029.json)):

| | Nemotron ladder | `Nemotron-3-Ultra-550b-a55b` alone |
|---|---:|---:|
| Task runs passed | 21 of 21 | 21 of 21 |
| US dollars per task run | 0.0101 | 0.0551 |
| Tokens per task run, cached included | 47,156 | 53,067 |
| Uncached tokens per task run | 22,878 | 50,787 |
| Minutes per task run | 0.75 | 0.68 |
| Escalations | 0 | 0 |

- The ladder spent 81.6% fewer dollars per task run. Its share of Ultra's dollars was 18.4%,
  with a 95% cluster-bootstrap interval over tasks of 13.8% to 23.6%.
- Per suite: general 0.0106 against 0.0522 dollars per task run, science 0.0089 against 0.0626.
- Where the ladder's dollars went: Super 80.0% (151 calls), Ultra 16.0% (42 calls), Lightning
  2.8% (47 calls), the second reviewer 1.2% (21 calls).
- Reviews (claim C-030): `gpt-oss-120b` agreed with Ultra's verdict on 20 of the 21 changes
  both reviewed. Every reviewed change had already passed its tests (reviews run after the
  gates), so this is agreement on passing changes.
- The ladder took a little longer per task run than Ultra alone (0.75 against 0.68 minutes).

## Inspiration

A coding agent makes dozens of model calls per task, and most of them are small: find a file,
read it, condense a test log. Agents still send every call to one model, usually the largest, and
report a pass rate without the bill. We wanted an agent that picks the model per step, proves
the change with the project's own tests, has the change checked by a second model family, and
publishes only numbers that anyone can re-run.

## What it does

- **Per-step routing.** Each step of a task has a type: plan, navigate, read, edit, run,
  triage, review, summarize. A policy file maps step types to models. The Nemotron ladder on
  Token Factory:
  - `nvidia/Nemotron-3_5-Lightning` navigates, reads, summarizes and writes short text;
  - `nvidia/nemotron-3-super-120b-a12b` edits, runs the tests and triages failures;
  - `nvidia/Nemotron-3-Ultra-550b-a55b` plans, reviews, and takes the work over when the gates
    fail twice on Super;
  - `openai/gpt-oss-120b` gives a second opinion on each of Ultra's reviews.
- **Gates.** After a change, the project's format, lint, type and test gates run (impacted tests
  first, then the full suite; science projects add numerical golden checks and protected
  constants). A change that fails goes back with the failure report; after two failures on one
  model, the task escalates up the ladder.
- **Dollars as a first-class budget.** Prices per model come from Token Factory's model list
  (`GET /v1/models?verbose=true`, which includes pricing). The ledger records each call's model,
  tokens, cached tokens and dollars; `--budget-usd` stops a task at a dollar cap and
  `--budget-usd-total` stops a bench run.
- **Claims you can re-run.** Each public claim has a test. `ssw prove` runs the tests, writes the
  evidence and renders the README's numbers from it; the README lint fails on any number typed
  by hand. The C-029 table above is regenerated from the committed runs with
  `uv run ssw prove --claim C-029`.
- **A demo you can audit.** The demo page replays the recorded Token Factory runs side by side,
  step by step: the model of each step, its tokens, its dollars, the gate results and the
  reviews.

## How we built it

- Python 3.11, uv, Typer (`ssw`), Pydantic v2, SQLite in WAL mode, httpx; a React dashboard for
  local use; the public demo is a static page built from the committed runs and published by a
  GitHub Actions workflow.
- A compatibility layer speaks the chat-completions, responses, messages and generate-content
  formats. Token Factory is a provider preset (`registry/providers/tokenfactory.toml`): base URL,
  bearer key from `NEBIUS_API_KEY`, the model IDs, list prices and the reasoning efforts each
  model accepts. We probed each model with `ssw probe` (tool calls, parallel calls, JSON Schema,
  streaming, usage, reasoning fields, prompt cache, context) and recorded the results in
  `probes/` and `docs/COMPATIBILITY.md`.
- Escalation-aware policy rules (`when = { step_type = [...], escalations = 0 }`) and a
  second-opinion review from another model family.
- The bench runs contestants interleaved on the same tasks under a dollar cap, writes each step
  to `steps.jsonl`, and records the policy and prices in `run.json`, so every number in this
  file traces back to committed files.

## Challenges we ran into

- **Thinking that effort does not bound.** In reviews, Ultra used its whole 4,000-token output
  cap on thinking at `low` and at `medium` effort and never wrote a verdict; at `none` it
  answered in 12 tokens. The ladder now reviews without thinking.
- **Truncated thinking in the answer.** When the output cap cuts a reply mid-thought, the
  unfinished thinking comes back in `content`. A summary step on Lightning with a 300-token cap
  returned its thinking as the summary. Summaries now run at effort `none`.
- **Different usage and reasoning fields per model**, and a reviewer model that rejects effort
  `none`: the codec reads both reasoning field names and top-level cache counters, and the
  registry records which efforts each model accepts so the router asks for the nearest one.
- **Windows file locks and long paths** during bench runs (the bench copies a repository per
  task run): retries on refused copies and deletes, and long paths turned on in the bench's
  git config.
- **Sandboxes** answered with every permission false for our project (beta access not granted),
  so the sandboxed gate backend stayed a design ([sandboxes.md](sandboxes.md)).

## Accomplishments that we're proud of

- The same pass rate as Ultra alone on both suites at 18.4% of its dollars per task run, from
  runs anyone can inspect step by step.
- A second reviewer from another family that disagreed with Ultra once in 21 changes, on a
  design question in a change that passed its tests, which is the kind of call a second opinion
  is for.
- Every number in the README rendered from evidence, and claims that fail are narrowed or
  withdrawn in the open (`claims/claims.yaml`, `docs/decisions/`).
- The whole bench bill for this submission is recorded run by run, failed and calibration runs
  included (below).

## What we learned

- **Most calls do not need the largest model.** Lightning ran the summaries with no cut-off
  calls, as Ultra did, at 6.8% of Ultra's dollars per call, over 21 calls each.
- **The money is in the edit loop.** Super made 151 of the ladder's 261 calls and took 80.0% of
  its dollars. The next saving is there, not in planning or review.
- **Prompt caching matters as much as model size.** Over these runs Super's input came from the
  prompt cache in 61.7% of tokens and Lightning's in 51.4%, Ultra's in 3.6%. The ladder sent
  fewer than half of Ultra alone's uncached tokens per task run.
- **Small models fail differently.** On navigate steps 10 of Lightning's 71 tool calls returned
  errors, against none of Ultra's 61: it guessed absolute paths such as `/repo/todo/model.py`,
  read the tool's message ("paths are relative to the repository root") and corrected itself.
  No task failed because of it. Clear tool errors are part of the routing design.
- **The smallest model alone is not the low-cost choice it looks like.** Lightning alone, on the
  same 21 tasks in separate runs, passed 19 (both failures ran out of steps at 40). It cost
  US$ 0.0071 per task run, 70% of the ladder's 0.0101, but used 130,369 tokens per task run:
  2.8 times the ladder's 47,156 and 2.5 times Ultra alone's 53,067. On the science suite it
  cost more per task run than the ladder (0.0100 against 0.0089) and took 1.24 minutes against
  0.65. Of the three, the ladder used the fewest tokens per task run.

## What's next

- Gates in Token Factory Sandboxes, with the local gates as fallback, and claim C-031: the same
  verdicts as local gates on every task run ([sandboxes.md](sandboxes.md)).
- A ladder that learns from these step records which step types each model handles, per
  repository, and the Nano tier for the shortest steps.
- The ladder on SWE-bench Verified Mini, which so far ran on a local model only.
- The mini suites again with the tool fixes above, to measure how many of Lightning's refused
  tool calls (and the turns spent on them) they remove.
- A live button on the demo, behind a rate-limited function that holds the key
  ([DEPLOY.md](DEPLOY.md)).

## Beyond Token Factory: SWE-bench Verified Mini on a local model

Before the hackathon work, Stepswitch and mini-SWE-agent each ran once on SWE-bench Verified Mini
with the same local open-weight model (`gpt-oss:120b`), graded by the official harness (claims
C-026 to C-028). Stepswitch resolved 24 of 49 instances and mini-SWE-agent 7. Most of the gap is
robustness: the model server ended 24 of mini-SWE-agent's runs and 1 of Stepswitch's. On the
instances where no server error ended either run, Stepswitch resolved 29.2% and mini-SWE-agent
25.0%. Stepswitch used 32.3% fewer tokens per instance, counting cached tokens.

## The bill

Every hosted bench run of this submission, by Stepswitch's ledger at list prices (the C-029
evidence recomputes this table from the committed result rows):

| Bench run | What it was | Task runs | US$ |
|---|---|---:|---:|
| `2026-10-28-mini-general-nemotron-pilot` | first pilot; stopped at run 4 of 10 on a Windows path-length error | 3 | 0.0321 |
| `2026-10-28-tf-pilot` | pilot, five mini-general tasks, ladder against Ultra alone | 10 | 0.3623 |
| `2026-10-28-tf-general` | first full run; stopped at run 2 of 30 on a Windows file lock | 1 | 0.0036 |
| `2026-10-28-tf-science` | first science run; no hosted model was eligible, nothing called | 12 | 0.0000 |
| `2026-10-28-tf-mini-general` | C-029, general suite | 30 | 0.9421 |
| `2026-10-28-tf-mini-science` | C-029, science suite | 12 | 0.4289 |
| `2026-10-28-tf-mini-general-lightning` | Lightning alone, general suite | 15 | 0.0889 |
| `2026-10-28-tf-mini-science-lightning` | Lightning alone, science suite | 6 | 0.0598 |
| `2026-10-28-tf-escalation-demo` | cheapest-first demo; no escalation | 1 | 0.0282 |
| `2026-10-28-tf-escalation-demo-2` | cheapest-first demo; no escalation | 1 | 0.0278 |
| `2026-10-28-tf-escalation-demo-nano` | Nano-first demo; both tasks escalated to Ultra | 2 | 0.2050 |
| **All bench runs** | | | **2.1787** |

The Token Factory console (Billing, Transactions, read 2026-10-28 04:12 UTC) showed US$ 2.38 of
consumption, tax included, for every call on the account: the bench runs above, the probes of
five models, a few direct API checks, two live test runs outside the bench (a toy `ssw run`,
US$ 0.0111, and the README quickstart in a fresh clone, US$ 0.0105), and the first pilot's
fourth task run, which ended without a result row. The account started with US$ 5.00 and had
US$ 2.62 left. `hackathon/bill.json` records the reading.

## What changed during the submission period

The submission period opened on 2026-08-26. Stepswitch's first commit, `e833c99`, is dated
2026-10-16, so the whole project was built during the period
([COMPLIANCE.md](COMPLIANCE.md) has the log). The Token Factory and Nemotron work for this
submission is the commit range `de1cf95..hackathon-2026-10`:

- hosted provider presets with per-model prices and reasoning efforts, dollar budgets per task
  and per bench run (ADR 0044);
- escalation-aware policy rules and a second-opinion review from another model family;
- the Token Factory preset, probes of the Nemotron models and the reviewer, and the Nemotron
  ladder policy;
- bench support for hosted runs (interleaving, dollar caps, step records) and fixes from the
  pilots;
- claims C-029 and C-030 with their evidence, the demo page, and this package;
- `ssw policy check`, which shows the worker each step type goes to, before and after an
  escalation, and flags rules that match no configured worker, without calling a model;
- tool fixes drawn from the refused tool calls in the recorded runs: container-style absolute
  paths, `cd <dir> &&` in `run`, edits sent as a JSON string with a stray bracket, and old text
  copied from read output with its row prefixes. These are tested; the recorded runs predate
  them, so no number on this page reflects them.

## Built with

python, uv, typer, fastapi, pydantic, sqlite, httpx, pytest, react, vite, typescript,
nemotron, token-factory, gpt-oss, github-actions, github-pages
