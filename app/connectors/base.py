from abc import ABC, abstractmethod

import pandas as pd


class DestinationConnector(ABC):
    """
    Base interface for all BizSync destinations.
    """

    @abstractmethod
    def read_existing(
        self,
    ) -> pd.DataFrame:
        """
        Read existing records from the destination.
        """
        raise NotImplementedError

    @abstractmethod
    def apply_changes(
        self,
        new_records: pd.DataFrame,
        updated_records: pd.DataFrame,
    ) -> dict:
        """
        Apply new and updated records to the destination.
        """
        raise NotImplementedError

    @abstractmethod
    def name(
        self,
    ) -> str:
        """
        Human-readable destination name.
        """
        raise NotImplementedError