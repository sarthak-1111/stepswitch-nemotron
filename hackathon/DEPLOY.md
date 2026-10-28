# Deploying the demo

The demo is a static, read-only page: `hackathon/demo/site/` (`index.html`, `app.js`,
`style.css` and `data.json`). It replays recorded Token Factory bench runs step by step and
shows the results tables. It has no login, holds no API key and calls no model, so it costs
nothing to host and has nothing to rate-limit.

- URL: https://sarthak-1111.github.io/stepswitch-nemotron/
- Host: GitHub Pages, free for public repositories, published by `.github/workflows/demo.yml`
  on every push to the `hackathon` branch that touches `hackathon/demo/`.
- Stays up: as long as the repository is public and Pages is on (Settings, Pages, Source:
  GitHub Actions). Nothing expires before the judging ends on 15 December.

## Rebuild the data

`data.json` is built from the committed runs under `bench/results/` and the claim evidence:

```bash
uv run python hackathon/demo/build.py          # writes hackathon/demo/site/data.json
uv run python hackathon/demo/build.py --check  # what the workflow runs before publishing
```

The workflow refuses to publish when `data.json` does not match the committed runs, so the page
never shows numbers that the repository does not hold.

## Preview locally

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory hackathon/demo/site
```

## Why there is no live button

A live button would send a visitor's task to Token Factory with the project's API key. The key
would have to live on a server we run (a serverless function with a rate limit and a daily
cap), and for this submission the key stays on the developer's machine only. To add one:

1. Deploy a small function (for example a Cloudflare Worker or a Netlify Function) that holds
   the key as a secret environment variable, accepts one of the bench's toy tasks by id (never
   free text), allows a few runs per visitor per hour and a fixed number per day, and refuses
   when the day's dollar cap is reached.
2. Have it run `ssw run --policy bench/policies/tokenfactory-ladder.toml` on that task in a
   disposable container and return the trajectory's step records, the same shape as
   `steps.jsonl`.
3. Point a button in `app.js` at the function's URL.
