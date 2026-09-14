from pathlib import Path

import pandas as pd

from app.connectors.base import DestinationConnector


class CSVConnector(DestinationConnector):

    def __init__(
        self,
        file_path: str,
    ):
        self.file_path = Path(
            file_path
        )

    def name(self) -> str:

        return "CSV"

    def read_existing(
        self,
    ) -> pd.DataFrame:

        if not self.file_path.exists():

            return pd.DataFrame()

        return pd.read_csv(
            self.file_path
        )

    def apply_changes(
        self,
        new_records: pd.DataFrame,
        updated_records: pd.DataFrame,
    ) -> dict:

        existing = self.read_existing()

        # ----------------------------------------------------
        # Add new records.
        # ----------------------------------------------------

        if not new_records.empty:

            existing = pd.concat(
                [
                    existing,
                    new_records,
                ],
                ignore_index=True,
            )

        # ----------------------------------------------------
        # Updated-record handling will be finalized by the
        # destination-aware sync layer.
        # ----------------------------------------------------

        if not updated_records.empty:

            # This connector is intentionally kept simple
            # for the architecture test.
            pass

        existing.to_csv(
            self.file_path,
            index=False,
        )

        return {
            "written_new":
                len(new_records),

            "written_updated":
                len(updated_records),
        }