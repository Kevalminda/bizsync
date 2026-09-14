import { i18n } from "../i18n.js";
import { store } from "../state.js";
import { ApiClient } from "../api.js";

let uploadError = null;


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


function getUploadErrorDetails(error) {
  const message = String(
    error?.message ||
    error ||
    "The file could not be processed."
  );

  const lower = message.toLowerCase();

  if (
    error?.code === "NETWORK_ERROR" ||
    lower.includes("could not reach the server")
  ) {
    return {
      title: "Backend unavailable",
      message:
        "BizSync could not reach the server. Make sure the FastAPI server is running and try again.",
      type: "error",
    };
  }

  if (
    error?.status === 400 ||
    lower.includes("unsupported") ||
    lower.includes("could not process") ||
    lower.includes("file format")
  ) {
    return {
      title: "File could not be processed",
      message: message,
      type: "warning",
    };
  }

  if (error?.status === 404) {
    return {
      title: "Sample dataset unavailable",
      message:
        "The selected demo dataset could not be found on the server.",
      type: "warning",
    };
  }

  return {
    title: "Upload failed",
    message: message,
    type: "error",
  };
}


/* ============================================================
   ERROR UI
   ============================================================ */

function renderUploadError() {
  if (!uploadError) {
    return "";
  }

  const details =
    getUploadErrorDetails(
      uploadError
    );

  const isWarning =
    details.type === "warning";

  return `
    <div
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

        <div>
          ${isWarning ? "⚠️" : "✕"}
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
          id="btn-dismiss-upload-error"
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
   RENDER
   ============================================================ */

export function renderUploadStep() {

  const fileLoaded =
    Boolean(
      store.wizard.fileId
    );


  return `
    <div class="card">

      <div class="card-header">

        <div>

          <h3 class="card-title">
            ${i18n.t("upload.title")}
          </h3>

          <p class="card-subtitle">
            ${i18n.t("upload.subtitle")}
          </p>

        </div>

      </div>


      <div
        id="dropzone"
        class="
          dropzone
          ${
            fileLoaded
              ? "dropzone-loaded"
              : ""
          }
        "
      >

        <div class="dropzone-icon">
          ${
            fileLoaded
              ? "📄"
              : "⬆️"
          }
        </div>

        <div class="dropzone-text">

          ${
            fileLoaded
              ? escapeHtml(
                  store.wizard.filename
                )
              : i18n.t(
                  "upload.dropzoneText"
                )
          }

        </div>

        <div class="dropzone-hint">
          ${i18n.t(
            "upload.supportedFormats"
          )}
        </div>

        <input
          type="file"
          id="file-input"
          accept=".csv,.xlsx,.xlsm"
          style="display: none;"
        />

      </div>


      <!-- Error -->
      ${renderUploadError()}


      <!-- ==================================================== -->
      <!-- DEMO DATA                                             -->
      <!-- ==================================================== -->

      <div
        style="
          margin-top: 1rem;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          flex-wrap: wrap;
        "
      >

        <span
          style="
            font-size: 0.825rem;
            color: var(--text-muted);
          "
        >
          Quick Test Data:
        </span>


        <button
          id="btn-sample-flipkart"
          class="btn btn-secondary btn-sm"
          type="button"
        >
          📦 Flipkart Sample CSV
        </button>


        <button
          id="btn-sample-generic"
          class="btn btn-secondary btn-sm"
          type="button"
        >
          📊 Generic Business Sample CSV
        </button>

      </div>


      <!-- ==================================================== -->
      <!-- FILE STATUS                                           -->
      <!-- ==================================================== -->

      <div
        id="upload-status-area"
        style="
          margin-top: 1.5rem;
        "
      >

        ${
          fileLoaded

            ? `
              <div
                class="stats-grid"
                style="
                  margin-bottom: 1.5rem;
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
                    📊
                  </div>

                  <div class="stat-content">

                    <span class="stat-value">
                      ${store.wizard.totalRows}
                    </span>

                    <span class="stat-label">
                      ${i18n.t(
                        "upload.totalRows"
                      )}
                    </span>

                  </div>

                </div>


                <div class="stat-card">

                  <div
                    class="stat-icon"
                    style="
                      background:
                        var(--accent-sky-bg);
                      color:
                        #38bdf8;
                    "
                  >
                    📑
                  </div>

                  <div class="stat-content">

                    <span class="stat-value">
                      ${
                        store.wizard
                          .sourceColumns
                          .length
                      }
                    </span>

                    <span class="stat-label">
                      ${i18n.t(
                        "upload.columnsFound"
                      )}
                    </span>

                  </div>

                </div>

              </div>


              <!-- ============================================ -->
              <!-- PREVIEW                                       -->
              <!-- ============================================ -->

              <div
                class="card"
                style="
                  background:
                    var(--bg-surface-elevated);
                  margin-bottom:
                    0;
                "
              >

                <h4
                  style="
                    font-size:
                      0.95rem;

                    font-weight:
                      600;

                    margin-bottom:
                      1rem;

                    color:
                      var(--text-primary);
                  "
                >
                  ${i18n.t(
                    "upload.samplePreview"
                  )}
                </h4>


                <div
                  class="table-container"
                >

                  <table
                    class="data-table"
                  >

                    <thead>

                      <tr>

                        ${store.wizard
                          .sourceColumns
                          .map(
                            (column) =>
                              `
                                <th>
                                  ${escapeHtml(
                                    column
                                  )}
                                </th>
                              `
                          )
                          .join("")}

                      </tr>

                    </thead>


                    <tbody>

                      ${store.wizard
                        .previewData
                        .map(
                          (row) =>
                            `
                              <tr>

                                ${store.wizard
                                  .sourceColumns
                                  .map(
                                    (
                                      column
                                    ) =>
                                      `
                                        <td>
                                          ${escapeHtml(
                                            row[
                                              column
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

                </div>

              </div>
            `

            : ""
        }

      </div>

    </div>
  `;
}


/* ============================================================
   LISTENERS
   ============================================================ */

export function attachUploadStepListeners(
  onSuccess
) {

  const dropzone =
    document.getElementById(
      "dropzone"
    );

  const fileInput =
    document.getElementById(
      "file-input"
    );


  /* ----------------------------------------------------------
     DROPZONE
     ---------------------------------------------------------- */

  if (
    dropzone &&
    fileInput
  ) {

    dropzone.addEventListener(
      "click",
      () => {
        fileInput.click();
      }
    );


    dropzone.addEventListener(
      "dragover",
      (event) => {

        event.preventDefault();

        dropzone.classList.add(
          "dragover"
        );

      }
    );


    dropzone.addEventListener(
      "dragleave",
      () => {

        dropzone.classList.remove(
          "dragover"
        );

      }
    );


    dropzone.addEventListener(
      "drop",
      (event) => {

        event.preventDefault();

        dropzone.classList.remove(
          "dragover"
        );


        if (
          event.dataTransfer.files &&
          event.dataTransfer.files[0]
        ) {

          handleFileUpload(
            event.dataTransfer.files[0],
            onSuccess
          );

        }

      }
    );


    fileInput.addEventListener(
      "change",
      (event) => {

        if (
          event.target.files &&
          event.target.files[0]
        ) {

          handleFileUpload(
            event.target.files[0],
            onSuccess
          );

        }

      }
    );

  }


  /* ----------------------------------------------------------
     FLIPKART SAMPLE
     ---------------------------------------------------------- */

  const sampleFlipkartBtn =
    document.getElementById(
      "btn-sample-flipkart"
    );


  if (sampleFlipkartBtn) {

    sampleFlipkartBtn.addEventListener(
      "click",
      async (event) => {

        event.stopPropagation();

        uploadError = null;

        sampleFlipkartBtn.disabled =
          true;

        const originalText =
          sampleFlipkartBtn.innerHTML;

        sampleFlipkartBtn.innerHTML =
          "Loading...";


        try {

          const res =
            await ApiClient.loadSample(
              "flipkart"
            );


          store.updateWizard({

            fileId:
              res.file_id,

            filename:
              res.filename,

            totalRows:
              res.total_rows,

            sourceColumns:
              res.source_columns,

            previewData:
              res.preview_data,

          });


          uploadError =
            null;


          if (onSuccess) {
            onSuccess();
          }


        } catch (error) {

          console.error(
            "Could not load Flipkart sample:",
            error
          );

          uploadError =
            error;

          store.notify();


        } finally {

          const button =
            document.getElementById(
              "btn-sample-flipkart"
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
     GENERIC SAMPLE
     ---------------------------------------------------------- */

  const sampleGenericBtn =
    document.getElementById(
      "btn-sample-generic"
    );


  if (sampleGenericBtn) {

    sampleGenericBtn.addEventListener(
      "click",
      async (event) => {

        event.stopPropagation();

        uploadError = null;

        sampleGenericBtn.disabled =
          true;

        const originalText =
          sampleGenericBtn.innerHTML;

        sampleGenericBtn.innerHTML =
          "Loading...";


        try {

          const res =
            await ApiClient.loadSample(
              "generic"
            );


          store.updateWizard({

            fileId:
              res.file_id,

            filename:
              res.filename,

            totalRows:
              res.total_rows,

            sourceColumns:
              res.source_columns,

            previewData:
              res.preview_data,

          });


          uploadError =
            null;


          if (onSuccess) {
            onSuccess();
          }


        } catch (error) {

          console.error(
            "Could not load generic sample:",
            error
          );

          uploadError =
            error;

          store.notify();


        } finally {

          const button =
            document.getElementById(
              "btn-sample-generic"
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
      "btn-dismiss-upload-error"
    );


  if (dismissBtn) {

    dismissBtn.addEventListener(
      "click",
      () => {

        uploadError =
          null;

        store.notify();

      }
    );

  }

}


/* ============================================================
   FILE UPLOAD
   ============================================================ */

async function handleFileUpload(
  file,
  onSuccess
) {

  uploadError =
    null;


  try {

    const res =
      await ApiClient.uploadFile(
        file
      );


    store.updateWizard({

      fileId:
        res.file_id,

      filename:
        res.filename,

      totalRows:
        res.total_rows,

      sourceColumns:
        res.source_columns,

      previewData:
        res.preview_data,

    });


    uploadError =
      null;


    if (onSuccess) {
      onSuccess();
    }


  } catch (error) {

    console.error(
      "File upload failed:",
      error
    );


    uploadError =
      error;

    store.notify();

  }

}