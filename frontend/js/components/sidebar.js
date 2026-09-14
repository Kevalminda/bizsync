import { i18n } from "../i18n.js";
import { store } from "../state.js";

export function renderSidebar() {
  const current = store.currentView;

  return `
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">🔄</div>
        <div class="brand-title">${i18n.t("app.title")}</div>
      </div>
      <ul class="nav-list">
        <li class="nav-item ${current === "dashboard" ? "active" : ""}" data-view="dashboard">
          <span class="nav-icon">📊</span>
          <span>${i18n.t("nav.dashboard")}</span>
        </li>
        <li class="nav-item ${current === "sync" ? "active" : ""}" data-view="sync">
          <span class="nav-icon">⚡</span>
          <span>${i18n.t("nav.newSync")}</span>
        </li>
        <li class="nav-item ${current === "configs" ? "active" : ""}" data-view="configs">
          <span class="nav-icon">📁</span>
          <span>${i18n.t("nav.configs")}</span>
        </li>
        <li class="nav-item ${current === "history" ? "active" : ""}" data-view="history">
          <span class="nav-icon">📜</span>
          <span>${i18n.t("nav.history")}</span>
        </li>
        <li class="nav-item ${current === "settings" ? "active" : ""}" data-view="settings">
          <span class="nav-icon">⚙️</span>
          <span>${i18n.t("nav.settings")}</span>
        </li>
      </ul>
    </aside>
  `;
}

export function attachSidebarListeners() {
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", () => {
      const view = item.getAttribute("data-view");
      if (view) {
        if (view === "sync" && store.currentView !== "sync") {
          // Keep draft or start
        }
        store.setView(view);
      }
    });
  });
}
