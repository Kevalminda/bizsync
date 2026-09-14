import { i18n } from "../i18n.js";
import { store } from "../state.js";

let activeTab = "new";


/* ============================================================
   BASIC HELPERS
   ============================================================ */

function formatConfidence(value) {
  const numeric = Number(value || 0);
  return `${Math.round(numeric * 100)}%`;
}


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


/* ============================================================
   LOCAL DUPLICATE BADGE
   ============================================================ */

function duplicateBadge(status) {

  if (status === "EXACT_DUPLICATE") {
    return `
      <span class="badge pill-skipped">
        EXACT DUPLICATE
      </span>
    `;
  }

  if (status === "POSSIBLE_DUPLICATE") {
    return `
      <span class="badge pill-updated">
        POSSIBLE DUPLICATE
      </span>
    `;
  }

  return `
    <span class="badge pill-unchanged">
      PROBABLY NEW
    </span>
  `;
}


/* ============================================================
   AI DECISION BADGE
   ============================================================ */

function aiDecisionBadge(
  decision,
  available
) {

  if (!available) {
    return `
      <span class="badge badge-warning">
        AI REVIEW UNAVAILABLE
      </span>
    `;
  }

  if (
    decision === "LIKELY_DUPLICATE"
  ) {
    return `
      <span class="badge pill-skipped">
        AI: LIKELY DUPLICATE
      </span>
    `;
  }

  if (
    decision === "LIKELY_NOT_DUPLICATE"
  ) {
    return `
      <span class="badge pill-new">
        AI: LIKELY NOT DUPLICATE
      </span>
    `;
  }

  if (
    decision === "REVIEW_REQUIRED"
  ) {
    return `
      <span class="badge pill-updated">
        AI: REVIEW REQUIRED
      </span>
    `;
  }

  return `
    <span class="badge pill-unchanged">
      AI: NOT RUN
    </span>
  `;
}


/* ============================================================
   RECOMMENDATION
   ============================================================ */

function getRecommendation(
  warning
) {

  const aiAvailable =
    Boolean(
      warning.ai_available
    );

  const decision =
    warning.ai_decision ||
    "NOT_RUN";


  /*
   * Gemini available
   */

  if (aiAvailable) {

    if (
      decision ===
      "LIKELY_NOT_DUPLICATE"
    ) {

      return {
        title:
          "Safe to add as a new record",

        text:
          "The AI verifier found meaningful differences between the two transactions.",

        icon:
          "✓",

        className:
          "new",
      };
    }


    if (
      decision ===
      "LIKELY_DUPLICATE"
    ) {

      return {
        title:
          "Review before syncing",

        text:
          "The AI verifier believes this incoming record is likely related to an existing destination record.",

        icon:
          "⚠",

        className:
          "warning",
      };
    }


    if (
      decision ===
      "REVIEW_REQUIRED"
    ) {

      return {
        title:
          "Manual review recommended",

        text:
          "The available evidence is ambiguous. Review the incoming and existing records before syncing.",

        icon:
          "!",
        
        className:
          "warning",
      };
    }
  }


  /*
   * Gemini unavailable / fallback
   */

  return {
    title:
      "Review similarity warning",

    text:
      "AI verification is unavailable. Review the local duplicate analysis before syncing.",

    icon:
      "⚠",

    className:
      "warning",
  };
}


/* ============================================================
   RECOMMENDATION UI
   ============================================================ */

function renderRecommendation(
  warning
) {

  const recommendation =
    getRecommendation(
      warning
    );


  const iconColor =
    recommendation.className ===
    "new"
      ? "#22c55e"
      : "#f59e0b";


  return `
    <div
      style="
        margin-top: 1rem;
        padding: 0.9rem 1rem;
        border-radius: 10px;
        border: 1px solid var(--border);
        background:
          rgba(255,255,255,0.025);
      "
    >

      <div
        style="
          display: flex;
          gap: 0.75rem;
          align-items: flex-start;
        "
      >

        <div
          style="
            width: 30px;
            height: 30px;
            min-width: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.9rem;
            color: ${iconColor};
            border: 1px solid ${iconColor};
          "
        >
          ${recommendation.icon}
        </div>


        <div>

          <div
            style="
              font-weight: 700;
              margin-bottom: 0.25rem;
            "
          >
            Recommendation:
            ${escapeHtml(
              recommendation.title
            )}
          </div>

          <div
            style="
              color: var(--text-muted);
              font-size: 0.84rem;
              line-height: 1.5;
            "
          >
            ${escapeHtml(
              recommendation.text
            )}
          </div>

        </div>

      </div>

    </div>
  `;
}


/* ============================================================
   RECORD COMPARISON TABLE
   ============================================================ */

function renderComparisonTable(
  incomingRecord,
  existingRecord,
  targetFields,
  matchedFields = [],
  differentFields = []
) {

  if (
    !incomingRecord ||
    !existingRecord
  ) {
    return "";
  }


  return `
    <div
      style="
        margin-top: 1rem;
        overflow-x: auto;
      "
    >

      <table class="data-table">

        <thead>

          <tr>
            <th>Field</th>
            <th>Incoming</th>
            <th>Existing</th>
            <th>Match</th>
          </tr>

        </thead>


        <tbody>

          ${targetFields
            .map(
              (field) => {

                const incomingValue =
                  incomingRecord[
                    field
                  ] ?? "";


                const existingValue =
                  existingRecord[
                    field
                  ] ?? "";


                const isMatched =
                  matchedFields.includes(
                    field
                  );


                const isDifferent =
                  differentFields.includes(
                    field
                  );


                let resultLabel = "";


                if (isMatched) {

                  resultLabel = `
                    <span
                      style="
                        color: #22c55e;
                        font-weight: 600;
                      "
                    >
                      ✓ Match
                    </span>
                  `;

                } else if (
                  isDifferent
                ) {

                  resultLabel = `
                    <span
                      style="
                        color: #f59e0b;
                        font-weight: 600;
                      "
                    >
                      ≠ Different
                    </span>
                  `;

                } else {

                  resultLabel = `
                    <span
                      style="
                        color: var(--text-muted);
                      "
                    >
                      —
                    </span>
                  `;
                }


                return `
                  <tr>

                    <td>
                      <strong>
                        ${escapeHtml(
                          field
                        )}
                      </strong>
                    </td>


                    <td>
                      ${escapeHtml(
                        incomingValue
                      )}
                    </td>


                    <td>
                      ${escapeHtml(
                        existingValue
                      )}
                    </td>


                    <td>
                      ${resultLabel}
                    </td>

                  </tr>
                `;
              }
            )
            .join("")}

        </tbody>

      </table>

    </div>
  `;
}


/* ============================================================
   AI VERIFICATION
   ============================================================ */

function renderAiVerification(
  warning
) {

  const aiAvailable =
    Boolean(
      warning.ai_available
    );


  const decision =
    warning.ai_decision ||
    "NOT_RUN";


  const aiConfidence =
    Number(
      warning.ai_confidence || 0
    );


  const aiReason =
    warning.ai_reason ||
    "No AI explanation available.";


  const aiModel =
    warning.ai_model ||
    "Gemini";


  /*
   * AI was not called.
   */

  if (
    decision === "NOT_RUN"
  ) {

    return `
      <div
        style="
          margin-top: 1rem;
          border: 1px dashed var(--border);
          border-radius: 10px;
          padding: 0.9rem;
        "
      >

        <div
          style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
          "
        >

          <div>

            <div
              style="
                font-weight: 700;
                margin-bottom: 0.2rem;
              "
            >
              🤖 AI Verification
            </div>

            <div
              style="
                color: var(--text-muted);
                font-size: 0.82rem;
              "
            >
              AI verification was not required.
            </div>

          </div>

          ${aiDecisionBadge(
            decision,
            false
          )}

        </div>

      </div>
    `;
  }


  /*
   * AI available or unavailable.
   */

  return `
    <div
      style="
        margin-top: 1rem;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem;
        background:
          rgba(255,255,255,0.02);
      "
    >

      <div
        style="
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          flex-wrap: wrap;
        "
      >

        <div>

          <div
            style="
              display: flex;
              align-items: center;
              gap: 0.5rem;
              flex-wrap: wrap;
              margin-bottom: 0.3rem;
            "
          >

            <strong>
              🤖 AI Verification
            </strong>

            ${aiDecisionBadge(
              decision,
              aiAvailable
            )}

          </div>


          <div
            style="
              color: var(--text-muted);
              font-size: 0.8rem;
            "
          >
            Model:
            ${escapeHtml(
              aiModel
            )}
          </div>

        </div>


        ${
          aiAvailable
            ? `
              <div
                style="
                  text-align: right;
                "
              >

                <div
                  style="
                    font-size: 1.15rem;
                    font-weight: 700;
                  "
                >
                  ${formatConfidence(
                    aiConfidence
                  )}
                </div>

                <div
                  style="
                    color: var(--text-muted);
                    font-size: 0.75rem;
                  "
                >
                  AI confidence
                </div>

              </div>
            `
            : ""
        }

      </div>


      <div
        style="
          margin-top: 0.75rem;
          color: var(--text-muted);
          font-size: 0.87rem;
          line-height: 1.55;
        "
      >

        ${
          aiAvailable
            ? escapeHtml(
                aiReason
              )
            : "Gemini verification was unavailable. The local similarity analysis remains available for manual review."
        }

      </div>

    </div>
  `;
}


/* ============================================================
   DUPLICATE WARNING SECTION
   ============================================================ */

function renderDuplicateWarnings(
  warnings,
  targetFields
) {

  if (
    !warnings ||
    warnings.length === 0
  ) {
    return "";
  }


  return `
    <div
      class="card"
      style="
        margin-top: 1rem;
        border: 1px solid var(--border);
      "
    >

      <div class="card-header">

        <div>

          <h3 class="card-title">
            🧠 Duplicate Intelligence
          </h3>

          <p class="card-subtitle">
            BizSync first checks record similarity,
            then uses AI to verify ambiguous cases.
          </p>

        </div>


        <span
          class="badge badge-warning"
        >
          ${warnings.length}
          warning${
            warnings.length === 1
              ? ""
              : "s"
          }
        </span>

      </div>


      <div
        style="
          display: flex;
          flex-direction: column;
          gap: 1rem;
        "
      >

        ${warnings
          .map(
            (warning) => {

              const incomingRecord =
                warning.incoming_record ||
                {};


              const existingRecord =
                warning.existing_record ||
                {};


              return `
                <div
                  class="card"
                  style="
                    padding: 1.1rem;
                    background:
                      var(
                        --surface-secondary,
                        rgba(255,255,255,0.03)
                      );
                  "
                >

                  <!-- ===================================== -->
                  <!-- LOCAL DETECTOR HEADER                -->
                  <!-- ===================================== -->

                  <div
                    style="
                      display: flex;
                      align-items: center;
                      justify-content: space-between;
                      gap: 1rem;
                      flex-wrap: wrap;
                    "
                  >

                    <div>

                      <div
                        style="
                          display: flex;
                          gap: 0.5rem;
                          align-items: center;
                          flex-wrap: wrap;
                          margin-bottom: 0.4rem;
                        "
                      >

                        ${duplicateBadge(
                          warning.status
                        )}

                        <strong>
                          Incoming Record #${
                            Number(
                              warning.incoming_index
                            ) + 1
                          }
                        </strong>

                      </div>


                      <div
                        style="
                          color: var(--text-muted);
                          font-size: 0.88rem;
                        "
                      >
                        Local similarity analysis
                        found a possible relationship
                        with an existing destination record.
                      </div>

                    </div>


                    <div
                      style="
                        text-align: right;
                      "
                    >

                      <div
                        style="
                          font-size: 1.25rem;
                          font-weight: 700;
                        "
                      >
                        ${formatConfidence(
                          warning.confidence
                        )}
                      </div>

                      <div
                        style="
                          color: var(--text-muted);
                          font-size: 0.78rem;
                        "
                      >
                        local similarity
                      </div>

                    </div>

                  </div>


                  <!-- ===================================== -->
                  <!-- RECORD COMPARISON                     -->
                  <!-- ===================================== -->

                  ${renderComparisonTable(
                    incomingRecord,
                    existingRecord,
                    targetFields,
                    warning.matched_fields ||
                      [],
                    warning.different_fields ||
                      []
                  )}


                  <!-- ===================================== -->
                  <!-- MATCHING FIELDS                       -->
                  <!-- ===================================== -->

                  ${
                    warning.matched_fields &&
                    warning.matched_fields.length
                      ? `
                        <div
                          style="
                            margin-top: 0.75rem;
                            font-size: 0.85rem;
                          "
                        >

                          <strong>
                            Matching fields:
                          </strong>

                          <span
                            style="
                              color: var(--text-muted);
                            "
                          >

                            ${warning.matched_fields
                              .map(
                                (field) =>
                                  escapeHtml(
                                    field
                                  )
                              )
                              .join(
                                ", "
                              )}

                          </span>

                        </div>
                      `
                      : ""
                  }


                  <!-- ===================================== -->
                  <!-- IDENTIFIER DIFFERENCES                 -->
                  <!-- ===================================== -->

                  ${
                    warning.identifier_conflicts &&
                    warning.identifier_conflicts.length
                      ? `
                        <div
                          style="
                            margin-top: 0.5rem;
                            font-size: 0.85rem;
                          "
                        >

                          <strong>
                            Identifier differences:
                          </strong>

                          <span
                            style="
                              color: var(--text-muted);
                            "
                          >

                            ${
                              warning.identifier_conflicts
                                .map(
                                  (
                                    conflict
                                  ) =>
                                    escapeHtml(
                                      conflict.field
                                    )
                                )
                                .join(
                                  ", "
                                )
                            }

                          </span>

                        </div>
                      `
                      : ""
                  }


                  <!-- ===================================== -->
                  <!-- AI VERIFICATION                        -->
                  <!-- ===================================== -->

                  ${renderAiVerification(
                    warning
                  )}


                  <!-- ===================================== -->
                  <!-- FINAL RECOMMENDATION                   -->
                  <!-- ===================================== -->

                  ${renderRecommendation(
                    warning
                  )}

                </div>
              `;
            }
          )
          .join("")}

      </div>

    </div>
  `;
}


/* ============================================================
   MAIN PREVIEW
   ============================================================ */

export function renderPreviewStep() {

  const {
    syncPreview,
    targetFields,
  } = store.wizard;


  if (!syncPreview) {

    return `
      <div class="card">

        <div class="empty-state">

          <div class="empty-icon">
            ⟳
          </div>

          <div class="empty-title">
            Calculating Sync Preview Diff...
          </div>

        </div>

      </div>
    `;
  }


  const {
    new_count,
    updated_count,
    unchanged_count,
    skipped_count,
    duplicate_count = 0,
    duplicate_warnings = [],
    errors,
    new_records = [],
    updated_records = [],
    unchanged_records = [],
    skipped_records = [],
  } = syncPreview;


  let currentRecords = [];


  if (
    activeTab === "new"
  ) {

    currentRecords =
      new_records;

  } else if (
    activeTab === "updated"
  ) {

    currentRecords =
      updated_records;

  } else if (
    activeTab === "unchanged"
  ) {

    currentRecords =
      unchanged_records;

  } else if (
    activeTab === "skipped"
  ) {

    currentRecords =
      skipped_records;
  }


  return `

    <div class="card">

      <div class="card-header">

        <div>

          <h3 class="card-title">
            ${i18n.t(
              "preview.title"
            )}
          </h3>

          <p class="card-subtitle">
            ${i18n.t(
              "preview.subtitle"
            )}
          </p>

        </div>

      </div>


      ${
        duplicate_count > 0
          ? `
            <div
              class="badge badge-warning"
              style="
                margin-bottom: 1rem;
                width: 100%;
                justify-content: flex-start;
                padding: 0.75rem 1rem;
              "
            >
              🧠 ${duplicate_count}
              possible duplicate${
                duplicate_count === 1
                  ? ""
                  : "s"
              }
              detected.
              AI verification is shown below.
            </div>
          `
          : ""
      }


      <!-- ============================================= -->
      <!-- PREVIEW TABS                                 -->
      <!-- ============================================= -->

      <div class="preview-tabs">

        <div
          class="
            preview-tab
            ${
              activeTab === "new"
                ? "active"
                : ""
            }
          "
          data-tab="new"
        >

          <span class="badge pill-new">
            NEW
          </span>

          <span>
            ${i18n.t(
              "preview.newRecords"
            )}
          </span>

          <span class="tab-count">
            ${new_count}
          </span>

        </div>


        <div
          class="
            preview-tab
            ${
              activeTab === "updated"
                ? "active"
                : ""
            }
          "
          data-tab="updated"
        >

          <span class="badge pill-updated">
            UPDATED
          </span>

          <span>
            ${i18n.t(
              "preview.updatedRecords"
            )}
          </span>

          <span class="tab-count">
            ${updated_count}
          </span>

        </div>


        <div
          class="
            preview-tab
            ${
              activeTab === "unchanged"
                ? "active"
                : ""
            }
          "
          data-tab="unchanged"
        >

          <span class="badge pill-unchanged">
            UNCHANGED
          </span>

          <span>
            ${i18n.t(
              "preview.unchangedRecords"
            )}
          </span>

          <span class="tab-count">
            ${unchanged_count}
          </span>

        </div>


        <div
          class="
            preview-tab
            ${
              activeTab === "skipped"
                ? "active"
                : ""
            }
          "
          data-tab="skipped"
        >

          <span class="badge pill-skipped">
            SKIPPED
          </span>

          <span>
            ${i18n.t(
              "preview.skippedRecords"
            )}
          </span>

          <span class="tab-count">
            ${skipped_count}
          </span>

        </div>

      </div>


      <!-- ============================================= -->
      <!-- ERRORS / WARNINGS                            -->
      <!-- ============================================= -->

      ${
        errors &&
        errors.length
          ? `
            <div
              class="badge badge-warning"
              style="
                margin-bottom: 1rem;
                width: 100%;
                justify-content: flex-start;
                padding: 0.75rem 1rem;
              "
            >
              ⚠️ Warnings / Errors:
              ${errors.join(" | ")}
            </div>
          `
          : ""
      }


      <!-- ============================================= -->
      <!-- CURRENT RECORD TABLE                         -->
      <!-- ============================================= -->

      <div class="table-container">

        ${
          currentRecords.length === 0

            ? `
              <div
                class="empty-state"
                style="
                  padding: 2.5rem;
                "
              >

                <div
                  class="empty-title"
                  style="
                    font-size: 1rem;
                  "
                >
                  No records in this category
                </div>

              </div>
            `

            : `
              <table class="data-table">

                <thead>

                  <tr>

                    <th>
                      #
                    </th>

                    ${targetFields
                      .map(
                        (field) =>
                          `
                            <th>
                              ${escapeHtml(
                                field
                              )}
                            </th>
                          `
                      )
                      .join("")}

                  </tr>

                </thead>


                <tbody>

                  ${currentRecords
                    .map(
                      (
                        row,
                        idx
                      ) => `

                        <tr>

                          <td
                            style="
                              color:
                                var(
                                  --text-muted
                                );
                            "
                          >
                            ${idx + 1}
                          </td>


                          ${targetFields
                            .map(
                              (field) =>
                                `
                                  <td>
                                    ${escapeHtml(
                                      row[
                                        field
                                      ] ??
                                      ""
                                    )}
                                  </td>
                                `
                            )
                            .join("")}

                        </tr>

                      `
                    )
                    .join("")}

                </tbody>

              </table>
            `
        }

      </div>

    </div>


    <!-- ============================================= -->
    <!-- DUPLICATE INTELLIGENCE                       -->
    <!-- ============================================= -->

    ${renderDuplicateWarnings(
      duplicate_warnings,
      targetFields
    )}

  `;
}


/* ============================================================
   EVENT LISTENERS
   ============================================================ */

export function attachPreviewStepListeners(
  renderCallback
) {

  document
    .querySelectorAll(
      ".preview-tab"
    )
    .forEach(
      (tab) => {

        tab.addEventListener(
          "click",
          () => {

            activeTab =
              tab.getAttribute(
                "data-tab"
              );

            if (renderCallback) {
              renderCallback();
            }

          }
        );

      }
    );
}