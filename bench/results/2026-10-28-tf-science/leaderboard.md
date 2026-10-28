# Leaderboard: mini-science

- Results: [`results.jsonl`](results.jsonl) (12 runs, 6 tasks, seeds [0])
- Command: `ssw bench run --suite mini-science --workers router,tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b --seeds 1 --router-pool tokenfactory/nvidia/Nemotron-3_5-Lightning,tokenfactory/nvidia/nemotron-3-super-120b-a12b,tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b,tokenfactory/openai/gpt-oss-120b --budget-usd 0.5 --budget-usd-total 0.6 --allow-remote --interleave --policy examples/tokenfactory/stepswitch.toml`
- Hardware: os Windows, arch x86_64, cpu_cores 32, ram_gb 1098.43, gpus 4, gpu_memory_gb [51.53, 48.31, 51.53, 51.53]
- Date: 2026-10-28T03:12:46+00:00
- Version: 0.1.0.dev0 (commit b3473a98ffe1)
- Pass-rate intervals: 95%, cluster bootstrap over tasks (10,000 resamples, seed 0); Wilson score interval with one task.
- Scoring: a run passes when every acceptance command exits with 0 on a fresh copy with the run's diff applied and the suite's protected paths restored.
- Router pool: `tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b`, `tokenfactory/nvidia/Nemotron-3_5-Lightning`, `tokenfactory/nvidia/nemotron-3-super-120b-a12b`, `tokenfactory/openai/gpt-oss-120b`

| Rank | Contestant | Pass rate | 95% interval | Runs | Median wall (s) | Median tokens | Median uncached | Median hosted | GPU-s | Escalations | Cache hits | Changed tests | Reference cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | router | 0% | 0% to 0% | 6 | 1.6 | 0 | 0 | 0 | 0.0 | 0% | - | 0 | - |
| 2 | tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b | 0% | 0% to 0% | 6 | 1.9 | 0 | 0 | 0 | 0.0 | 0% | - | 0 | - |

![Pass rate by contestant](pass-rate.svg)
