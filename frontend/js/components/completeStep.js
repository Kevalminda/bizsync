import { i18n } from "../i18n.js";
import { store } from "../state.js";

export function renderCompleteStep() {
  const { executionResult, spreadsheetUrl } = store.wizard;

  if (!executionResult) {
    return `
      <div class="card">
        <div class="empty-state">
          <div class="empty-icon">🔄</div>
          <div class="empty-title">Applying changes to Google Sheets...</div>
        </div>
      </div>
    `;
  }

  const { written_new, written_updated, summary, errors } = executionResult;

  return `
    <div class="card" style="text-align: center; padding: 3rem 2rem;">
      <div style="width: 72px; height: 72px; border-radius: var(--radius-full); background: var(--accent-green-bg); border: 2px solid #34d399; color: #34d399; font-size: 2.5rem; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 1.5rem;">
        ✓
      </div>

      <h2 style="font-size: 1.75rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.5rem;">
        ${i18n.t("execution.title")}
      </h2>
      <p style="color: var(--text-secondary); margin-bottom: 2rem;">
        ${i18n.t("execution.subtitle")}
      </p>

      <div class="stats-grid" style="max-width: 600px; margin: 0 auto 2.5rem auto;">
        <div class="stat-card">
          <div class="stat-icon" style="background: var(--accent-green-bg); color: #34d399;">➕</div>
          <div class="stat-content">
            <span class="stat-value">${written_new}</span>
            <span class="stat-label">${i18n.t("execution.newWritten")}</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background: var(--accent-amber-bg); color: #fbbf24;">✏️</div>
          <div class="stat-content">
            <span class="stat-value">${written_updated}</span>
            <span class="stat-label">${i18n.t("execution.updatedWritten")}</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(100, 116, 139, 0.2); color: #94a3b8;">🛡️</div>
          <div class="stat-content">
            <span class="stat-value">${summary.skipped || 0}</span>
            <span class="stat-label">${i18n.t("execution.skippedCount")}</span>
          </div>
        </div>
      </div>

      ${
        errors && errors.length
          ? `
          <div class="badge badge-warning" style="margin-bottom: 2rem; max-width: 600px; margin: 0 auto 2rem auto; display: flex; justify-content: center;">
            ⚠️ ${errors.join(" | ")}
          </div>
        `
          : ""
      }

      <div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
        ${
          spreadsheetUrl
            ? `
            <a href="${spreadsheetUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
              📊 ${i18n.t("execution.openSheet")} ↗
            </a>
          `
            : ""
        }
        <button id="btn-start-another" class="btn btn-secondary">
          🔄 ${i18n.t("execution.startAnother")}
        </button>
      </div>
    </div>
  `;
}

export function attachCompleteStepListeners() {
  const btn = document.getElementById("btn-start-another");
  if (btn) {
    btn.addEventListener("click", () => {
      store.resetWizard();
      store.setView("sync");
    });
  }
}
