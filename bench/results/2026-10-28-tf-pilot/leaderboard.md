# Leaderboard: mini-general

- Results: [`results.jsonl`](results.jsonl) (10 runs, 5 tasks, seeds [0])
- Command: `ssw bench run --suite mini-general --workers router,tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b --seeds 1 --tasks pager-first-page,notes-corrupt-file,billing-month-end,recipe-scaling,todo-priority --router-pool tokenfactory/nvidia/Nemotron-3_5-Lightning,tokenfactory/nvidia/nemotron-3-super-120b-a12b,tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b,tokenfactory/openai/gpt-oss-120b --budget-usd 0.5 --budget-usd-total 1.5 --allow-remote --interleave --policy examples/tokenfactory/stepswitch.toml`
- Hardware: os Windows, arch x86_64, cpu_cores 32, ram_gb 1098.43, gpus 4, gpu_memory_gb [51.53, 48.31, 51.53, 51.53]
- Date: 2026-10-28T02:58:57+00:00
- Version: 0.1.0.dev0 (commit 6059b7eca2d2)
- Pass-rate intervals: 95%, cluster bootstrap over tasks (10,000 resamples, seed 0); Wilson score interval with one task.
- Scoring: a run passes when every acceptance command exits with 0 on a fresh copy with the run's diff applied and the suite's protected paths restored.
- Router pool: `tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b`, `tokenfactory/nvidia/Nemotron-3_5-Lightning`, `tokenfactory/nvidia/nemotron-3-super-120b-a12b`, `tokenfactory/openai/gpt-oss-120b`

| Rank | Contestant | Pass rate | 95% interval | Runs | Median wall (s) | Median tokens | Median uncached | Median hosted | GPU-s | Escalations | Cache hits | Changed tests | Reference cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b | 100% | 100% to 100% | 5 | 45.2 | 39,288 | 39,288 | 39,288 | 0.0 | 0% | 0% | 0 | - |
| 2 | router | 100% | 100% to 100% | 5 | 48.8 | 37,764 | 16,270 | 37,764 | 0.0 | 0% | 57% | 0 | - |

![Pass rate by contestant](pass-rate.svg)
