// Stepswitch replay: a read-only view of recorded Token Factory bench runs (data.json, built by
// hackathon/demo/build.py from bench/results). No model is called from this page.
"use strict";

const LADDER = "router";
// What each kind of run is (build.py sets `kind`).
const KINDS = {
  main: "ladder vs Ultra alone (claim C-029)",
  demo: "escalation demo: edits start on Nano",
  alone: "Lightning alone",
  pilot: "pilot",
};
const kindOf = (run) => run.kind || "main";
const MODELS = [
  // [match, css class, short label]
  [/lightning/i, "m-lightning", "Nemotron 3.5 Lightning"],
  [/nano/i, "m-nano", "Nemotron 3 Nano"],
  [/super/i, "m-super", "Nemotron 3 Super"],
  [/ultra/i, "m-ultra", "Nemotron 3 Ultra"],
  [/gpt-oss/i, "m-gptoss", "gpt-oss-120b"],
];

const $ = (sel) => document.querySelector(sel);

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function model(worker) {
  for (const [match, css, label] of MODELS) if (match.test(worker || "")) return { css, label };
  return { css: "m-other", label: (worker || "?").split("/").pop() };
}

function badge(worker) {
  const m = model(worker);
  return el("span", { class: `badge ${m.css}` }, m.label);
}

function contestantLabel(name, kind) {
  if (name === LADDER) return kind === "demo" ? "Nemotron ladder, edits starting on Nano" : "Nemotron ladder (Stepswitch)";
  return `${model(name).label} alone`;
}

const usd = (v, digits = 4) => (v === null || v === undefined ? "–" : `$${Number(v).toFixed(digits)}`);
const int = (v) => (v === null || v === undefined ? "–" : Math.round(v).toLocaleString("en-US"));
const pct = (v) => `${(100 * v).toFixed(0)}%`;
const tokensOf = (row) => (row.tokens?.input || 0) + (row.tokens?.output || 0);

function summarize(rows) {
  const n = rows.length;
  const priced = rows.filter((r) => r.cost_usd !== null && r.cost_usd !== undefined);
  const sum = (f, list = rows) => list.reduce((a, r) => a + (f(r) || 0), 0);
  return {
    runs: n,
    passed: rows.filter((r) => r.passed).length,
    cost: sum((r) => r.cost_usd, priced),
    costPerTask: priced.length ? sum((r) => r.cost_usd, priced) / priced.length : null,
    tokensPerTask: n ? sum(tokensOf) / n : null,
    minutesPerTask: n ? sum((r) => r.wall_seconds) / n / 60 : null,
    escalations: sum((r) => r.escalations),
  };
}

function shared(rows) {
  // Task runs every contestant of the run has, so both sides cover the same tasks.
  const keys = new Map();
  for (const r of rows) {
    const k = `${r.task}|${r.seed}`;
    keys.set(k, (keys.get(k) || new Set()).add(r.contestant));
  }
  const contestants = new Set(rows.map((r) => r.contestant));
  return rows.filter((r) => keys.get(`${r.task}|${r.seed}`).size === contestants.size);
}

function suiteCard(title, rows, note) {
  const both = shared(rows);
  const names = [...new Set(both.map((r) => r.contestant))].sort((a, b) => (a === LADDER ? -1 : b === LADDER ? 1 : 0));
  const stats = Object.fromEntries(names.map((n) => [n, summarize(both.filter((r) => r.contestant === n))]));
  const card = el("div", { class: "card" }, el("h3", {}, title));
  for (const n of names) {
    const s = stats[n];
    card.append(
      el("p", { class: "st" }, badgeFor(n), contestantLabel(n)),
      el("dl", {},
        el("dt", {}, "passed"), el("dd", {}, `${s.passed} of ${s.runs}`),
        el("dt", {}, "dollars per task"), el("dd", {}, usd(s.costPerTask)),
        el("dt", {}, "tokens per task"), el("dd", {}, int(s.tokensPerTask)),
        el("dt", {}, "minutes per task"), el("dd", {}, s.minutesPerTask === null ? "–" : s.minutesPerTask.toFixed(2)),
        el("dt", {}, "escalations"), el("dd", {}, int(s.escalations)),
      ),
    );
  }
  const ladder = stats[LADDER];
  const other = names.find((n) => n !== LADDER);
  if (ladder && other && stats[other].cost > 0) {
    const saved = 1 - ladder.cost / stats[other].cost;
    card.append(el("p", { class: "delta" }, `The ladder's dollars: ${pct(1 - saved)} of ${model(other).label}'s on these task runs`));
  }
  if (note) card.append(el("p", { class: "meta" }, note));
  return card;
}

function badgeFor(name) {
  return name === LADDER ? el("span", { class: "badge m-other" }, "ladder") : badge(name);
}

function renderResults(data) {
  const complete = data.runs.filter((r) => kindOf(r) === "main");
  const cards = $("#result-cards");
  for (const run of complete) cards.append(suiteCard(run.suite, run.rows, `run ${run.name}`));
  if (complete.length > 1) {
    const rows = complete.flatMap((run) => run.rows.map((r) => ({ ...r, task: `${run.suite}/${r.task}` })));
    cards.append(suiteCard("both mini suites", rows));
  }
  const alone = $("#alone-cards");
  for (const run of data.runs.filter((r) => kindOf(r) === "alone")) {
    alone.append(suiteCard(run.suite, run.rows, `run ${run.name}: a separate run on the same tasks, after the main runs`));
  }
  const pilot = data.runs.find((r) => kindOf(r) === "pilot");
  if (pilot) alone.append(suiteCard(`${pilot.suite}, five-task pilot`, pilot.rows, "calibration run before the main runs; see provenance"));
  const total = data.runs.reduce((a, run) => a + summarize(run.rows).cost, 0);
  $("#bill").textContent = `Recorded spend of the runs on this page: ${usd(total, 2)} at list prices (Stepswitch's ledger). The submission's SUBMISSION file has the whole bill, failed runs included.`;
}

function renderLadder(data) {
  const run = data.runs.find((r) => r.policy?.rules?.length) || data.runs[0];
  const body = $("#ladder-table tbody");
  const prices = run?.worker_prices || {};
  const rows = new Map();
  const untilEscalation = new Set();
  for (const rule of run?.policy?.rules || []) {
    const target = rule.to?.model;
    if (!target) continue;
    const types = rule.when?.step_type || [];
    const first = types.filter((t) => !untilEscalation.has(t));
    const later = types.filter((t) => untilEscalation.has(t));
    const parts = [];
    if (first.length) parts.push(first.join(", ") + (rule.when?.escalations === 0 ? " until the gates fail twice" : ""));
    if (later.length) parts.push(`${later.join(", ")} after an escalation`);
    if (rule.when?.escalations === 0) types.forEach((t) => untilEscalation.add(t));
    rows.set(target, [...(rows.get(target) || []), ...parts]);
  }
  if (run?.policy?.review?.second_opinion) rows.set("openai/gpt-oss-120b", ["a second review of each change, from another model family"]);
  const money = (v) => (v === null || v === undefined ? "–" : `$${Number(v).toFixed(2)}`);
  for (const [target, steps] of rows) {
    const price = Object.entries(prices).find(([id]) => id.endsWith(target))?.[1];
    const priceText = price ? `${money(price.input_per_million)} / ${money(price.cached_input_per_million)} / ${money(price.output_per_million)}` : "–";
    body.append(el("tr", {}, el("td", {}, badge(target)), el("td", {}, steps.join("; ")), el("td", { class: "num" }, priceText)));
  }
}

// ---- replay ---------------------------------------------------------------------------------

let timer = null;

function stepLine(ev, rules) {
  const u = ev.usage || {};
  const tools = (ev.tool_calls || []).length ? ` → ${ev.tool_calls.join(", ")}` : "";
  const rule = rules.get(ev.step);
  return el("div", {},
    badge(ev.worker), el("span", { class: "st" }, ev.step_type), tools,
    el("div", { class: "meta" },
      `in ${int(u.input_tokens)}`, u.cached_input_tokens ? ` (cached ${int(u.cached_input_tokens)})` : "",
      ` · out ${int(u.output_tokens)} · ${usd(ev.cost_usd, 5)}`,
      ev.effort ? ` · effort ${ev.effort}` : "",
      rule ? ` · rule ${rule}` : "",
    ),
  );
}

function gateLine(ev) {
  const chips = (ev.results || []).map((g) =>
    el("span", { class: `chip ${g.status === "passed" ? "ok" : g.status === "failed" ? "bad" : "skip"}` }, `${g.name.replace("_", " ")}: ${g.status}`));
  return el("div", {}, el("span", { class: `verdict ${ev.passed ? "ok" : "bad"}` }, ev.passed ? "Gates passed" : `Gate failed: ${ev.failed_gate}`), el("div", {}, chips));
}

function reviewLine(ev) {
  const who = model(ev.reviewer).label;
  const verdict = ev.failed ? "gave no verdict" : ev.approved ? "approved" : "blocked";
  const extra = ev.second_opinion ? (ev.agrees === true ? " · agrees with the first review" : ev.agrees === false ? " · disagrees with the first review" : "") : "";
  const issues = ev.issues ? ` · ${ev.issues} issue(s)` : "";
  return el("div", {}, badge(ev.reviewer), el("span", { class: `verdict ${ev.approved ? "ok" : "bad"}` }, `${ev.second_opinion ? "Second opinion" : "Review"}: ${verdict}`), `${issues}${extra}`, ev.cross_family ? el("span", { class: "meta" }, " · other model family") : "");
}

function escalationLine(ev, events) {
  // The escalation names tiers; the next model call shows which model took over.
  const next = events.find((e) => e.type === "step" && e.seq > ev.seq);
  return el("div", {},
    el("span", { class: "verdict bad" }, "Escalated"),
    ` ${ev.reason || "the gates failed"}: tier ${ev.from} → ${ev.to}`,
    next ? el("span", {}, " · the work moves to ", badge(next.worker)) : "");
}

function lane(name, row, events, kind) {
  // The rule that picked each step's model; a single-model contestant is pinned, not routed.
  const rules = new Map(events.filter((e) => e.type === "decision" && e.rule && e.rule !== "--worker").map((e) => [e.step, e.rule]));
  const list = el("ol", { class: "events" });
  let n = 0;
  for (const ev of events) {
    let body = null;
    let cls = "ev";
    if (ev.type === "step") body = stepLine(ev, rules);
    else if (ev.type === "gates") { body = gateLine(ev); cls += " gate"; }
    else if (ev.type === "review") { body = reviewLine(ev); cls += " review"; }
    else if (ev.type === "escalation") { body = escalationLine(ev, events); cls += " escalation"; }
    else if (ev.type === "tool" && ev.is_error) body = el("div", { class: "meta" }, `tool error in ${ev.name}`);
    else if (ev.type === "task_end") body = el("div", { class: "st" }, `Task ${ev.status}${ev.stop_reason ? ` (${ev.stop_reason})` : ""}`);
    if (!body) continue;
    n += 1;
    list.append(el("li", { class: cls }, el("span", { class: "n" }, ev.type === "step" ? `${ev.step}` : ""), el("div", { class: "body" }, body)));
  }
  const s = summarize([row]);
  return el("div", { class: "lane" },
    el("h3", {}, badgeFor(name), contestantLabel(name, kind)),
    el("div", { class: "totals" },
      el("span", { class: `verdict ${row.passed ? "ok" : "bad"}` }, row.passed ? "passed" : "failed"),
      ` · ${usd(row.cost_usd)} · ${int(tokensOf(row))} tokens · ${(s.minutesPerTask || 0).toFixed(2)} min · ${row.steps} steps`),
    events.length ? list : el("p", { class: "meta" }, "No step records for this run."));
}

function renderReplay(data) {
  const runSelect = $("#run-select");
  const taskSelect = $("#task-select");
  data.runs.forEach((run, i) => runSelect.append(el("option", { value: i }, `${run.suite} · ${KINDS[kindOf(run)]}`)));
  // Escalated tasks, the ones that finished with the gates passing first.
  const escalated = (run) => run.rows
    .filter((r) => r.escalations > 0)
    .sort((a, b) => (b.status === "done") - (a.status === "done"))
    .map((r) => r.task);
  function fillTasks(preferred) {
    const run = data.runs[runSelect.value];
    taskSelect.replaceChildren(...[...new Set(run.rows.map((r) => r.task))].map((t) => el("option", { value: t }, t)));
    if (preferred) taskSelect.value = preferred;
    show();
  }
  function show() {
    stop();
    const run = data.runs[runSelect.value];
    const task = taskSelect.value;
    const rows = run.rows.filter((r) => r.task === task).sort((a, b) => (a.contestant === LADDER ? -1 : b.contestant === LADDER ? 1 : 0));
    const tags = rows[0]?.tags?.length ? `tags: ${rows[0].tags.join(", ")}` : "";
    $("#task-tags").textContent = kindOf(run) === "demo"
      ? `Escalation demo, not part of the comparison: the same ladder with edits starting on Nemotron 3 Nano, so a failed gate is more likely. ${tags}`
      : tags;
    $("#lanes").replaceChildren(...rows.map((r) => lane(r.contestant, r, run.steps[`${r.contestant}|${r.task}|${r.seed}`] || [], kindOf(run))));
  }
  runSelect.addEventListener("change", () => fillTasks());
  taskSelect.addEventListener("change", show);
  $("#play").addEventListener("click", play);
  $("#show-all").addEventListener("click", () => { stop(); document.querySelectorAll(".ev").forEach((e) => e.classList.remove("hidden")); });
  $("#show-escalation")?.addEventListener("click", () => {
    const i = data.runs.findIndex((run) => escalated(run).length);
    if (i < 0) return;
    runSelect.value = i;
    fillTasks(escalated(data.runs[i])[0]);
    play();
  });
  if (!data.runs.some((run) => escalated(run).length)) $("#show-escalation")?.remove();
  fillTasks();
}

function stop() {
  if (timer) clearInterval(timer);
  timer = null;
}

function play() {
  stop();
  const lanes = [...document.querySelectorAll(".lane .events")].map((l) => [...l.children]);
  lanes.flat().forEach((e) => e.classList.add("hidden"));
  let i = 0;
  const longest = Math.max(0, ...lanes.map((l) => l.length));
  timer = setInterval(() => {
    for (const l of lanes) if (l[i]) l[i].classList.remove("hidden");
    i += 1;
    if (i >= longest) stop();
  }, 450);
}

// ---- reviewers and step types ---------------------------------------------------------------

function renderReviews(data) {
  const complete = data.runs.filter((r) => kindOf(r) === "main");
  let pairs = 0, agree = 0, disagree = 0, noVerdict = 0, firstApproved = 0, secondApproved = 0;
  for (const run of complete) {
    for (const [key, events] of Object.entries(run.steps)) {
      if (!key.startsWith(`${LADDER}|`)) continue;
      const reviews = events.filter((e) => e.type === "review");
      for (const second of reviews.filter((e) => e.second_opinion)) {
        pairs += 1;
        if (second.agrees === true) agree += 1;
        else if (second.agrees === false) disagree += 1;
        else noVerdict += 1;
      }
      firstApproved += reviews.filter((e) => !e.second_opinion && e.approved).length;
      secondApproved += reviews.filter((e) => e.second_opinion && e.approved).length;
    }
  }
  const cards = $("#review-stats");
  cards.append(
    el("div", { class: "card" }, el("h3", {}, "Changes with both reviews"), el("div", { class: "big" }, pairs)),
    el("div", { class: "card" }, el("h3", {}, "Verdicts agree"), el("div", { class: "big" }, pairs ? `${agree} of ${pairs}` : "–"),
      el("p", { class: "meta" }, `${disagree} disagree, ${noVerdict} without a verdict on one side`)),
    el("div", { class: "card" }, el("h3", {}, "Approvals"), el("dl", {},
      el("dt", {}, "Nemotron 3 Ultra"), el("dd", {}, firstApproved),
      el("dt", {}, "gpt-oss-120b"), el("dd", {}, secondApproved))),
  );
}

function renderStepTypes(data) {
  const complete = data.runs.filter((r) => kindOf(r) === "main");
  const stats = {};
  for (const run of complete) {
    for (const [key, events] of Object.entries(run.steps)) {
      const contestant = key.split("|")[0];
      const side = contestant === LADDER ? "ladder" : "single";
      const typeOf = new Map();
      for (const ev of events) {
        if (ev.type === "step") {
          typeOf.set(ev.step, ev.step_type);
          const s = (stats[ev.step_type] ||= { ladder: { calls: 0, tokens: 0, cost: 0, errors: 0, models: new Set() }, single: { calls: 0, tokens: 0, cost: 0, errors: 0, models: new Set() } })[side];
          s.calls += 1;
          s.tokens += (ev.usage?.input_tokens || 0) + (ev.usage?.output_tokens || 0);
          s.cost += ev.cost_usd || 0;
          s.models.add(model(ev.worker).label);
        } else if (ev.type === "tool" && ev.is_error && typeOf.has(ev.step)) {
          stats[typeOf.get(ev.step)][side].errors += 1;
        }
      }
    }
  }
  const order = ["plan", "navigate", "read", "edit", "run", "triage", "review", "summarize", "write-text"];
  const body = $("#step-table tbody");
  for (const type of order) {
    const s = stats[type];
    if (!s) continue;
    const per = (side, f) => (s[side].calls ? f(s[side]) : "–");
    body.append(el("tr", {},
      el("td", {}, type),
      el("td", {}, [...s.ladder.models].join(", ") || "–"),
      el("td", { class: "num" }, `${s.ladder.calls} / ${s.single.calls}`),
      el("td", { class: "num" }, `${per("ladder", (x) => int(x.tokens / x.calls))} / ${per("single", (x) => int(x.tokens / x.calls))}`),
      el("td", { class: "num" }, `${per("ladder", (x) => usd(x.cost / x.calls, 5))} / ${per("single", (x) => usd(x.cost / x.calls, 5))}`),
      el("td", { class: "num" }, `${s.ladder.errors} / ${s.single.errors}`),
    ));
  }
}

function renderProvenance(data) {
  const box = $("#prov");
  for (const run of data.runs) {
    box.append(el("p", {},
      el("strong", {}, run.name), ` (${KINDS[kindOf(run)]}) · ${run.suite} · started ${run.started || "?"} · commit ${run.commit || "?"}`,
      run.policy?.file ? ` · policy ${run.policy.file.file || ""}` : "",
      run.stopped ? ` · stopped by the dollar cap after ${run.stopped.runs} of ${run.stopped.of} runs` : "",
      el("br"), el("code", {}, run.command || ""),
    ));
  }
}

fetch("data.json")
  .then((r) => r.json())
  .then((data) => {
    renderResults(data);
    renderLadder(data);
    renderReplay(data);
    renderReviews(data);
    renderStepTypes(data);
    renderProvenance(data);
  })
  .catch((err) => {
    document.querySelector("main").prepend(el("p", { class: "verdict bad" }, `Could not load data.json: ${err}`));
  });
