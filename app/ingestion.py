from pathlib import Path
import pandas as pd

def read_source(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, encoding="utf-8-sig")
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(path)

    raise ValueError(
        f"Unsupported file type: {suffix}. Supported: .csv, .xlsx, .xlsm"
    )
