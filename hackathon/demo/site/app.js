// Stepswitch replay: a read-only view of recorded Token Factory bench runs (data.json, built by
// hackathon/demo/build.py from bench/results). No model is called from this page. The headline
// numbers come from the claim evidence in data.json (claims/evidence/C-029.json, C-030.json).
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
// Fixed categorical order of the model colours (the order the palette was validated in).
const MODEL_ORDER = ["m-super", "m-lightning", "m-ultra", "m-gptoss", "m-nano", "m-other"];
const SVG_NS = "http://www.w3.org/2000/svg";

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

function svg(tag, attrs, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === undefined || value === null) continue;
    // Fills name CSS variables (the theme's colours), which only the style property resolves.
    if (key === "fill") node.style.fill = value;
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined) continue;
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

const USD = new Map();
const usd = (v, digits = 4) => {
  if (v === null || v === undefined) return "–";
  if (!USD.has(digits)) USD.set(digits, new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: digits, maximumFractionDigits: digits }));
  return USD.get(digits).format(v);
};
const INT = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const int = (v) => (v === null || v === undefined ? "–" : INT.format(Math.round(v)));
const UTC = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" });
const when = (iso) => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? iso : `${UTC.format(d)} UTC`; };
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

// ---- theme --------------------------------------------------------------------------------

function setupTheme() {
  const button = $("#theme");
  const current = () => document.documentElement.dataset.theme
    || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const label = () => {
    button.dataset.mode = current();
    button.setAttribute("aria-label", current() === "dark" ? "Switch to the light theme" : "Switch to the dark theme");
  };
  label();
  button.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("ssw-theme", next); } catch (e) { /* storage blocked: the choice lasts this visit */ }
    label();
    redrawCharts();
  });
}

// ---- tooltip ------------------------------------------------------------------------------

const tooltip = () => $("#tooltip");

function showTip(target, value, label, event) {
  const tip = tooltip();
  tip.replaceChildren(el("strong", {}, value), el("span", {}, label));
  tip.hidden = false;
  const box = target.getBoundingClientRect();
  const x = event && "clientX" in event && event.clientX ? event.clientX : box.left + box.width / 2;
  const y = event && "clientY" in event && event.clientY ? event.clientY : box.top;
  const w = tip.offsetWidth;
  tip.style.left = `${Math.min(Math.max(8, x - w / 2), innerWidth - w - 8)}px`;
  tip.style.top = `${Math.max(8, y - tip.offsetHeight - 12)}px`;
}

function hideTip() {
  tooltip().hidden = true;
}

// A hit target over a mark: hover and keyboard focus show the same tooltip.
function hit(plot, mark, attrs, value, label) {
  const target = svg("rect", { ...attrs, class: "hit", tabindex: "0", role: "img", "aria-label": `${label}: ${value}` });
  const on = (event) => { plot.classList.add("hovering"); mark.classList.add("active"); showTip(target, value, label, event); };
  const off = () => { plot.classList.remove("hovering"); mark.classList.remove("active"); hideTip(); };
  target.addEventListener("pointermove", on);
  target.addEventListener("pointerleave", off);
  target.addEventListener("focus", on);
  target.addEventListener("blur", off);
  return target;
}

// A bar growing from the baseline at x0: square at the baseline, 4px round at the data end.
function barPath(x0, y, width, height, radius = 4) {
  const r = Math.min(radius, width / 2, height / 2);
  if (width <= 0) return "";
  return `M${x0},${y}h${width - r}a${r},${r} 0 0 1 ${r},${r}v${height - 2 * r}a${r},${r} 0 0 1 ${-r},${r}h${-(width - r)}z`;
}

// ---- charts -------------------------------------------------------------------------------

let evidence = null;
const charts = [];

function redrawCharts() {
  for (const draw of charts) draw();
}

function chart(selector, draw) {
  const plot = document.querySelector(`${selector} .plot`);
  const render = () => {
    const width = Math.max(260, Math.round(plot.clientWidth));
    plot.replaceChildren(draw(plot, width));
  };
  charts.push(render);
  render();
  if ("ResizeObserver" in window) {
    let last = plot.clientWidth;
    new ResizeObserver(() => { if (Math.abs(plot.clientWidth - last) > 2) { last = plot.clientWidth; render(); } }).observe(plot);
  }
}

function costChart(comparison) {
  const groups = [
    ...Object.entries(comparison.per_suite || {}).map(([suite, s]) => [suite, s.results, s.task_runs]),
    ["both suites", comparison.results, comparison.task_runs],
  ];
  const max = Math.max(...groups.flatMap(([, r]) => [r.ladder.cost_per_task_usd, r.single.cost_per_task_usd]));
  $("#cost-chart-desc").textContent = groups
    .map(([name, r]) => `${name}: ladder ${usd(r.ladder.cost_per_task_usd)}, Ultra alone ${usd(r.single.cost_per_task_usd)} per task run`)
    .join("; ");
  chart("#cost-chart", (plot, width) => {
    const bar = 18, gap = 2, labelH = 22, groupGap = 22, right = 64;
    const height = groups.length * (labelH + 2 * bar + gap + groupGap) - groupGap + 24;
    const scale = (v) => (v / (max * 1.02)) * (width - right);
    const root = svg("svg", { viewBox: `0 0 ${width} ${height}`, width, height, "aria-hidden": "true" });
    const ticks = [0, 0.02, 0.04, 0.06].filter((t) => t <= max * 1.02);
    for (const t of ticks) {
      const x = scale(t);
      root.append(svg("line", { class: "gridline", x1: x, x2: x, y1: 0, y2: height - 20 }),
        svg("text", { x, y: height - 4, "text-anchor": t === 0 ? "start" : "middle" }, `$${t.toFixed(2)}`));
    }
    let y = 0;
    for (const [name, r, runs] of groups) {
      root.append(svg("text", { x: 0, y: y + 15 }, `${name} · ${runs} task runs`));
      y += labelH;
      for (const [side, fill, who] of [["ladder", "var(--accent)", "Nemotron ladder"], ["single", "var(--s-single)", "Nemotron 3 Ultra alone"]]) {
        const v = r[side].cost_per_task_usd;
        const w = scale(v);
        const mark = svg("path", { class: "mark", d: barPath(0, y, w, bar), fill });
        root.append(mark,
          svg("text", { class: "value-label", x: w + 6, y: y + bar / 2 + 4.5 }, usd(v)),
          hit(plot, mark, { x: 0, y: y - 1, width: Math.max(w + 56, 24), height: bar + 2 }, `${usd(v)} per task run`, `${who}, ${name}`));
        y += bar + gap;
      }
      y += groupGap - gap;
    }
    return root;
  });
}

function shareChart(comparison) {
  const parts = Object.values(comparison.ladder_dollars_by_model || {})
    .map((m) => ({ ...m, ...model(m.worker) }))
    .sort((a, b) => MODEL_ORDER.indexOf(a.css) - MODEL_ORDER.indexOf(b.css));
  const total = parts.reduce((a, p) => a + p.cost_usd, 0);
  $("#share-chart-desc").textContent = parts.map((p) => `${p.label} ${p.percent}%`).join(", ");
  const legend = $("#share-chart .legend-list");
  legend.replaceChildren(...parts.map((p) => el("li", {},
    el("i", { class: "swatch", style: `background: var(--${p.css})` }),
    el("span", { class: "who" }, p.label),
    el("span", { class: "pct" }, `${p.percent.toFixed(1)}%`),
    el("span", { class: "calls" }, `${p.calls} calls · ${usd(p.cost_usd)}`))));
  chart("#share-chart", (plot, width) => {
    const bar = 24, gap = 2, height = bar + 28;
    const usable = width - gap * (parts.length - 1);
    const root = svg("svg", { viewBox: `0 0 ${width} ${height}`, width, height, "aria-hidden": "true" });
    let x = 0;
    parts.forEach((p, i) => {
      const w = Math.max(2, (p.cost_usd / total) * usable);
      const first = i === 0, last = i === parts.length - 1;
      const d = last ? barPath(x, 0, w, bar) : first ? `M${x},0h${w}v${bar}h${-w}z` : `M${x},0h${w}v${bar}h${-w}z`;
      const mark = svg("path", { class: "mark", d, fill: `var(--${p.css})` });
      root.append(mark, hit(plot, mark, { x, y: -2, width: Math.max(w, 12), height: bar + 4 },
        `${p.percent.toFixed(1)}% · ${usd(p.cost_usd)}`, `${p.label}, ${p.calls} calls`));
      x += w + gap;
    });
    const lead = parts.reduce((a, p) => (p.cost_usd > a.cost_usd ? p : a), parts[0]);
    root.append(svg("text", { x: 0, y: bar + 20 }, `${usd(total)} over ${comparison.task_runs} task runs; ${lead.label} took the most`));
    return root;
  });
}

function tokenChart(comparison) {
  const r = comparison.results;
  const rows = [
    ["Nemotron ladder", r.ladder.tokens_per_task, r.ladder.uncached_tokens_per_task],
    ["Nemotron 3 Ultra alone", r.single.tokens_per_task, r.single.uncached_tokens_per_task],
  ];
  const max = Math.max(...rows.map(([, total]) => total));
  $("#token-chart-desc").textContent = rows
    .map(([name, total, uncached]) => `${name}: ${int(total)} tokens per task run, ${int(uncached)} uncached`)
    .join("; ");
  chart("#token-chart", (plot, width) => {
    const bar = 20, gap = 2, labelH = 22, rowGap = 18, right = 150;
    const height = rows.length * (labelH + bar + rowGap) - rowGap + 4;
    const scale = (v) => (v / max) * (width - right);
    const root = svg("svg", { viewBox: `0 0 ${width} ${height}`, width, height, "aria-hidden": "true" });
    let y = 0;
    for (const [name, total, uncached] of rows) {
      const cached = total - uncached;
      root.append(svg("text", { x: 0, y: y + 15 }, name));
      y += labelH;
      const wu = scale(uncached), wc = Math.max(0, scale(cached) - gap);
      const mu = svg("path", { class: "mark", d: `M0,${y}h${wu}v${bar}h${-wu}z`, fill: "var(--s-uncached)" });
      const mc = svg("path", { class: "mark", d: barPath(wu + gap, y, wc, bar), fill: "var(--s-cached)" });
      root.append(mu, mc,
        svg("text", { class: "value-label", x: wu + gap + wc + 8, y: y + bar / 2 + 4.5 }, `${int(total)} tokens`),
        hit(plot, mu, { x: 0, y: y - 1, width: Math.max(wu, 12), height: bar + 2 }, `${int(uncached)} uncached tokens`, `${name}, per task run`),
        hit(plot, mc, { x: wu + gap, y: y - 1, width: Math.max(wc, 12), height: bar + 2 }, `${int(cached)} cached input tokens`, `${name}, per task run`));
      y += bar + rowGap;
    }
    return root;
  });
}

function kpi(label, value, detail) {
  return el("div", { class: "kpi" }, el("p", { class: "label" }, label), el("p", { class: "value" }, value), detail ? el("p", { class: "detail" }, detail) : null);
}

function renderHeadline(data) {
  const comparison = data.evidence?.["C-029"]?.sections?.comparison;
  if (!comparison) return;
  evidence = comparison;
  const share = comparison.cost_share;
  const r = comparison.results;
  $("#hero-saving").textContent = `${share.saving_percent.toFixed(1)}%`;
  $("#hero-caption").textContent = `per task run than Nemotron 3 Ultra alone, on the same ${comparison.tasks} tasks, `
    + `with ${r.ladder.passed} of ${r.ladder.runs} passed on both sides. The ladder spent ${share.percent.toFixed(1)}% of Ultra’s dollars `
    + `(${Math.round(share.interval.confidence * 100)}% interval ${share.interval.low.toFixed(1)}% to ${share.interval.high.toFixed(1)}%, `
    + `bootstrap over tasks).`;
  $("#kpis").replaceChildren(
    kpi("Tasks passed", `${r.ladder.passed} / ${r.ladder.runs}`, `Ultra alone: ${r.single.passed} / ${r.single.runs}`),
    kpi("Dollars per task run", usd(r.ladder.cost_per_task_usd), `Ultra alone: ${usd(r.single.cost_per_task_usd)}`),
    kpi("Uncached tokens per task run", int(r.ladder.uncached_tokens_per_task), `Ultra alone: ${int(r.single.uncached_tokens_per_task)}`),
    kpi("Minutes per task run", r.ladder.minutes_per_task.toFixed(2), `Ultra alone: ${r.single.minutes_per_task.toFixed(2)}; the ladder is slower`),
  );
  costChart(comparison);
  shareChart(comparison);
  tokenChart(comparison);
  const bill = comparison.bill;
  if (bill) {
    const c = bill.console;
    $("#bill").textContent = `The whole bill: every hosted bench run, failed ones included, came to ${usd(bill.total_usd, 2)} `
      + `at list prices on Stepswitch’s ledger. The Token Factory console showed ${usd(c.consumption_usd_incl_tax, 2)} `
      + `including tax for the day when read (${when(c.read)}); it also covers ${c.not_in_the_ledger}.`;
  }
}

// ---- the recorded run in the hero ---------------------------------------------------------

// The escalation demo's first escalated task that finished, condensed: consecutive calls of one
// model become one row, with every gate, review and escalation in between.
function renderHeroRun(data) {
  const run = data.runs.find((r) => kindOf(r) === "demo");
  const row = run?.rows.filter((r) => r.contestant === LADDER && r.escalations > 0)
    .sort((a, b) => (b.status === "done") - (a.status === "done"))[0];
  const card = $(".run-card");
  if (!row) { card?.remove(); return; }
  const events = run.steps[`${row.contestant}|${row.task}|${row.seed}`] || [];
  const rows = [];
  let group = null;
  for (const ev of events) {
    if (ev.type === "step" && ev.step_type === "review") continue; // its verdict row names the reviewer
    if (ev.type === "step") {
      if (group && group.worker === ev.worker) group.types.push(ev.step_type);
      else { group = { worker: ev.worker, types: [ev.step_type] }; rows.push(group); }
      continue;
    }
    if (["gates", "review", "escalation", "task_end"].includes(ev.type)) { rows.push(ev); group = null; }
  }
  const counted = (types) => [...types.reduce((m, t) => m.set(t, (m.get(t) || 0) + 1), new Map())]
    .map(([t, n]) => (n > 1 ? `${t} ×${n}` : t)).join(", ");
  $("#run-steps").replaceChildren(...rows.map((r) => {
    if (r.worker) return el("li", { class: "run-row" }, badge(r.worker), el("span", { class: "run-types" }, counted(r.types)));
    if (r.type === "gates") return el("li", { class: "run-row" }, el("span", { class: `verdict ${r.passed ? "ok" : "bad"}` }, r.passed ? "Gates passed" : `Gate failed: ${r.failed_gate.replace("_", " ")}`));
    if (r.type === "review") {
      const verdict = r.failed ? "no verdict" : r.approved ? "approved" : "blocked";
      return el("li", { class: "run-row" }, badge(r.reviewer), el("span", { class: `verdict ${r.approved ? "ok" : "bad"}` }, `${r.second_opinion ? "second opinion" : "review"}: ${verdict}`));
    }
    if (r.type === "escalation") return el("li", { class: "run-row escalated" }, el("span", { class: "verdict" }, "Escalated"), el("span", { class: "run-types" }, r.reason || ""));
    return el("li", { class: "run-row" }, el("span", { class: "st" }, `Task ${r.status}`));
  }));
  $("#run-foot").textContent = `Task ${row.task}, ${KINDS.demo}. ${usd(row.cost_usd)}, ${row.steps} model calls, `
    + `${(row.wall_seconds / 60).toFixed(1)} minutes. Recorded in run ${run.name}.`;
}

// ---- result tables ------------------------------------------------------------------------

function suiteCard(title, rows, note) {
  const both = shared(rows);
  const names = [...new Set(both.map((r) => r.contestant))].sort((a, b) => (a === LADDER ? -1 : b === LADDER ? 1 : 0));
  const stats = Object.fromEntries(names.map((n) => [n, summarize(both.filter((r) => r.contestant === n))]));
  const card = el("div", { class: "card" }, el("h3", {}, title));
  for (const n of names) {
    const s = stats[n];
    card.append(
      el("p", { class: "st" }, badgeFor(n), n === LADDER ? "" : "alone"),
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
    card.append(el("p", { class: "delta" }, `The ladder’s dollars: ${pct(1 - saved)} of ${model(other).label}’s on these task runs`));
  }
  if (note) card.append(el("p", { class: "meta" }, note));
  return card;
}

function badgeFor(name) {
  return name === LADDER ? el("span", { class: "badge m-ladder" }, "Nemotron ladder") : badge(name);
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
  if (pilot) alone.append(suiteCard(`${pilot.suite}, five-task pilot`, pilot.rows, "calibration run before the main runs; see the sources"));
  if (!evidence) {
    const total = data.runs.reduce((a, run) => a + summarize(run.rows).cost, 0);
    $("#bill").textContent = `Recorded spend of the runs on this page: ${usd(total, 2)} at list prices (Stepswitch’s ledger).`;
  }
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
  return el("div", {}, badge(ev.reviewer), el("span", { class: `verdict ${ev.approved ? "ok" : "bad"}` }, `${ev.second_opinion ? "Second opinion" : "Review"}: ${verdict}`), `${issues}${extra}`, ev.cross_family ? el("span", { class: "meta" }, ` · ${who} is from another model family`) : "");
}

function escalationLine(ev, events) {
  // The escalation names tiers; the next model call shows which model took over.
  const next = events.find((e) => e.type === "step" && e.seq > ev.seq);
  return el("div", {},
    el("span", { class: "verdict" }, "Escalated"),
    ` ${ev.reason || "the gates failed"}: tier ${ev.from} → ${ev.to}`,
    next ? el("span", {}, " · the work moves to ", badge(next.worker)) : "");
}

function lane(name, row, events, kind) {
  // The rule that picked each step's model; a single-model contestant is pinned, not routed.
  const rules = new Map(events.filter((e) => e.type === "decision" && e.rule && e.rule !== "--worker").map((e) => [e.step, e.rule]));
  const list = el("ol", { class: "events" });
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

let watchEscalation = null;

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
    const url = new URL(location.href);
    url.searchParams.set("run", run.name);
    url.searchParams.set("task", task);
    history.replaceState(null, "", url);
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
  watchEscalation = () => {
    const i = data.runs.findIndex((run) => escalated(run).length);
    if (i < 0) return;
    runSelect.value = i;
    fillTasks(escalated(data.runs[i])[0]);
    play();
  };
  $("#show-escalation")?.addEventListener("click", watchEscalation);
  $("#hero-escalation")?.addEventListener("click", (event) => {
    if (!watchEscalation) return;
    event.preventDefault();
    $("#replay").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    watchEscalation();
  });
  if (!data.runs.some((run) => escalated(run).length)) $("#show-escalation")?.remove();
  const params = new URLSearchParams(location.search);
  const linked = data.runs.findIndex((run) => run.name === params.get("run"));
  if (linked >= 0) runSelect.value = linked;
  const wanted = params.get("task");
  fillTasks(wanted && data.runs[runSelect.value].rows.some((r) => r.task === wanted) ? wanted : undefined);
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
    for (const l of lanes) if (l[i]) { l[i].classList.remove("hidden"); l[i].classList.add("reveal"); }
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
  $("#review-stats").replaceChildren(
    kpi("Changes with both reviews", int(pairs)),
    kpi("Verdicts agree", pairs ? `${agree} of ${pairs}` : "–", `${disagree} disagree, ${noVerdict} without a verdict on one side`),
    kpi("Approved by Nemotron 3 Ultra", int(firstApproved)),
    kpi("Approved by gpt-oss-120b", int(secondApproved)),
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
          s.models.add(ev.worker);
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
      el("td", {}, [...s.ladder.models].map((w) => badge(w))),
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
      el("code", {}, run.command || ""),
    ));
  }
}

setupTheme();
fetch("data.json")
  .then((r) => r.json())
  .then((data) => {
    renderHeadline(data);
    renderHeroRun(data);
    renderResults(data);
    renderLadder(data);
    renderReplay(data);
    renderReviews(data);
    renderStepTypes(data);
    renderProvenance(data);
  })
  .catch((err) => {
    document.querySelector("main").prepend(el("p", { class: "error" }, `Could not load the recorded runs (${err}). Reload the page; the same data is in the repository at hackathon/demo/site/data.json.`));
  });
