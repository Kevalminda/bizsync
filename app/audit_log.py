"""
BizSync - Audit Log

Stores a lightweight local history of synchronization runs.

Later this can be replaced with a database-backed audit system.
"""

from datetime import datetime
from pathlib import Path
import json


# ============================================================
# STORAGE
# ============================================================

LOG_DIR = Path("logs")

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

LOG_FILE = LOG_DIR / "sync_history.json"


# ============================================================
# LOAD HISTORY
# ============================================================

def load_history() -> list[dict]:
    """
    Load all stored synchronization records.
    """

    if not LOG_FILE.exists():
        return []

    try:

        with LOG_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return []


# ============================================================
# SAVE HISTORY
# ============================================================

def save_history(
    history: list[dict],
) -> None:
    """
    Persist the full synchronization history.
    """

    with LOG_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            history,
            file,
            indent=2,
        )


# ============================================================
# ADD SYNC EVENT
# ============================================================

def add_sync_event(
    *,
    configuration: str | None,
    incoming_file: str,
    existing_file: str | None,
    new_count: int,
    updated_count: int,
    unchanged_count: int,
    skipped_count: int,
    error_count: int,
) -> dict:
    """
    Add one synchronization event to history.
    """

    event = {

        "timestamp":
            datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),

        "configuration":
            configuration,

        "incoming_file":
            incoming_file,

        "existing_file":
            existing_file,

        "new":
            new_count,

        "updated":
            updated_count,

        "unchanged":
            unchanged_count,

        "skipped":
            skipped_count,

        "errors":
            error_count,
    }

    history = load_history()

    history.insert(
        0,
        event,
    )

    save_history(
        history
    )

    return event


# ============================================================
# CLEAR HISTORY
# ============================================================

def clear_history() -> None:
    """
    Delete all stored synchronization history.
    """

    if LOG_FILE.exists():

        LOG_FILE.unlink()