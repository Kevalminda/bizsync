import { i18n } from "./i18n.js";
import { store } from "./state.js";
import { ApiClient } from "./api.js";

import {
  renderHeader,
  attachHeaderListeners,
} from "./components/header.js";

import {
  renderSidebar,
  attachSidebarListeners,
} from "./components/sidebar.js";

import {
  renderDashboardView,
  loadDashboardData,
  attachDashboardListeners,
} from "./components/dashboardView.js";

import {
  renderWizardView,
  attachWizardListeners,
} from "./components/wizardView.js";

import {
  renderConfigsView,
  loadConfigsViewData,
  attachConfigsListeners,
} from "./components/configsView.js";

import {
  renderHistoryView,
  loadHistoryViewData,
  attachHistoryListeners,
} from "./components/historyView.js";

import {
  renderSettingsView,
  attachSettingsListeners,
} from "./components/settingsView.js";


/* ============================================================
   GLOBAL NOTIFICATION STATE
   ============================================================ */

let activeNotification = null;


/* ============================================================
   USER-FACING ERROR MESSAGE
   ============================================================ */

function getFriendlyError(
  error
) {

  if (!error) {
    return "Something went wrong. Please try again.";
  }


  const message =
    String(
      error.message ||
      error
    );


  if (
    message.toLowerCase()
      .includes("network")
  ) {

    return {
      title: "Backend unavailable",
      message:
        "BizSync could not reach the server. Make sure the FastAPI server is running and try again.",
      type: "error",
    };

  }


  if (
    message.toLowerCase()
      .includes("google") &&
    message.toLowerCase()
      .includes("access")
  ) {

    return {
      title: "Google Sheets access problem",
      message:
        "Check that the Google Sheet is shared with your authorized account and that the spreadsheet URL is correct.",
      type: "warning",
    };

  }


  if (
    message.toLowerCase()
      .includes("spreadsheet")
  ) {

    return {
      title: "Google Sheet problem",
      message:
        message,
      type: "warning",
    };

  }


  if (
    message.toLowerCase()
      .includes("unique")
  ) {

    return {
      title: "Unique key problem",
      message:
        "BizSync could not safely identify one or more records. Check your unique-key mapping and make sure the source contains values.",
      type: "warning",
    };

  }


  if (
    message.toLowerCase()
      .includes("session file") ||
    message.toLowerCase()
      .includes("expired")
  ) {

    return {
      title: "Upload session expired",
      message:
        "Please upload the source file again and restart the sync.",
      type: "warning",
    };

  }


  if (
    message.toLowerCase()
      .includes("ai") ||
    message.toLowerCase()
      .includes("gemini")
  ) {

    return {
      title: "AI assistance unavailable",
      message:
        "Gemini could not complete this request. BizSync's local deterministic tools remain available.",
      type: "warning",
    };

  }


  return {
    title: "BizSync error",
    message:
      message,
    type: "error",
  };
}


/* ============================================================
   NOTIFICATION UI
   ============================================================ */

function renderNotification() {

  if (!activeNotification) {
    return "";
  }


  const notification =
    getFriendlyError(
      activeNotification
    );


  const isWarning =
    notification.type ===
    "warning";


  return `
    <div
      id="global-notification"
      style="
        position: fixed;
        top: 1rem;
        right: 1rem;
        width: min(430px, calc(100vw - 2rem));
        z-index: 9999;
        padding: 0.9rem 1rem;
        border-radius: 11px;
        border: 1px solid ${
          isWarning
            ? "rgba(245,158,11,0.35)"
            : "rgba(239,68,68,0.35)"
        };
        background: ${
          isWarning
            ? "rgba(120,53,15,0.94)"
            : "rgba(127,29,29,0.94)"
        };
        color: #ffffff;
        box-shadow: 0 18px 45px rgba(0,0,0,0.35);
        backdrop-filter: blur(10px);
      "
    >

      <div
        style="
          display: flex;
          align-items: flex-start;
          gap: 0.7rem;
        "
      >

        <div
          style="
            font-size: 1.05rem;
            line-height: 1;
            margin-top: 0.1rem;
          "
        >
          ${
            isWarning
              ? "⚠️"
              : "✕"
          }
        </div>


        <div
          style="
            flex: 1;
            min-width: 0;
          "
        >

          <div
            style="
              font-weight: 700;
              margin-bottom: 0.25rem;
            "
          >
            ${notification.title}
          </div>


          <div
            style="
              color: rgba(255,255,255,0.82);
              font-size: 0.78rem;
              line-height: 1.45;
              overflow-wrap: anywhere;
            "
          >
            ${notification.message}
          </div>

        </div>


        <button
          id="btn-close-notification"
          style="
            border: none;
            background: transparent;
            color: rgba(255,255,255,0.75);
            cursor: pointer;
            font-size: 1rem;
            padding: 0;
          "
          aria-label="Close"
        >
          ✕
        </button>

      </div>

    </div>
  `;
}


/* ============================================================
   SHOW ERROR
   ============================================================ */

export function showError(
  error
) {

  activeNotification =
    error;

  const root =
    document.getElementById(
      "app"
    );


  if (root) {
    const existing =
      document.getElementById(
        "global-notification"
      );

    if (existing) {
      existing.remove();
    }

    root.insertAdjacentHTML(
      "beforeend",
      renderNotification()
    );

    attachNotificationListener();
  }
}


/* ============================================================
   CLEAR ERROR
   ============================================================ */

function clearNotification() {

  activeNotification =
    null;


  const element =
    document.getElementById(
      "global-notification"
    );


  if (element) {
    element.remove();
  }
}


/* ============================================================
   NOTIFICATION LISTENER
   ============================================================ */

function attachNotificationListener() {

  const button =
    document.getElementById(
      "btn-close-notification"
    );


  if (!button) {
    return;
  }


  button.addEventListener(
    "click",
    () => {
      clearNotification();
    }
  );
}


/* ============================================================
   INITIAL HEALTH CHECK
   ============================================================ */

async function initApp() {

  try {

    const health =
      await ApiClient.getHealth();

    store.health =
      health;

  } catch (error) {

    console.warn(
      "Initial health check failed:",
      error
    );

    store.health = {
      status: "offline",
      google_credentials_present:
        false,
    };

  }


  store.onChange(
    render
  );

  i18n.onChange(
    render
  );


  render();
}


/* ============================================================
   MAIN RENDER
   ============================================================ */

async function render() {

  const root =
    document.getElementById(
      "app"
    );


  if (!root) {
    return;
  }


  const view =
    store.currentView;


  try {

    /*
     * Pre-load data for individual views.
     */

    if (
      view === "dashboard"
    ) {

      await loadDashboardData();

    } else if (
      view === "configs"
    ) {

      await loadConfigsViewData();

    } else if (
      view === "history"
    ) {

      await loadHistoryViewData();

    }


    /*
     * Render page.
     */

    root.innerHTML = `
      ${renderSidebar()}

      <div class="main-wrapper">

        ${renderHeader()}

        <main class="content-viewport">

          ${
            view === "dashboard"

              ? renderDashboardView()

              : view === "sync"

              ? renderWizardView()

              : view === "configs"

              ? renderConfigsView()

              : view === "history"

              ? renderHistoryView()

              : renderSettingsView()
          }

        </main>

      </div>

    `;


    /*
     * Attach shared listeners.
     */

    attachHeaderListeners();

    attachSidebarListeners();


    /*
     * Attach view listeners.
     */

    if (
      view === "dashboard"
    ) {

      attachDashboardListeners();

    } else if (
      view === "sync"
    ) {

      attachWizardListeners(
        render
      );

    } else if (
      view === "configs"
    ) {

      attachConfigsListeners();

    } else if (
      view === "history"
    ) {

      attachHistoryListeners(
        render
      );

    } else if (
      view === "settings"
    ) {

      attachSettingsListeners();

    }


    /*
     * Restore any active notification.
     */

    if (
      activeNotification
    ) {

      root.insertAdjacentHTML(
        "beforeend",
        renderNotification()
      );

      attachNotificationListener();
    }


  } catch (error) {

    console.error(
      "BizSync render error:",
      error
    );


    root.innerHTML = `
      ${renderSidebar()}

      <div class="main-wrapper">

        ${renderHeader()}

        <main class="content-viewport">

          <div
            class="card"
            style="
              border:
                1px solid
                rgba(
                  239,
                  68,
                  68,
                  0.30
                );
            "
          >

            <div
              class="empty-state"
              style="
                padding:
                  3rem 1rem;
              "
            >

              <div
                class="empty-icon"
              >
                ⚠️
              </div>


              <div
                class="empty-title"
              >
                BizSync could not render this page
              </div>


              <div
                style="
                  color:
                    var(--text-muted);

                  font-size:
                    0.82rem;

                  margin-top:
                    0.5rem;

                  max-width:
                    520px;
                "
              >
                ${
                  error?.message ||
                  "An unexpected frontend error occurred."
                }
              </div>

            </div>

          </div>

        </main>

      </div>
    `;


    attachHeaderListeners();
    attachSidebarListeners();


    showError(
      error
    );
  }
}


/* ============================================================
   START
   ============================================================ */

document.addEventListener(
  "DOMContentLoaded",
  initApp
);