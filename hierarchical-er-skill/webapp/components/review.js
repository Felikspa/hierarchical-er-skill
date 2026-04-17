function entityRow(entity) {
  return `
    <tr>
      <td class="mono">${entity.entity_id}</td>
      <td><input data-kind="entity-label" data-id="${entity.entity_id}" value="${entity.label}" /></td>
      <td><input data-kind="entity-canonical" data-id="${entity.entity_id}" value="${entity.canonical_name}" /></td>
    </tr>
  `;
}

function relationRow(relation) {
  return `
    <tr>
      <td class="mono">${relation.relation_id}</td>
      <td><input data-kind="relation-type" data-id="${relation.relation_id}" value="${relation.type}" /></td>
      <td><input data-kind="relation-head" data-id="${relation.relation_id}" value="${relation.head_id}" /></td>
      <td><input data-kind="relation-tail" data-id="${relation.relation_id}" value="${relation.tail_id}" /></td>
      <td><input data-kind="relation-direction" data-id="${relation.relation_id}" value="${relation.direction}" /></td>
    </tr>
  `;
}

export function renderReview(container, draft, reviewStatus, onSave, onReset) {
  container.innerHTML = `
    <div class="panel-title">
      <h2>人工 Review</h2>
      <span class="subtle">${reviewStatus.status}</span>
    </div>
    <div class="review-grid">
      <div>
        <h3>实体编辑</h3>
        <table class="review-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Label</th>
              <th>Canonical</th>
            </tr>
          </thead>
          <tbody>${draft.entities.map(entityRow).join("")}</tbody>
        </table>
      </div>
      <div>
        <h3>关系编辑</h3>
        <table class="review-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Head</th>
              <th>Tail</th>
              <th>Direction</th>
            </tr>
          </thead>
          <tbody>${draft.relations.map(relationRow).join("")}</tbody>
        </table>
      </div>
      <label>
        <span class="subtle">Review note</span>
        <textarea class="review-note" id="reviewNote">${draft.reviewNote ?? ""}</textarea>
      </label>
      <div class="review-actions">
        <button class="secondary-button" type="button" id="resetReviewButton">重置草稿</button>
        <button class="save-button" type="button" id="saveReviewButton">保存修订</button>
      </div>
    </div>
  `;

  container.querySelectorAll("input[data-kind]").forEach((input) => {
    input.addEventListener("input", () => {
      const { kind, id } = input.dataset;
      if (kind.startsWith("entity")) {
        const entity = draft.entities.find((item) => item.entity_id === id);
        if (kind === "entity-label") entity.label = input.value;
        if (kind === "entity-canonical") entity.canonical_name = input.value;
      }
      if (kind.startsWith("relation")) {
        const relation = draft.relations.find((item) => item.relation_id === id);
        if (kind === "relation-type") relation.type = input.value;
        if (kind === "relation-head") relation.head_id = input.value;
        if (kind === "relation-tail") relation.tail_id = input.value;
        if (kind === "relation-direction") relation.direction = input.value;
      }
    });
  });

  container.querySelector("#saveReviewButton").addEventListener("click", () => {
    draft.reviewNote = container.querySelector("#reviewNote").value;
    onSave(draft);
  });
  container.querySelector("#resetReviewButton").addEventListener("click", onReset);
}

