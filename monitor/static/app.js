/**
 * dbt Agent Monitor — Dashboard JavaScript
 *
 * Connects to the monitor WebSocket for real-time events and renders
 * them in the event log. Also fetches historical runs via REST API.
 */

// ── DOM elements ─────────────────────────────────────────────────────
const $status = document.getElementById("connection-status");
const $runSelect = document.getElementById("run-select");
const $btnRefresh = document.getElementById("btn-refresh");
const $runSummary = document.getElementById("run-summary");
const $eventLog = document.getElementById("event-log");
const $autoScroll = document.getElementById("auto-scroll");

// Summary fields
const $summaryRunId = document.getElementById("summary-run-id");
const $summaryAgentType = document.getElementById("summary-agent-type");
const $summaryStatus = document.getElementById("summary-status");
const $summaryDuration = document.getElementById("summary-duration");
const $summaryTokensIn = document.getElementById("summary-tokens-in");
const $summaryTokensOut = document.getElementById("summary-tokens-out");
const $summaryCost = document.getElementById("summary-cost");

// ── State ────────────────────────────────────────────────────────────
let ws = null;
let reconnectTimer = null;
let activeRunId = null;     // The run currently being displayed
let liveRunId = null;       // The run currently streaming live
let isLiveMode = false;     // Whether we're watching a live run
let runStartTime = null;    // For duration tracking
let durationTimer = null;   // Interval for live duration updates
let inSubAgent = false;     // Whether we're inside a sub-agent block

// Accumulated metrics for the summary bar (updated on invocation_end)
let metrics = {
  inputTokens: 0,
  outputTokens: 0,
  cost: 0,
};

// ── Formatting helpers ───────────────────────────────────────────────

function formatTime(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString);
  return d.toLocaleTimeString("en-US", { hour12: false });
}

function formatNumber(n) {
  if (n == null) return "-";
  return Number(n).toLocaleString("en-US");
}

function formatDuration(seconds) {
  if (seconds == null) return "-";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(0);
  return `${m}m ${s}s`;
}

function formatCost(usd) {
  if (usd == null) return "-";
  return `$${usd.toFixed(4)}`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function truncate(str, max) {
  if (!str) return "";
  if (str.length <= max) return str;
  return str.substring(0, max) + "...";
}


// ── WebSocket connection ─────────────────────────────────────────────

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  setConnectionStatus("connecting");

  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}/ws/live`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    setConnectionStatus("connected");
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  ws.onmessage = (evt) => {
    try {
      const event = JSON.parse(evt.data);
      handleLiveEvent(event);
    } catch (err) {
      console.error("Failed to parse event:", err);
    }
  };

  ws.onclose = () => {
    setConnectionStatus("disconnected");
    scheduleReconnect();
  };

  ws.onerror = () => {
    setConnectionStatus("disconnected");
  };
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, 3000);
}

function setConnectionStatus(state) {
  $status.textContent = state;
  $status.className = `status-${state}`;
}


// ── Live event handling ──────────────────────────────────────────────

function handleLiveEvent(event) {
  const runId = event.run_id;

  // If this is a run_start, switch to this live run
  if (event.type === "run_start") {
    liveRunId = runId;
    activeRunId = runId;
    isLiveMode = true;
    inSubAgent = false;

    // Clear the log and show this run
    clearEventLog();
    showSummary(runId, event.data.agent_type || event.agent, "running");
    runStartTime = new Date(event.timestamp);
    startDurationTimer();
    metrics = { inputTokens: 0, outputTokens: 0, cost: 0 };

    // Add to dropdown if not already there
    addRunToDropdown(runId, event.data.agent_type || event.agent, event.timestamp);
    $runSelect.value = "";
  }

  // Only render events for the active run
  if (runId !== activeRunId) return;

  // Update summary on certain event types
  if (event.type === "run_end") {
    const data = event.data || {};
    const statusText = data.success ? "success" : "failed";
    $summaryStatus.textContent = statusText;
    $summaryStatus.className = `summary-value ${data.success ? "status-success" : "status-error"}`;
    if (data.duration_s != null) {
      $summaryDuration.textContent = formatDuration(data.duration_s);
    }
    stopDurationTimer();
    isLiveMode = false;
    liveRunId = null;
  }

  if (event.type === "invocation_end") {
    const m = (event.data || {}).metrics || {};
    if (m.input_tokens) {
      metrics.inputTokens = m.input_tokens;
      $summaryTokensIn.textContent = formatNumber(m.input_tokens);
    }
    if (m.output_tokens) {
      metrics.outputTokens = m.output_tokens;
      $summaryTokensOut.textContent = formatNumber(m.output_tokens);
    }
    if (m.estimated_cost_usd != null) {
      metrics.cost = m.estimated_cost_usd;
      $summaryCost.textContent = formatCost(m.estimated_cost_usd);
    }
  }

  // Track sub-agent nesting
  if (event.type === "sub_agent_start") {
    inSubAgent = true;
  }
  if (event.type === "sub_agent_end") {
    inSubAgent = false;
  }

  // Render the event
  renderEvent(event);
}


// ── Event rendering ──────────────────────────────────────────────────

function renderEvent(event) {
  removeEmptyState();

  const entry = document.createElement("div");
  entry.className = "event-entry";
  if (inSubAgent && event.type !== "sub_agent_start" && event.type !== "sub_agent_end") {
    entry.classList.add("nested");
  }

  // Time column
  const timeEl = document.createElement("span");
  timeEl.className = "event-time";
  timeEl.textContent = formatTime(event.timestamp);
  entry.appendChild(timeEl);

  // Badge
  const badge = document.createElement("span");
  badge.className = `event-badge ${getBadgeClass(event.type)}`;
  badge.textContent = getBadgeLabel(event.type);
  entry.appendChild(badge);

  // Content
  const content = document.createElement("div");
  content.className = "event-content";
  content.appendChild(renderEventContent(event));
  entry.appendChild(content);

  $eventLog.appendChild(entry);
  maybeAutoScroll();
}

function getBadgeClass(type) {
  switch (type) {
    case "run_start":
    case "run_end":
      return "badge-run";
    case "invocation_start":
    case "invocation_end":
      return "badge-run";
    case "model_call_start":
    case "model_call_end":
      return "badge-llm";
    case "tool_start":
    case "tool_end":
      return "badge-tool";
    case "sub_agent_start":
    case "sub_agent_end":
      return "badge-agent";
    case "token":
      return "badge-token";
    case "reasoning":
      return "badge-think";
    case "metrics":
      return "badge-metrics";
    default:
      return "badge-run";
  }
}

function getBadgeLabel(type) {
  switch (type) {
    case "run_start": return "RUN";
    case "run_end": return "RUN";
    case "invocation_start": return "INVOKE";
    case "invocation_end": return "INVOKE";
    case "model_call_start": return "LLM";
    case "model_call_end": return "LLM";
    case "tool_start": return "TOOL";
    case "tool_end": return "TOOL";
    case "sub_agent_start": return "AGENT";
    case "sub_agent_end": return "AGENT";
    case "token": return "TOKEN";
    case "reasoning": return "THINK";
    case "metrics": return "STATS";
    default: return type.toUpperCase().substring(0, 6);
  }
}

function renderEventContent(event) {
  const frag = document.createDocumentFragment();
  const data = event.data || {};

  switch (event.type) {
    case "run_start": {
      const span = document.createElement("span");
      span.textContent = `Run started: ${data.agent_type || event.agent} (${event.run_id})`;
      frag.appendChild(span);
      break;
    }

    case "run_end": {
      const span = document.createElement("span");
      const statusClass = data.success ? "status-success" : "status-error";
      span.innerHTML = `Run ended: <span class="${statusClass}">${data.success ? "SUCCESS" : "FAILED"}</span>`;
      if (data.duration_s != null) {
        span.innerHTML += ` in ${formatDuration(data.duration_s)}`;
      }
      if (data.error) {
        span.innerHTML += ` — ${escapeHtml(truncate(data.error, 200))}`;
      }
      frag.appendChild(span);
      break;
    }

    case "invocation_start": {
      const span = document.createElement("span");
      span.textContent = `Agent invocation started (${data.agent_name || event.agent})`;
      frag.appendChild(span);
      break;
    }

    case "invocation_end": {
      const span = document.createElement("span");
      let text = `Agent invocation ended (${data.agent_name || event.agent})`;
      if (data.stop_reason) text += ` — stop: ${data.stop_reason}`;
      span.textContent = text;
      frag.appendChild(span);

      // Render metrics if present
      if (data.metrics) {
        frag.appendChild(renderMetrics(data.metrics));
      }
      break;
    }

    case "model_call_start": {
      const span = document.createElement("span");
      span.textContent = `LLM call started`;
      frag.appendChild(span);
      break;
    }

    case "model_call_end": {
      const span = document.createElement("span");
      let text = `LLM call ended`;
      if (data.stop_reason) text += ` — stop: ${data.stop_reason}`;
      span.textContent = text;
      if (data.error) {
        const errSpan = document.createElement("span");
        errSpan.className = "status-error";
        errSpan.textContent = ` Error: ${truncate(data.error, 200)}`;
        span.appendChild(errSpan);
      }
      frag.appendChild(span);
      break;
    }

    case "tool_start": {
      const span = document.createElement("span");
      span.textContent = `Tool call: ${data.tool_name || "unknown"}`;
      frag.appendChild(span);
      if (data.input) {
        frag.appendChild(renderCollapsible("Input", data.input));
      }
      break;
    }

    case "tool_end": {
      const span = document.createElement("span");
      const statusClass = data.status === "error" ? "status-error" : "status-success";
      span.innerHTML = `Tool result: ${escapeHtml(data.tool_name || "unknown")} — <span class="${statusClass}">${escapeHtml(data.status || "done")}</span>`;
      if (data.duration_s != null) {
        span.innerHTML += ` (${data.duration_s}s)`;
      }
      frag.appendChild(span);
      if (data.error) {
        frag.appendChild(renderCollapsible("Error", data.error));
      } else if (data.result) {
        frag.appendChild(renderCollapsible("Output", data.result));
      }
      break;
    }

    case "sub_agent_start": {
      const span = document.createElement("span");
      span.innerHTML = `Sub-agent delegated: <strong>${escapeHtml(data.sub_agent_name || "unknown")}</strong>`;
      frag.appendChild(span);
      if (data.input) {
        frag.appendChild(renderCollapsible("Input", data.input));
      }
      break;
    }

    case "sub_agent_end": {
      const span = document.createElement("span");
      const statusClass = data.status === "error" ? "status-error" : "status-success";
      span.innerHTML = `Sub-agent returned: <strong>${escapeHtml(data.tool_name || "unknown")}</strong> — <span class="${statusClass}">${escapeHtml(data.status || "done")}</span>`;
      if (data.duration_s != null) {
        span.innerHTML += ` (${data.duration_s}s)`;
      }
      frag.appendChild(span);
      if (data.error) {
        frag.appendChild(renderCollapsible("Error", data.error));
      } else if (data.result) {
        frag.appendChild(renderCollapsible("Output", data.result));
      }
      break;
    }

    case "token": {
      const span = document.createElement("span");
      span.className = "streaming-text";
      span.textContent = data.text || "";
      frag.appendChild(span);
      break;
    }

    case "reasoning": {
      const span = document.createElement("span");
      span.className = "reasoning-text";
      span.textContent = data.text || "";
      frag.appendChild(span);
      break;
    }

    case "metrics": {
      const span = document.createElement("span");
      span.textContent = "Final metrics";
      frag.appendChild(span);
      frag.appendChild(renderMetrics(data));
      break;
    }

    default: {
      const span = document.createElement("span");
      span.textContent = JSON.stringify(data);
      frag.appendChild(span);
    }
  }

  return frag;
}


// ── Metrics rendering ────────────────────────────────────────────────

function renderMetrics(m) {
  const wrapper = document.createElement("div");

  // Metrics grid
  const grid = document.createElement("div");
  grid.className = "metrics-grid";

  const cards = [
    { label: "Input Tokens", value: formatNumber(m.input_tokens) },
    { label: "Output Tokens", value: formatNumber(m.output_tokens) },
    { label: "Total Tokens", value: formatNumber(m.total_tokens) },
    { label: "Cache Read", value: formatNumber(m.cache_read_tokens) },
    { label: "Cache Write", value: formatNumber(m.cache_write_tokens) },
    { label: "Latency", value: m.latency_ms ? `${(m.latency_ms / 1000).toFixed(1)}s` : "-" },
    { label: "Cycles", value: m.cycle_count || "-" },
    { label: "Est. Cost", value: formatCost(m.estimated_cost_usd) },
  ];

  for (const c of cards) {
    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `
      <div class="metric-label">${escapeHtml(c.label)}</div>
      <div class="metric-value">${escapeHtml(String(c.value))}</div>
    `;
    grid.appendChild(card);
  }
  wrapper.appendChild(grid);

  // Tool summary table
  if (m.tools && Object.keys(m.tools).length > 0) {
    const table = document.createElement("table");
    table.className = "tool-summary-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>Tool</th>
          <th>Calls</th>
          <th>Success</th>
          <th>Errors</th>
          <th>Total Time</th>
        </tr>
      </thead>
    `;
    const tbody = document.createElement("tbody");
    for (const [name, tm] of Object.entries(m.tools)) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(name)}</td>
        <td>${tm.call_count || 0}</td>
        <td>${tm.success_count || 0}</td>
        <td>${tm.error_count || 0}</td>
        <td>${tm.total_time_s != null ? tm.total_time_s + "s" : "-"}</td>
      `;
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrapper.appendChild(table);
  }

  return wrapper;
}


// ── Collapsible details ──────────────────────────────────────────────

function renderCollapsible(label, content) {
  const details = document.createElement("details");
  details.className = "event-details";

  const summary = document.createElement("summary");
  summary.textContent = label;
  details.appendChild(summary);

  const pre = document.createElement("pre");
  // Try to pretty-print JSON
  if (typeof content === "string") {
    try {
      const parsed = JSON.parse(content);
      pre.textContent = JSON.stringify(parsed, null, 2);
    } catch {
      pre.textContent = content;
    }
  } else if (typeof content === "object") {
    pre.textContent = JSON.stringify(content, null, 2);
  } else {
    pre.textContent = String(content);
  }
  details.appendChild(pre);

  return details;
}


// ── Summary bar ──────────────────────────────────────────────────────

function showSummary(runId, agentType, status) {
  $runSummary.classList.remove("hidden");
  $summaryRunId.textContent = truncate(runId, 24);
  $summaryRunId.title = runId;
  $summaryAgentType.textContent = agentType || "-";
  $summaryStatus.textContent = status || "-";
  $summaryStatus.className = "summary-value";
  $summaryDuration.textContent = "-";
  $summaryTokensIn.textContent = "-";
  $summaryTokensOut.textContent = "-";
  $summaryCost.textContent = "-";
}

function hideSummary() {
  $runSummary.classList.add("hidden");
}

function startDurationTimer() {
  stopDurationTimer();
  durationTimer = setInterval(() => {
    if (runStartTime) {
      const elapsed = (Date.now() - runStartTime.getTime()) / 1000;
      $summaryDuration.textContent = formatDuration(elapsed);
    }
  }, 1000);
}

function stopDurationTimer() {
  if (durationTimer) {
    clearInterval(durationTimer);
    durationTimer = null;
  }
}


// ── Event log helpers ────────────────────────────────────────────────

function clearEventLog() {
  $eventLog.innerHTML = "";
}

function removeEmptyState() {
  const empty = $eventLog.querySelector(".empty-state");
  if (empty) empty.remove();
}

function maybeAutoScroll() {
  if ($autoScroll.checked) {
    $eventLog.scrollTop = $eventLog.scrollHeight;
  }
}


// ── Historical runs ──────────────────────────────────────────────────

async function fetchRuns() {
  try {
    const resp = await fetch("/api/runs");
    if (!resp.ok) return;
    const runs = await resp.json();
    populateRunDropdown(runs);
  } catch (err) {
    console.error("Failed to fetch runs:", err);
  }
}

function populateRunDropdown(runs) {
  // Keep the first "Select a run..." option
  while ($runSelect.options.length > 1) {
    $runSelect.remove(1);
  }

  for (const run of runs) {
    const opt = document.createElement("option");
    opt.value = run.run_id;
    const time = formatTime(run.started_at);
    const status = run.success === 1 ? "ok" : run.success === 0 ? "fail" : "...";
    opt.textContent = `${time} | ${run.agent_type || "?"} | ${status} | ${truncate(run.run_id, 16)}`;
    $runSelect.appendChild(opt);
  }
}

function addRunToDropdown(runId, agentType, timestamp) {
  // Check if already present
  for (const opt of $runSelect.options) {
    if (opt.value === runId) return;
  }
  const opt = document.createElement("option");
  opt.value = runId;
  const time = formatTime(timestamp);
  opt.textContent = `${time} | ${agentType || "?"} | ... | ${truncate(runId, 16)}`;
  // Insert after the placeholder
  if ($runSelect.options.length > 1) {
    $runSelect.insertBefore(opt, $runSelect.options[1]);
  } else {
    $runSelect.appendChild(opt);
  }
}

async function loadHistoricalRun(runId) {
  if (!runId) {
    // Deselected — go back to live mode if there is one
    if (liveRunId) {
      activeRunId = liveRunId;
      isLiveMode = true;
    } else {
      clearEventLog();
      hideSummary();
      activeRunId = null;
    }
    return;
  }

  activeRunId = runId;
  isLiveMode = false;
  inSubAgent = false;
  stopDurationTimer();
  clearEventLog();

  try {
    const resp = await fetch(`/api/runs/${encodeURIComponent(runId)}`);
    if (!resp.ok) return;
    const events = await resp.json();

    if (events.length === 0) {
      $eventLog.innerHTML = '<div class="empty-state"><p>No events found for this run.</p></div>';
      hideSummary();
      return;
    }

    // Find run_start to populate summary
    const startEvt = events.find(e => e.type === "run_start");
    const endEvt = events.find(e => e.type === "run_end");
    const invEnd = [...events].reverse().find(e => e.type === "invocation_end");

    if (startEvt) {
      const startData = startEvt.data || {};
      showSummary(
        runId,
        startData.agent_type || startEvt.agent_name,
        endEvt ? (endEvt.data?.success ? "success" : "failed") : "unknown"
      );

      if (endEvt && endEvt.data?.duration_s != null) {
        $summaryDuration.textContent = formatDuration(endEvt.data.duration_s);
      }

      if (endEvt) {
        $summaryStatus.className = `summary-value ${endEvt.data?.success ? "status-success" : "status-error"}`;
      }
    }

    if (invEnd && invEnd.data?.metrics) {
      const m = invEnd.data.metrics;
      $summaryTokensIn.textContent = formatNumber(m.input_tokens);
      $summaryTokensOut.textContent = formatNumber(m.output_tokens);
      $summaryCost.textContent = formatCost(m.estimated_cost_usd);
    }

    // Render all events
    for (const evt of events) {
      // Reconstruct the event in the expected shape
      const event = {
        type: evt.type,
        run_id: evt.run_id,
        agent: evt.agent_name,
        timestamp: evt.timestamp,
        data: evt.data || {},
      };

      if (event.type === "sub_agent_start") inSubAgent = true;
      if (event.type === "sub_agent_end") inSubAgent = false;

      renderEvent(event);
    }

  } catch (err) {
    console.error("Failed to load historical run:", err);
  }
}


// ── Event listeners ──────────────────────────────────────────────────

$runSelect.addEventListener("change", () => {
  loadHistoricalRun($runSelect.value);
});

$btnRefresh.addEventListener("click", () => {
  fetchRuns();
});


// ── Initialize ───────────────────────────────────────────────────────

connect();
fetchRuns();
