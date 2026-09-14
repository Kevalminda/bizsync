from fastapi import APIRouter

from app.audit_log import load_history, clear_history
from app.api.schemas import SyncHistoryEventResponse

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[SyncHistoryEventResponse])
def get_sync_history():
    raw_history = load_history()
    events = []
    for item in raw_history:
        events.append(
            SyncHistoryEventResponse(
                timestamp=item.get("timestamp", ""),
                configuration=item.get("configuration"),
                incoming_file=item.get("incoming_file", ""),
                existing_file=item.get("existing_file"),
                new=int(item.get("new", 0)),
                updated=int(item.get("updated", 0)),
                unchanged=int(item.get("unchanged", 0)),
                skipped=int(item.get("skipped", 0)),
                errors=int(item.get("errors", 0)),
            )
        )
    return events


@router.delete("")
def delete_sync_history():
    clear_history()
    return {"message": "Sync history cleared successfully."}
