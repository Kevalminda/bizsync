from fastapi import APIRouter, HTTPException

from app.connectors.google_sheets import GoogleSheetsConnector
from app.api.schemas import (
    ConnectSheetsRequest,
    ConnectSheetsResponse,
    EnsureSchemaRequest,
    EnsureSchemaResponse,
)

router = APIRouter(prefix="/api/sheets", tags=["sheets"])


@router.post("/connect", response_model=ConnectSheetsResponse)
def connect_google_sheet(req: ConnectSheetsRequest):
    url = req.spreadsheet_url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Google Sheet URL cannot be empty.")

    try:
        connector = GoogleSheetsConnector(spreadsheet_url=url)
        connector.connect()

        sheet_title = connector.spreadsheet.title if connector.spreadsheet else "Google Sheet"
        worksheets = [ws.title for ws in connector.spreadsheet.worksheets()] if connector.spreadsheet else []

        return ConnectSheetsResponse(
            title=sheet_title,
            worksheets=worksheets,
            connected=True,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials.json missing on backend server.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not connect to Google Sheet: {str(e)}",
        )


@router.post("/ensure-schema", response_model=EnsureSchemaResponse)
def ensure_sheet_schema(req: EnsureSchemaRequest):
    url = req.spreadsheet_url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Google Sheet URL required.")
    if not req.target_fields:
        raise HTTPException(status_code=400, detail="Target fields required.")

    try:
        connector = GoogleSheetsConnector(
            spreadsheet_url=url,
            worksheet_name=req.worksheet_name,
        )
        connector.connect()

        schema_res = connector.ensure_schema(target_fields=req.target_fields)

        return EnsureSchemaResponse(
            created_headers=schema_res.get("created_headers", False),
            added_columns=schema_res.get("added_columns", []),
            matches=schema_res.get("matches", []),
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Schema validation error: {str(e)}",
        )
