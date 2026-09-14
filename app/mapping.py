import pandas as pd
from .models import MappingConfig

def apply_mapping(df: pd.DataFrame, config: MappingConfig) -> pd.DataFrame:
    missing = [s for s in config.source_to_target if s not in df.columns]
    if missing:
        raise ValueError("Source columns missing: " + ", ".join(missing))

    result = pd.DataFrame(index=df.index)
    for source, target in config.source_to_target.items():
        result[target] = df[source]
    return result.reset_index(drop=True)
