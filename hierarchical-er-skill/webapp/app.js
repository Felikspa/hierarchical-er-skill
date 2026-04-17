import { renderHistory } from "./components/history.js";
import {
  renderConfidence,
  renderGraph,
  renderIssues,
  renderSelectableList,
  renderSummaryCards,
} from "./components/lists.js";
import { renderReview } from "./components/review.js";

const THEME_KEY = "hierarchical-er-theme";
const state = {
  index: null,
  payload: null,
  viewMode: "fine",
  selectedEntityId: null,
  selectedRelationId: null,
  leftDockCollapsed: false,
  rightDockCollapsed: false,
  theme: localStorage.getItem(THEME_KEY) ?? "light",
  filters: {
    low: false,
    conflicts: false,
    edited: false,
  },
  draft: {
    entities: [],
    relations: [],
    reviewNote: "",
  },
};

const nodes = {
  shell: document.querySelector("#shell"),
  latestRunChip: document.querySelector("#latestRunChip"),
  themeButton: document.querySelector("#themeButton"),
  refreshButton: document.querySelector("#refreshButton"),
  leftDockToggle: document.querySelector("#leftDockToggle"),
  rightDockToggle: document.querySelector("#rightDockToggle"),
  historyPanel: document.querySelector("#historyPanel"),
  summaryCards: document.querySelector("#summaryCards"),
  modeSwitch: document.querySelector("#modeSwitch"),
  filterRow: document.querySelector("#filterRow"),
  sourcePanel: document.querySelector("#sourcePanel"),
  entityPanel: document.querySelector("#entityPanel"),
  relationPanel: document.querySelector("#relationPanel"),
  graphPanel: document.querySelector("#graphPanel"),
  confidencePanel: document.querySelector("#confidencePanel"),
  issuePanel: document.querySelector("#issuePanel"),
  errorPanel: document.querySelector("#errorPanel"),
  reviewPanel: document.querySelector("#reviewPanel"),
};

function structuredCloneSafe(value) {
  return JSON.parse(JSON.stringify(value));
}

function applyShellState() {
  nodes.shell.classList.toggle("left-collapsed", state.leftDockCollapsed);
  nodes.shell.classList.toggle("right-collapsed", state.rightDockCollapsed);
  document.documentElement.dataset.theme = state.theme;
  document.documentElement.style.colorScheme = state.theme;
  nodes.leftDockToggle.setAttribute("aria-expanded", String(!state.leftDockCollapsed));
  nodes.rightDockToggle.setAttribute("aria-expanded", String(!state.rightDockCollapsed));
  nodes.themeButton.setAttribute("aria-pressed", String(state.theme === "dark"));
  nodes.themeButton.setAttribute(
    "aria-label",
    state.theme === "dark" ? "切换到浅色主题" : "切换到深色主题",
  );
  nodes.themeButton.querySelector(".button-label").textContent =
    state.theme === "dark" ? "切换浅色" : "切换深色";
  nodes.themeButton.querySelector(".button-icon").innerHTML =
    state.theme === "dark"
      ? `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="4"></circle>
          <path d="M12 2v2.4M12 19.6V22M4.93 4.93l1.7 1.7M17.37 17.37l1.7 1.7M2 12h2.4M19.6 12H22M4.93 19.07l1.7-1.7M17.37 6.63l1.7-1.7"></path>
        </svg>
      `
      : `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"></path>
        </svg>
      `;
  nodes.leftDockToggle.querySelector(".dock-icon").innerHTML = state.leftDockCollapsed
    ? `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10 6l6 6-6 6"></path>
      </svg>
    `
    : `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 6l-6 6 6 6"></path>
      </svg>
    `;
  nodes.rightDockToggle.querySelector(".dock-icon").innerHTML = state.rightDockCollapsed
    ? `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 6l-6 6 6 6"></path>
      </svg>
    `
    : `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10 6l6 6-6 6"></path>
      </svg>
    `;
}

function setTheme(nextTheme) {
  state.theme = nextTheme;
  localStorage.setItem(THEME_KEY, nextTheme);
  applyShellState();
}

function toggleTheme() {
  setTheme(state.theme === "dark" ? "light" : "dark");
}

function toggleDock(side) {
  if (side === "left") {
    state.leftDockCollapsed = !state.leftDockCollapsed;
  } else {
    state.rightDockCollapsed = !state.rightDockCollapsed;
  }
  applyShellState();
}

function getCollections(run, mode) {
  if (mode === "coarse") {
    return {
      entities: run.entities_coarse,
      relations: run.relations_coarse,
    };
  }
  return {
    entities: run.entities_fine,
    relations: run.relations_fine,
  };
}

function getBaselineCollections() {
  return getCollections(state.payload.run, state.viewMode);
}

function getEditedIds() {
  const baseline = getBaselineCollections();
  const entityChanges = new Set();
  const relationChanges = new Set();

  baseline.entities.forEach((entity) => {
    const draftEntity = state.draft.entities.find((item) => item.entity_id === entity.entity_id);
    if (!draftEntity) {
      entityChanges.add(entity.entity_id);
      return;
    }
    if (draftEntity.label !== entity.label || draftEntity.canonical_name !== entity.canonical_name) {
      entityChanges.add(entity.entity_id);
    }
  });

  baseline.relations.forEach((relation) => {
    const draftRelation = state.draft.relations.find((item) => item.relation_id === relation.relation_id);
    if (!draftRelation) {
      relationChanges.add(relation.relation_id);
      return;
    }
    if (
      draftRelation.type !== relation.type ||
      draftRelation.head_id !== relation.head_id ||
      draftRelation.tail_id !== relation.tail_id ||
      draftRelation.direction !== relation.direction
    ) {
      relationChanges.add(relation.relation_id);
    }
  });

  return { entityChanges, relationChanges };
}

function applyFilters() {
  const base = getBaselineCollections();
  const issuesByTarget = new Map();
  state.payload.run.issues.forEach((issue) => {
    issue.target_ids.forEach((targetId) => {
      const current = issuesByTarget.get(targetId) ?? [];
      current.push(issue);
      issuesByTarget.set(targetId, current);
    });
  });
  const lowIds = new Set(
    [...state.payload.run.confidence.entities, ...state.payload.run.confidence.relations]
      .filter((item) => item.band === "low")
      .map((item) => item.target_id),
  );
  const editedIds = getEditedIds();

  return {
    entities: base.entities.filter((entity) => {
      if (state.filters.low && !lowIds.has(entity.entity_id)) return false;
      if (state.filters.conflicts && !(issuesByTarget.get(entity.entity_id)?.length > 0)) return false;
      if (state.filters.edited && !editedIds.entityChanges.has(entity.entity_id)) return false;
      return true;
    }),
    relations: base.relations.filter((relation) => {
      if (state.filters.low && !lowIds.has(relation.relation_id)) return false;
      if (state.filters.conflicts && !(issuesByTarget.get(relation.relation_id)?.length > 0)) return false;
      if (state.filters.edited && !editedIds.relationChanges.has(relation.relation_id)) return false;
      return true;
    }),
  };
}

function renderSource() {
  const run = state.payload.run;
  const selectedEntity = getBaselineCollections().entities.find(
    (entity) => entity.entity_id === state.selectedEntityId,
  );
  nodes.sourcePanel.innerHTML = `
    <div class="panel-title">
      <h2>原文与证据</h2>
      <span class="subtle">${run.language} · ${run.mode}</span>
    </div>
    <div class="source-grid">
      <div class="item-list">
        ${run.chunks
          .map((chunk) => {
            let text = chunk.text;
            if (selectedEntity && selectedEntity.span.chunk_id === chunk.chunk_id) {
              const start = selectedEntity.span.start - chunk.start;
              const end = selectedEntity.span.end - chunk.start;
              text = `
                ${chunk.text.slice(0, start)}
                <span class="chunk-highlight">${chunk.text.slice(start, end)}</span>
                ${chunk.text.slice(end)}
              `;
            }
            return `
              <article class="chunk-card">
                <div class="row-inline">
                  <span class="badge mono">${chunk.chunk_id}</span>
                  <span class="badge">sentences ${chunk.sentence_start}-${chunk.sentence_end}</span>
                </div>
                <p class="chunk-text">${text}</p>
              </article>
            `;
          })
          .join("")}
      </div>
      <div>
        <div class="panel-title panel-title-tight">
          <h3>证据卡片</h3>
          <span class="subtle">${run.evidence.length} evidence</span>
        </div>
        <div class="evidence-list">
          ${run.evidence
            .map(
              (evidence) => `
                <article class="evidence-card">
                  <div class="row-inline">
                    <span class="badge mono">${evidence.evidence_id}</span>
                    <span class="badge">sentence ${evidence.sentence_index}</span>
                  </div>
                  <p class="subtle">${evidence.text}</p>
                </article>
              `,
            )
            .join("")}
        </div>
      </div>
    </div>
  `;
}

function renderModeSwitch() {
  const modes = ["coarse", "standard", "fine"];
  nodes.modeSwitch.innerHTML = modes
    .map(
      (mode) => `
        <button class="mode-button ${state.viewMode === mode ? "active" : ""}" data-mode="${mode}" type="button">${mode}</button>
      `,
    )
    .join("");
  nodes.modeSwitch.querySelectorAll("[data-mode]").forEach((button) => {
    button.addEventListener("click", () => {
      state.viewMode = button.dataset.mode;
      resetDraftFromCurrent();
      renderApp();
    });
  });
}

function renderFilters() {
  const filterDefs = [
    ["low", "仅低置信"],
    ["conflicts", "仅冲突项"],
    ["edited", "仅已编辑"],
  ];
  nodes.filterRow.innerHTML = filterDefs
    .map(
      ([key, label]) => `
        <button class="filter-button ${state.filters[key] ? "active" : ""}" data-filter="${key}" type="button">${label}</button>
      `,
    )
    .join("");
  nodes.filterRow.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.filter;
      state.filters[key] = !state.filters[key];
      renderApp();
    });
  });
}

function renderErrorCapture() {
  const capture = state.payload.run.error_capture;
  nodes.errorPanel.innerHTML = `
    <div class="panel-title">
      <h2>Error Set</h2>
      <span class="subtle">${capture.should_capture ? "captured" : "not captured"}</span>
    </div>
    <div class="item-list">
      <article class="item-card">
        <div class="item-meta">
          <span class="badge ${capture.should_capture ? "warning" : ""}">${capture.should_capture}</span>
          <span class="badge mono">${capture.case_id ?? "no-case"}</span>
        </div>
        <p class="subtle">${capture.reasons.join(" / ") || "当前没有触发错误样本规则。"}</p>
      </article>
      <article class="item-card">
        <h3>Few-shot tags</h3>
        <p class="subtle">${capture.suggestions.few_shot_tags.join(", ") || "暂无建议"}</p>
      </article>
      <article class="item-card">
        <h3>Prompt 优化点</h3>
        <p class="subtle">${capture.suggestions.prompt_optimizations.join("；") || "暂无建议"}</p>
      </article>
    </div>
  `;
}

function renderReviewPanel() {
  renderReview(
    nodes.reviewPanel,
    state.draft,
    state.payload.run.review_status,
    async (draft) => {
      await fetch("/api/review", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          run_id: state.payload.run.run_id,
          mode: state.viewMode,
          entities: draft.entities,
          relations: draft.relations,
          review_note: draft.reviewNote ?? "",
        }),
      });
      await loadIndex();
      await loadRun(state.payload.run.run_id);
    },
    () => {
      resetDraftFromCurrent();
      renderApp();
    },
  );
}

function attachSelectionHandlers() {
  nodes.entityPanel.querySelectorAll("[data-item-id]").forEach((node) => {
    node.addEventListener("click", () => {
      state.selectedEntityId = node.dataset.itemId;
      renderApp();
    });
  });
  nodes.relationPanel.querySelectorAll("[data-item-id]").forEach((node) => {
    node.addEventListener("click", () => {
      state.selectedRelationId = node.dataset.itemId;
      renderApp();
    });
  });
}

function resetDraftFromCurrent() {
  const reviewed = state.payload.reviewed_run;
  const sourceRun = reviewed ?? state.payload.run;
  const collections = getCollections(sourceRun, state.viewMode);
  state.draft = {
    entities: structuredCloneSafe(collections.entities),
    relations: structuredCloneSafe(collections.relations),
    reviewNote: sourceRun.review_note ?? "",
  };
}

function renderApp() {
  if (!state.index || !state.payload) return;
  const filtered = applyFilters();
  const run = state.payload.run;

  nodes.latestRunChip.textContent = `latest ${state.index.latest_run_id ?? "none"}`;
  renderHistory(nodes.historyPanel, state.index.runs, run.run_id, (runId) => loadRun(runId));
  renderModeSwitch();
  renderFilters();
  renderSummaryCards(nodes.summaryCards, [
    { label: "当前模式", value: state.viewMode },
    { label: "实体数", value: `${getBaselineCollections().entities.length}` },
    { label: "关系数", value: `${getBaselineCollections().relations.length}` },
    { label: "低置信项", value: `${run.confidence.summary.low}` },
  ]);
  renderSelectableList(
    nodes.entityPanel,
    "实体结果",
    filtered.entities,
    state.selectedEntityId,
    "entity",
    `${filtered.entities.length} visible`,
  );
  renderSelectableList(
    nodes.relationPanel,
    "关系结果",
    filtered.relations,
    state.selectedRelationId,
    "relation",
    `${filtered.relations.length} visible`,
  );
  renderGraph(nodes.graphPanel, state.payload.graph_memory, run.graph_updates);
  renderReviewPanel();
  renderSource();
  renderConfidence(nodes.confidencePanel, [...run.confidence.entities, ...run.confidence.relations]);
  renderIssues(nodes.issuePanel, run.issues);
  renderErrorCapture();
  attachSelectionHandlers();
}

async function loadIndex() {
  const response = await fetch("/api/state.json");
  state.index = await response.json();
}

async function loadRun(runId) {
  const response = await fetch(`/api/run.json?run_id=${encodeURIComponent(runId)}`);
  state.payload = await response.json();
  state.selectedEntityId = getCollections(state.payload.run, state.viewMode).entities[0]?.entity_id ?? null;
  state.selectedRelationId = getCollections(state.payload.run, state.viewMode).relations[0]?.relation_id ?? null;
  resetDraftFromCurrent();
  renderApp();
}

async function boot() {
  await loadIndex();
  if (state.index.latest_run_id) {
    await loadRun(state.index.latest_run_id);
  }
}

nodes.refreshButton.addEventListener("click", boot);
nodes.themeButton.addEventListener("click", toggleTheme);
nodes.leftDockToggle.addEventListener("click", () => toggleDock("left"));
nodes.rightDockToggle.addEventListener("click", () => toggleDock("right"));

applyShellState();
boot();
