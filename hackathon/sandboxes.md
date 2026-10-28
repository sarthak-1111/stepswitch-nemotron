# Token Factory Sandboxes: checked, not yet usable, on the roadmap

StepSwitch's gates run a project's impacted tests and its full test suite after every change.
Running them in a Token Factory Sandbox (a microVM per run) would let the gates run untrusted,
model-written code away from the developer's machine, and run several candidates' test suites
in parallel. This is what we checked during the hackathon, and the design we would build.

## What we found (2026-10-28)

- Sandboxes is in beta. The console's Sandboxes page offers "Request beta access" and says runs
  are free while in beta.
- With the project's API key and project ID, `GET https://api.tokenfactory.nebius.com/sandboxes/v1/whoami`
  answered HTTP 200 with every permission false: `spawn`, `spawn_disposable`, `list`,
  `import`, `cancel`, `set_image_tag`. The limits it reported: an instance runs for at most
  3600 seconds, 50 instances at a time, 12 GiB per image layer.
- So no sandbox could be started from this project, and claim C-031 (gates in a sandbox) was
  not attempted. Requesting beta access is a manual step for the account owner.

The check is a read-only call; `hackathon/FEEDBACK.md` has the details we would like to see
changed (the API key works for inference at once, but Sandboxes needs a separate grant that the
API reports only as `false` flags).

## The design

A gate backend chosen per project in `stepswitch.toml`:

```toml
[gates]
backend = "sandbox"          # or "local" (default)
sandbox_image = "python:3.12-slim"
fallback = "local"           # when the sandbox cannot start
```

For each gate run:

1. Pack the task's worktree (tracked files and the change, no `.git`, no caches) into a tar
   archive, and record its SHA-256.
2. Upload it once per change (`files=` in the Python SDK, keyed by content hash, so a retry or a
   second gate reuses the upload).
3. Start a disposable instance from a prepared image: the project's dependencies installed once
   and saved with `disposable=False` and a tag named after the lock file's hash, so later runs
   start from that state.
4. Run the gate's command (`pytest -q <impacted tests>`, then the full suite) with `shell=` and
   read `exit_code`, `stdout` and `stderr`, which map onto StepSwitch's existing gate results.
5. On a start failure or a missing permission, run the same command locally and mark the gate
   result `ran: local (sandbox unavailable)` in the trajectory.

All of it would go through StepSwitch's egress layer (`stepswitch.net`), so the audit log lists
every upload and call.

## Roadmap

1. Request beta access for the project (account owner).
2. Implement `verify/backends/sandbox.py` behind the existing gate interface, with the local
   backend as fallback, and conformance tests against a recorded mock of the REST API.
3. Claim C-031: on the mini suites, gates run in a Sandbox give the same verdicts as local gates
   on every task run, with the time each took.
4. Then parallel best-of-N candidates, each checked in its own sandbox.
