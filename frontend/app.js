const backendModeEl = document.getElementById("backend-mode");
const formEl = document.getElementById("search-form");
const queryInputEl = document.getElementById("query-input");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const rawOutputSectionEl = document.getElementById("raw-output");
const rawOutputTextEl = document.getElementById("raw-output-text");
const resultTemplateEl = document.getElementById("result-template");
const searchButtonEl = document.getElementById("search-button");
const softButtonEl = document.getElementById("soft-button");
const exactButtonEl = document.getElementById("exact-button");
const modeButtons = Array.from(document.querySelectorAll(".mode-button"));

let currentMode = "search";

async function loadHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) {
      throw new Error("Failed to load backend status");
    }
    const payload = await response.json();
    backendModeEl.textContent = payload.backend;
  } catch (error) {
    backendModeEl.textContent = "unavailable";
    setStatus(error.message, "error");
  }
}

function setStatus(message, kind = "info") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`;
}

function clearResults() {
  resultsEl.innerHTML = "";
  rawOutputTextEl.textContent = "";
  rawOutputSectionEl.classList.add("hidden");
}

function setMode(mode) {
  currentMode = mode;
  modeButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.mode === mode);
  });
  console.log("[softmatcha-playground] mode set", mode);
}

function renderResults(payload) {
  clearResults();

  if (!payload.matches.length) {
    setStatus("No matches found for this query.", "empty");
  } else {
    setStatus(`Showing ${payload.matches.length} result(s) from ${payload.backend}.`, "success");
  }

  payload.matches.forEach((match) => {
    const fragment = resultTemplateEl.content.cloneNode(true);
    fragment.querySelector(".match-type").textContent = match.match_type;
    fragment.querySelector(".score").textContent = match.score == null ? "score: n/a" : `score: ${match.score}`;
    fragment.querySelector(".text").textContent = match.text;
    fragment.querySelector(".source").textContent = match.source ? `source: ${match.source}` : "source: n/a";
    fragment.querySelector(".rank").textContent =
      match.metadata && typeof match.metadata.rank !== "undefined" ? `rank: ${match.metadata.rank}` : "";
    resultsEl.appendChild(fragment);
  });

  if (payload.raw_output) {
    rawOutputTextEl.textContent = payload.raw_output;
    rawOutputSectionEl.classList.remove("hidden");
  }
}

async function runQuery(mode) {
  const query = queryInputEl.value.trim();
  clearResults();

  if (!query) {
    setStatus("Enter a query first.", "error");
    return;
  }

  setStatus(`Running ${mode}...`, "info");
  console.log("[softmatcha-playground] request", { mode, query, url: `/${mode}?q=${encodeURIComponent(query)}` });

  try {
    const response = await fetch(`/${mode}?q=${encodeURIComponent(query)}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Request failed");
    }
    renderResults(payload);
  } catch (error) {
    setStatus(error.message, "error");
  }
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  runQuery(currentMode);
});

searchButtonEl.addEventListener("click", () => {
  setMode("search");
  runQuery("search");
});

softButtonEl.addEventListener("click", () => {
  setMode("soft");
  runQuery("soft");
});

exactButtonEl.addEventListener("click", () => {
  setMode("exact");
  runQuery("exact");
});

loadHealth();
