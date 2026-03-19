"""
Tests for Community Guardian API
Run with: pytest tests/test_alerts.py -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ─── Happy Path Tests ────────────────────────────────────────────────────────

class TestHappyPath:

    def test_health_check(self):
        """API should be reachable and healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_all_alerts_returns_list(self):
        """GET /api/alerts should return a list of alerts."""
        response = client.get("/api/alerts/")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        assert isinstance(data["alerts"], list)

    def test_create_valid_alert(self):
        """POSTing a valid alert should return 201 and the created alert."""
        payload = {
            "raw_text": "Suspicious vehicle parked outside community center for 3 hours.",
            "location": "Community Center Drive",
            "source": "neighborhood_watch",
            "category": "suspicious_activity"
        }
        response = client.post("/api/alerts/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "alert" in data
        assert data["alert"]["location"] == "Community Center Drive"

    def test_get_digest(self):
        """GET /api/digest should return digest with required fields."""
        response = client.get("/api/digest/?location=Oak Street")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "headline" in data
        assert "mood" in data
        assert data["overall_status"] in ["all_clear", "stay_informed", "take_action"]

    def test_generate_checklist_digital_threat(self):
        """POST /api/checklist should return a 5-step checklist for digital threats."""
        payload = {
            "threat_type": "digital_threat",
            "threat_description": "Phishing emails targeting local bank customers"
        }
        response = client.post("/api/checklist/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert len(data["steps"]) >= 3
        assert "title" in data

    def test_filter_alerts_by_category(self):
        """Filtering alerts by category should return only matching alerts."""
        response = client.get("/api/alerts/?category=digital_threat")
        assert response.status_code == 200
        data = response.json()
        for alert in data["alerts"]:
            assert alert["category"] == "digital_threat"

    def test_update_alert_verified_status(self):
        """PATCH on an existing alert should update its verified status."""
        # First get alerts to find a valid ID
        response = client.get("/api/alerts/?hide_noise=false")
        alerts = response.json()["alerts"]
        if not alerts:
            pytest.skip("No alerts available to update")

        alert_id = alerts[0]["id"]
        patch_response = client.patch(f"/api/alerts/{alert_id}", json={"verified": True})
        assert patch_response.status_code == 200
        assert patch_response.json()["alert"]["verified"] == True


# ─── Edge Case Tests ──────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_create_alert_empty_text(self):
        """Empty alert text should return 422 validation error."""
        payload = {
            "raw_text": "",
            "location": "Oak Street"
        }
        response = client.post("/api/alerts/", json=payload)
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("empty" in str(e).lower() or "short" in str(e).lower() for e in errors)

    def test_create_alert_text_too_short(self):
        """Alert text under 10 chars should fail validation."""
        payload = {
            "raw_text": "help",
            "location": "Oak Street"
        }
        response = client.post("/api/alerts/", json=payload)
        assert response.status_code == 422

    def test_create_alert_missing_location(self):
        """Missing location should return 422."""
        payload = {"raw_text": "Something suspicious happened here."}
        response = client.post("/api/alerts/", json=payload)
        assert response.status_code == 422

    def test_get_nonexistent_alert(self):
        """Getting a non-existent alert ID should return 404."""
        response = client.get("/api/alerts/DOES_NOT_EXIST_999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_nonexistent_alert(self):
        """Patching a non-existent alert should return 404."""
        response = client.patch("/api/alerts/FAKE_ID_123", json={"verified": True})
        assert response.status_code == 404

    def test_invalid_severity_in_update(self):
        """Invalid severity value should be rejected."""
        response = client.get("/api/alerts/?hide_noise=false")
        alerts = response.json()["alerts"]
        if not alerts:
            pytest.skip("No alerts available")

        alert_id = alerts[0]["id"]
        patch_response = client.patch(f"/api/alerts/{alert_id}", json={"severity": "ultra_mega_critical"})
        assert patch_response.status_code == 422

    def test_checklist_invalid_threat_type(self):
        """Invalid threat type should return 422."""
        payload = {
            "threat_type": "alien_invasion",
            "threat_description": "Something weird"
        }
        response = client.post("/api/checklist/", json=payload)
        assert response.status_code == 422

    def test_alert_text_too_long(self):
        """Alert text over 1000 chars should be rejected."""
        payload = {
            "raw_text": "x" * 1001,
            "location": "Oak Street"
        }
        response = client.post("/api/alerts/", json=payload)
        assert response.status_code == 422

    def test_noise_filtered_by_default(self):
        """Noise alerts should be filtered by default (hide_noise=True)."""
        response = client.get("/api/alerts/")
        data = response.json()
        for alert in data["alerts"]:
            assert not alert.get("is_noise", False)

    def test_digest_default_location(self):
        """Digest without location param should still work."""
        response = client.get("/api/digest/")
        assert response.status_code == 200
        assert "headline" in response.json()
