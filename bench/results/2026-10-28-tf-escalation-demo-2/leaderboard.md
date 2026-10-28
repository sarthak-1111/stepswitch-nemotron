# Leaderboard: mini-general

- Results: [`results.jsonl`](results.jsonl) (1 run, 1 task, seeds [0])
- Command: `ssw bench run --suite mini-general --workers router --seeds 1 --tasks billing-month-end --router-pool tokenfactory/nvidia/Nemotron-3_5-Lightning,tokenfactory/nvidia/nemotron-3-super-120b-a12b,tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b,tokenfactory/openai/gpt-oss-120b --max-steps 60 --budget-usd 0.2 --budget-usd-total 0.2 --allow-remote --policy bench/policies/tokenfactory-cheapest-first.toml`
- Hardware: os Windows, arch x86_64, cpu_cores 32, ram_gb 1098.43, gpus 4, gpu_memory_gb [51.53, 48.31, 51.53, 51.53]
- Date: 2026-10-28T03:48:55+00:00
- Version: 0.1.0.dev0 (commit c436b3345384)
- Pass-rate intervals: 95%, cluster bootstrap over tasks (10,000 resamples, seed 0); Wilson score interval with one task.
- Scoring: a run passes when every acceptance command exits with 0 on a fresh copy with the run's diff applied and the suite's protected paths restored.
- Router pool: `tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b`, `tokenfactory/nvidia/Nemotron-3_5-Lightning`, `tokenfactory/nvidia/nemotron-3-super-120b-a12b`, `tokenfactory/openai/gpt-oss-120b`

| Rank | Contestant | Pass rate | 95% interval | Runs | Median wall (s) | Median tokens | Median uncached | Median hosted | GPU-s | Escalations | Cache hits | Changed tests | Reference cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | router | 100% | 21% to 100% | 1 | 170.1 | 514,904 | 221,272 | 514,904 | 0.0 | 0% | 59% | 0 | - |

![Pass rate by contestant](pass-rate.svg)
