export function renderSummaryCards(container, cards) {
  container.innerHTML = cards
    .map(
      (card) => `
        <div class="metric-card">
          <div class="metric-label">${card.label}</div>
          <div class="metric-value">${card.value}</div>
        </div>
      `,
    )
    .join("");
}

export function renderSelectableList(container, title, items, selectedId, type, subtitle = "") {
  const idKey = type === "entity" ? "entity_id" : "relation_id";
  const headline = type === "entity" ? "canonical_name" : "type";
  container.innerHTML = `
    <div class="panel-title">
      <h2>${title}</h2>
      <span class="subtle">${subtitle}</span>
    </div>
    <div class="item-list">
      ${
        items.length === 0
          ? `<div class="empty-state">当前过滤条件下没有项目。</div>`
          : items
              .map((item) => {
                const itemId = item[idKey];
                return `
                  <article class="item-card ${itemId === selectedId ? "active" : ""}" data-item-id="${itemId}" data-item-type="${type}">
                    <h3>${item[headline]}</h3>
                    <div class="item-meta">
                      <span class="badge">${type === "entity" ? item.label : item.direction}</span>
                      <span class="badge mono">${itemId}</span>
                    </div>
                    <p class="subtle">${type === "entity" ? item.text : `${item.head_id} → ${item.tail_id}`}</p>
                  </article>
                `;
              })
              .join("")
      }
    </div>
  `;
}

export function renderConfidence(container, items) {
  container.innerHTML = `
    <div class="panel-title">
      <h2>置信度分层</h2>
      <span class="subtle">${items.length} items</span>
    </div>
    <div class="confidence-list">
      ${
        items.length === 0
          ? `<div class="empty-state">当前运行还没有置信度数据。</div>`
          : items
              .map(
                (item) => `
                  <article class="confidence-card">
                    <div class="row-inline">
                      <strong>${item.target_id}</strong>
                      <span class="badge ${item.band === "low" ? "danger" : item.band === "medium" ? "warning" : ""}">${item.band}</span>
                    </div>
                    <div class="confidence-bar"><div class="confidence-fill" style="width:${item.final * 100}%"></div></div>
                    <div class="stack-inline subtle">
                      <span>final ${item.final}</span>
                      <span>model ${item.model_score}</span>
                      <span>evidence ${item.evidence_score}</span>
                      <span>rule ${item.rule_score}</span>
                    </div>
                  </article>
                `,
              )
              .join("")
      }
    </div>
  `;
}

export function renderIssues(container, issues) {
  container.innerHTML = `
    <div class="panel-title">
      <h2>冲突与问题</h2>
      <span class="subtle">${issues.length} issues</span>
    </div>
    <div class="issue-list">
      ${
        issues.length === 0
          ? `<div class="empty-state">当前运行没有显式 issues。</div>`
          : issues
              .map(
                (issue) => `
                  <article class="issue-card">
                    <h3>${issue.code}</h3>
                    <div class="item-meta">
                      <span class="badge ${issue.level === "error" ? "danger" : issue.level === "warning" ? "warning" : ""}">${issue.level}</span>
                      <span class="badge mono">${issue.target_ids.join(", ")}</span>
                    </div>
                    <p class="subtle">${issue.message}</p>
                  </article>
                `,
              )
              .join("")
      }
    </div>
  `;
}

export function renderGraph(container, graphMemory, graphUpdates) {
  container.innerHTML = `
    <div class="panel-title">
      <h2>Graph Memory 增量摘要</h2>
      <span class="subtle">entities ${graphMemory.entities.length} · relations ${graphMemory.relations.length}</span>
    </div>
    <div class="graph-list">
      <article class="graph-card">
        <div class="item-meta">
          <span class="badge">matched ${graphUpdates.summary.matched}</span>
          <span class="badge">new ${graphUpdates.summary.created}</span>
          <span class="badge">relations ${graphUpdates.summary.relations_created}</span>
        </div>
        <p class="subtle">last updated: ${graphMemory.last_updated}</p>
      </article>
      ${graphUpdates.new_relations
        .map(
          (relation) => `
            <article class="graph-card">
              <h3>${relation.type}</h3>
              <p class="subtle mono">${relation.head_graph_id} → ${relation.tail_graph_id}</p>
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

