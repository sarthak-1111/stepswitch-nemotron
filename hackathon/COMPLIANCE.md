# Submission compliance checklist

Event: Nebius x NVIDIA Global AI Hackathon, Coding and Agentic Engineering track.
Read on 2026-10-28 from the official pages:
[overview](https://nebiusglobalaihackathon.devpost.com/),
[rules](https://nebiusglobalaihackathon.devpost.com/rules),
[FAQs](https://nebiusglobalaihackathon.devpost.com/details/faqs),
[resources](https://nebiusglobalaihackathon.devpost.com/resources).

Key dates (rules §1): submission period from Wed 2026-08-26 09:00 PT to **Fri 2026-10-30 10:00 PT**
(= Sat 2026-10-31 02:00 JST). Judging from 2026-12-01 to **2026-12-15 12:00 PT**. Winners around
2027-01-11. Our own target: submit by 2026-10-30 23:00 JST.

Legend: ✅ done and checked · 🟡 in progress · 👤 the entrant does it by hand.

## Platform and model requirements

| # | Requirement (source) | How Stepswitch meets it | Status |
|---|---|---|---|
| 1 | "must run on either Nebius Token Factory or Nebius AI Cloud and use at least one NVIDIA open source model" ([overview](https://nebiusglobalaihackathon.devpost.com/)) | Every model call of the Nemotron ladder goes to the Token Factory chat-completions API at `https://api.tokenfactory.nebius.com/v1/`. Models: `nvidia/Nemotron-3_5-Lightning`, `nvidia/nemotron-3-super-120b-a12b`, `nvidia/Nemotron-3-Ultra-550b-a55b` (IDs from `GET /v1/models`, 2026-10-28). | 🟡 |
| 2 | "Runs on Nebius Token Factory … means the project makes a runtime call to the Token Factory inference API" ([rules §4](https://nebiusglobalaihackathon.devpost.com/rules)) | `ssw run` calls the API at run time; the ledger records each call with its model, tokens and dollars. | 🟡 |
| 3 | The same NVIDIA model through another provider does not count ([FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs)) | The endpoint is `tokenfactory` only; no other hosted provider is configured for the ladder. | 🟡 |
| 4 | Track fit: "agents that write, run, and test code in Token Factory" ([rules §4](https://nebiusglobalaihackathon.devpost.com/rules)) | Stepswitch is a coding agent: it plans, edits, runs tests and reviews, each step on a Nemotron model on Token Factory. | ✅ |

## What to submit (rules §4, "Submission Requirements")

| # | Requirement | Where | Status |
|---|---|---|---|
| 5 | A working demo URL, hosted application or test build, free and without restriction **until judging ends (2026-12-15)** | [hackathon/DEPLOY.md](DEPLOY.md) | 🟡 |
| 6 | A text description of features and functionality | [hackathon/SUBMISSION.md](SUBMISSION.md) | 🟡 |
| 7 | A public repository on GitHub, GitLab or Bitbucket with all source, assets and instructions | `sarthak-1111/stepswitch-nemotron` | 👤 create, then 🟡 push |
| 8 | An open-source licence file, "detectable and visible at the top of the repository page (in the About section)" | [LICENSE](../LICENSE) (MIT) at the root | ✅ file; 👤 check the About box |
| 9 | A README with setup instructions and clear guidance for running the project | [README.md](../README.md), section "Built for the Nebius x NVIDIA Global AI Hackathon" | 🟡 |
| 10 | The README highlights how NVIDIA Nemotron is used, where Token Factory accelerated the workflow, and any other Nebius tools used | same section: model table, results, bill | 🟡 |
| 11 | A demo video **under 3 minutes**, public on YouTube, showing the project working and how Token Factory and Nemotron are used; no third-party trademarks or copyrighted music without permission | [hackathon/VIDEO.md](VIDEO.md) (script, shot list, tapes) | 🟡 script; 👤 record and upload |
| 12 | The track is named | Coding and Agentic Engineering | 👤 in the form |
| 13 | Feedback on Nebius Token Factory, AI Cloud and NVIDIA tools or models used | [hackathon/FEEDBACK.md](FEEDBACK.md) | 🟡 |
| 14 | If the project existed before the submission period, what was significantly updated during it | [hackathon/SUBMISSION.md](SUBMISSION.md), "What changed during the submission period" | 🟡 |
| 15 | City: only for entrants who attended an in-person Builders & Brews event | We did not attend; **leave the city field empty** | 👤 |
| 16 | All materials in English | all files | ✅ |

## Built during the submission period

`git log --reverse --format='%ad %h %s' | head`, run on 2026-10-28 in a fresh clone of
`sarthak-1111/stepswitch`:

```
Fri Oct 16 13:01:09 2026 +0900 e833c99 docs: spec and repository settings
Fri Oct 16 13:01:10 2026 +0900 594944d build: uv project for Phase 0 tooling
Fri Oct 16 13:01:11 2026 +0900 b821661 test: claims registry, integrity meta-tests and repository hygiene
Fri Oct 16 13:01:11 2026 +0900 5584391 build: phase checks for phases 0-4
Fri Oct 16 13:01:12 2026 +0900 92a660b docs: Phase 0 research, architecture and decisions
Fri Oct 16 13:01:13 2026 +0900 1b30140 docs: spec v0.3 with Phase 0 research applied
Fri Oct 16 13:01:13 2026 +0900 348d20b docs: Phase 0 progress
Fri Oct 16 14:24:37 2026 +0900 16327c8 chore: rename the project to Stepswitch, CLI ssw (ADR 0001)
Fri Oct 16 14:24:53 2026 +0900 106ebba build: package skeleton, runtime dependencies and hatchling build
Fri Oct 16 14:24:53 2026 +0900 9c8953f test: Phase 1 claim tests for C-004, C-007 and C-016
```

The first commit, `e833c99`, is dated 2026-10-16, after the submission period opened on
2026-08-26. The Token Factory and Nemotron work for this submission starts after `de1cf95`, the
last commit of the original repository; SUBMISSION.md gives the exact range.

## Prizes we aim for (rules §8)

- Overall awards (Grand Prize, 2nd, 3rd), or the Coding and Agentic Engineering track award. A
  project can win one overall award *or* one track award, plus one bonus award.
- Most Valuable Feedback (bonus, ten winners): judged on "completeness, viability, and potential
  impact of the feedback" (rules §6).

## Judging criteria (rules §6, equally weighted)

| Criterion | Our evidence |
|---|---|
| Technological Implementation: how well it is built and how effectively it uses Token Factory and Nemotron | per-step Nemotron ladder; prices from the API in the ledger; probes of each model; re-runnable claims |
| Design: a complete, coherent product, not a proof of concept | CLI, dashboard, public demo, installers, docs site, CI on three OSes |
| Potential Impact: a real problem for a real audience, demonstrated | the cost and reliability of coding agents, with measured dollars per task |
| Quality of the Idea: a creative, non-obvious use of Token Factory and Nemotron | routing inside a task across Nemotron sizes, checked by tests and a reviewer from another family |

Stage One is pass/fail on fit with the track and use of the required APIs; Stage Two scores the
four criteria. Judges are not required to run the project and may judge from the description,
images and video alone, so the video and SUBMISSION.md carry the case.
