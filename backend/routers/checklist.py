from fastapi import APIRouter
from pydantic import BaseModel, field_validator
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ai_service import ai_generate_checklist

router = APIRouter()

class ChecklistRequest(BaseModel):
    threat_type: str
    threat_description: str = ""

    @field_validator("threat_type")
    @classmethod
    def valid_type(cls, v):
        allowed = ["digital_threat", "property_crime", "suspicious_activity", "infrastructure", "general"]
        if v not in allowed:
            raise ValueError(f"threat_type must be one of: {', '.join(allowed)}")
        return v

@router.post("/")
def generate_checklist(request: ChecklistRequest):
    return ai_generate_checklist(request.threat_type, request.threat_description)
