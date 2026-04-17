export function renderHistory(container, runs, currentRunId, onSelect) {
  container.innerHTML = `
    <div class="panel-title">
      <h2>历史运行</h2>
      <span class="subtle">${runs.length} runs</span>
    </div>
    <div class="history-list">
      ${runs
        .map(
          (run) => `
            <article class="history-item ${run.run_id === currentRunId ? "active" : ""}" data-run-id="${run.run_id}">
              <h3>${run.run_id}</h3>
              <div class="item-meta">
                <span class="badge">${run.mode}</span>
                <span class="badge">${run.issue_count} issues</span>
              </div>
              <p class="subtle">${run.created_at}</p>
            </article>
          `,
        )
        .join("")}
    </div>
  `;

  container.querySelectorAll("[data-run-id]").forEach((node) => {
    node.addEventListener("click", () => onSelect(node.dataset.runId));
  });
}

