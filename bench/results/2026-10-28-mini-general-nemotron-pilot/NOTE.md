# A stopped pilot

The first Token Factory pilot: five mini-general tasks, the Nemotron ladder (`router`) and
Nemotron 3 Ultra alone. It stopped at run 4 of 10, after Ultra had finished the task, when the
bench's `git add` in the scoring copy failed with "Filename too long": the workspace path passed
Windows' 260-character limit. Bench git now runs with `core.longpaths` (commit 7f3da64).

Three finished runs are in `results.jsonl`; the fourth task run is in the ledger but has no row.
The run also used a local model to classify tasks for the Ultra contestant, which made the
contestants unequal. It is kept for the bill (`hackathon/FEEDBACK.md`), not as evidence; the
calibration run is `2026-10-28-tf-pilot`, and claim C-029 reads the runs its thresholds name.
