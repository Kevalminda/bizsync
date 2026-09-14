import unittest
from fastapi.testclient import TestClient
from app.api.main import app

class TestFastAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["engine"], "BizSync Core")

    def test_list_configs(self):
        response = self.client.get("/api/configs")
        self.assertEqual(response.status_code, 200)
        configs = response.json()
        self.assertIsInstance(configs, list)

    def test_suggest_mapping(self):
        payload = {
            "target_fields": ["Order No.", "Product Name", "Quantity", "Date"],
            "source_columns": ["order_id", "product", "qty", "ordered_on"]
        }
        response = self.client.post("/api/sync/suggest-mapping", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggestions", data)
        self.assertIn("Order No.", data["suggestions"])

    def test_load_sample_file(self):
        response = self.client.get("/api/sync/samples/generic")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_rows"], 3)
        self.assertEqual(len(data["source_columns"]), 5)
        self.assertIn("order_number", data["source_columns"])

if __name__ == "__main__":
    unittest.main()
