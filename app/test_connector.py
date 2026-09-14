import pandas as pd

from app.connectors.csv_connector import CSVConnector


connector = CSVConnector(
    "sample_data/destination_test.csv"
)


new_records = pd.DataFrame(
    [
        {
            "Order ID": "TX004",
            "Customer Name": "Priya Shah",
            "Product": "Salted Chips",
            "Quantity": 2,
            "Amount": 240,
            "Date": "2026-09-14",
        }
    ]
)


updated_records = pd.DataFrame()


result = connector.apply_changes(
    new_records=new_records,
    updated_records=updated_records,
)


print(
    "\nDestination:",
    connector.name()
)

print(
    "New written:",
    result["written_new"]
)

print(
    "Updated written:",
    result["written_updated"]
)

print(
    "\n✅ Destination connector test completed."
)