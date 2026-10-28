# ADR 0048: C-032 withdrawn: the replication missed its registered bound

- Status: accepted
- Date: 2026-10-28
- Phase: after 13

## Context

C-032 was registered before its runs (ADR 0047, commit `4ad5e18`, pushed before the first
task run): C-029 made again with the same contestants, pool, policy and caps, holding when the
ladder passes at least as many task runs as Ultra alone and its dollars' share of Ultra's, with
the whole 95% cluster-bootstrap interval over tasks, lies below 25%.

The runs, `2026-10-28-tf-mini-general-replication-2` and
`2026-10-28-tf-mini-science-replication-2`, next to C-029's (evidence in
`claims/evidence/C-032.json` and `C-029.json`):

| | C-029 | C-032 |
|---|---:|---:|
| Task runs passed, ladder / Ultra alone | 21 / 21 of 21 | 21 / 21 of 21 |
| Dollars per task run, ladder | 0.0101 | 0.0108 |
| Dollars per task run, Ultra alone | 0.0551 | 0.0600 |
| Ladder's share of Ultra's dollars | 18.4% | 18.0% |
| 95% interval | 13.8% to 23.6% | 12.1% to 27.7% |

The pass counts and the point estimate replicated; the interval did not stay below 25%. One
task widened it: on `vectorize-gaussian-sum` the ladder spent 0.0489 against Ultra's 0.0630
(77.6%; 15.4% in C-029). Super's replies on its edit steps stopped at the output cap four
times (`finish_reason: length`) and two of its edits were refused. After the fourth cut-off
reply, which had no tool call, the gates ran and the golden gate failed; Super finished the
change at step 19 of 22. No task escalated.

## Decision

1. C-032 is withdrawn (`withdrawn_by` this ADR). Its wording, thresholds, test and evidence
   stay in the registry; `ssw prove` no longer runs it and the README does not show it.
2. No third pair of runs is made for this claim, and its threshold is not moved: a bound chosen
   after seeing the interval would not be a replication.
3. C-029 stays as worded. It is scoped to its own runs and its test still passes on them. The
   submission text reports the replication next to it: the same pass counts and point
   estimate, an interval reaching 27.7%, and the task that caused it.
4. The cause on that task is the output cap on Super's thinking, already the second ask in
   `hackathon/FEEDBACK.md`; the step records of both runs are its evidence.

## Consequences

- "Under a quarter of Ultra's dollars" holds on C-029's runs only. Across both pairs of runs
  the ladder's share was 18.4% and 18.0%, and one task in 21 can move the upper end of the
  interval past 25%.
- A future claim of this kind needs more tasks or seeds per suite before it is registered, so
  that one task cannot move its interval this far.
