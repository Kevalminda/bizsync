import unittest

import pandas as pd

from app.ai.duplicate_detector import (
    compare_records,
    detect_duplicates,
)


class DuplicateDetectorTest(unittest.TestCase):

    def test_exact_duplicate(self):
        incoming = pd.Series(
            {
                "customer_name": "Rahul Sharma",
                "product": "Premium Chips",
                "quantity": 3,
                "amount": 360,
            }
        )

        existing = pd.Series(
            {
                "customer_name": "Rahul Sharma",
                "product": "Premium Chips",
                "quantity": 3,
                "amount": 360,
            }
        )

        result = compare_records(
            incoming,
            existing,
        )

        self.assertEqual(
            result["status"],
            "EXACT_DUPLICATE",
        )

        self.assertGreaterEqual(
            result["score"],
            0.98,
        )


    def test_possible_duplicate(self):
        incoming = pd.Series(
            {
                "customer_name": "Rahul S.",
                "product": "Premium Chips - 500 GM",
                "quantity": 3,
            }
        )

        existing = pd.Series(
            {
                "customer_name": "Rahul Sharma",
                "product": "Premium Chips 500g",
                "quantity": 3,
            }
        )

        result = compare_records(
            incoming,
            existing,
        )

        self.assertEqual(
            result["status"],
            "POSSIBLE_DUPLICATE",
        )

        self.assertGreater(
            result["score"],
            0.72,
        )


    def test_probably_new(self):
        incoming_df = pd.DataFrame(
            [
                {
                    "customer_name": "Aman Jain",
                    "product": "Cheese Chips",
                    "quantity": 1,
                }
            ]
        )

        existing_df = pd.DataFrame(
            [
                {
                    "customer_name": "Rahul Sharma",
                    "product": "Premium Chips",
                    "quantity": 3,
                }
            ]
        )

        results = detect_duplicates(
            incoming_df,
            existing_df,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["status"],
            "PROBABLY_NEW",
        )


if __name__ == "__main__":
    unittest.main()