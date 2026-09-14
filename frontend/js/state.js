class Store {
  constructor() {
    this.currentView = "dashboard"; // dashboard | sync | configs | history | settings
    this.currentStep = 1; // 1: Upload, 2: Fields, 3: Mapping, 4: Sheets, 5: Preview, 6: Complete
    this.health = { status: "unknown", google_credentials_present: false };
    
    // Wizard state
    this.wizard = this.loadDraft() || this.defaultWizardState();
    this.listeners = [];
  }

  defaultWizardState() {
    return {
      fileId: null,
      filename: "",
      totalRows: 0,
      sourceColumns: [],
      previewData: [],
      targetFields: ["Order No.", "SKU ID", "Product Name", "Quantity", "Date"],
      requiredFields: ["Order No.", "Product Name", "Quantity"],
      uniqueKeyFields: ["Order No.", "SKU ID"],
      mapping: {},
      suggestions: {},
      configName: "",
      spreadsheetUrl: "",
      spreadsheetTitle: "",
      worksheets: [],
      selectedWorksheet: null,
      schemaInfo: null,
      syncPreview: null,
      executionResult: null,
    };
  }

  loadDraft() {
    try {
      const saved = sessionStorage.getItem("bizsync_wizard_draft");
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  }

  saveDraft() {
    try {
      sessionStorage.setItem("bizsync_wizard_draft", JSON.stringify(this.wizard));
    } catch (e) {}
  }

  resetWizard() {
    this.wizard = this.defaultWizardState();
    this.currentStep = 1;
    sessionStorage.removeItem("bizsync_wizard_draft");
    this.notify();
  }

  setStep(step) {
    this.currentStep = Math.max(1, Math.min(6, step));
    this.saveDraft();
    this.notify();
  }

  setView(view) {
    this.currentView = view;
    this.notify();
  }

  updateWizard(patch) {
    this.wizard = { ...this.wizard, ...patch };
    this.saveDraft();
    this.notify();
  }

  onChange(callback) {
    this.listeners.push(callback);
  }

  notify() {
    this.listeners.forEach((cb) => cb(this));
  }
}

export const store = new Store();
