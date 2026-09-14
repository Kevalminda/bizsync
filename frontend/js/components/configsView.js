import { i18n } from "../i18n.js";
import { store } from "../state.js";
import { ApiClient } from "../api.js";

let savedConfigs = [];


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


function safeArray(value) {
  return Array.isArray(value)
    ? value
    : [];
}


function getConfigObject(item) {
  return item?.config || {};
}


/* ============================================================
   LOAD DATA
   ============================================================ */

export async function loadConfigsViewData() {
  try {

    const result =
      await ApiClient.listConfigs();

    savedConfigs =
      Array.isArray(result)
        ? result
        : [];

  } catch (error) {

    console.error(
      "Failed to load saved configurations:",
      error
    );

    savedConfigs = [];
  }
}


/* ============================================================
   CONFIG CARD
   ============================================================ */

function renderConfigCard(
  cfg,
  index
) {

  const config =
    getConfigObject(
      cfg
    );


  const targets =
    safeArray(
      config.target_fields
    );


  const required =
    safeArray(
      config.required_fields
    );


  const uniqueKeys =
    safeArray(
      config.unique_key_fields
    );


  const mapping =
    config.mapping ||
    config.source_to_target ||
    {};


  const mappingCount =
    Object.keys(
      mapping
    ).filter(
      (key) =>
        mapping[key]
    ).length;


  return `
    <div
      class="card"
      style="
        padding:
          1.15rem;

        display:
          flex;

        flex-direction:
          column;

        gap:
          1rem;

        border:
          1px solid
          var(--border);

        background:
          rgba(
            255,
            255,
            255,
            0.015
          );
      "
    >

      <!-- ================================================== -->
      <!-- HEADER                                             -->
      <!-- ================================================== -->

      <div
        style="
          display:
            flex;

          align-items:
            flex-start;

          justify-content:
            space-between;

          gap:
            1rem;
        "
      >

        <div
          style="
            min-width:
              0;
          "
        >

          <div
            style="
              display:
                flex;

              align-items:
                center;

              gap:
                0.6rem;

              flex-wrap:
                wrap;

              margin-bottom:
                0.3rem;
            "
          >

            <h3
              style="
                margin:
                  0;

                font-size:
                  1rem;

                font-weight:
                  700;

                overflow:
                  hidden;

                text-overflow:
                  ellipsis;

                white-space:
                  nowrap;
              "
            >
              ${escapeHtml(
                cfg.name ||
                config.name ||
                "Unnamed Configuration"
              )}
            </h3>


            <span
              class="
                badge
                badge-success
              "
            >
              Saved
            </span>

          </div>


          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.76rem;
            "
          >
            ${targets.length}
            target field${
              targets.length === 1
                ? ""
                : "s"
            }

            ·

            ${mappingCount}
            mapping${
              mappingCount === 1
                ? ""
                : "s"
            }
          </div>

        </div>


        <button
          class="
            btn
            btn-primary
            btn-sm
            btn-use-template
          "
          data-index="${index}"
        >
          ⚡ ${i18n.t(
            "configs.useTemplate"
          )}
        </button>

      </div>


      <!-- ================================================== -->
      <!-- TEMPLATE DETAILS                                  -->
      <!-- ================================================== -->

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
            0.75rem;
        "
      >

        <!-- Target fields -->

        <div
          style="
            padding:
              0.8rem;

            border:
              1px solid
              var(--border);

            border-radius:
              9px;
          "
        >

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.7rem;

              margin-bottom:
                0.35rem;

              text-transform:
                uppercase;

              letter-spacing:
                0.04em;
            "
          >
            Target Fields
          </div>


          <div
            style="
              font-size:
                0.78rem;

              line-height:
                1.45;
            "
          >
            ${
              targets.length
                ? targets
                    .map(
                      (field) =>
                        `
                          <span
                            class="
                              badge
                              badge-info
                            "
                            style="
                              margin:
                                0.1rem
                                0.15rem
                                0.1rem
                                0;
                            "
                          >
                            ${escapeHtml(
                              field
                            )}
                          </span>
                        `
                    )
                    .join("")
                : "—"
            }
          </div>

        </div>


        <!-- Required fields -->

        <div
          style="
            padding:
              0.8rem;

            border:
              1px solid
              var(--border);

            border-radius:
              9px;
          "
        >

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.7rem;

              margin-bottom:
                0.35rem;

              text-transform:
                uppercase;

              letter-spacing:
                0.04em;
            "
          >
            Required Fields
          </div>


          <div
            style="
              font-size:
                0.78rem;

              line-height:
                1.45;
            "
          >
            ${
              required.length
                ? required
                    .map(
                      (field) =>
                        `
                          <span
                            class="
                              badge
                              badge-warning
                            "
                            style="
                              margin:
                                0.1rem
                                0.15rem
                                0.1rem
                                0;
                            "
                          >
                            ${escapeHtml(
                              field
                            )}
                          </span>
                        `
                    )
                    .join("")
                : "None"
            }
          </div>

        </div>


        <!-- Unique keys -->

        <div
          style="
            padding:
              0.8rem;

            border:
              1px solid
              var(--border);

            border-radius:
              9px;
          "
        >

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.7rem;

              margin-bottom:
                0.35rem;

              text-transform:
                uppercase;

              letter-spacing:
                0.04em;
            "
          >
            Unique Key
          </div>


          <div
            style="
              font-size:
                0.78rem;

              line-height:
                1.45;
            "
          >
            ${
              uniqueKeys.length
                ? uniqueKeys
                    .map(
                      (field) =>
                        `
                          <span
                            class="
                              badge
                              badge-info
                            "
                            style="
                              margin:
                                0.1rem
                                0.15rem
                                0.1rem
                                0;
                            "
                          >
                            🔑
                            ${escapeHtml(
                              field
                            )}
                          </span>
                        `
                    )
                    .join("")
                : "Not configured"
            }
          </div>

        </div>

      </div>


      <!-- ================================================== -->
      <!-- MAPPING PREVIEW                                  -->
      <!-- ================================================== -->

      ${
        mappingCount > 0
          ? `
            <details
              style="
                border-top:
                  1px solid
                  var(--border);

                padding-top:
                  0.8rem;
              "
            >

              <summary
                style="
                  cursor:
                    pointer;

                  color:
                    var(--text-secondary);

                  font-size:
                    0.8rem;

                  font-weight:
                    600;
                "
              >
                View saved field mappings
              </summary>


              <div
                style="
                  margin-top:
                    0.7rem;

                  display:
                    flex;

                  flex-direction:
                    column;

                  gap:
                    0.4rem;
                "
              >

                ${Object.entries(
                  mapping
                )
                  .filter(
                    (
                      [
                        ,
                        value,
                      ]
                    ) =>
                      value
                  )
                  .map(
                    (
                      [
                        target,
                        source,
                      ]
                    ) =>
                      `
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

                            padding:
                              0.45rem
                              0.6rem;

                            border-radius:
                              7px;

                            background:
                              rgba(
                                255,
                                255,
                                255,
                                0.02
                              );

                            font-size:
                              0.76rem;
                          "
                        >

                          <span>
                            ${escapeHtml(
                              target
                            )}
                          </span>

                          <span
                            style="
                              color:
                                var(--text-muted);
                            "
                          >
                            →
                          </span>

                          <strong>
                            ${escapeHtml(
                              source
                            )}
                          </strong>

                        </div>
                      `
                  )
                  .join("")}

              </div>

            </details>
          `
          : ""
      }

    </div>
  `;
}


/* ============================================================
   MAIN VIEW
   ============================================================ */

export function renderConfigsView() {

  return `

    <!-- ====================================================== -->
    <!-- HEADER                                                 -->
    <!-- ====================================================== -->

    <div
      class="card"
      style="
        margin-bottom:
          1.25rem;

        background:
          linear-gradient(
            135deg,
            rgba(
              79,
              70,
              229,
              0.12
            ),
            rgba(
              15,
              23,
              42,
              0.96
            )
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
              color:
                #818cf8;

              text-transform:
                uppercase;

              letter-spacing:
                0.07em;

              font-size:
                0.72rem;

              font-weight:
                700;

              margin-bottom:
                0.35rem;
            "
          >
            Reusable Workflows
          </div>


          <h2
            style="
              margin:
                0 0 0.35rem 0;

              font-size:
                1.45rem;

              font-weight:
                750;
            "
          >
            ${i18n.t(
              "configs.title"
            )}
          </h2>


          <p
            style="
              margin:
                0;

              color:
                var(--text-secondary);

              font-size:
                0.88rem;

              line-height:
                1.5;
            "
          >
            ${i18n.t(
              "configs.subtitle"
            )}
          </p>

        </div>


        <div
          style="
            display:
              flex;

            align-items:
              center;

            gap:
              0.6rem;
          "
        >

          <span
            class="
              badge
              badge-info
            "
            style="
              padding:
                0.55rem
                0.75rem;
            "
          >
            📁
            ${savedConfigs.length}
            template${
              savedConfigs.length === 1
                ? ""
                : "s"
            }
          </span>


          <button
            id="btn-config-new-sync"
            class="
              btn
              btn-primary
              btn-sm
            "
          >
            ⚡ New Sync
          </button>

        </div>

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- CONFIG LIST                                            -->
    <!-- ====================================================== -->

    ${
      savedConfigs.length === 0

        ? `
          <div class="card">

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
                📁
              </div>


              <div
                class="empty-title"
              >
                ${i18n.t(
                  "configs.noConfigs"
                )}
              </div>


              <div
                style="
                  color:
                    var(--text-muted);

                  font-size:
                    0.82rem;

                  max-width:
                    480px;

                  margin:
                    0.5rem
                    auto
                    1.1rem;

                  line-height:
                    1.5;
                "
              >
                Save a mapping during a sync and
                reuse it the next time the same
                type of business export arrives.
              </div>


              <button
                id="btn-config-empty-sync"
                class="
                  btn
                  btn-primary
                  btn-sm
                "
              >
                ⚡ Create Your First Sync
              </button>

            </div>

          </div>
        `

        : `
          <div
            style="
              display:
                flex;

              flex-direction:
                column;

              gap:
                1rem;
            "
          >

            ${savedConfigs
              .map(
                (
                  cfg,
                  index
                ) =>
                  renderConfigCard(
                    cfg,
                    index
                  )
              )
              .join("")}

          </div>
        `
    }

  `;
}


/* ============================================================
   EVENT LISTENERS
   ============================================================ */

export function attachConfigsListeners() {

  /* ----------------------------------------------------------
     USE TEMPLATE
     ---------------------------------------------------------- */

  document
    .querySelectorAll(
      ".btn-use-template"
    )
    .forEach(
      (button) => {

        button.addEventListener(
          "click",
          () => {

            const index =
              parseInt(
                button.getAttribute(
                  "data-index"
                ),
                10
              );


            const selected =
              savedConfigs[
                index
              ];


            if (
              !selected ||
              !selected.config
            ) {
              return;
            }


            const config =
              selected.config;


            const targetFields =
              safeArray(
                config.target_fields
              );


            const requiredFields =
              safeArray(
                config.required_fields
              );


            const uniqueKeyFields =
              safeArray(
                config.unique_key_fields
              );


            const mapping =
              config.mapping ||
              config.source_to_target ||
              {};


            store.updateWizard({

              configName:
                config.name ||
                selected.name ||
                "",

              targetFields:
                targetFields.length
                  ? targetFields
                  : store.wizard
                      .targetFields,

              requiredFields:
                requiredFields,

              uniqueKeyFields:
                uniqueKeyFields.length
                  ? uniqueKeyFields
                  : (
                      targetFields.length
                        ? [targetFields[0]]
                        : store.wizard
                            .uniqueKeyFields
                    ),

              mapping:
                mapping,

              /*
               * New file needs to be uploaded.
               * Don't carry over stale source file
               * state from the previous sync.
               */

              fileId:
                null,

              filename:
                "",

              totalRows:
                0,

              sourceColumns:
                [],

              previewData:
                [],

              suggestions:
                {},

              spreadsheetUrl:
                "",

              spreadsheetTitle:
                "",

              worksheets:
                [],

              selectedWorksheet:
                null,

              schemaInfo:
                null,

              syncPreview:
                null,

              executionResult:
                null,

            });


            store.setView(
              "sync"
            );

            store.setStep(
              1
            );

          }
        );

      }
    );


  /* ----------------------------------------------------------
     NEW SYNC FROM HEADER
     ---------------------------------------------------------- */

  const newSyncButton =
    document.getElementById(
      "btn-config-new-sync"
    );


  if (newSyncButton) {

    newSyncButton.addEventListener(
      "click",
      () => {

        store.resetWizard();

        store.setView(
          "sync"
        );

      }
    );
  }


  /* ----------------------------------------------------------
     NEW SYNC FROM EMPTY STATE
     ---------------------------------------------------------- */

  const emptySyncButton =
    document.getElementById(
      "btn-config-empty-sync"
    );


  if (emptySyncButton) {

    emptySyncButton.addEventListener(
      "click",
      () => {

        store.resetWizard();

        store.setView(
          "sync"
        );

      }
    );
  }
}