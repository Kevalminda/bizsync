import { i18n } from "../i18n.js";
import { store } from "../state.js";
import { ApiClient } from "../api.js";


/* ============================================================
   ERROR STATE
   ============================================================ */

let sheetsError = null;


/* ============================================================
   HTML ESCAPE
   ============================================================ */

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


/* ============================================================
   GOOGLE SHEETS URL VALIDATION
   ============================================================ */

/*
 * This function performs ONLY client-side structural
 * validation.
 *
 * It does NOT try to determine:
 * - whether the sheet exists
 * - whether the user owns the sheet
 * - whether the user has access
 *
 * Those checks are performed by the backend.
 */
function validateSpreadsheetUrl(url) {

  const value =
    String(url || "").trim();


  /* ----------------------------------------------------------
     1. Empty URL
     ---------------------------------------------------------- */

  if (!value) {

    return {
      valid: false,

      title:
        "Google Sheet URL required",

      message:
        "Enter the URL of the Google spreadsheet you want BizSync to use.",
    };

  }


  /* ----------------------------------------------------------
     2. Basic URL parsing
     ---------------------------------------------------------- */

  let parsedUrl;

  try {

    parsedUrl =
      new URL(value);

  } catch (error) {

    return {
      valid: false,

      title:
        "Invalid Google Sheets URL",

      message:
        "The value you entered is not a valid web address. Paste the complete Google Sheets URL from your browser.",
    };

  }


  /* ----------------------------------------------------------
     3. Protocol check
     * --------------------------------------------------------- */

  if (
    parsedUrl.protocol !==
      "http:" &&
    parsedUrl.protocol !==
      "https:"
  ) {

    return {
      valid: false,

      title:
        "Invalid Google Sheets URL",

      message:
        "The spreadsheet link must begin with http:// or https://.",
    };

  }


  /* ----------------------------------------------------------
     4. Host check
     * --------------------------------------------------------- */

  const hostname =
    parsedUrl.hostname.toLowerCase();


  if (
    hostname !==
    "docs.google.com"
  ) {

    return {
      valid: false,

      title:
        "Not a Google Sheets URL",

      message:
        "BizSync expects a Google Sheets link from docs.google.com.",
    };

  }


  /* ----------------------------------------------------------
     5. Path check
     * --------------------------------------------------------- */

  const path =
    parsedUrl.pathname;


  const sheetsPrefix =
    "/spreadsheets/d/";


  if (
    !path
      .toLowerCase()
      .startsWith(
        sheetsPrefix
      )
  ) {

    return {
      valid: false,

      title:
        "Invalid Google Sheets URL",

      message:
        "The link uses Google, but it does not have the expected Google Sheets format: /spreadsheets/d/...",
    };

  }


  /* ----------------------------------------------------------
     6. Extract spreadsheet ID
     * --------------------------------------------------------- */

  const pathAfterPrefix =
    path.substring(
      sheetsPrefix.length
    );


  /*
   * The spreadsheet ID is the first path segment
   * after /spreadsheets/d/
   */
  const spreadsheetId =
    pathAfterPrefix
      .split("/")[0]
      .trim();


  if (!spreadsheetId) {

    return {
      valid: false,

      title:
        "Incomplete Google Sheets URL",

      message:
        "The spreadsheet ID is missing. Copy the complete Google Sheets link, including the part after /d/.",
    };

  }


  /* ----------------------------------------------------------
     7. Basic spreadsheet ID sanity check
     * --------------------------------------------------------- */

  /*
   * Google spreadsheet IDs normally use URL-safe characters.
   *
   * This is intentionally NOT extremely strict.
   * We don't want to reject a legitimate Google ID because
   * of an unnecessary client-side assumption.
   */
  const validIdPattern =
    /^[A-Za-z0-9_-]+$/;


  if (
    !validIdPattern.test(
      spreadsheetId
    )
  ) {

    return {
      valid: false,

      title:
        "Invalid spreadsheet ID",

      message:
        "The Google Sheets link contains an invalid or incomplete spreadsheet ID.",
    };

  }


  /* ----------------------------------------------------------
     8. URL passed structural validation
     * --------------------------------------------------------- */

  return {
    valid: true,

    spreadsheetId:
      spreadsheetId,
  };

}


/* ============================================================
   ERROR PRESENTATION
   ============================================================ */

function getSheetsErrorDetails(error) {

  const message =
    String(
      error?.message ||
      error ||
      "An unexpected Google Sheets error occurred."
    );


  const lower =
    message.toLowerCase();


  /* Network */

  if (
    error?.code ===
      "NETWORK_ERROR" ||
    lower.includes(
      "could not reach the server"
    )
  ) {

    return {

      title:
        "Backend unavailable",

      message:
        "BizSync could not reach the server. Make sure the FastAPI server is running and try again.",

      type:
        "error",

    };

  }


  /* Authorization */

  if (
    error?.status === 401 ||
    lower.includes(
      "authorization"
    )
  ) {

    return {

      title:
        "Google authorization required",

      message:
        "The Google account authorization is missing or expired. Authorize the account used by BizSync and try again.",

      type:
        "warning",

    };

  }


  /* Permission */

  if (
    error?.status === 403 ||
    lower.includes(
      "access denied"
    ) ||
    lower.includes(
      "permission"
    )
  ) {

    return {

      title:
        "Google Sheet access denied",

      message:
        "Your authorized Google account does not appear to have access to this spreadsheet.",

      type:
        "warning",

    };

  }


  /* Not found */

  if (
    error?.status === 404 ||
    lower.includes(
      "not found"
    )
  ) {

    return {

      title:
        "Google Sheet not found",

      message:
        "The spreadsheet could not be found. Check that the URL is complete and that the sheet still exists.",

      type:
        "warning",

    };

  }


  /* URL related */

  if (
    lower.includes(
      "url"
    ) ||
    lower.includes(
      "spreadsheet"
    ) ||
    lower.includes(
      "google sheet"
    )
  ) {

    return {

      title:
        "Google Sheet connection failed",

      message:
        message,

      type:
        "warning",

    };

  }


  return {

    title:
      "Google Sheet error",

    message:
      message,

    type:
      "error",

  };

}


/* ============================================================
   ERROR BANNER
   ============================================================ */

function renderSheetsError() {

  if (!sheetsError) {
    return "";
  }


  const details =
    getSheetsErrorDetails(
      sheetsError
    );


  const isWarning =
    details.type ===
    "warning";


  return `
    <div
      class="sheets-error-banner"
      role="alert"
      style="
        margin-top: 1rem;
        padding: 0.9rem 1rem;
        border-radius: 10px;

        border: 1px solid ${
          isWarning
            ? "rgba(245,158,11,0.35)"
            : "rgba(239,68,68,0.35)"
        };

        background: ${
          isWarning
            ? "rgba(120,53,15,0.10)"
            : "rgba(127,29,29,0.10)"
        };
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
            font-size: 1rem;
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
              color: var(--text-primary);
              margin-bottom: 0.25rem;
            "
          >
            ${escapeHtml(
              details.title
            )}
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
              details.message
            )}
          </div>

        </div>


        <button
          id="btn-dismiss-sheets-error"
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
   MAIN VIEW
   ============================================================ */

export function renderSheetsStep() {

  const {
    spreadsheetUrl,
    spreadsheetTitle,
    worksheets,
    selectedWorksheet,
    schemaInfo,
  } = store.wizard;


  const isConnected =
    Array.isArray(
      worksheets
    ) &&
    worksheets.length > 0;


  return `

    <div class="card">

      <div class="card-header">

        <div>

          <h3 class="card-title">
            ${i18n.t(
              "sheets.title"
            )}
          </h3>


          <p class="card-subtitle">
            ${i18n.t(
              "sheets.subtitle"
            )}
          </p>

        </div>

      </div>


      <div class="form-group">

        <label class="form-label">
          ${i18n.t(
            "sheets.urlLabel"
          )}
        </label>


        <div
          style="
            display: flex;
            gap: 0.75rem;
          "
        >

          <input
            type="text"
            id="sheets-url-input"
            class="form-input"
            placeholder="${i18n.t(
              "sheets.urlPlaceholder"
            )}"
            value="${escapeHtml(
              spreadsheetUrl
            )}"
            style="flex: 1;"
          />


          <button
            id="btn-connect-sheet"
            class="btn btn-primary"
            type="button"
          >
            🔗 ${i18n.t(
              "sheets.connectButton"
            )}
          </button>

        </div>


        ${renderSheetsError()}

      </div>


      ${
        isConnected

          ? `
            <div
              class="card"
              style="
                background:
                  var(--bg-surface-elevated);

                margin-top:
                  1.5rem;
              "
            >

              <div
                style="
                  display:
                    flex;

                  align-items:
                    center;

                  gap:
                    0.75rem;

                  margin-bottom:
                    1rem;
                "
              >

                <span
                  style="
                    font-size:
                      1.5rem;
                  "
                >
                  🟢
                </span>


                <div>

                  <h4
                    style="
                      font-size:
                        1rem;

                      font-weight:
                        700;

                      color:
                        var(--text-primary);

                      margin:
                        0 0 0.2rem;
                    "
                  >
                    ${escapeHtml(
                      spreadsheetTitle
                    )}
                  </h4>


                  <span
                    class="
                      badge
                      badge-success
                    "
                  >
                    ${i18n.t(
                      "sheets.connectedTitle"
                    )}
                  </span>

                </div>

              </div>


              <div
                class="form-group"
                style="
                  margin-bottom:
                    0;
                "
              >

                <label class="form-label">
                  ${i18n.t(
                    "sheets.selectWorksheet"
                  )}
                </label>


                <select
                  id="worksheet-select"
                  class="form-select"
                  style="
                    max-width:
                      360px;
                  "
                >

                  ${worksheets
                    .map(
                      (ws) => `
                        <option
                          value="${escapeHtml(
                            ws
                          )}"
                          ${
                            ws ===
                            selectedWorksheet
                              ? "selected"
                              : ""
                          }
                        >
                          ${escapeHtml(
                            ws
                          )}
                        </option>
                      `
                    )
                    .join("")}

                </select>

              </div>


              ${
                schemaInfo

                  ? `
                    <div
                      style="
                        margin-top:
                          1rem;

                        padding:
                          0.75rem
                          1rem;

                        border-radius:
                          var(--radius-md);

                        background:
                          rgba(
                            5,
                            150,
                            105,
                            0.1
                          );

                        border:
                          1px solid
                          rgba(
                            5,
                            150,
                            105,
                            0.3
                          );

                        font-size:
                          0.875rem;

                        color:
                          #34d399;
                      "
                    >
                      ✓ ${
                        schemaInfo.created_headers
                          ? i18n.t(
                              "sheets.emptySheetNotice"
                            )
                          : i18n.t(
                              "sheets.schemaReady"
                            )
                      }
                    </div>
                  `
                  : ""
              }

            </div>
          `
          : ""
      }

    </div>

  `;
}


/* ============================================================
   LISTENERS
   ============================================================ */

export function attachSheetsStepListeners() {


  /* ----------------------------------------------------------
     CONNECT BUTTON
     ---------------------------------------------------------- */

  const connectBtn =
    document.getElementById(
      "btn-connect-sheet"
    );


  if (connectBtn) {

    connectBtn.addEventListener(
      "click",
      async () => {

        const urlInput =
          document.getElementById(
            "sheets-url-input"
          );


        const url =
          urlInput
            ? urlInput.value.trim()
            : "";


        /* ====================================================
           STEP 1:
           LOCAL URL VALIDATION
           ==================================================== */

        const validation =
          validateSpreadsheetUrl(
            url
          );


        if (
          !validation.valid
        ) {

          sheetsError = {

            title:
              validation.title,

            message:
              validation.message,

            type:
              "warning",

          };


          /*
           * Clear any previously valid destination.
           */
          store.updateWizard({

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

          });


          return;
        }


        /* ====================================================
           STEP 2:
           CLEAR OLD CONNECTION
           ==================================================== */

        sheetsError =
          null;


        store.updateWizard({

          spreadsheetUrl:
            url,

          spreadsheetTitle:
            "",

          worksheets:
            [],

          selectedWorksheet:
            null,

          schemaInfo:
            null,

        });


        /*
         * updateWizard() re-renders the page.
         * Get the button again after the render.
         */

        const currentConnectBtn =
          document.getElementById(
            "btn-connect-sheet"
          );


        if (!currentConnectBtn) {
          return;
        }


        const originalText =
          currentConnectBtn.innerHTML;


        currentConnectBtn.disabled =
          true;


        currentConnectBtn.innerHTML =
          "Connecting...";


        /* ====================================================
           STEP 3:
           BACKEND / GOOGLE VALIDATION
           ==================================================== */

        try {

          const res =
            await ApiClient.connectSheets(
              url
            );


          /*
           * Google connection succeeded.
           */

          const firstSheet =
            Array.isArray(
              res.worksheets
            ) &&
            res.worksheets.length
              ? res.worksheets[0]
              : null;


          let schemaRes =
            null;


          /* ==================================================
             STEP 4:
             ENSURE DESTINATION SCHEMA
             ================================================== */

          if (firstSheet) {

            schemaRes =
              await ApiClient.ensureSheetSchema(

                url,

                firstSheet,

                store.wizard
                  .targetFields

              );

          }


          /* ==================================================
             STEP 5:
             STORE SUCCESSFUL CONNECTION
             ================================================== */

          sheetsError =
            null;


          store.updateWizard({

            spreadsheetUrl:
              url,

            spreadsheetTitle:
              res.title,

            worksheets:
              res.worksheets,

            selectedWorksheet:
              firstSheet,

            schemaInfo:
              schemaRes,

          });


        } catch (error) {

          console.error(
            "Google Sheets connection error:",
            error
          );


          /* -----------------------------------------------
             Failed connection MUST remain disconnected.
             ----------------------------------------------- */

          sheetsError =
            error;


          store.updateWizard({

            spreadsheetTitle:
              "",

            worksheets:
              [],

            selectedWorksheet:
              null,

            schemaInfo:
              null,

          });

        } finally {

          const buttonAfterRequest =
            document.getElementById(
              "btn-connect-sheet"
            );


          if (
            buttonAfterRequest &&
            buttonAfterRequest.isConnected
          ) {

            buttonAfterRequest.disabled =
              false;

            buttonAfterRequest.innerHTML =
              "🔗 " +
              i18n.t(
                "sheets.connectButton"
              );

          }

        }

      }
    );

  }


  /* ----------------------------------------------------------
     URL INPUT
     ---------------------------------------------------------- */

  const urlInput =
    document.getElementById(
      "sheets-url-input"
    );


  if (urlInput) {

    urlInput.addEventListener(
      "change",
      () => {

        const currentUrl =
          urlInput.value.trim();


        /*
         * Don't make a network request here.
         *
         * We only invalidate an existing connection if
         * the user changed the URL.
         */
        if (
          currentUrl !==
          store.wizard.spreadsheetUrl
        ) {

          sheetsError =
            null;


          store.updateWizard({

            spreadsheetUrl:
              currentUrl,

            spreadsheetTitle:
              "",

            worksheets:
              [],

            selectedWorksheet:
              null,

            schemaInfo:
              null,

          });

        }

      }
    );

  }


  /* ----------------------------------------------------------
     WORKSHEET SELECTOR
     ---------------------------------------------------------- */

  const wsSelect =
    document.getElementById(
      "worksheet-select"
    );


  if (wsSelect) {

    wsSelect.addEventListener(
      "change",
      async (event) => {

        const ws =
          event.target.value;


        sheetsError =
          null;


        wsSelect.disabled =
          true;


        try {

          const schemaRes =
            await ApiClient.ensureSheetSchema(

              store.wizard
                .spreadsheetUrl,

              ws,

              store.wizard
                .targetFields

            );


          store.updateWizard({

            selectedWorksheet:
              ws,

            schemaInfo:
              schemaRes,

          });


        } catch (error) {

          console.error(
            "Worksheet schema check error:",
            error
          );


          sheetsError =
            error;


          store.notify();

        } finally {

          if (
            wsSelect &&
            wsSelect.isConnected
          ) {

            wsSelect.disabled =
              false;

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
      "btn-dismiss-sheets-error"
    );


  if (dismissBtn) {

    dismissBtn.addEventListener(
      "click",
      () => {

        sheetsError =
          null;

        store.notify();

      }
    );

  }

}