import { i18n } from "../i18n.js";
import { store } from "../state.js";

export function renderHeader() {
  const isOAuthConnected = store.health && store.health.google_credentials_present;

  return `
    <header class="header">
      <div class="header-title-area">
        <h2 class="header-title">${i18n.t("app.subtitle")}</h2>
      </div>
      <div class="header-actions">
        <div class="badge ${isOAuthConnected ? "badge-success" : "badge-warning"}">
          <span class="status-dot"></span>
          ${i18n.t("header.oauthStatus")}: ${
            isOAuthConnected
              ? i18n.t("header.connected")
              : i18n.t("header.disconnected")
          }
        </div>
        <button id="lang-toggle-btn" class="lang-toggle" title="Switch Language / भाषा बदलें">
          🌐 <span>${i18n.lang === "en" ? "हिंदी (HI)" : "English (EN)"}</span>
        </button>
      </div>
    </header>
  `;
}

export function attachHeaderListeners() {
  const btn = document.getElementById("lang-toggle-btn");
  if (btn) {
    btn.addEventListener("click", () => {
      i18n.toggleLanguage();
    });
  }
}
