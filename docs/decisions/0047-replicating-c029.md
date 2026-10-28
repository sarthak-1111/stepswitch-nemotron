# ADR 0047: Replicating C-029, and the runs a long-path bug spoiled

- Status: accepted
- Date: 2026-10-28
- Phase: after 13

## Context

C-029's wording was chosen with its runs in view (ADR 0046). A second pair of runs, with the
claim's thresholds fixed before they are made, shows whether the result holds on new data. It
also runs on a later commit, after the tool fixes made since C-029 (container-style paths, `cd
<dir> &&`, edits copied with read's line prefixes, JSON strings of edits).

The first attempt, `2026-10-28-tf-mini-general-replication` and
`2026-10-28-tf-mini-science-replication` on commit `3802071`, passed every task run on both
sides (21 of 21 each), but its step records showed a problem on Ultra alone's side:

- the protected gate ended with an error on all six science task runs, so the agent was told
  verification failed, finished again, failed again and stopped as `gates_failed` (the bench's
  scorer still passed the diffs); the last one ran into the run's dollar cap;
- on three general task runs the gates could not tell the changed files and ran the whole
  suite.

The gate's message was "cannot resolve the base revision". Git for Windows stops at 260
characters unless `core.longpaths` is set, and the gates' read-only git queries did not set
it (the worktree pool and the bench workspaces did). A task worktree lives under
`.stepswitch/bench/<run>/<contestant>/<task>/s0/repo`; with Ultra's 46-character contestant
name, the replication's longer run names and the longer task names, the paths of its git
objects passed 260 characters ("unable to open loose object ...: Filename too long"). The
ladder's contestant is `router`, so its side never reached the limit. C-029's runs have shorter
names, and their step records show no such error and every changed-file set known.

## Decision

1. Fix the cause: the gates' git helper and the prompt's file listing pass `core.longpaths` on
   Windows (`fix(verify): git queries take long paths on Windows`), with a test that resolves
   the base commit of a checkout whose git paths pass 260 characters.
2. The first attempt's runs stay committed and in the bill; no claim uses them. Their science
   half overstates Ultra's dollars (the ladder came to 8.7% of Ultra's there, against 14.2% in
   C-029), so it would flatter the ladder. On the general suite, where three of Ultra's task
   runs only lost the impacted-test selection, the ladder came to 19.7% of Ultra's dollars
   (C-029: 20.4%); that is reported as context only.
3. Claim C-032 names the second attempt, `2026-10-28-tf-mini-general-replication-2` and
   `2026-10-28-tf-mini-science-replication-2`, made on the commit that registers this ADR or a
   later one, with C-029's thresholds unchanged: at least as many task runs passed as Ultra
   alone, and the ladder's dollars below 25% of Ultra's with the whole 95% interval. The claim,
   its test and this ADR are committed before the runs start.
4. If the runs miss a threshold, the claim fails and is reported as failing, or narrowed with
   another ADR; the test and the thresholds stay as they are.

## Consequences

- C-032 is the first claim of this project registered before its data.
- C-029's comparison is a function (`tests/claims/test_c029_nemotron_ladder.compare`) that
  both claims call, so a replication is checked exactly as the original is.
- The bill grows by both attempts, and the evidence of C-029 lists them run by run.
