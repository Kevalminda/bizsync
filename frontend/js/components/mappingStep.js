import { i18n } from "../i18n.js";
import { store } from "../state.js";
import { ApiClient } from "../api.js";


let mappingError = null;


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


function getScore(suggestion) {
  return Number(
    suggestion?.score || 0
  );
}


function isAiSuggestion(suggestion) {
  return Boolean(
    suggestion &&
    suggestion.ai_used
  );
}


/* ============================================================
   SAFETY POLICY
   ============================================================ */

function getMappingSafety(
  suggestion
) {

  if (!suggestion) {

    return {
      level: "UNMAPPED",
      autoAccept: false,
      label: "Unmapped",
      className: "badge-info",
    };

  }


  const score =
    getScore(
      suggestion
    );


  const aiUsed =
    isAiSuggestion(
      suggestion
    );


  /* AI */

  if (aiUsed) {

    if (score >= 0.90) {

      return {
        level: "AI_HIGH",
        autoAccept: true,
        label:
          `🤖 AI HIGH · ${Math.round(score * 100)}%`,
        className:
          "badge-success",
      };

    }


    if (score >= 0.75) {

      return {
        level: "AI_REVIEW",
        autoAccept: false,
        label:
          `🤖 Review · ${Math.round(score * 100)}%`,
        className:
          "badge-warning",
      };

    }


    return {
      level: "AI_LOW",
      autoAccept: false,
      label:
        `🤖 Low confidence · ${Math.round(score * 100)}%`,
      className:
        "badge-danger",
    };

  }


  /* Local */

  if (
    suggestion.confidence ===
      "HIGH" ||
    score >= 0.85
  ) {

    return {
      level: "LOCAL_HIGH",
      autoAccept: true,
      label:
        `High Match · ${Math.round(score * 100)}%`,
      className:
        "badge-success",
    };

  }


  if (
    suggestion.confidence ===
      "MEDIUM" ||
    score >= 0.65
  ) {

    return {
      level: "LOCAL_REVIEW",
      autoAccept: false,
      label:
        `Review · ${Math.round(score * 100)}%`,
      className:
        "badge-warning",
    };

  }


  return {
    level: "LOCAL_LOW",
    autoAccept: false,
    label:
      `Low Match · ${Math.round(score * 100)}%`,
    className:
      "badge-danger",
  };
}


/* ============================================================
   ERROR UI
   ============================================================ */

function renderMappingError() {

  if (!mappingError) {
    return "";
  }


  const message =
    String(
      mappingError?.message ||
      mappingError ||
      "The mapping operation failed."
    );


  return `
    <div
      role="alert"
      style="
        margin-bottom: 1rem;
        padding: 0.9rem 1rem;
        border-radius: 10px;
        border: 1px solid rgba(239,68,68,0.30);
        background: rgba(127,29,29,0.10);
      "
    >

      <div
        style="
          display: flex;
          align-items: flex-start;
          gap: 0.7rem;
        "
      >

        <div>
          ⚠️
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
            Mapping operation failed
          </div>


          <div
            style="
              color: var(--text-secondary);
              font-size: 0.8rem;
              line-height: 1.45;
              overflow-wrap: anywhere;
            "
          >
            ${escapeHtml(
              message
            )}
          </div>

        </div>


        <button
          id="btn-dismiss-mapping-error"
          class="btn btn-secondary btn-sm"
          type="button"
        >
          Dismiss
        </button>

      </div>

    </div>
  `;
}


/* ============================================================
   AI INDICATOR
   ============================================================ */

function renderAiIndicator(
  suggestion
) {

  if (
    !suggestion ||
    !suggestion.ai_used
  ) {
    return "";
  }


  return `
    <span
      style="
        display:
          inline-flex;

        align-items:
          center;

        gap:
          0.25rem;

        margin-left:
          0.45rem;

        padding:
          0.15rem 0.45rem;

        border-radius:
          999px;

        font-size:
          0.67rem;

        font-weight:
          700;

        color:
          #a7f3d0;

        background:
          rgba(
            16,
            185,
            129,
            0.14
          );

        border:
          1px solid
          rgba(
            16,
            185,
            129,
            0.30
          );
      "
    >
      🤖 AI
    </span>
  `;
}


/* ============================================================
   SUGGESTION REASON
   ============================================================ */

function renderSuggestionReason(
  suggestion
) {

  if (!suggestion) {
    return "";
  }


  const reason =
    suggestion.reason ||
    "";


  if (!reason) {
    return "";
  }


  return `
    <div
      style="
        margin-top:
          0.4rem;

        color:
          var(--text-muted);

        font-size:
          0.76rem;

        line-height:
          1.4;
      "
    >
      ${
        suggestion.ai_used
          ? "🤖 "
          : ""
      }

      ${escapeHtml(
        reason
      )}
    </div>
  `;
}


/* ============================================================
   REVIEW NOTICE
   ============================================================ */

function renderReviewNotice(
  suggestion
) {

  if (!suggestion) {
    return "";
  }


  const safety =
    getMappingSafety(
      suggestion
    );


  if (
    safety.level !==
    "AI_REVIEW"
  ) {
    return "";
  }


  return `
    <div
      style="
        margin-top:
          0.4rem;

        color:
          #fbbf24;

        font-size:
          0.72rem;

        font-weight:
          600;
      "
    >
      ⚠ Review before using this AI suggestion
    </div>
  `;
}


/* ============================================================
   SUMMARY
   ============================================================ */

function getMappingSummary(
  suggestions
) {

  const items =
    Object.values(
      suggestions || {}
    );


  let autoAccepted = 0;
  let aiReview = 0;
  let lowConfidence = 0;


  for (
    const suggestion
    of items
  ) {

    const safety =
      getMappingSafety(
        suggestion
      );


    if (
      safety.autoAccept
    ) {
      autoAccepted += 1;
    }


    if (
      safety.level ===
      "AI_REVIEW"
    ) {
      aiReview += 1;
    }


    if (
      safety.level ===
        "AI_LOW" ||
      safety.level ===
        "LOCAL_LOW"
    ) {
      lowConfidence += 1;
    }

  }


  return {
    autoAccepted,
    aiReview,
    lowConfidence,
  };
}


function renderMappingSummary(
  suggestions
) {

  const summary =
    getMappingSummary(
      suggestions
    );


  const hasAiReview =
    summary.aiReview > 0;


  const hasLowConfidence =
    summary.lowConfidence > 0;


  if (
    !hasAiReview &&
    !hasLowConfidence
  ) {

    return `
      <div
        style="
          margin-top:
            1.5rem;

          padding:
            0.85rem 1rem;

          border-radius:
            10px;

          border:
            1px solid
            rgba(
              16,
              185,
              129,
              0.25
            );

          background:
            rgba(
              16,
              185,
              129,
              0.06
            );

          color:
            var(--text-muted);

          font-size:
            0.82rem;
        "
      >
        ✓ All detected mappings meet the current
        automatic-acceptance threshold.
      </div>
    `;
  }


  return `
    <div
      style="
        margin-top:
          1.5rem;

        padding:
          0.9rem 1rem;

        border-radius:
          10px;

        border:
          1px solid
          var(--border);

        background:
          rgba(
            255,
            255,
            255,
            0.025
          );
      "
    >

      <div
        style="
          font-weight:
            700;

          margin-bottom:
            0.55rem;
        "
      >
        🛡 Mapping Safety Check
      </div>


      <div
        style="
          display:
            flex;

          flex-wrap:
            wrap;

          gap:
            0.7rem;

          color:
            var(--text-muted);

          font-size:
            0.8rem;
        "
      >

        <span>
          ✓ Auto-accepted:
          <strong>
            ${summary.autoAccepted}
          </strong>
        </span>


        ${
          hasAiReview
            ? `
              <span>
                ⚠ AI review:
                <strong>
                  ${summary.aiReview}
                </strong>
              </span>
            `
            : ""
        }


        ${
          hasLowConfidence
            ? `
              <span>
                ⛔ Low confidence:
                <strong>
                  ${summary.lowConfidence}
                </strong>
              </span>
            `
            : ""
        }

      </div>


      ${
        hasAiReview
          ? `
            <div
              style="
                margin-top:
                  0.55rem;

                color:
                  var(--text-muted);

                font-size:
                  0.76rem;
              "
            >
              Medium-confidence AI mappings are shown as
              suggestions and are not automatically trusted.
            </div>
          `
          : ""
      }

    </div>
  `;
}


/* ============================================================
   MAIN RENDER
   ============================================================ */

export function renderMappingStep() {

  const {
    targetFields,
    sourceColumns,
    mapping,
    suggestions,
  } = store.wizard;


  return `
    <div class="card">

      <div class="card-header">

        <div>

          <h3 class="card-title">
            ${i18n.t(
              "mapping.title"
            )}
          </h3>

          <p class="card-subtitle">
            ${i18n.t(
              "mapping.subtitle"
            )}
          </p>

        </div>


        <button
          id="btn-auto-suggest"
          class="
            btn
            btn-secondary
            btn-sm
          "
          type="button"
        >
          🤖 Run Auto-Suggest Magic
        </button>

      </div>


      ${renderMappingError()}


      <div
        class="badge badge-info"
        style="
          margin-bottom:
            1.5rem;

          width:
            100%;

          justify-content:
            flex-start;

          padding:
            0.75rem 1rem;
        "
      >
        💡 ${i18n.t(
          "mapping.autoSuggestInfo"
        )}
      </div>


      <div
        style="
          margin-bottom:
            1rem;

          padding:
            0.8rem 1rem;

          border-radius:
            10px;

          border:
            1px solid
            var(--border);

          background:
            rgba(
              255,
              255,
              255,
              0.02
            );

          color:
            var(--text-muted);

          font-size:
            0.78rem;

          line-height:
            1.5;
        "
      >
        🛡
        <strong
          style="
            color:
              var(--text-primary);
          "
        >
          Smart mapping safety:
        </strong>

        high-confidence matches are accepted
        automatically, medium-confidence AI results
        require review, and low-confidence results
        remain unmapped.
      </div>


      <div class="mapping-grid">

        ${targetFields
          .map(
            (target) => {

              const currentSource =
                mapping[target] ||
                "";


              const suggestion =
                suggestions[target];


              const safety =
                getMappingSafety(
                  suggestion
                );


              return `
                <div
                  class="mapping-row"
                  style="
                    ${
                      safety.level ===
                      "AI_REVIEW"
                        ? "border-color: rgba(245,158,11,0.45);"
                        : ""
                    }

                    ${
                      safety.level ===
                      "AI_LOW"
                        ? "border-color: rgba(239,68,68,0.45);"
                        : ""
                    }
                  "
                >

                  <div
                    class="mapping-target-name"
                  >

                    <span>
                      ${escapeHtml(
                        target
                      )}
                    </span>


                    ${
                      store.wizard
                        .uniqueKeyFields
                        .includes(
                          target
                        )
                        ? `
                          <span
                            class="mapping-target-badge"
                            style="
                              background:
                                var(
                                  --primary-light
                                );

                              color:
                                #818cf8;
                            "
                          >
                            🔑 Key
                          </span>
                        `
                        : ""
                    }


                    ${renderAiIndicator(
                      suggestion
                    )}

                  </div>


                  <div
                    class="mapping-arrow"
                  >
                    ➜
                  </div>


                  <div>

                    <select
                      class="
                        form-select
                        mapping-select
                      "
                      data-target="${escapeHtml(
                        target
                      )}"
                    >

                      <option value="">
                        -- Select Source Column --
                      </option>

                      ${sourceColumns
                        .map(
                          (column) =>
                            `
                              <option
                                value="${escapeHtml(
                                  column
                                )}"
                                ${
                                  column ===
                                  currentSource
                                    ? "selected"
                                    : ""
                                }
                              >
                                ${escapeHtml(
                                  column
                                )}
                              </option>
                            `
                        )
                        .join("")}

                    </select>


                    ${
                      suggestion &&
                      suggestion.source
                        ? `
                          <div
                            style="
                              margin-top:
                                0.35rem;

                              color:
                                var(
                                  --text-muted
                                );

                              font-size:
                                0.72rem;
                            "
                          >
                            Suggested:
                            <strong>
                              ${escapeHtml(
                                suggestion.source
                              )}
                            </strong>
                          </div>
                        `
                        : ""
                    }


                    ${renderSuggestionReason(
                      suggestion
                    )}


                    ${renderReviewNotice(
                      suggestion
                    )}

                  </div>


                  <div>

                    <span
                      class="
                        badge
                        ${
                          safety.className
                        }
                      "
                    >
                      ${
                        suggestion
                          ? safety.label
                          : "Unmapped"
                      }
                    </span>

                  </div>

                </div>
              `;

            }
          )
          .join("")}

      </div>


      ${
        Object.keys(
          suggestions
        ).length > 0
          ? renderMappingSummary(
              suggestions
            )
          : ""
      }


      <!-- ================================================== -->
      <!-- SAVE CONFIG                                        -->
      <!-- ================================================== -->

      <div
        style="
          margin-top:
            2rem;

          padding-top:
            1.5rem;

          border-top:
            1px solid
            var(--border-subtle);

          display:
            flex;

          align-items:
            center;

          gap:
            1rem;

          flex-wrap:
            wrap;
        "
      >

        <input
          type="text"
          id="config-name-input"
          class="form-input"
          placeholder="${i18n.t(
            "mapping.configNamePlaceholder"
          )}"
          value="${escapeHtml(
            store.wizard.configName
          )}"
          style="
            max-width:
              320px;
          "
        />


        <button
          id="btn-save-template"
          class="
            btn
            btn-secondary
            btn-sm
          "
          type="button"
        >
          💾 ${i18n.t(
            "mapping.saveConfig"
          )}
        </button>

      </div>

    </div>
  `;
}


/* ============================================================
   LISTENERS
   ============================================================ */

export function attachMappingStepListeners() {

  /* ----------------------------------------------------------
     AUTO SUGGEST
     ---------------------------------------------------------- */

  const autoSuggestBtn =
    document.getElementById(
      "btn-auto-suggest"
    );


  if (autoSuggestBtn) {

    autoSuggestBtn.addEventListener(
      "click",
      async () => {

        mappingError =
          null;


        const originalText =
          autoSuggestBtn.innerHTML;


        autoSuggestBtn.disabled =
          true;


        autoSuggestBtn.innerHTML =
          "🤖 Analyzing mappings...";


        try {

          const res =
            await ApiClient.suggestMapping(

              store.wizard
                .targetFields,

              store.wizard
                .sourceColumns

            );


          const newMapping = {
            ...store.wizard.mapping,
          };


          for (
            const [
              target,
              item
            ]
              of Object.entries(
                res.suggestions || {}
              )
          ) {

            const safety =
              getMappingSafety(
                item
              );


            /*
             * Only auto-accept:
             *
             * Local high confidence
             * OR
             * AI >= 90%
             */

            if (
              item.source &&
              safety.autoAccept
            ) {

              newMapping[
                target
              ] = item.source;

            } else {

              /*
               * Medium and low confidence
               * suggestions remain for review,
               * but we do not silently trust them.
               */
              if (
                safety.level ===
                  "AI_REVIEW" ||
                safety.level ===
                  "AI_LOW" ||
                safety.level ===
                  "LOCAL_LOW"
              ) {

                if (
                  !store.wizard.mapping[
                    target
                  ]
                ) {

                  newMapping[
                    target
                  ] = "";

                }

              }

            }

          }


          store.updateWizard({

            suggestions:
              res.suggestions || {},

            mapping:
              newMapping,

          });


          mappingError =
            null;


        } catch (error) {

          console.error(
            "Auto-suggest failed:",
            error
          );


          mappingError =
            error;

          store.notify();


        } finally {

          const button =
            document.getElementById(
              "btn-auto-suggest"
            );


          if (
            button &&
            button.isConnected
          ) {

            button.disabled =
              false;

            button.innerHTML =
              originalText;

          }

        }

      }
    );

  }


  /* ----------------------------------------------------------
     MANUAL MAPPING
     ---------------------------------------------------------- */

  document
    .querySelectorAll(
      ".mapping-select"
    )
    .forEach(
      (select) => {

        select.addEventListener(
          "change",
          (event) => {

            const target =
              event.target.getAttribute(
                "data-target"
              );


            const value =
              event.target.value;


            const updatedMapping = {

              ...store.wizard.mapping,

              [target]:
                value,

            };


            mappingError =
              null;


            store.updateWizard({

              mapping:
                updatedMapping,

            });

          }
        );

      }
    );


  /* ----------------------------------------------------------
     SAVE CONFIGURATION
     ---------------------------------------------------------- */

  const saveBtn =
    document.getElementById(
      "btn-save-template"
    );


  if (saveBtn) {

    saveBtn.addEventListener(
      "click",
      async () => {

        const nameInput =
          document.getElementById(
            "config-name-input"
          );


        const name =
          nameInput
            ? nameInput.value.trim()
            : "";


        if (!name) {

          mappingError = {
            message:
              "Please enter a template name.",
          };


          store.notify();

          return;
        }


        mappingError =
          null;


        saveBtn.disabled =
          true;


        const originalText =
          saveBtn.innerHTML;


        saveBtn.innerHTML =
          "Saving...";


        try {

          await ApiClient.saveConfig({

            name:
              name,

            target_fields:
              store.wizard
                .targetFields,

            required_fields:
              store.wizard
                .requiredFields,

            unique_key_fields:
              store.wizard
                .uniqueKeyFields,

            mapping:
              store.wizard
                .mapping,

          });


          store.updateWizard({
            configName:
              name,
          });


          mappingError =
            null;


        } catch (error) {

          console.error(
            "Failed to save template:",
            error
          );


          mappingError =
            error;


          store.notify();


        } finally {

          const button =
            document.getElementById(
              "btn-save-template"
            );


          if (
            button &&
            button.isConnected
          ) {

            button.disabled =
              false;

            button.innerHTML =
              originalText;

          }

        }

      }
    );

  }


  /* ----------------------------------------------------------
     DISMISS ERROR
     ---------------------------------------------------------- */

  const dismissBtn =
    document.getElementById(
      "btn-dismiss-mapping-error"
    );


  if (dismissBtn) {

    dismissBtn.addEventListener(
      "click",
      () => {

        mappingError =
          null;

        store.notify();

      }
    );

  }

}