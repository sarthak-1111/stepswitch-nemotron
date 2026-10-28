# ADR 0044: Hosted providers, prices in dollars, and a per-step Nemotron ladder

- Status: accepted
- Date: 2026-10-28
- Phase: after 13

## Context

Stepswitch could already call a hosted chat-completions endpoint, but four things were missing
to run a whole task on one hosted service, Token Factory, with the Nemotron models:

1. Every user had to copy the service's URL, authentication and models into
   `.stepswitch/local.toml`, and set each model's tier and family by hand. Without them every
   hosted model was a separate family on the one "remote" rung, so the ladder and cross-family
   review could not tell the models apart.
2. The ledger counted tokens but not dollars, and the bench had one reference price for every
   model, which billed cached input at the full price.
3. A `[[policy.rules]]` pin ignores the escalation rung, so a rule that sends edits to a
   mid-size model kept sending them there after the gates failed.
4. A rule that pins reviews to the largest model of the authors' family turns off the review by
   another family (SPEC §8.5).

## Decision

1. **Provider files.** `registry/providers/<id>.toml` holds a hosted service's URL, format,
   authentication, default models, and per model the keys of a `[models."<name>"]` table:
   tier, family, roles, context, reasoning and prices. An endpoint uses it with
   `preset = "<id>"`, and an endpoint whose URL is the provider's gets its model facts too. The
   endpoint's own keys and the user's `[models."<name>"]` table win. The first provider is
   `tokenfactory`, checked on 2026-10-28 (RESEARCH.md, "Token Factory"). The URL lives in the
   committed provider file, so `.stepswitch/local.toml` holds only the preset name.
2. **Prices.** `price_input`, `price_cached_input` and `price_output` (US dollars per million
   tokens) in a provider's or the user's model table give a worker its prices
   (`stepswitch.pricing`). Each ledger row gets `cost_usd`: uncached input at the input price,
   cached input at the cached price (the input price when there is none), output at the output
   price (migration 6). Models without prices, the local ones, have no cost. Task totals,
   `usage_by_worker`, step events and bench rows carry the cost.
3. **Dollar budgets.** `[budgets] usd`, `ssw run --budget-usd` and `ssw bench run --budget-usd`
   stop a task at a dollar limit like the other budgets (at most one step over).
   `ssw bench run --budget-usd-total` caps the whole bench: no run starts once the bench's runs
   cost that much, and each run's dollar budget is at most what is left. `--interleave` runs
   every contestant on a task before the next, so a cap stops both contestants at the same
   task.
4. **Hosted endpoints in the bench.** `ssw bench run --allow-remote` lets the `router`,
   `best-of-n` and `harness:` contestants route to hosted workers; pinned contestants on a
   hosted worker always could. The manifest records the flag, the caps, the money spent and
   every configured worker's prices.
5. **Rules that know about escalation.** Rules can match `escalations` (how often the ladder
   has escalated in the task) in `when`, for example `escalations = 0` or `">=1"`. A step
   type can therefore start on one model and move to another once the gates have failed on it.
6. **A second opinion on reviews.** With `[review] second_opinion = true`, a review given by
   a worker of the authors' own family gets a second review from another family on the same
   diff. Rules that pin the review step are set aside for that call only. Either reviewer's
   issues go back to the author; both verdicts are recorded as `review` events, the second
   with `second_opinion` and `agrees`. Nothing changes when the setting is off, when
   `--worker` pins a worker, or when no other family is available.
7. **Usage variants.** Some Token Factory models leave `prompt_tokens_details` out and report
   their prompt cache in top-level `prompt_cache_hit_tokens`; the chat-completions codec reads
   the hit count as cached input when the detail field is missing.

## Consequences

- `examples/tokenfactory/` runs every step on Token Factory with the Nemotron ladder: the
  small model navigates, reads and summarizes, Super edits and triages, Ultra plans, reviews
  and takes the work steps after an escalation, and a model of another family gives a second
  opinion on Ultra's review.
- Dollar figures are as good as the prices in the provider file, which are dated. A change in
  price needs a new date and source in the file and in RESEARCH.md.
- The ledger's cost is computed from server-reported tokens. It is not the provider's invoice;
  the hackathon bill in `hackathon/` compares the two.
