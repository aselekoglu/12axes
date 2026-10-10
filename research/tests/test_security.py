"""No externally exposed credentials or real participant data."""
import unittest
from fastapi.testclient import TestClient

from research.security import SlidingWindowLimiter
from research.service import app


class SecurityTests(unittest.TestCase):
    def test_sliding_window_and_peer_separation(self):
        limiter = SlidingWindowLimiter(max_keys=2)
        self.assertTrue(limiter.allow("one", limit=2, window=60, now=100))
        self.assertTrue(limiter.allow("one", limit=2, window=60, now=101))
        self.assertFalse(limiter.allow("one", limit=2, window=60, now=102))
        self.assertTrue(limiter.allow("two", limit=2, window=60, now=102))
        self.assertFalse(limiter.allow("three", limit=2, window=60, now=103))
        self.assertTrue(limiter.allow("one", limit=2, window=60, now=165))

    def test_safe_response_headers(self):
        response = TestClient(app).get("/research-api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertEqual(response.headers.get("Referrer-Policy"), "no-referrer")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")

    def test_large_json_body_rejected(self):
        response = TestClient(app).post("/research-api/sessions",
            content=b"x" * 100000, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
