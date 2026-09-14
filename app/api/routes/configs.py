import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    SaveConfigRequest,
    ConfigItemResponse,
)

router = APIRouter(prefix="/api/configs", tags=["configs"])

CONFIG_DIR = Path("configs")
SAVED_CONFIG_DIR = CONFIG_DIR / "saved"
SAVED_CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_name(name: str) -> str:
    safe = "".join(c if (c.isalnum() or c in ("-", "_", " ")) else "_" for c in name)
    return "_".join(safe.split()).strip("_")


@router.get("", response_model=list[ConfigItemResponse])
def list_configurations():
    configs = []

    # Read base configs and saved configs
    for folder in [CONFIG_DIR, SAVED_CONFIG_DIR]:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                configs.append(
                    ConfigItemResponse(
                        name=data.get("name", path.stem),
                        filename=path.name,
                        config=data,
                    )
                )
            except Exception:
                continue

    return configs


@router.post("", response_model=ConfigItemResponse)
def save_configuration(req: SaveConfigRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Configuration name cannot be empty.")

    safe_filename = _sanitize_name(req.name)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid configuration name.")

    config_data = {
        "name": req.name.strip(),
        "target_fields": req.target_fields,
        "required_fields": req.required_fields,
        "unique_key_fields": req.unique_key_fields,
        "mapping": req.mapping,
    }

    target_path = SAVED_CONFIG_DIR / f"{safe_filename}.json"

    try:
        with target_path.open("w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        return ConfigItemResponse(
            name=req.name.strip(),
            filename=target_path.name,
            config=config_data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save configuration: {str(e)}",
        )
