const API_BASE = "/api";


/* ============================================================
   API ERROR
   ============================================================ */

export class ApiError extends Error {
  constructor(
    message,
    {
      status = 0,
      detail = null,
      code = null,
    } = {}
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = code;
  }
}


/* ============================================================
   ERROR HELPERS
   ============================================================ */

async function parseErrorResponse(
  response
) {
  let payload = null;

  try {
    payload = await response.json();
  } catch (error) {
    payload = null;
  }

  const detail =
    payload?.detail ||
    payload?.message ||
    null;

  let message;

  switch (response.status) {

    case 400:
      message =
        detail ||
        "The request could not be processed. Check your input and try again.";
      break;

    case 401:
      message =
        detail ||
        "Authorization is required. Please reconnect your Google account.";
      break;

    case 403:
      message =
        detail ||
        "Access was denied. Make sure your account has permission to use this resource.";
      break;

    case 404:
      message =
        detail ||
        "The requested resource could not be found. It may have expired or been removed.";
      break;

    case 408:
      message =
        detail ||
        "The request timed out. Please try again.";
      break;

    case 429:
      message =
        detail ||
        "The service is temporarily rate-limited. Please wait a moment and try again.";
      break;

    case 500:
      message =
        detail ||
        "BizSync encountered a server-side error. Please try again.";
      break;

    case 502:
    case 503:
    case 504:
      message =
        detail ||
        "BizSync is temporarily unavailable. Check that the server is running and try again.";
      break;

    default:
      message =
        detail ||
        `Request failed with status ${response.status}.`;
      break;
  }

  return new ApiError(
    message,
    {
      status:
        response.status,

      detail,

      code:
        payload?.code ||
        null,
    }
  );
}


async function request(
  url,
  options = {}
) {

  let response;

  try {

    response =
      await fetch(
        url,
        options
      );

  } catch (error) {

    throw new ApiError(
      "BizSync could not reach the server. Make sure the backend is running and try again.",
      {
        status: 0,
        detail:
          error?.message ||
          null,
        code:
          "NETWORK_ERROR",
      }
    );
  }


  if (!response.ok) {
    throw await parseErrorResponse(
      response
    );
  }


  try {
    return await response.json();
  } catch (error) {

    throw new ApiError(
      "BizSync received an invalid response from the server.",
      {
        status:
          response.status,

        detail:
          error?.message ||
          null,

        code:
          "INVALID_RESPONSE",
      }
    );
  }
}


/* ============================================================
   PUBLIC API
   ============================================================ */

export class ApiClient {

  static async getHealth() {

    return request(
      `${API_BASE}/health`
    );

  }


  static async uploadFile(
    file
  ) {

    const formData =
      new FormData();

    formData.append(
      "file",
      file
    );


    return request(
      `${API_BASE}/sync/upload`,
      {
        method: "POST",
        body: formData,
      }
    );

  }


  static async loadSample(
    sampleName
  ) {

    return request(
      `${API_BASE}/sync/samples/${encodeURIComponent(
        sampleName
      )}`
    );

  }


  static async suggestMapping(
    targetFields,
    sourceColumns
  ) {

    return request(
      `${API_BASE}/sync/suggest-mapping`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          target_fields:
            targetFields,

          source_columns:
            sourceColumns,
        }),
      }
    );

  }


  static async listConfigs() {

    return request(
      `${API_BASE}/configs`
    );

  }


  static async saveConfig(
    configData
  ) {

    return request(
      `${API_BASE}/configs`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify(
            configData
          ),
      }
    );

  }


  static async connectSheets(
    spreadsheetUrl
  ) {

    return request(
      `${API_BASE}/sheets/connect`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          spreadsheet_url:
            spreadsheetUrl,
        }),
      }
    );

  }


  static async ensureSheetSchema(
    spreadsheetUrl,
    worksheetName,
    targetFields
  ) {

    return request(
      `${API_BASE}/sheets/ensure-schema`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          spreadsheet_url:
            spreadsheetUrl,

          worksheet_name:
            worksheetName,

          target_fields:
            targetFields,
        }),
      }
    );

  }


  static async getSyncPreview(
    payload
  ) {

    return request(
      `${API_BASE}/sync/preview`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify(
            payload
          ),
      }
    );

  }


  static async executeSync(
    payload
  ) {

    return request(
      `${API_BASE}/sync/execute`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify(
            payload
          ),
      }
    );

  }


  static async getHistory() {

    return request(
      `${API_BASE}/history`
    );

  }


  static async clearHistory() {

    return request(
      `${API_BASE}/history`,
      {
        method: "DELETE",
      }
    );

  }

}