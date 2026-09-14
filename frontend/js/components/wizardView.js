import { i18n } from "../i18n.js";
import { store } from "../state.js";
import { ApiClient } from "../api.js";
import { renderUploadStep, attachUploadStepListeners } from "./uploadStep.js";
import { renderFieldConfigStep, saveFieldConfigStep } from "./fieldConfigStep.js";
import { renderMappingStep, attachMappingStepListeners } from "./mappingStep.js";
import { renderSheetsStep, attachSheetsStepListeners } from "./sheetsStep.js";
import { renderPreviewStep, attachPreviewStepListeners } from "./previewStep.js";
import { renderCompleteStep, attachCompleteStepListeners } from "./completeStep.js";

export function renderWizardView() {
  const step = store.currentStep;

  const steps = [
    { num: 1, title: i18n.t("wizard.step1") },
    { num: 2, title: i18n.t("wizard.step2") },
    { num: 3, title: i18n.t("wizard.step3") },
    { num: 4, title: i18n.t("wizard.step4") },
    { num: 5, title: i18n.t("wizard.step6") },
    { num: 6, title: i18n.t("wizard.step7") },
  ];

  return `
    <div class="stepper-container">
      ${steps
        .map((s, idx) => {
          const isActive = s.num === step;
          const isCompleted = s.num < step;
          return `
            <div class="step-item ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""}">
              <div class="step-number">${isCompleted ? "✓" : s.num}</div>
              <div class="step-title">${s.title}</div>
            </div>
            ${idx < steps.length - 1 ? `<div class="stepper-divider"></div>` : ""}
          `;
        })
        .join("")}
    </div>

    <div id="step-content">
      ${
        step === 1
          ? renderUploadStep()
          : step === 2
          ? renderFieldConfigStep()
          : step === 3
          ? renderMappingStep()
          : step === 4
          ? renderSheetsStep()
          : step === 5
          ? renderPreviewStep()
          : renderCompleteStep()
      }
    </div>

    ${
      step < 6
        ? `
      <div class="wizard-footer">
        <button id="btn-wizard-back" class="btn btn-secondary" ${step === 1 ? "disabled" : ""}>
          ← ${i18n.t("wizard.back")}
        </button>

        <div style="display: flex; gap: 1rem;">
          <button id="btn-wizard-reset" class="btn btn-danger btn-sm">
            ❌ ${i18n.t("wizard.cancel")}
          </button>
          
          ${
            step === 5
              ? `
              <button id="btn-wizard-execute" class="btn btn-success">
                🚀 ${i18n.t("wizard.execute")}
              </button>
            `
              : `
              <button id="btn-wizard-next" class="btn btn-primary" ${!canGoNext() ? "disabled" : ""}>
                ${i18n.t("wizard.next")} →
              </button>
            `
          }
        </div>
      </div>
    `
        : ""
    }
  `;
}

function canGoNext() {
  const step = store.currentStep;
  if (step === 1) return Boolean(store.wizard.fileId);
  if (step === 2) return store.wizard.targetFields.length > 0;
  if (step === 3) return Object.values(store.wizard.mapping).some(Boolean);
  if (step === 4) {
    const input = document.getElementById("sheets-url-input");
    return Boolean((store.wizard.spreadsheetUrl && store.wizard.selectedWorksheet) || (input && input.value.trim()));
  }
  return true;
}

export function attachWizardListeners(reRenderAll) {
  const step = store.currentStep;

  if (step === 1) attachUploadStepListeners(() => reRenderAll());
  if (step === 3) attachMappingStepListeners();
  if (step === 4) attachSheetsStepListeners();
  if (step === 5) attachPreviewStepListeners(() => reRenderAll());
  if (step === 6) attachCompleteStepListeners();

  const backBtn = document.getElementById("btn-wizard-back");
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      if (step > 1) store.setStep(step - 1);
    });
  }

  const resetBtn = document.getElementById("btn-wizard-reset");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (confirm("Reset current sync wizard?")) {
        store.resetWizard();
        store.setView("dashboard");
      }
    });
  }

  const nextBtn = document.getElementById("btn-wizard-next");
  if (nextBtn) {
    nextBtn.addEventListener("click", async () => {
      if (step === 2) {
        saveFieldConfigStep();
      }

      if (step === 4) {
        // Calculate preview before showing preview step
        try {
          const urlInput = document.getElementById("sheets-url-input");
          let url = store.wizard.spreadsheetUrl;
          let sheetName = store.wizard.selectedWorksheet;

          if (urlInput && urlInput.value.trim()) {
            url = urlInput.value.trim();
          }

          if (url && !sheetName) {
            nextBtn.disabled = true;
            nextBtn.innerText = "⏳ Connecting Google Sheet...";
            const res = await ApiClient.connectSheets(url);
            sheetName = res.worksheets.length ? res.worksheets[0] : null;
            store.updateWizard({
              spreadsheetUrl: url,
              spreadsheetTitle: res.title,
              worksheets: res.worksheets,
              selectedWorksheet: sheetName,
            });
          }

          if (!url || !sheetName) {
            alert("Please connect to a valid Google Sheet and select a worksheet tab.");
            nextBtn.disabled = false;
            nextBtn.innerText = "Next →";
            return;
          }

          nextBtn.disabled = true;
          nextBtn.innerText = "⏳ Calculating Diff Preview...";

          const previewRes = await ApiClient.getSyncPreview({
            file_id: store.wizard.fileId,
            mapping: store.wizard.mapping,
            target_fields: store.wizard.targetFields,
            unique_key_fields: store.wizard.uniqueKeyFields,
            spreadsheet_url: url,
            worksheet_name: sheetName,
          });
          store.updateWizard({ syncPreview: previewRes });
        } catch (e) {
          alert("Preview diff failed: " + e.message);
          nextBtn.disabled = false;
          nextBtn.innerText = "Next →";
          return;
        }
      }

      store.setStep(step + 1);
    });
  }

  const executeBtn = document.getElementById("btn-wizard-execute");
  if (executeBtn) {
    executeBtn.addEventListener("click", async () => {
      try {
        executeBtn.disabled = true;
        executeBtn.innerText = "⏳ Executing Sync...";

        const result = await ApiClient.executeSync({
          file_id: store.wizard.fileId,
          mapping: store.wizard.mapping,
          target_fields: store.wizard.targetFields,
          required_fields: store.wizard.requiredFields,
          unique_key_fields: store.wizard.uniqueKeyFields,
          spreadsheet_url: store.wizard.spreadsheetUrl,
          worksheet_name: store.wizard.selectedWorksheet,
          config_name: store.wizard.configName,
        });

        store.updateWizard({ executionResult: result });
        store.setStep(6);
      } catch (err) {
        alert("Execution Error: " + err.message);
        executeBtn.disabled = false;
        executeBtn.innerText = "🚀 Confirm & Execute Sync";
      }
    });
  }
}
