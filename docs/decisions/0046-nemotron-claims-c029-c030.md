# ADR 0046: The Nemotron claims C-029 and C-030, and how their wording was chosen

- Status: accepted
- Date: 2026-10-28
- Phase: after 13

## Context

The hackathon work needs two claims on Token Factory: the Nemotron ladder against Nemotron 3
Ultra alone (C-029), and a finding about the cross-family reviewer and the small tier (C-030).
Both were registered after the runs, so their wording and thresholds were chosen with the data
in view. This ADR records what the first drafts said and why they changed, so the choice is
open to review.

## Decision

1. **C-029.** The runs are `2026-10-28-tf-mini-general` and `2026-10-28-tf-mini-science`: both
   contestants interleaved on Token Factory, one task run per task, the ladder policy in
   `bench/policies/tokenfactory-ladder.toml`. The first draft said "for under half of its
   dollars". Both contestants passed 21 of 21 task runs and the ladder's dollars were 18.4% of
   Ultra's, with a 95% cluster-bootstrap interval over tasks of 13.8% to 23.6% (seeded, so it is
   the same on every re-run). The claim says "under a quarter" (threshold 25%), which the whole
   interval meets. The threshold is not set at the interval's edge.
2. **C-030.** The first draft claimed agreement on every change both reviewers saw and no more
   tool errors than Ultra on all the small tier's steps (navigate, read, summarize). The data:
   - the reviewers agreed on 20 of 21 changes; Ultra blocked one change that passed its tests and
     the second reviewer approved it;
   - on navigate steps 10 of Lightning's 71 tool calls returned errors against none of Ultra's
     61 (absolute paths, corrected after the tool's message);
   - Ultra alone ran 3 read steps against Lightning's 5, too few to compare;
   - summarize: 21 calls each, no cut-off calls on either side, Lightning at 6.8% of Ultra's
     dollars per call.

   The claim was narrowed before registration to what holds: agreement on at least 95% of the
   changes both reviewed, and summarize steps with no more cut-off calls than Ultra at under a
   tenth of its dollars per call. The navigate and read numbers stay in the evidence and in the
   scope, as findings, not claims.
3. **Reported, not claimed.** Lightning alone on the same tasks ran in separate runs after the
   main runs (`2026-10-28-tf-mini-*-lightning`), not interleaved with the others, so it is
   evidence context for C-030 and appears in the submission text, not in a claim.
4. **Escalation demo.** No task of the C-029 runs escalated. The demo policies
   `tokenfactory-cheapest-first.toml` and `tokenfactory-nano-first.toml` are the ladder with the
   work steps starting on a smaller model (a unit test keeps every other rule equal), used only to
   show an escalation. Their runs are committed and counted in the bill, and no claim uses them.

## Consequences

- Both claims hold on the committed runs and are re-checked by `ssw prove` on every CI run.
- A re-run with new data that misses a threshold fails the claim; the wording is then narrowed
  with another ADR, never the test.
