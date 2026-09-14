import { i18n } from "../i18n.js";
import { store } from "../state.js";


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


function getGoogleStatus() {
  const connected =
    Boolean(
      store.health &&
      store.health.google_credentials_present
    );

  return connected
    ? {
        connected: true,
        label: "Connected",
        className: "badge-success",
        icon: "🟢",
      }
    : {
        connected: false,
        label: "Not Connected",
        className: "badge-warning",
        icon: "⚠️",
      };
}


/* ============================================================
   MAIN SETTINGS VIEW
   ============================================================ */

export function renderSettingsView() {

  const google =
    getGoogleStatus();


  return `

    <!-- ====================================================== -->
    <!-- SETTINGS HEADER                                        -->
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

      <div>

        <div
          style="
            color:
              #818cf8;

            font-size:
              0.72rem;

            font-weight:
              700;

            text-transform:
              uppercase;

            letter-spacing:
              0.06em;

            margin-bottom:
              0.35rem;
          "
        >
          Preferences & System
        </div>


        <h2
          style="
            margin:
              0 0 0.35rem;

            font-size:
              1.45rem;

            font-weight:
              750;
          "
        >
          ${i18n.t(
            "settings.title"
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
            "settings.subtitle"
          )}
        </p>

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- GOOGLE SHEETS                                          -->
    <!-- ====================================================== -->

    <div class="card">

      <div class="card-header">

        <div>

          <h3 class="card-title">
            ${i18n.t(
              "settings.oauthHeader"
            )}
          </h3>

          <p class="card-subtitle">
            Google Sheets connection status
          </p>

        </div>


        <span
          class="
            badge
            ${google.className}
          "
          style="
            padding:
              0.55rem
              0.75rem;
          "
        >
          ${google.icon}
          ${google.label}
        </span>

      </div>


      <div
        style="
          display:
            flex;

          flex-direction:
            column;

          gap:
            0.85rem;
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

            padding:
              0.9rem 1rem;

            border:
              1px solid
              var(--border);

            border-radius:
              10px;
          "
        >

          <div>

            <div
              style="
                font-weight:
                  650;

                margin-bottom:
                  0.2rem;
              "
            >
              Google OAuth
            </div>

            <div
              style="
                color:
                  var(--text-muted);

                font-size:
                  0.76rem;
              "
            >
              ${google.connected
                ? "BizSync can access your authorized Google Sheets."
                : "Connect Google OAuth before using Google Sheets sync."
              }
            </div>

          </div>


          <span
            class="
              badge
              ${
                google.connected
                  ? "badge-success"
                  : "badge-warning"
              }
            "
          >
            ${
              google.connected
                ? "Ready"
                : "Action Needed"
            }
          </span>

        </div>


        <p
          class="form-help"
          style="
            margin:
              0;
          "
        >
          ${i18n.t(
            "settings.oauthGuide"
          )}
        </p>


        <div
          style="
            padding:
              0.75rem
              0.9rem;

            border-radius:
              8px;

            background:
              rgba(
                99,
                102,
                241,
                0.06
              );

            border:
              1px solid
              rgba(
                99,
                102,
                241,
                0.18
              );

            color:
              var(--text-muted);

            font-size:
              0.76rem;

            line-height:
              1.45;
          "
        >
          🔐 BizSync keeps the Google connection
          separate from your synchronization configuration.
          Your spreadsheet URL is supplied per sync.
        </div>

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- AI MAPPING                                            -->
    <!-- ====================================================== -->

    <div
      class="card"
      style="
        margin-top:
          1.25rem;
      "
    >

      <div class="card-header">

        <div>

          <h3 class="card-title">
            AI Mapping
          </h3>

          <p class="card-subtitle">
            Gemini is used only when local mapping confidence
            is insufficient.
          </p>

        </div>


        <span
          class="
            badge
            badge-success
          "
        >
          🤖 Enabled
        </span>

      </div>


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

        <div
          style="
            padding:
              0.9rem;

            border:
              1px solid
              var(--border);

            border-radius:
              10px;
          "
        >

          <div
            style="
              font-size:
                0.72rem;

              color:
                var(--text-muted);

              margin-bottom:
                0.25rem;
            "
          >
            Mapping Engine
          </div>

          <strong>
            Hybrid
          </strong>

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.73rem;

              margin-top:
                0.25rem;
            "
          >
            Local + AI fallback
          </div>

        </div>


        <div
          style="
            padding:
              0.9rem;

            border:
              1px solid
              var(--border);

            border-radius:
              10px;
          "
        >

          <div
            style="
              font-size:
                0.72rem;

              color:
                var(--text-muted);

              margin-bottom:
                0.25rem;
            "
          >
            AI Model
          </div>

          <strong>
            Gemini
          </strong>

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.73rem;

              margin-top:
                0.25rem;
            "
          >
            gemini-3.6-flash
          </div>

        </div>


        <div
          style="
            padding:
              0.9rem;

            border:
              1px solid
              var(--border);

            border-radius:
              10px;
          "
        >

          <div
            style="
              font-size:
                0.72rem;

              color:
                var(--text-muted);

              margin-bottom:
                0.25rem;
            "
          >
            Safety
          </div>

          <strong>
            Confidence Based
          </strong>

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.73rem;

              margin-top:
                0.25rem;
            "
          >
            Review before uncertain mappings
          </div>

        </div>

      </div>


      <div
        style="
          margin-top:
            0.9rem;

          padding:
            0.8rem
            0.9rem;

          border-radius:
            8px;

          background:
            rgba(
              16,
              185,
              129,
              0.05
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
            0.76rem;

          line-height:
            1.45;
        "
      >
        💡 High-confidence local mappings avoid unnecessary AI
        calls. Ambiguous mappings can be sent to Gemini for
        semantic interpretation.
      </div>

    </div>


    <!-- ====================================================== -->
    <!-- SYNC SAFETY                                           -->
    <!-- ====================================================== -->

    <div
      class="card"
      style="
        margin-top:
          1.25rem;
      "
    >

      <div class="card-header">

        <div>

          <h3 class="card-title">
            Sync Safety
          </h3>

          <p class="card-subtitle">
            Protection mechanisms used during synchronization.
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
            0.65rem;
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

            padding:
              0.75rem
              0.9rem;

            border:
              1px solid
              var(--border);

            border-radius:
              9px;
          "
        >

          <span>
            Unique-key protection
          </span>

          <span
            class="badge badge-success"
          >
            ON
          </span>

        </div>


        <div
          style="
            display:
              flex;

            align-items:
              center;

            justify-content:
              space-between;

            padding:
              0.75rem
              0.9rem;

            border:
              1px solid
              var(--border);

            border-radius:
              9px;
          "
        >

          <span>
            Duplicate intelligence
          </span>

          <span
            class="badge badge-success"
          >
            ON
          </span>

        </div>


        <div
          style="
            display:
              flex;

            align-items:
              center;

            justify-content:
              space-between;

            padding:
              0.75rem
              0.9rem;

            border:
              1px solid
              var(--border);

            border-radius:
              9px;
          "
        >

          <span>
            AI duplicate verification
          </span>

          <span
            class="badge badge-success"
          >
            ON
          </span>

        </div>


        <div
          style="
            display:
              flex;

            align-items:
              center;

            justify-content:
              space-between;

            padding:
              0.75rem
              0.9rem;

            border:
              1px solid
              var(--border);

            border-radius:
              9px;
          "
        >

          <span>
            Audit history
          </span>

          <span
            class="badge badge-success"
          >
            ON
          </span>

        </div>

      </div>


      <div
        style="
          margin-top:
            0.9rem;

          color:
            var(--text-muted);

          font-size:
            0.76rem;

          line-height:
            1.45;
        "
      >
        BizSync will not blindly insert records with missing
        unique-key values, helping prevent duplicate or
        untraceable destination records.
      </div>

    </div>


    <!-- ====================================================== -->
    <!-- LANGUAGE                                              -->
    <!-- ====================================================== -->

    <div
      class="card"
      style="
        margin-top:
          1.25rem;
      "
    >

      <div class="card-header">

        <div>

          <h3 class="card-title">
            ${i18n.t(
              "settings.languageHeader"
            )}
          </h3>

          <p class="card-subtitle">
            Choose the BizSync interface language.
          </p>

        </div>

      </div>


      <div
        style="
          display:
            flex;

          gap:
            0.75rem;

          flex-wrap:
            wrap;
        "
      >

        <button
          id="btn-lang-en"
          class="
            btn
            ${
              i18n.lang === "en"
                ? "btn-primary"
                : "btn-secondary"
            }
          "
        >
          🇬🇧 English (EN)
        </button>


        <button
          id="btn-lang-hi"
          class="
            btn
            ${
              i18n.lang === "hi"
                ? "btn-primary"
                : "btn-secondary"
            }
          "
        >
          🇮🇳 हिन्दी (HI)
        </button>

      </div>

    </div>


    <!-- ====================================================== -->
    <!-- SUPPORTED FILES / ABOUT                                -->
    <!-- ====================================================== -->

    <div
      class="card"
      style="
        margin-top:
          1.25rem;
      "
    >

      <div class="card-header">

        <div>

          <h3 class="card-title">
            About BizSync
          </h3>

          <p class="card-subtitle">
            Current capabilities of this build.
          </p>

        </div>

      </div>


      <div
        style="
          display:
            grid;

          grid-template-columns:
            repeat(
              2,
              minmax(
                0,
                1fr
              )
            );

          gap:
            0.75rem;
        "
      >

        <div>

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.72rem;

              margin-bottom:
                0.25rem;
            "
          >
            Supported input
          </div>

          <strong>
            CSV · XLSX · XLSM
          </strong>

        </div>


        <div>

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.72rem;

              margin-bottom:
                0.25rem;
            "
          >
            Destination
          </div>

          <strong>
            Google Sheets
          </strong>

        </div>


        <div>

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.72rem;

              margin-bottom:
                0.25rem;
            "
          >
            Mapping
          </div>

          <strong>
            Automatic + AI-assisted
          </strong>

        </div>


        <div>

          <div
            style="
              color:
                var(--text-muted);

              font-size:
                0.72rem;

              margin-bottom:
                0.25rem;
            "
          >
            Interface
          </div>

          <strong>
            English + Hindi
          </strong>

        </div>

      </div>


      <div
        style="
          margin-top:
            1rem;

          padding-top:
            0.9rem;

          border-top:
            1px solid
            var(--border);

          color:
            var(--text-muted);

          font-size:
            0.74rem;
        "
      >
        BizSync · Business Data Synchronization Engine
      </div>

    </div>

  `;
}


/* ============================================================
   LISTENERS
   ============================================================ */

export function attachSettingsListeners() {

  const enBtn =
    document.getElementById(
      "btn-lang-en"
    );

  const hiBtn =
    document.getElementById(
      "btn-lang-hi"
    );


  if (enBtn) {

    enBtn.addEventListener(
      "click",
      () => {

        i18n.setLanguage(
          "en"
        );

      }
    );
  }


  if (hiBtn) {

    hiBtn.addEventListener(
      "click",
      () => {

        i18n.setLanguage(
          "hi"
        );

      }
    );
  }

}