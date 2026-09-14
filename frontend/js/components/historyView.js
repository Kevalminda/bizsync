import { i18n } from "../i18n.js";
import { ApiClient } from "../api.js";

let historyEvents = [];
let historySearch = "";
let historyStatus = "all";
let selectedHistoryIndex = null;


/* ============================================================
   HELPERS
   ============================================================ */

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function formatDate(timestamp) {
  if (!timestamp) {
    return "—";
  }

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return String(timestamp);
  }

  return date.toLocaleString();
}


function getStatus(event) {
  const errors = Number(
    event?.errors || 0
  );

  if (errors > 0) {
    return "issues";
  }

  return "success";
}


function getStatusBadge(event) {
  if (
    getStatus(event) === "issues"
  ) {
    return `
      <span class="badge badge-warning">
        ⚠ Completed with issues
      </span>
    `;
  }

  return `
    <span class="badge badge-success">
      ✓ Completed
    </span>
  `;
}


function getFilteredHistory() {
  const query =
    historySearch
      .trim()
      .toLowerCase();

  return historyEvents.filter(
    (event) => {

      const status =
        getStatus(event);

      if (
        historyStatus !== "all" &&
        historyStatus !== status
      ) {
        return false;
      }

      if (!query) {
        return true;
      }

      const searchableText = [
        event.configuration,
        event.incoming_file,
        event.existing_file,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return searchableText.includes(
        query
      );
    }
  );
}


function getTotalRecordsChanged() {
  return historyEvents.reduce(
    (total, event) =>
      total +
      Number(event.new || 0) +
      Number(event.updated || 0),
    0
  );
}


function getSuccessfulRuns() {
  return historyEvents.filter(
    (event) =>
      getStatus(event) ===
      "success"
  ).length;
}


function getRunsWithIssues() {
  return historyEvents.filter(
    (event) =>
      getStatus(event) ===
      "issues"
  ).length;
}


/* ============================================================
   LOAD HISTORY
   ============================================================ */

export async function loadHistoryViewData() {
  try {

    const result =
      await ApiClient.getHistory();

    historyEvents =
      Array.isArray(result)
        ? [...result].sort(
            (a, b) =>
              new Date(
                b.timestamp
              ) -
              new Date(
                a.timestamp
              )
          )
        : [];

  } catch (error) {

    console.error(
      "Failed to load synchronization history:",
      error
    );

    historyEvents = [];
  }
}


/* ============================================================
   DETAIL PANEL
   ============================================================ */

function renderHistoryDetails() {

  if (
    selectedHistoryIndex === null
  ) {
    return "";
  }

  const event =
    historyEvents[
      selectedHistoryIndex
    ];

  if (!event) {
    selectedHistoryIndex = null;
    return "";
  }

  return `
    <div
      id="history-detail-overlay"
      style="
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.55);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1.25rem;
      "
    >

      <div
        style="
          width: min(720px, 100%);
          max-height: 90vh;
          overflow-y: auto;
          background: var(--surface, #0f172a);
          border: 1px solid var(--border-active);
          border-radius: 14px;
          box-shadow: 0 25px 70px rgba(0,0,0,0.45);
        "
      >

        <!-- ================================================= -->
        <!-- HEADER                                           -->
        <!-- ================================================= -->

        <div
          style="
            padding: 1.15rem 1.25rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
          "
        >

          <div>

            <div
              style="
                color: #818cf8;
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                margin-bottom: 0.35rem;
              "
            >
              Synchronization Details
            </div>

            <h3
              style="
                margin: 0 0 0.25rem;
                font-size: 1.1rem;
              "
            >
              ${escapeHtml(
                event.configuration ||
                "Custom Mapping"
              )}
            </h3>

            <div
              style="
                color: var(--text-muted);
                font-size: 0.78rem;
              "
            >
              ${formatDate(
                event.timestamp
              )}
            </div>

          </div>


          <button
            id="btn-close-history-details"
            class="
              btn
              btn-secondary
              btn-sm
            "
          >
            ✕
          </button>

        </div>


        <!-- ================================================= -->
        <!-- STATUS                                           -->
        <!-- ================================================= -->

        <div
          style="
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border);
          "
        >

          ${getStatusBadge(event)}

        </div>


        <!-- ================================================= -->
        <!-- SOURCE / DESTINATION                             -->
        <!-- ================================================= -->

        <div
          style="
            padding: 1rem 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
          "
        >

          <div
            style="
              padding: 0.85rem;
              border: 1px solid var(--border);
              border-radius: 9px;
            "
          >

            <div
              style="
                color: var(--text-muted);
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                margin-bottom: 0.3rem;
              "
            >
              Source File
            </div>

            <div
              style="
                font-size: 0.84rem;
                font-weight: 600;
                overflow-wrap: anywhere;
              "
            >
              ${escapeHtml(
                event.incoming_file ||
                "—"
              )}
            </div>

          </div>


          <div
            style="
              padding: 0.85rem;
              border: 1px solid var(--border);
              border-radius: 9px;
            "
          >

            <div
              style="
                color: var(--text-muted);
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                margin-bottom: 0.3rem;
              "
            >
              Destination
            </div>

            ${
              event.existing_file
                ? `
                  <a
                    href="${escapeHtml(
                      event.existing_file
                    )}"
                    target="_blank"
                    rel="noopener noreferrer"
                    style="
                      color: #818cf8;
                      text-decoration: none;
                      font-size: 0.82rem;
                      overflow-wrap: anywhere;
                    "
                  >
                    ${escapeHtml(
                      event.existing_file
                    )}
                  </a>
                `
                : "—"
            }

          </div>

        </div>


        <!-- ================================================= -->
        <!-- COUNTS                                           -->
        <!-- ================================================= -->

        <div
          style="
            padding: 0 1.25rem 1.25rem;
          "
        >

          <div
            style="
              display: grid;
              grid-template-columns:
                repeat(4, minmax(0, 1fr));
              gap: 0.65rem;
            "
          >

            <div
              style="
                padding: 0.8rem;
                border: 1px solid var(--border);
                border-radius: 9px;
              "
            >

              <div
                style="
                  color: var(--text-muted);
                  font-size: 0.7rem;
                  margin-bottom: 0.2rem;
                "
              >
                New
              </div>

              <strong
                style="
                  color: #34d399;
                  font-size: 1.05rem;
                "
              >
                +${Number(
                  event.new || 0
                )}
              </strong>

            </div>


            <div
              style="
                padding: 0.8rem;
                border: 1px solid var(--border);
                border-radius: 9px;
              "
            >

              <div
                style="
                  color: var(--text-muted);
                  font-size: 0.7rem;
                  margin-bottom: 0.2rem;
                "
              >
                Updated
              </div>

              <strong
                style="
                  color: #fbbf24;
                  font-size: 1.05rem;
                "
              >
                ~${Number(
                  event.updated || 0
                )}
              </strong>

            </div>


            <div
              style="
                padding: 0.8rem;
                border: 1px solid var(--border);
                border-radius: 9px;
              "
            >

              <div
                style="
                  color: var(--text-muted);
                  font-size: 0.7rem;
                  margin-bottom: 0.2rem;
                "
              >
                Unchanged
              </div>

              <strong
                style="
                  font-size: 1.05rem;
                "
              >
                =${Number(
                  event.unchanged || 0
                )}
              </strong>

            </div>


            <div
              style="
                padding: 0.8rem;
                border: 1px solid var(--border);
                border-radius: 9px;
              "
            >

              <div
                style="
                  color: var(--text-muted);
                  font-size: 0.7rem;
                  margin-bottom: 0.2rem;
                "
              >
                Skipped
              </div>

              <strong
                style="
                  color: #f87171;
                  font-size: 1.05rem;
                "
              >
                !${Number(
                  event.skipped || 0
                )}
              </strong>

            </div>

          </div>


          ${
            Number(event.errors || 0) > 0
              ? `
                <div
                  style="
                    margin-top: 0.75rem;
                    padding: 0.8rem;
                    border-radius: 9px;
                    border: 1px solid rgba(245,158,11,0.3);
                    background: rgba(245,158,11,0.06);
                    color: #fbbf24;
                    font-size: 0.8rem;
                  "
                >
                  ⚠️
                  ${Number(
                    event.errors || 0
                  )}
                  error${
                    Number(
                      event.errors || 0
                    ) === 1
                      ? ""
                      : "s"
                  }
                  were reported during this run.
                </div>
              `
              : ""
          }

        </div>

      </div>

    </div>
  `;
}


/* ============================================================
   MAIN VIEW
   ============================================================ */

export function renderHistoryView() {

  const filteredEvents =
    getFilteredHistory();


  const totalRuns =
    historyEvents.length;


  const successfulRuns =
    getSuccessfulRuns();


  const issueRuns =
    getRunsWithIssues();


  const recordsChanged =
    getTotalRecordsChanged();


  return `

    <!-- ====================================================== -->
    <!-- HEADER                                                -->
    <!-- ====================================================== -->

    <div
      class="card"
      style="
        margin-bottom: 1.25rem;

        background:
          linear-gradient(
            135deg,
            rgba(79,70,229,0.12),
            rgba(15,23,42,0.96)
          );
      "
    >

      <div
        style="
          display:
            flex;

          align-items:
            center;

          justify-content:
            space-between;

          gap:
            1.5rem;

          flex-wrap:
            wrap;
        "
      >

        <div>

          <div
            style="
              color: #818cf8;
              font-size: 0.72rem;
              font-weight: 700;
              text-transform: uppercase;
              letter-spacing: 0.06em;
              margin-bottom: 0.35rem;
            "
          >
            Audit & Activity
          </div>


          <h2
            style="
              margin: 0 0 0.35rem;
              font-size: 1.45rem;
              font-weight: 750;
            "
          >
            ${i18n.t(
              "history.title"
            )}
          </h2>


          <p
            style="
              margin: 0;
              color: var(--text-secondary);
              font-size: 0.88rem;
              line-height: 1.5;
            "
          >
            ${i18n.t(
              "history.subtitle"
            )}
          </p>

        </div>


        ${
          historyEvents.length
            ? `
              <button
                id="btn-clear-history"
                class="
                  btn
                  btn-danger
                  btn-sm
                "
              >
                🗑️
                ${i18n.t(
                  "history.clearHistory"
                )}
              </button>
            `
            : ""
        }

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- STATS                                                  -->
    <!-- ====================================================== -->

    <div
      class="stats-grid"
      style="
        margin-bottom: 1.25rem;
      "
    >

      <div class="stat-card">

        <div
          class="stat-icon"
          style="
            background: var(--primary-light);
            color: #818cf8;
          "
        >
          🔄
        </div>

        <div class="stat-content">

          <span class="stat-value">
            ${totalRuns}
          </span>

          <span class="stat-label">
            Total Runs
          </span>

        </div>

      </div>


      <div class="stat-card">

        <div
          class="stat-icon"
          style="
            background: var(--accent-green-bg);
            color: #34d399;
          "
        >
          ✓
        </div>

        <div class="stat-content">

          <span class="stat-value">
            ${successfulRuns}
          </span>

          <span class="stat-label">
            Successful
          </span>

        </div>

      </div>


      <div class="stat-card">

        <div
          class="stat-icon"
          style="
            background: var(--accent-amber-bg);
            color: #fbbf24;
          "
        >
          ⚠
        </div>

        <div class="stat-content">

          <span class="stat-value">
            ${issueRuns}
          </span>

          <span class="stat-label">
            With Issues
          </span>

        </div>

      </div>


      <div class="stat-card">

        <div
          class="stat-icon"
          style="
            background: var(--accent-rose-bg);
            color: #f87171;
          "
        >
          📊
        </div>

        <div class="stat-content">

          <span class="stat-value">
            ${recordsChanged}
          </span>

          <span class="stat-label">
            Records Changed
          </span>

        </div>

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- SEARCH + FILTERS                                      -->
    <!-- ====================================================== -->

    <div
      class="card"
      style="
        margin-bottom: 1.25rem;
      "
    >

      <div
        style="
          display:
            grid;

          grid-template-columns:
            minmax(0, 1fr)
            180px;

          gap:
            0.75rem;

          align-items:
            center;
        "
      >

        <input
          id="history-search-input"
          type="text"
          class="form-input"
          placeholder="Search configuration or source file..."
          value="${escapeHtml(
            historySearch
          )}"
        />


        <select
          id="history-status-filter"
          class="form-select"
        >

          <option
            value="all"
            ${
              historyStatus === "all"
                ? "selected"
                : ""
            }
          >
            All Status
          </option>

          <option
            value="success"
            ${
              historyStatus ===
              "success"
                ? "selected"
                : ""
            }
          >
            Successful
          </option>

          <option
            value="issues"
            ${
              historyStatus ===
              "issues"
                ? "selected"
                : ""
            }
          >
            With Issues
          </option>

        </select>

      </div>


      <div
        style="
          margin-top: 0.65rem;
          color: var(--text-muted);
          font-size: 0.75rem;
        "
      >
        Showing
        <strong>
          ${filteredEvents.length}
        </strong>
        of
        <strong>
          ${historyEvents.length}
        </strong>
        synchronization run${
          historyEvents.length === 1
            ? ""
            : "s"
        }.
      </div>

    </div>


    <!-- ====================================================== -->
    <!-- HISTORY TABLE                                         -->
    <!-- ====================================================== -->

    <div class="card">

      <div class="card-header">

        <div>

          <h3 class="card-title">
            Recent Synchronizations
          </h3>

          <p class="card-subtitle">
            Review what BizSync changed during each run.
          </p>

        </div>

      </div>


      ${
        historyEvents.length === 0

          ? `
            <div class="empty-state">

              <div class="empty-icon">
                📜
              </div>

              <div class="empty-title">
                ${i18n.t(
                  "history.noHistory"
                )}
              </div>

              <div
                style="
                  color: var(--text-muted);
                  font-size: 0.82rem;
                  margin-top: 0.4rem;
                "
              >
                Your synchronization activity will appear here.
              </div>

            </div>
          `

          : filteredEvents.length === 0

          ? `
            <div
              class="empty-state"
              style="
                padding: 2.5rem 1rem;
              "
            >

              <div class="empty-icon">
                🔎
              </div>

              <div class="empty-title">
                No matching synchronization runs
              </div>

              <div
                style="
                  color: var(--text-muted);
                  font-size: 0.82rem;
                  margin-top: 0.4rem;
                "
              >
                Try changing your search or status filter.
              </div>

            </div>
          `

          : `
            <div class="table-container">

              <table class="data-table">

                <thead>

                  <tr>

                    <th>
                      ${i18n.t(
                        "history.timestamp"
                      )}
                    </th>

                    <th>
                      ${i18n.t(
                        "history.configName"
                      )}
                    </th>

                    <th>
                      ${i18n.t(
                        "history.sourceFile"
                      )}
                    </th>

                    <th>
                      ${i18n.t(
                        "history.counts"
                      )}
                    </th>

                    <th>
                      Status
                    </th>

                    <th>
                      Details
                    </th>

                  </tr>

                </thead>


                <tbody>

                  ${filteredEvents
                    .map(
                      (event) => {

                        const originalIndex =
                          historyEvents.indexOf(
                            event
                          );

                        return `
                          <tr>

                            <td
                              style="
                                font-size: 0.8rem;
                                color: var(--text-secondary);
                                white-space: nowrap;
                              "
                            >
                              ${formatDate(
                                event.timestamp
                              )}
                            </td>


                            <td>

                              <span
                                class="
                                  badge
                                  badge-info
                                "
                              >
                                ${escapeHtml(
                                  event.configuration ||
                                  "Custom Mapping"
                                )}
                              </span>

                            </td>


                            <td
                              style="
                                font-weight: 600;
                                max-width: 240px;
                                overflow: hidden;
                                text-overflow: ellipsis;
                                white-space: nowrap;
                              "
                              title="${escapeHtml(
                                event.incoming_file ||
                                ""
                              )}"
                            >
                              ${escapeHtml(
                                event.incoming_file ||
                                "—"
                              )}
                            </td>


                            <td
                              style="
                                white-space: nowrap;
                              "
                            >

                              <span
                                class="
                                  badge
                                  pill-new
                                "
                                title="New Rows"
                              >
                                +${Number(
                                  event.new || 0
                                )}
                              </span>

                              <span
                                class="
                                  badge
                                  pill-updated
                                "
                                title="Updated Rows"
                              >
                                ~${Number(
                                  event.updated || 0
                                )}
                              </span>

                              <span
                                class="
                                  badge
                                  pill-unchanged
                                "
                                title="Unchanged Rows"
                              >
                                =${Number(
                                  event.unchanged || 0
                                )}
                              </span>

                              <span
                                class="
                                  badge
                                  pill-skipped
                                "
                                title="Skipped Rows"
                              >
                                !${Number(
                                  event.skipped || 0
                                )}
                              </span>

                            </td>


                            <td>
                              ${getStatusBadge(
                                event
                              )}
                            </td>


                            <td>

                              <button
                                class="
                                  btn
                                  btn-secondary
                                  btn-sm
                                  btn-history-details
                                "
                                data-index="${originalIndex}"
                              >
                                View Details
                              </button>

                            </td>

                          </tr>
                        `;
                      }
                    )
                    .join("")}

                </tbody>

              </table>

            </div>
          `
      }

    </div>


    <!-- ====================================================== -->
    <!-- DETAIL MODAL                                          -->
    <!-- ====================================================== -->

    ${renderHistoryDetails()}

  `;
}


/* ============================================================
   EVENT LISTENERS
   ============================================================ */

export function attachHistoryListeners(
  reRender
) {

  /* ----------------------------------------------------------
     SEARCH
     ---------------------------------------------------------- */

  const searchInput =
    document.getElementById(
      "history-search-input"
    );


  if (searchInput) {

    searchInput.addEventListener(
      "input",
      (event) => {

        historySearch =
          event.target.value;

        if (reRender) {
          reRender();
        }

      }
    );
  }


  /* ----------------------------------------------------------
     STATUS FILTER
     ---------------------------------------------------------- */

  const statusFilter =
    document.getElementById(
      "history-status-filter"
    );


  if (statusFilter) {

    statusFilter.addEventListener(
      "change",
      (event) => {

        historyStatus =
          event.target.value;

        if (reRender) {
          reRender();
        }

      }
    );
  }


  /* ----------------------------------------------------------
     CLEAR HISTORY
     ---------------------------------------------------------- */

  const clearBtn =
    document.getElementById(
      "btn-clear-history"
    );


  if (clearBtn) {

    clearBtn.addEventListener(
      "click",
      async () => {

        const confirmed =
          confirm(
            "Clear all synchronization audit history?"
          );


        if (!confirmed) {
          return;
        }


        try {

          await ApiClient.clearHistory();

          historyEvents = [];

          historySearch = "";

          historyStatus = "all";

          selectedHistoryIndex = null;


          if (reRender) {
            reRender();
          }


        } catch (error) {

          alert(
            "Error clearing history: "
            + error.message
          );

        }

      }
    );
  }


  /* ----------------------------------------------------------
     VIEW DETAILS
     ---------------------------------------------------------- */

  document
    .querySelectorAll(
      ".btn-history-details"
    )
    .forEach(
      (button) => {

        button.addEventListener(
          "click",
          () => {

            selectedHistoryIndex =
              parseInt(
                button.getAttribute(
                  "data-index"
                ),
                10
              );


            if (reRender) {
              reRender();
            }

          }
        );

      }
    );


  /* ----------------------------------------------------------
     CLOSE DETAILS MODAL
     ---------------------------------------------------------- */

  const closeDetails =
    document.getElementById(
      "btn-close-history-details"
    );


  if (closeDetails) {

    closeDetails.addEventListener(
      "click",
      () => {

        selectedHistoryIndex =
          null;

        if (reRender) {
          reRender();
        }

      }
    );
  }


  /* ----------------------------------------------------------
     CLOSE BY CLICKING OVERLAY
     ---------------------------------------------------------- */

  const overlay =
    document.getElementById(
      "history-detail-overlay"
    );


  if (overlay) {

    overlay.addEventListener(
      "click",
      (event) => {

        if (
          event.target ===
          overlay
        ) {

          selectedHistoryIndex =
            null;

          if (reRender) {
            reRender();
          }

        }

      }
    );
  }

}