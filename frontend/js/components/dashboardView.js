import { i18n } from "../i18n.js";
import { store } from "../state.js";
import { ApiClient } from "../api.js";

let historyData = [];


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

  const date = new Date(
    timestamp
  );

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleString();
}


function getLastSync() {
  if (!historyData.length) {
    return null;
  }

  return historyData[0];
}


function getLastSyncText() {
  const latest = getLastSync();

  if (!latest) {
    return "No syncs yet";
  }

  const date = new Date(
    latest.timestamp
  );

  if (Number.isNaN(date.getTime())) {
    return "Recently";
  }

  const diff =
    Date.now() -
    date.getTime();

  const minutes = Math.floor(
    diff / 60000
  );

  if (minutes < 1) {
    return "Just now";
  }

  if (minutes < 60) {
    return `${minutes} min ago`;
  }

  const hours = Math.floor(
    minutes / 60
  );

  if (hours < 24) {
    return `${hours} hr ago`;
  }

  const days = Math.floor(
    hours / 24
  );

  if (days === 1) {
    return "Yesterday";
  }

  if (days < 7) {
    return `${days} days ago`;
  }

  return date.toLocaleDateString();
}


function getSyncStatus(historyItem) {
  if (!historyItem) {
    return {
      text: "Unknown",
      className: "badge-info",
    };
  }

  const errors =
    Number(
      historyItem.errors || 0
    );

  if (errors > 0) {
    return {
      text: "Completed with issues",
      className: "badge-warning",
    };
  }

  return {
    text: "Completed",
    className: "badge-success",
  };
}


/* ============================================================
   DASHBOARD DATA
   ============================================================ */

export async function loadDashboardData() {
  try {
    const result =
      await ApiClient.getHistory();

    /*
     * Most recent events should appear first.
     */
    historyData = Array.isArray(
      result
    )
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
      "Failed to load dashboard history:",
      error
    );

    historyData = [];
  }
}


/* ============================================================
   DASHBOARD RENDER
   ============================================================ */

export function renderDashboardView() {

  const totalSyncs =
    historyData.length;


  const totalAdded =
    historyData.reduce(
      (
        total,
        item
      ) =>
        total +
        Number(
          item.new || 0
        ),
      0
    );


  const totalUpdated =
    historyData.reduce(
      (
        total,
        item
      ) =>
        total +
        Number(
          item.updated || 0
        ),
      0
    );


  const totalSkipped =
    historyData.reduce(
      (
        total,
        item
      ) =>
        total +
        Number(
          item.skipped || 0
        ),
      0
    );


  const totalErrors =
    historyData.reduce(
      (
        total,
        item
      ) =>
        total +
        Number(
          item.errors || 0
        ),
      0
    );


  const latest =
    getLastSync();


  return `

    <!-- ====================================================== -->
    <!-- HERO                                                   -->
    <!-- ====================================================== -->

    <div
      class="card"
      style="
        background:
          linear-gradient(
            135deg,
            rgba(79,70,229,0.20),
            rgba(15,23,42,0.96)
          );

        border:
          1px solid
          var(--border-active);

        margin-bottom:
          1.5rem;

        overflow:
          hidden;

        position:
          relative;
      "
    >

      <div
        style="
          position:
            absolute;

          width:
            260px;

          height:
            260px;

          border-radius:
            50%;

          background:
            rgba(99,102,241,0.08);

          right:
            -90px;

          top:
            -110px;

          pointer-events:
            none;
        "
      ></div>


      <div
        style="
          display:
            flex;

          align-items:
            center;

          justify-content:
            space-between;

          gap:
            2rem;

          flex-wrap:
            wrap;

          position:
            relative;
        "
      >

        <div>

          <div
            style="
              font-size:
                0.78rem;

              text-transform:
                uppercase;

              letter-spacing:
                0.08em;

              color:
                #818cf8;

              font-weight:
                700;

              margin-bottom:
                0.45rem;
            "
          >
            BizSync Control Center
          </div>


          <h2
            style="
              font-size:
                1.7rem;

              font-weight:
                750;

              color:
                #ffffff;

              margin-bottom:
                0.45rem;
            "
          >
            ${i18n.t(
              "dashboard.title"
            )}
          </h2>


          <p
            style="
              color:
                var(--text-secondary);

              font-size:
                0.95rem;

              max-width:
                620px;

              line-height:
                1.55;
            "
          >
            ${i18n.t(
              "dashboard.subtitle"
            )}
          </p>

        </div>


        <button
          id="btn-quick-sync"
          class="
            btn
            btn-primary
            btn-lg
          "
          style="
            padding:
              0.9rem 1.5rem;

            white-space:
              nowrap;
          "
        >
          ⚡ ${i18n.t(
            "dashboard.quickStart"
          )}
        </button>

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- QUICK STATS                                            -->
    <!-- ====================================================== -->

    <div
      class="stats-grid"
      style="
        margin-bottom:
          1.5rem;
      "
    >

      <div class="stat-card">

        <div
          class="stat-icon"
          style="
            background:
              var(--primary-light);

            color:
              #818cf8;
          "
        >
          🔄
        </div>

        <div class="stat-content">

          <span class="stat-value">
            ${totalSyncs}
          </span>

          <span class="stat-label">
            ${i18n.t(
              "dashboard.totalSyncs"
            )}
          </span>

        </div>

      </div>


      <div class="stat-card">

        <div
          class="stat-icon"
          style="
            background:
              var(--accent-green-bg);

            color:
              #34d399;
          "
        >
          ➕
        </div>

        <div class="stat-content">

          <span class="stat-value">
            ${totalAdded}
          </span>

          <span class="stat-label">
            ${i18n.t(
              "dashboard.recordsAdded"
            )}
          </span>

        </div>

      </div>


      <div class="stat-card">

        <div
          class="stat-icon"
          style="
            background:
              var(--accent-amber-bg);

            color:
              #fbbf24;
          "
        >
          ✏️
        </div>

        <div class="stat-content">

          <span class="stat-value">
            ${totalUpdated}
          </span>

          <span class="stat-label">
            ${i18n.t(
              "dashboard.recordsUpdated"
            )}
          </span>

        </div>

      </div>


      <div class="stat-card">

        <div
          class="stat-icon"
          style="
            background:
              var(--accent-rose-bg);

            color:
              #f87171;
          "
        >
          🛡️
        </div>

        <div class="stat-content">

          <span class="stat-value">
            ${totalSkipped}
          </span>

          <span class="stat-label">
            ${i18n.t(
              "dashboard.recordsSkipped"
            )}
          </span>

        </div>

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- OVERVIEW ROW                                            -->
    <!-- ====================================================== -->

    <div
      style="
        display:
          grid;

        grid-template-columns:
          minmax(0, 1.4fr)
          minmax(280px, 0.6fr);

        gap:
          1.25rem;

        margin-bottom:
          1.5rem;
      "
    >

      <!-- ---------------------------------------------------- -->
      <!-- LAST SYNC                                             -->
      <!-- ---------------------------------------------------- -->

      <div class="card">

        <div class="card-header">

          <div>

            <h3 class="card-title">
              Last Synchronization
            </h3>

            <p class="card-subtitle">
              Your most recent BizSync activity
            </p>

          </div>


          ${
            latest
              ? `
                <span
                  class="
                    badge
                    ${
                      getSyncStatus(
                        latest
                      ).className
                    }
                  "
                >
                  ${
                    getSyncStatus(
                      latest
                    ).text
                  }
                </span>
              `
              : ""
          }

        </div>


        ${
          latest
            ? `
              <div
                style="
                  display:
                    grid;

                  grid-template-columns:
                    repeat(
                      4,
                      minmax(
                        0,
                        1fr
                      )
                    );

                  gap:
                    0.75rem;
                "
              >

                <div
                  style="
                    padding:
                      0.85rem;

                    border:
                      1px solid
                      var(--border);

                    border-radius:
                      10px;
                  "
                >

                  <div
                    style="
                      color:
                        var(--text-muted);

                      font-size:
                        0.72rem;

                      margin-bottom:
                        0.2rem;
                    "
                  >
                    Configuration
                  </div>

                  <div
                    style="
                      font-weight:
                        650;

                      overflow:
                        hidden;

                      text-overflow:
                        ellipsis;

                      white-space:
                        nowrap;
                    "
                  >
                    ${escapeHtml(
                      latest.configuration ||
                        "Custom"
                    )}
                  </div>

                </div>


                <div
                  style="
                    padding:
                      0.85rem;

                    border:
                      1px solid
                      var(--border);

                    border-radius:
                      10px;
                  "
                >

                  <div
                    style="
                      color:
                        var(--text-muted);

                      font-size:
                        0.72rem;

                      margin-bottom:
                        0.2rem;
                    "
                  >
                    Added
                  </div>

                  <div
                    style="
                      font-size:
                        1.1rem;

                      font-weight:
                        700;

                      color:
                        #34d399;
                    "
                  >
                    +${Number(
                      latest.new || 0
                    )}
                  </div>

                </div>


                <div
                  style="
                    padding:
                      0.85rem;

                    border:
                      1px solid
                      var(--border);

                    border-radius:
                      10px;
                  "
                >

                  <div
                    style="
                      color:
                        var(--text-muted);

                      font-size:
                        0.72rem;

                      margin-bottom:
                        0.2rem;
                    "
                  >
                    Updated
                  </div>

                  <div
                    style="
                      font-size:
                        1.1rem;

                      font-weight:
                        700;

                      color:
                        #fbbf24;
                    "
                  >
                    ${Number(
                      latest.updated || 0
                    )}
                  </div>

                </div>


                <div
                  style="
                    padding:
                      0.85rem;

                    border:
                      1px solid
                      var(--border);

                    border-radius:
                      10px;
                  "
                >

                  <div
                    style="
                      color:
                        var(--text-muted);

                      font-size:
                        0.72rem;

                      margin-bottom:
                        0.2rem;
                    "
                  >
                    Run
                  </div>

                  <div
                    style="
                      font-weight:
                        650;

                      font-size:
                        0.9rem;
                    "
                  >
                    ${getLastSyncText()}
                  </div>

                </div>

              </div>
            `
            : `
              <div
                class="empty-state"
                style="
                  padding:
                    2rem 1rem;
                "
              >

                <div
                  class="empty-icon"
                >
                  📊
                </div>

                <div
                  class="empty-title"
                >
                  No synchronization yet
                </div>

                <div
                  style="
                    color:
                      var(--text-muted);

                    margin-top:
                      0.35rem;

                    font-size:
                      0.82rem;
                  "
                >
                  Start your first sync to see activity here.
                </div>

              </div>
            `
        }

      </div>


      <!-- ---------------------------------------------------- -->
      <!-- SYSTEM SUMMARY                                       -->
      <!-- ---------------------------------------------------- -->

      <div class="card">

        <div class="card-header">

          <div>

            <h3 class="card-title">
              Sync Health
            </h3>

            <p class="card-subtitle">
              Overall synchronization activity
            </p>

          </div>

        </div>


        <div
          style="
            display:
              flex;

            flex-direction:
              column;

            gap:
              0.8rem;
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
                1rem;
            "
          >

            <span
              style="
                color:
                  var(--text-muted);

                font-size:
                  0.83rem;
              "
            >
              Successful syncs
            </span>

            <strong>
              ${Math.max(
                totalSyncs -
                  historyData.filter(
                    (item) =>
                      Number(
                        item.errors || 0
                      ) > 0
                  ).length,
                0
              )}
            </strong>

          </div>


          <div
            style="
              display:
                flex;

              align-items:
                center;

              justify-content:
                space-between;

              gap:
                1rem;
            "
          >

            <span
              style="
                color:
                  var(--text-muted);

                font-size:
                  0.83rem;
              "
            >
              Records processed
            </span>

            <strong>
              ${
                totalAdded +
                totalUpdated
              }
            </strong>

          </div>


          <div
            style="
              display:
                flex;

              align-items:
                center;

              justify-content:
                space-between;

              gap:
                1rem;
            "
          >

            <span
              style="
                color:
                  var(--text-muted);

                font-size:
                  0.83rem;
              "
            >
              Records safely skipped
            </span>

            <strong>
              ${totalSkipped}
            </strong>

          </div>


          <div
            style="
              display:
                flex;

              align-items:
                center;

              justify-content:
                space-between;

              gap:
                1rem;
            "
          >

            <span
              style="
                color:
                  var(--text-muted);

                font-size:
                  0.83rem;
              "
            >
              Reported errors
            </span>

            <strong
              style="
                color:
                  ${
                    totalErrors > 0
                      ? "#f87171"
                      : "inherit"
                  };
              "
            >
              ${totalErrors}
            </strong>

          </div>

        </div>


        <div
          style="
            margin-top:
              1rem;

            padding:
              0.7rem 0.8rem;

            border-radius:
              8px;

            background:
              rgba(
                16,
                185,
                129,
                0.06
              );

            border:
              1px solid
              rgba(
                16,
                185,
                129,
                0.18
              );

            color:
              var(--text-muted);

            font-size:
              0.75rem;

            line-height:
              1.45;
          "
        >
          🛡️ BizSync uses safe row-aware synchronization to
          avoid unnecessary duplicate inserts.
        </div>

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- RECENT ACTIVITY                                       -->
    <!-- ====================================================== -->

    <div class="card">

      <div class="card-header">

        <div>

          <h3 class="card-title">
            ${i18n.t(
              "dashboard.recentActivity"
            )}
          </h3>

          <p class="card-subtitle">
            Your latest synchronization runs
          </p>

        </div>


        ${
          historyData.length
            ? `
              <button
                id="btn-goto-history"
                class="
                  btn
                  btn-secondary
                  btn-sm
                "
              >
                ${i18n.t(
                  "dashboard.viewAllHistory"
                )}
              </button>
            `
            : ""
        }

      </div>


      ${
        historyData.length === 0

          ? `
            <div
              class="empty-state"
            >

              <div class="empty-icon">
                📜
              </div>

              <div class="empty-title">
                ${i18n.t(
                  "dashboard.noHistory"
                )}
              </div>

            </div>
          `

          : `
            <div
              class="table-container"
            >

              <table
                class="data-table"
              >

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

                  </tr>

                </thead>


                <tbody>

                  ${historyData
                    .slice(
                      0,
                      5
                    )
                    .map(
                      (item) => {

                        const status =
                          getSyncStatus(
                            item
                          );

                        return `
                          <tr>

                            <td>
                              ${formatDate(
                                item.timestamp
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
                                  item.configuration ||
                                    "Custom"
                                )}
                              </span>

                            </td>


                            <td>
                              ${escapeHtml(
                                item.incoming_file ||
                                  "—"
                              )}
                            </td>


                            <td>

                              <span
                                class="
                                  badge
                                  pill-new
                                "
                              >
                                +${Number(
                                  item.new || 0
                                )}
                              </span>

                              <span
                                class="
                                  badge
                                  pill-updated
                                "
                              >
                                ~${Number(
                                  item.updated || 0
                                )}
                              </span>

                              <span
                                class="
                                  badge
                                  pill-unchanged
                                "
                              >
                                =${Number(
                                  item.unchanged || 0
                                )}
                              </span>

                              <span
                                class="
                                  badge
                                  pill-skipped
                                "
                              >
                                !${Number(
                                  item.skipped || 0
                                )}
                              </span>

                            </td>


                            <td>

                              <span
                                class="
                                  badge
                                  ${status.className}
                                "
                              >
                                ${status.text}
                              </span>

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
    <!-- QUICK ACTIONS                                         -->
    <!-- ====================================================== -->

    <div
      style="
        display:
          grid;

        grid-template-columns:
          repeat(
            3,
            minmax(
              0,
              1fr
            )
          );

        gap:
          1rem;

        margin-top:
          1.25rem;
      "
    >

      <button
        id="btn-dashboard-new-sync"
        class="card"
        style="
          text-align:
            left;

          cursor:
            pointer;

          border:
            1px solid
            var(--border);

          color:
            inherit;
        "
      >

        <div
          style="
            font-size:
              1.25rem;

            margin-bottom:
              0.6rem;
          "
        >
          ⚡
        </div>

        <div
          style="
            font-weight:
              700;

            margin-bottom:
              0.2rem;
          "
        >
          Start New Sync
        </div>

        <div
          style="
            color:
              var(--text-muted);

            font-size:
              0.78rem;
          "
        >
          Upload a new business export and synchronize it.
        </div>

      </button>


      <button
        id="btn-dashboard-configs"
        class="card"
        style="
          text-align:
            left;

          cursor:
            pointer;

          border:
            1px solid
            var(--border);

          color:
            inherit;
        "
      >

        <div
          style="
            font-size:
              1.25rem;

            margin-bottom:
              0.6rem;
          "
        >
          📁
        </div>

        <div
          style="
            font-weight:
              700;

            margin-bottom:
              0.2rem;
          "
        >
          Saved Configurations
        </div>

        <div
          style="
            color:
              var(--text-muted);

            font-size:
              0.78rem;
          "
        >
          Reuse mappings and sync settings for recurring work.
        </div>

      </button>


      <button
        id="btn-dashboard-history"
        class="card"
        style="
          text-align:
            left;

          cursor:
            pointer;

          border:
            1px solid
            var(--border);

          color:
            inherit;
        "
      >

        <div
          style="
            font-size:
              1.25rem;

            margin-bottom:
              0.6rem;
          "
        >
          📜
        </div>

        <div
          style="
            font-weight:
              700;

            margin-bottom:
              0.2rem;
          "
        >
          Sync History
        </div>

        <div
          style="
            color:
              var(--text-muted);

            font-size:
              0.78rem;
          "
        >
          Review previous synchronization activity and results.
        </div>

      </button>

    </div>

  `;
}


/* ============================================================
   LISTENERS
   ============================================================ */

export function attachDashboardListeners() {

  const syncBtn =
    document.getElementById(
      "btn-quick-sync"
    );


  if (syncBtn) {

    syncBtn.addEventListener(
      "click",
      () => {
        store.setView(
          "sync"
        );
      }
    );
  }


  const historyBtn =
    document.getElementById(
      "btn-goto-history"
    );


  if (historyBtn) {

    historyBtn.addEventListener(
      "click",
      () => {
        store.setView(
          "history"
        );
      }
    );
  }


  const dashboardNewSync =
    document.getElementById(
      "btn-dashboard-new-sync"
    );


  if (dashboardNewSync) {

    dashboardNewSync.addEventListener(
      "click",
      () => {
        store.setView(
          "sync"
        );
      }
    );
  }


  const dashboardConfigs =
    document.getElementById(
      "btn-dashboard-configs"
    );


  if (dashboardConfigs) {

    dashboardConfigs.addEventListener(
      "click",
      () => {
        store.setView(
          "configs"
        );
      }
    );
  }


  const dashboardHistory =
    document.getElementById(
      "btn-dashboard-history"
    );


  if (dashboardHistory) {

    dashboardHistory.addEventListener(
      "click",
      () => {
        store.setView(
          "history"
        );
      }
    );
  }
}