import os
import json
import anthropic
from typing import Optional

client: Optional[anthropic.Anthropic] = None

def get_client():
    global client
    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            client = anthropic.Anthropic(api_key=api_key)
    return client


# ─── AI-powered functions ────────────────────────────────────────────────────

def ai_filter_and_summarize(alerts: list[dict]) -> list[dict]:
    """Use Claude to filter noise and summarize real alerts."""
    c = get_client()
    if not c:
        return _rule_based_filter(alerts)

    try:
        alerts_text = json.dumps(alerts, indent=2)
        message = c.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a community safety AI assistant. 
Analyze these alerts and for each one:
1. Determine if it's a real safety concern (not venting, spam, or irrelevant).
2. Assign severity: critical, high, medium, low, or none.
3. Write a calm, 1-sentence actionable summary (max 20 words).
4. Set is_noise=true for venting/irrelevant posts.

Return ONLY a JSON array with same order as input, each item having:
- id (same as input)
- is_noise (boolean)
- severity (string)
- ai_summary (string, null if is_noise)
- action_step (string, 1 actionable tip, null if is_noise)

Alerts:
{alerts_text}"""
                }
            ]
        )
        result = json.loads(message.content[0].text)
        # Merge AI output back into alerts
        ai_map = {item["id"]: item for item in result}
        for alert in alerts:
            ai_data = ai_map.get(alert["id"], {})
            alert["is_noise"] = ai_data.get("is_noise", False)
            alert["severity"] = ai_data.get("severity", alert.get("severity", "low"))
            alert["ai_summary"] = ai_data.get("ai_summary")
            alert["action_step"] = ai_data.get("action_step")
            alert["ai_powered"] = True
        return alerts
    except Exception as e:
        print(f"[AI] Claude unavailable, using rule-based fallback: {e}")
        return _rule_based_filter(alerts)


def ai_generate_digest(alerts: list[dict], location: str) -> dict:
    """Generate a calm safety digest for the user's area."""
    c = get_client()
    real_alerts = [a for a in alerts if not a.get("is_noise", False)]

    if not c:
        return _rule_based_digest(real_alerts, location)

    try:
        alerts_text = json.dumps(real_alerts, indent=2)
        message = c.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a calm, reassuring community safety assistant.
Generate a brief safety digest for a resident of {location}.
Based on these verified alerts, write:
1. overall_status: one of "all_clear", "stay_informed", "take_action"
2. headline: one calm sentence summarizing the situation (max 15 words)
3. summary: 2-3 calm, empowering sentences. Focus on what residents CAN DO.
4. top_threats: list of max 3 most important threats (strings)
5. mood: "calm", "alert", or "urgent"

Alerts: {alerts_text}

Return ONLY valid JSON with keys: overall_status, headline, summary, top_threats, mood"""
                }
            ]
        )
        result = json.loads(message.content[0].text)
        result["ai_powered"] = True
        return result
    except Exception as e:
        print(f"[AI] Claude unavailable for digest: {e}")
        return _rule_based_digest(real_alerts, location)


def ai_generate_checklist(threat_type: str, threat_description: str) -> dict:
    """Generate a 1-2-3 action checklist for a specific threat."""
    c = get_client()
    if not c:
        return _rule_based_checklist(threat_type)

    try:
        message = c.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a cybersecurity and personal safety expert.
A user needs help responding to this threat:
Type: {threat_type}
Description: {threat_description}

Generate a calm, numbered checklist of exactly 5 steps to protect themselves.
Each step should be:
- Specific and actionable (not vague)
- Written in simple, non-technical language
- Empowering, not fear-inducing

Return ONLY valid JSON with keys:
- title: short checklist title
- steps: array of 5 strings (the action steps)
- estimated_time: how long this takes (e.g., "10 minutes")
- difficulty: "easy", "medium", or "advanced" """
                }
            ]
        )
        result = json.loads(message.content[0].text)
        result["ai_powered"] = True
        result["threat_type"] = threat_type
        return result
    except Exception as e:
        print(f"[AI] Claude unavailable for checklist: {e}")
        return _rule_based_checklist(threat_type)


# ─── Rule-based fallbacks ─────────────────────────────────────────────────────

NOISE_KEYWORDS = ["ugh", "hate", "annoying", "pizza", "lol", "rant", "venting", "so loud", "gone downhill"]
SEVERITY_KEYWORDS = {
    "critical": ["ransomware", "malware", "attack", "breach", "critical"],
    "high": ["phishing", "scam", "fraud", "alert", "warning", "official"],
    "medium": ["break-in", "theft", "stolen", "suspicious", "crime"],
    "low": ["noise", "streetlight", "graffiti", "minor"]
}

def _rule_based_filter(alerts: list[dict]) -> list[dict]:
    for alert in alerts:
        text = alert.get("raw_text", "").lower()
        is_noise = any(kw in text for kw in NOISE_KEYWORDS)
        alert["is_noise"] = is_noise
        alert["ai_powered"] = False

        if not is_noise:
            severity = "low"
            for sev, keywords in SEVERITY_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    severity = sev
                    break
            alert["severity"] = severity
            alert["ai_summary"] = f"Alert from {alert.get('source', 'community')}: {alert.get('category', 'incident')} reported near {alert.get('location', 'your area')}."
            alert["action_step"] = "Stay aware and follow official guidance."
        else:
            alert["ai_summary"] = None
            alert["action_step"] = None
    return alerts

def _rule_based_digest(alerts: list[dict], location: str) -> dict:
    critical = [a for a in alerts if a.get("severity") in ["critical", "high"]]
    status = "all_clear" if not alerts else ("take_action" if critical else "stay_informed")
    mood = "calm" if not critical else ("urgent" if any(a["severity"] == "critical" for a in critical) else "alert")
    return {
        "overall_status": status,
        "headline": f"{len(alerts)} safety item(s) in your area this week.",
        "summary": f"There are {len(alerts)} alerts near {location}. {len(critical)} require immediate attention. Stay informed and follow official guidance.",
        "top_threats": [a.get("category", "unknown") for a in critical[:3]],
        "mood": mood,
        "ai_powered": False
    }

CHECKLIST_TEMPLATES = {
    "digital_threat": {
        "title": "Protect Yourself from Digital Threats",
        "steps": [
            "Do NOT click any suspicious links or download unknown attachments.",
            "Change your passwords immediately for affected accounts.",
            "Enable two-factor authentication (2FA) on all critical accounts.",
            "Run a security scan on your device using trusted antivirus software.",
            "Report the incident to your local cybercrime helpline."
        ],
        "estimated_time": "15 minutes",
        "difficulty": "easy"
    },
    "property_crime": {
        "title": "Secure Your Property",
        "steps": [
            "Do not leave valuables visible in your car or home entrance.",
            "Ensure all doors and windows are properly locked.",
            "Install or activate a security camera or motion sensor light.",
            "Share this alert with your immediate neighbors.",
            "Report any suspicious activity to local police immediately."
        ],
        "estimated_time": "20 minutes",
        "difficulty": "easy"
    },
    "suspicious_activity": {
        "title": "Stay Safe — Suspicious Activity Nearby",
        "steps": [
            "Stay indoors and avoid isolated areas after dark.",
            "Share your location with a trusted contact.",
            "Keep emergency contacts saved and easily accessible.",
            "If you see suspicious behavior, call non-emergency police (do not confront).",
            "Connect with neighbors to keep watch on your street."
        ],
        "estimated_time": "5 minutes",
        "difficulty": "easy"
    }
}

def _rule_based_checklist(threat_type: str) -> dict:
    template = CHECKLIST_TEMPLATES.get(threat_type, CHECKLIST_TEMPLATES["digital_threat"])
    return {**template, "ai_powered": False, "threat_type": threat_type}
