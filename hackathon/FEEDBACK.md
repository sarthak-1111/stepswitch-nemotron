# Feedback on Token Factory, Sandboxes and Nemotron

From building Stepswitch's Nemotron ladder on Token Factory and benchmarking it on 2026-10-28.
Every number below comes from files in this repository: the step records of each bench run
(`bench/results/<run>/steps.jsonl`, one line per model call, tool call, gate run and review),
the probe results (`probes/*--tokenfactory.json`) and the notes in `docs/RESEARCH.md`
("Verified after Phase 13: Token Factory"). In all: nine hosted bench runs with 1,180 model calls
on Token Factory, the probes of five models, and a handful of direct API checks.

## The asks, by the dollars or failures they would save

| # | Ask | What we measured | Impact |
|---|---|---|---|
| 1 | Prompt caching on Nemotron 3 Ultra | Ultra alone: 4.5% of 1,071,517 input tokens came from the cache, against 61.1% for Super in the same agent loops | Ultra alone's runs would have cost 46.1% less at Super's cache share |
| 2 | A thinking budget that holds | At `low` and `medium` effort Ultra spent a whole 4,000-token cap thinking and wrote no review verdict, 5 times out of 5 | Each such call bills 4,000 output tokens at the output price and returns nothing usable |
| 3 | Keep cut-off thinking out of `content` | A reply cut off mid-thought returns the unfinished thinking as the answer | A client shows the model's thoughts as its summary with `finish_reason: length` as the only sign |
| 4 | One usage schema for every model | Five models, five different shapes of `usage`; Nano reports neither cached nor reasoning tokens | Every client needs per-model parsing to bill correctly |
| 5 | Advertise the efforts each model accepts | Nemotron models accept six effort levels; `gpt-oss-120b` answers HTTP 400 to `none` and `minimal` | A router that sets one effort for every model breaks on one of them |
| 6 | A usage view that keeps up with the balance | The Usage page was two hours behind while the balance had dropped by US$ 2.10 | Nobody can tell which run cost what during a timed event |
| 7 | Say why Sandboxes is off | `whoami` answers HTTP 200 with every permission `false` and no message | We found the beta-access step only by reading the console |
| 8 | Lightning: follow the system prompt, use relative paths | Lightning failed the probe's system-prompt check; 10 of its 71 tool calls on navigate steps used absolute paths | Avoidable turns, and a system prompt that may not hold |

## What worked well

- **Onboarding.** The API key answered HTTP 200 on the first `GET /v1/models`. With
  `?verbose=true` the list gives each model's context length, quantization, supported features,
  per-request limits and **prices per token**. Our ledger reads those prices, so the dollar
  figures in our claims come from Token Factory's own numbers rather than a hand-copied table.
- **Tool calling.** All five models we used (`nvidia/Nemotron-3_5-Lightning`,
  `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, `nvidia/nemotron-3-super-120b-a12b`,
  `nvidia/Nemotron-3-Ultra-550b-a55b`, `openai/gpt-oss-120b`) returned native `tool_calls`,
  JSON Schema output and streamed tool arguments in our probes. All four Nemotron models made
  parallel tool calls and honoured a forced `tool_choice`.
- **No rate-limit errors, no retries.** Of the 1,227 calls in our ledger (the bench calls plus
  a live test run), 1,225 succeeded on the first attempt and the other two record no attempt
  count; no task run failed over to another model. The per-model limits in the response
  headers (1000 requests per minute for Lightning, Super and Ultra) were far above what an
  agent needs.
- **Latency was steady.** Median seconds per call over the bench runs: gpt-oss-120b 1.26,
  Lightning 1.95, Ultra 2.20, Super 2.66 (90th percentile 3.39, 5.53, 3.28 and 5.72). Nano was
  the exception (below).
- **Prices that make routing worth it.** Ultra's list price is 16.7 times Lightning's for input
  and 12.5 times for output. With the ladder, the same 21 tasks passed at 18.4% of Ultra alone's
  dollars (claim C-029).

## Token Factory

### 1. Prompt caching on Ultra

- Over the two C-029 runs, Ultra alone sent 1,071,517 input tokens over 21 task runs; 47,872 of
  them (4.5%) were served from the cache. In the same runs, Super, working in the same agent
  loop with the same growing context, had 61.1% of its input served from the cache.
- Our probe sent the same 1,416-token prompt twice in a row to Ultra: 0 cached tokens on the
  second request. The same probe on `gpt-oss-120b`: 1,232 of 1,251 tokens cached.
- Input was 88.9% of Ultra alone's dollars. At Super's cache share and the listed cached price
  (US$ 0.12 per million against 1.00), the same tokens would have cost US$ 0.6242 instead of
  1.1581, **46.1% less**.
- Ask: prefix caching for Ultra like the other models get, or a note in the model list
  (`supported_features`) when a model has none, so a router can plan for it.

### 2. `reasoning_effort` does not bound Ultra's thinking

- Reviewing one recorded three-file change with a 4,000-token output cap, Ultra used all 4,000
  tokens on thinking and wrote no verdict at `low` (two of two tries, and once more without the
  JSON Schema) and at `medium` (two of two). At `none` it answered `{"approve": true, "issues": []}`
  in 12 tokens (two of two). `gpt-oss-120b` at `low` answered in 65 tokens.
- The same effort means different amounts of thinking per model. Asked "What is 17 times 23?"
  at `low`, Lightning used 287 reasoning tokens, Ultra 32 and Super 16 (one request each,
  2026-10-28).
- An agent cannot know in advance how long a model will think at a given effort. We now review
  with thinking off, which works, but it gives up the thinking.
- Edits need the thinking, and there the cap costs a claim. In the replication of C-029
  (`bench/results/2026-10-28-tf-mini-science-replication-2`, task `vectorize-gaussian-sum`),
  four of Super's edit replies stopped at the output cap (`finish_reason: length`), the gates
  failed once, and the task took 22 steps. That one task cost the ladder 77.6% of Ultra's
  dollars, against 15.4% in the first pair of runs, and put the replication's interval above
  its registered bound (ADR 0048).
- Ask: an enforced thinking budget (a maximum number of reasoning tokens, after which the model
  must answer), or a documented budget per effort level and model.

### 3. Cut-off thinking arrives as the answer

- When `max_tokens` ends a reply while the model is still thinking, the unfinished thinking
  comes back in `content`, and `reasoning_tokens` equals `completion_tokens`. Seen on Lightning
  at `low` effort with a 300-token cap (a summary step) and on Ultra in reviews.
- A client that reads `content` shows the model's half-finished thoughts as its answer. The
  only sign is `finish_reason: length`.
- Ask: keep the thinking in `reasoning`/`reasoning_content` and leave `content` empty when the
  answer never started.

### 4. One usage schema

What each model returned for the same one-line question at `low` effort (2026-10-28):

| Model | Cached input | Reasoning tokens | Reasoning text |
|---|---|---|---|
| Lightning | top-level `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`; `prompt_tokens_details` is null | `completion_tokens_details.reasoning_tokens` | `reasoning` and `reasoning_content`, same text |
| Nano | not reported (both detail objects null, no top-level counters) | not reported | `reasoning` |
| Super | `prompt_tokens_details.cached_tokens` and `created_cache_tokens`, and the top-level counters | `completion_tokens_details.reasoning_tokens` | `reasoning` and `reasoning_content`, same text |
| Ultra | `prompt_tokens_details.cached_tokens` and the top-level counters | `completion_tokens_details.reasoning_tokens` | `reasoning_content` |
| `gpt-oss-120b` | `prompt_tokens_details.cached_tokens` | not reported (`completion_tokens_details` is null) | `reasoning` |

- Ask: the same `usage` shape for every model (`prompt_tokens_details.cached_tokens` and
  `completion_tokens_details.reasoning_tokens`, zero when there are none), one reasoning field
  name, and ideally the request's cost in the response, which would make client-side price
  tables unnecessary.

### 5. Effort levels per model

- The three Nemotron models answered HTTP 200 to `none`, `minimal`, `low`, `medium`, `high` and
  `xhigh`; `none` turned thinking off. `gpt-oss-120b` answered HTTP 400 to `none` ("Harmony does
  not support reasoning_effort='none'") and to `minimal` ("Supported values are: high, medium,
  low").
- Ask: list each model's accepted efforts in `supported_features`, or clamp an unsupported
  effort to the nearest accepted one. We now record the accepted levels per model and clamp in
  the client.

### 6. The bill

- Our ledger, at the list prices from `/v1/models?verbose=true`, came to US$ 5.4783 for the
  bench runs; the console showed US$ 5.89 of consumption, tax included, read at 21:00 UTC,
  which also covers probes, direct API checks, the bench runs' canary calls and two test runs
  outside the bench. (At 04:12 UTC the two readings were US$ 2.1787 and 2.38.) We could not
  check the difference (US$ 0.41, including the test runs' 0.02) line by line, because the usage
  view lagged (next point) and the transactions show one consumption line per month.
- A reading at 11:39 UTC showed US$ 5.64, five minutes after our last bench run ended; by
  21:00 UTC it was US$ 5.89 with no call in between. Consumption that posts hours after the
  calls makes "stop when the console reaches the budget" unsafe: a budget check has to use the
  client's own ledger, as ours does. A "posted up to" time on the transactions page would help.
- At 03:56 UTC the Usage page (Billing, Usage) said "Last updated: 02:17, UTC" and showed a few
  hundred tokens per model and a total under US$ 0.01, while the account balance had already
  dropped by US$ 2.10. During a timed event, a usage view that is hours behind the balance makes
  it hard to see which runs cost what.
- In "Rounded numbers" format every line of the usage table read "< $0.01"; only "Full numbers"
  showed values.
- Ask: a usage view that keeps up with the balance, per model and per API key, and a cost
  field per request in the API response.

### 7. Docs

- The project ID variable is `NEBIUS_PROJECT_ID` for the Sandboxes SDK and REST API and has a
  different name for the CLI; one name would save a lookup.
- The cached-token page explains billing well; a line on which models cache would answer the
  question in section 1 before anyone measures it.

## Sandboxes

- We wanted to run Stepswitch's gates (the project's test suite after each model-written change)
  in a Sandbox, so untrusted code runs away from the developer's machine and best-of-N
  candidates can be tested in parallel. The limits fit that well: 3600 seconds per instance,
  50 instances at a time, 12 GiB per image layer.
- With the project's API key and project ID, `GET /sandboxes/v1/whoami` answered HTTP 200 with
  every permission `false` (`spawn`, `spawn_disposable`, `list`, `import`, `cancel`,
  `set_image_tag`). Nothing in the response said why; the console's Sandboxes page shows
  "Request beta access".
- Ask: a response that says the beta has not been granted and links to the request, or a 403
  with that message; and access for hackathon participants by default, since the track invites
  agents that "write, run, and test code in Token Factory".
- The design we would build is in [sandboxes.md](sandboxes.md).

## Nemotron models

Per model over the nine bench runs (seconds are the wall time of a call; output tokens per
second divide a call's output tokens by its wall time, for calls with more than 50 output
tokens):

| Model | Calls | Median s per call | 90th percentile s | Output tokens per s (median) | Input served from the cache | Reasoning share of output | Calls cut off at the output cap |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Nemotron-3_5-Lightning` | 505 | 1.95 | 5.53 | 90 | 53.4% of 3,798,780 | 55.6% | 18 |
| `Nemotron-3-Ultra-550b-a55b` | 420 | 2.20 | 3.28 | 72 | 3.2% of 1,508,109 | 59.2% | 5 |
| `nemotron-3-super-120b-a12b` | 193 | 2.66 | 5.72 | 81 | 61.2% of 1,001,364 | 71.2% | 3 |
| `NVIDIA-Nemotron-3-Nano-30B-A3B` | 32 | 12.46 | 21.83 | 79 | 46.6% of 181,358 | not reported | 9 |
| `gpt-oss-120b` | 30 | 1.26 | 3.39 | 95 | 26.7% of 18,204 | not reported | 0 |

- **Nano** (edits in the escalation demo only) wrote long replies: 34,418 output tokens over
  32 calls, a median of 12.46 seconds per call, and 9 of 32 calls cut off at the output cap at
  `low` effort. It reports no reasoning tokens, so a client cannot tell thinking from answer
  length. Its changes failed the gates twice on both demo tasks and Ultra took over.

- **Lightning** ran the ladder's summaries with no cut-off calls, as Ultra did, at 6.8% of
  Ultra's dollars per call (21 calls each, claim C-030). On navigate steps 10 of its 71 tool
  calls returned errors against none of Ultra's 61: it asked for absolute paths such as
  `/repo/todo/model.py`, got "absolute paths are not accepted; paths are relative to the
  repository root." and corrected itself. In the probe it did not follow a system prompt: the
  reply began "Here's a thinking process" and lacked the code word the system prompt asked for.
  Alone on the same 21 tasks, Lightning passed 19 at US$ 0.0071 per task run (70% of the
  ladder's) but used 130,369 tokens per task run, 2.8 times the ladder's; both failures ran out
  of steps.
- **Tool arguments.** Three shapes recurred in the edit and run calls our tools refused.
  Lightning copied rows of the read output into an edit's old and new text with their `ab|`
  hash prefixes. Super and Ultra sometimes sent the `edits` array as a JSON string, with a
  docstring's `"""` left unescaped inside it or one closing bracket too many. And Lightning
  wrote container paths such as `/repo/...` and `cd /workspace && ...`. Ultra, working alone,
  often put the test command itself into the test tool's `selector` (`-m pytest -q`); appended
  to the configured `python -m pytest -q`, pytest reads the second `-m pytest` as a marker
  filter that deselects every test, so the call reported that no test ran and Ultra tried
  again. Stepswitch now takes the unambiguous cases (each checked against the file, or the
  repeated command dropped with a note), but a model that keeps tool arguments
  as structured JSON and leaves display prefixes out would save those turns in every agent
  harness. The counts come from our local run records, which are not in this repository, so we
  give none here.
- **Super** did the ladder's work: 151 of its 261 calls and 80.0% of its dollars, with every
  change passing the gates within two attempts (no escalations in 21 task runs).
- **Ultra** as the reviewer blocked one change in 21 that passed its tests, over a design
  concern (temperature units kept in a table of linear conversion factors); `gpt-oss-120b`
  approved the same change. Its review notes were useful but its reasoning in one note wandered
  ("Uses 459.67 instead of 459.67? Actually ..."). With thinking on, reviews need an output cap
  far above the verdict's size (section 2).
- **Reasoning share.** More than half of every Nemotron model's output tokens were reasoning
  tokens (table above), 71.2% for Super. At the output price that is most of the output bill,
  so an effort level that predictably bounds thinking (Token Factory section 2) matters for
  cost as much as for latency.
