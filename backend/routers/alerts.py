from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional
import json, os, uuid
from datetime import datetime, timezone
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ai_service import ai_filter_and_summarize

router = APIRouter()

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_alerts.json")

def load_alerts():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_alerts(alerts):
    with open(DATA_FILE, "w") as f:
        json.dump(alerts, f, indent=2)


class AlertCreate(BaseModel):
    raw_text: str
    location: str
    source: str = "community_report"
    category: Optional[str] = "general"

    @field_validator("raw_text")
    @classmethod
    def text_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Alert text cannot be empty")
        if len(v) < 10:
            raise ValueError("Alert text too short — please provide more detail (min 10 chars)")
        if len(v) > 1000:
            raise ValueError("Alert text too long (max 1000 characters)")
        return v

    @field_validator("location")
    @classmethod
    def location_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Location is required")
        return v


class AlertUpdate(BaseModel):
    verified: Optional[bool] = None
    category: Optional[str] = None
    severity: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def valid_severity(cls, v):
        if v is not None and v not in ["critical", "high", "medium", "low", "none"]:
            raise ValueError("Severity must be one of: critical, high, medium, low, none")
        return v


@router.get("/")
def get_alerts(
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    verified_only: bool = Query(False),
    hide_noise: bool = Query(True)
):
    alerts = load_alerts()
    # Run AI filter
    alerts = ai_filter_and_summarize(alerts)

    # Apply filters
    if hide_noise:
        alerts = [a for a in alerts if not a.get("is_noise", False)]
    if category:
        alerts = [a for a in alerts if a.get("category", "").lower() == category.lower()]
    if severity:
        alerts = [a for a in alerts if a.get("severity", "").lower() == severity.lower()]
    if location:
        alerts = [a for a in alerts if location.lower() in a.get("location", "").lower()]
    if verified_only:
        alerts = [a for a in alerts if a.get("verified", False)]

    # Sort: critical first
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
    alerts.sort(key=lambda a: severity_order.get(a.get("severity", "none"), 4))

    return {"alerts": alerts, "total": len(alerts)}


@router.get("/{alert_id}")
def get_alert(alert_id: str):
    alerts = load_alerts()
    alert = next((a for a in alerts if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert


@router.post("/", status_code=201)
def create_alert(alert: AlertCreate):
    alerts = load_alerts()
    new_alert = {
        "id": f"a{str(uuid.uuid4())[:6]}",
        "source": alert.source,
        "raw_text": alert.raw_text,
        "category": alert.category,
        "location": alert.location,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verified": False,
        "severity": "low",
        "ai_summary": None,
        "tags": []
    }
    alerts.append(new_alert)
    save_alerts(alerts)
    # Run AI on new alert
    processed = ai_filter_and_summarize([new_alert])
    return {"message": "Alert submitted successfully", "alert": processed[0]}


@router.patch("/{alert_id}")
def update_alert(alert_id: str, update: AlertUpdate):
    alerts = load_alerts()
    alert = next((a for a in alerts if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")

    if update.verified is not None:
        alert["verified"] = update.verified
    if update.category is not None:
        alert["category"] = update.category
    if update.severity is not None:
        alert["severity"] = update.severity

    save_alerts(alerts)
    return {"message": "Alert updated", "alert": alert}


@router.delete("/{alert_id}")
def delete_alert(alert_id: str):
    alerts = load_alerts()
    original_len = len(alerts)
    alerts = [a for a in alerts if a["id"] != alert_id]
    if len(alerts) == original_len:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    save_alerts(alerts)
    return {"message": f"Alert '{alert_id}' deleted"}
