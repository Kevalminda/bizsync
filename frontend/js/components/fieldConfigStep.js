import { i18n } from "../i18n.js";
import { store } from "../state.js";

export function renderFieldConfigStep() {
  const targetStr = store.wizard.targetFields.join(", ");
  const requiredStr = store.wizard.requiredFields.join(", ");

  return `
    <div class="card">
      <div class="card-header">
        <div>
          <h3 class="card-title">${i18n.t("targetFields.title")}</h3>
          <p class="card-subtitle">${i18n.t("targetFields.subtitle")}</p>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">${i18n.t("targetFields.targetFieldsLabel")}</label>
        <textarea id="target-fields-input" class="form-textarea" rows="3" placeholder="Order No., SKU ID, Product Name, Quantity, Date">${targetStr}</textarea>
        <p class="form-help">Enter all destination column headers in desired column order.</p>
      </div>

      <div class="form-group">
        <label class="form-label">${i18n.t("targetFields.requiredFieldsLabel")}</label>
        <textarea id="required-fields-input" class="form-textarea" rows="2" placeholder="Order No., Product Name, Quantity">${requiredStr}</textarea>
        <p class="form-help">Records missing any required field values will be flagged as SKIPPED.</p>
      </div>

      <div class="form-group">
        <label class="form-label">${i18n.t("targetFields.uniqueKeysLabel")}</label>
        <div id="key-fields-checkboxes" style="display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 0.5rem;">
          ${store.wizard.targetFields
            .map((field) => {
              const isChecked = store.wizard.uniqueKeyFields.includes(field);
              return `
              <label style="display: inline-flex; align-items: center; gap: 0.5rem; background: var(--bg-surface-elevated); padding: 0.5rem 0.85rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); cursor: pointer;">
                <input type="checkbox" class="key-field-checkbox" value="${field}" ${isChecked ? "checked" : ""} />
                <span style="font-size: 0.9rem; font-weight: 600; color: var(--text-primary);">${field}</span>
              </label>
            `;
            })
            .join("")}
        </div>
        <p class="form-help">${i18n.t("targetFields.selectKeyHelp")}</p>
      </div>
    </div>
  `;
}

export function saveFieldConfigStep() {
  const targetInput = document.getElementById("target-fields-input");
  const requiredInput = document.getElementById("required-fields-input");
  const keyCheckboxes = document.querySelectorAll(".key-field-checkbox:checked");

  if (targetInput) {
    const targets = targetInput.value
      .split(",")
      .map((s) => s.strip ? s.strip() : s.trim())
      .filter(Boolean);

    const required = requiredInput
      ? requiredInput.value
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
      : [];

    const keys = Array.from(keyCheckboxes).map((cb) => cb.value);

    store.updateWizard({
      targetFields: targets.length ? targets : store.wizard.targetFields,
      requiredFields: required,
      uniqueKeyFields: keys.length ? keys : [targets[0]],
    });
  }
}
