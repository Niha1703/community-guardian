from fastapi import APIRouter, Query
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ai_service import ai_filter_and_summarize, ai_generate_digest
import json

router = APIRouter()

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample_alerts.json")
def load_alerts():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

@router.get("/")
def get_digest(location: str = Query(default="your area")):
    alerts = load_alerts()
    alerts = ai_filter_and_summarize(alerts)
    digest = ai_generate_digest(alerts, location)
    real_alerts = [a for a in alerts if not a.get("is_noise", False)]
    digest["alert_count"] = len(real_alerts)
    digest["location"] = location
    return digest
