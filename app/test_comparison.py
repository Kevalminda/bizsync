import pandas as pd

from app.sync_engine import (
    sync_dataframes,
    summarize_sync_result,
)


# ============================================================
# EXISTING DATA
# ============================================================

existing = pd.DataFrame([
    {
        "Order ID": "TX001",
        "Customer Name": "Rahul Sharma",
        "Product": "Premium Chips",
        "Quantity": 3,
        "Amount": 360,
        "Date": "2026-09-12",
    },
    {
        "Order ID": "TX002",
        "Customer Name": "Neha Verma",
        "Product": "Masala Chips",
        "Quantity": 3,
        "Amount": 360,
        "Date": "2026-09-12",
    },
    {
        "Order ID": "TX003",
        "Customer Name": "Aman Jain",
        "Product": "Cheese Chips",
        "Quantity": 1,
        "Amount": 120,
        "Date": "2026-09-13",
    },
])


# ============================================================
# INCOMING DATA
# ============================================================

incoming = pd.DataFrame([
    {
        # Same as TX001, but different formatting
        "Order ID": " tx001 ",
        "Customer Name": "RAHUL SHARMA",
        "Product": "Premium Chips",
        "Quantity": "3.0",
        "Amount": "360.00",
        "Date": "12/09/2026",
    },
    {
        # Actually changed
        "Order ID": "TX002",
        "Customer Name": "Neha Verma",
        "Product": "Masala Chips",
        "Quantity": "4",
        "Amount": "480",
        "Date": "2026-09-12",
    },
    {
        # Same as TX003
        "Order ID": "TX003",
        "Customer Name": "Aman Jain",
        "Product": "Cheese Chips",
        "Quantity": 1,
        "Amount": 120,
        "Date": "2026-09-13",
    },
    {
        # Completely new
        "Order ID": "TX004",
        "Customer Name": "Priya Shah",
        "Product": "Salted Chips",
        "Quantity": 2,
        "Amount": 240,
        "Date": "2026-09-14",
    },
])


# ============================================================
# RUN SYNC ENGINE
# ============================================================

result = sync_dataframes(
    incoming_df=incoming,
    existing_df=existing,
    unique_key_fields=["Order ID"],
)


summary = summarize_sync_result(result)


# ============================================================
# DISPLAY RESULT
# ============================================================

print()
print("=" * 60)
print("BIZSYNC - COMPARISON ENGINE TEST")
print("=" * 60)

print()
print("New:        ", summary["new"])
print("Updated:    ", summary["updated"])
print("Unchanged:  ", summary["unchanged"])
print("Skipped:    ", summary["skipped"])
print("Errors:     ", summary["errors"])


print()
print("NEW RECORDS")
print("-" * 60)

if result["new_records"].empty:
    print("None")
else:
    print(
        result["new_records"].to_string(
            index=False
        )
    )


print()
print("UPDATED RECORDS")
print("-" * 60)

if result["updated_records"].empty:
    print("None")
else:
    print(
        result["updated_records"].to_string(
            index=False
        )
    )


print()
print("UNCHANGED RECORDS")
print("-" * 60)

if result["unchanged_records"].empty:
    print("None")
else:
    print(
        result["unchanged_records"].to_string(
            index=False
        )
    )


print()
print("SKIPPED RECORDS")
print("-" * 60)

if result["skipped_records"].empty:
    print("None")
else:
    print(
        result["skipped_records"].to_string(
            index=False
        )
    )


print()
print("ERRORS")
print("-" * 60)

if result["errors"]:
    for error in result["errors"]:
        print("-", error)
else:
    print("None")


# ============================================================
# AUTOMATIC TEST CHECK
# ============================================================

assert summary["new"] == 1
assert summary["updated"] == 1
assert summary["unchanged"] == 2
assert summary["skipped"] == 0


print()
print("=" * 60)
print("✅ COMPARISON ENGINE TEST PASSED")
print("=" * 60)