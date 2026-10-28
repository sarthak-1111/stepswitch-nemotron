# ADR 0045: Bench claims and runs on hosted models

- Status: accepted
- Date: 2026-10-28
- Phase: after 13

## Context

The Token Factory runs of ADR 0044 are bench runs of the mini suites like any other, with a
`router` contestant, and they sit in `bench/results` beside the local runs. Two claim tests read
every run there and failed on the first hosted pilot:

- C-022 compares the newest run with a `router` contestant against Claude Code alone. Its claim
  is about Stepswitch on local models that sends no token to a hosted model, so a hosted run
  became "the newest router run" and the comparison found no shared task runs.
- C-010 requires every HANDOFF brief to be counted exactly with the receiving model's tokenizer.
  Stepswitch has tokenizer files for registry models and a mapping for some names, but none for
  the hosted Nemotron models, so a brief handed to one is counted by estimate (characters / 4).

The pilot's two briefs came from compaction at about 9,000 tokens, because the probe's needle
test (which stops at 16,384 tokens when the server reports no window) was read as the model's
context. That reading is fixed (`catalog._probe_hit_limit`), but a hosted model can still
receive a brief on an escalation with a long transcript.

## Decision

1. The frontier comparison (C-021 to C-023) reads only runs that kept the router on local
   models: a run whose `run.json` has `allow_remote: true` is another experiment.
2. C-010's scope says what is counted exactly: briefs to a model whose tokenizer Stepswitch has.
   A brief to a hosted model with no registry entry, tokenizer or engine is counted by estimate;
   it must still validate, match its rendered Markdown and stay under the limit by that
   estimate, and the evidence lists it under `hosted_estimated`. Every other brief must still
   be exact, as before.
3. The probe's context check caps a model's context only where it found a limit: a lost needle
   or the server's own window. Finding every needle up to the test's cap shows the model works
   that far, not that its context ends there.

## Consequences

- Hosted runs can share `bench/results` with local runs without changing what the local claims
  measure.
- C-010 says less about hosted receivers than about local ones, openly: their counts are
  estimates until a tokenizer for them is verified and added to the mapping.
- Hosted models with a declared context of a million tokens are no longer compacted at about
  nine thousand.
