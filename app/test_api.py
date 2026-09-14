import unittest

from fastapi.testclient import TestClient

from app.api.main import app


class TestFastAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "BizSync")
        self.assertEqual(data["version"], "1.0.0")

        self.assertIn("google_credentials_present", data)
        self.assertIn("google_authorized_user_present", data)

    def test_list_configs(self):
        response = self.client.get("/api/configs")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_suggest_mapping(self):
        payload = {
            "target_fields": [
                "Order No.",
                "Product Name",
                "Quantity",
            ],
            "source_columns": [
                "order_id",
                "product",
                "quantity",
            ],
        }

        response = self.client.post(
            "/api/sync/suggest-mapping",
            json=payload,
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertIn("suggestions", data)
        self.assertIsInstance(data["suggestions"], dict)

    def test_load_sample_file(self):
        response = self.client.get(
            "/api/sync/samples/flipkart"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertIn("file_id", data)
        self.assertIn("filename", data)
        self.assertIn("total_rows", data)
        self.assertIn("source_columns", data)
        self.assertIn("preview_data", data)

        self.assertEqual(
            data["filename"],
            "flipkart_sample.csv",
        )


if __name__ == "__main__":
    unittest.main()