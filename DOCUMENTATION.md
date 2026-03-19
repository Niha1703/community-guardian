# 📐 Design Documentation — Community Guardian

## Problem Statement

As digital and physical security threats grow more complex, individuals struggle to stay informed without experiencing alert fatigue or unnecessary anxiety. Information is scattered across news sites and social media — full of noise, venting, and repetition — with few actionable steps.

**Community Guardian** aggregates local safety and digital security data, uses AI to filter noise, and provides calm, actionable safety digests to empower residents rather than frighten them.

---

## Target Audience

| User | Pain Point | Solution |
|---|---|---|
| **Neighborhood Groups** | Too much noise on NextDoor/Facebook | AI filters venting; shows only verified incidents |
| **Remote Workers** | Unaware of local network scams | Digital Defense tab with instant checklists |
| **Elderly Users** | Complex security alerts, phone scams | Calm plain-English summaries + step-by-step guides |

---

## Design Decisions

### 1. Why FastAPI?
FastAPI auto-generates Swagger/OpenAPI docs (`/docs`), has native async support, and Pydantic v2 makes input validation clean and readable. For a prototype that needs to be demo-ready quickly, FastAPI is the most productive choice.

### 2. Why a flat JSON file instead of a database?
The 4–6 hour timebox made database setup a poor tradeoff. The JSON flat-file is human-readable, easily included in the repo as synthetic data, and trivially replaceable with SQLite or PostgreSQL in production (just swap the `load_alerts()`/`save_alerts()` functions).

### 3. Why three separate AI functions?
Separation of concerns: noise filtering, digest generation, and checklist generation are distinct tasks with different prompts and different failure modes. Keeping them separate means each has its own fallback and each can be independently improved.

### 4. Why the `ai_powered` flag in every response?
Transparency is a core Responsible AI principle. The UI shows users whether their information came from AI analysis or the rule-based fallback. This builds trust and sets correct expectations.

### 5. Why a dark cybersecurity aesthetic?
The target company (Palo Alto Networks) is a cybersecurity firm. A clean, dark, terminal-inspired UI signals domain awareness and intentional design — not just a generic CRUD app.

---

## AI Prompt Design

### Noise Filter Prompt Strategy
The noise filter prompt asks Claude to evaluate each alert holistically — not just for keywords — and return structured JSON. Key design choices:
- Ask for `is_noise` (boolean) rather than a score, to force a clear decision
- Ask for `action_step` separately from `ai_summary` to keep UX clean
- Return all alerts in the same order as input, using `id` as a stable key

### Digest Prompt Strategy
The digest prompt explicitly asks for a "calm, reassuring" tone — this is intentional. Fear-based UX is a known problem in safety apps. By prompting for empowerment, we align with the "Anxiety Reduction" success metric in the case study.

### Checklist Prompt Strategy
The checklist prompt constrains the output to exactly 5 steps in "simple, non-technical language." This serves the elderly user persona who needs clarity over completeness.

---

## Fallback Design

```
AI Call Attempted
       ↓
  API Key exists?  ──No──→ Rule-based fallback
       ↓ Yes
  Claude API call
       ↓
  Exception thrown? ──Yes──→ Rule-based fallback
       ↓ No
  JSON parse valid? ──No──→ Rule-based fallback
       ↓ Yes
  Return AI result (ai_powered: true)
```

The fallback is never "error out" — it's always "degrade gracefully." The user experience is nearly identical; only the `ai_powered` badge changes.

---

## Data Model

### Alert
```json
{
  "id": "a001",
  "source": "local_police | neighborhood_watch | community_forum | cybersecurity_feed",
  "raw_text": "Original report text",
  "category": "digital_threat | suspicious_activity | property_crime | infrastructure | general",
  "location": "Street or area name",
  "timestamp": "ISO 8601",
  "verified": true,
  "severity": "critical | high | medium | low | none",
  "ai_summary": "AI-generated 1-sentence summary",
  "action_step": "AI-generated actionable tip",
  "is_noise": false,
  "ai_powered": true,
  "tags": ["phishing", "banking"]
}
```

### Digest
```json
{
  "overall_status": "all_clear | stay_informed | take_action",
  "headline": "Calm one-sentence summary",
  "summary": "2-3 empowering sentences",
  "top_threats": ["digital_threat", "property_crime"],
  "mood": "calm | alert | urgent",
  "alert_count": 5,
  "location": "Oak Street",
  "ai_powered": true
}
```

### Checklist
```json
{
  "title": "Protect Yourself from Phishing",
  "steps": ["Step 1...", "Step 2...", "Step 3...", "Step 4...", "Step 5..."],
  "estimated_time": "10 minutes",
  "difficulty": "easy",
  "threat_type": "digital_threat",
  "ai_powered": true
}
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/alerts/` | List alerts (with filter/search params) |
| `GET` | `/api/alerts/{id}` | Get single alert |
| `POST` | `/api/alerts/` | Submit new alert |
| `PATCH` | `/api/alerts/{id}` | Update alert (verify, change category/severity) |
| `DELETE` | `/api/alerts/{id}` | Remove alert |
| `GET` | `/api/digest/` | Get AI safety digest for a location |
| `POST` | `/api/checklist/` | Generate action checklist for a threat type |
| `GET` | `/health` | Health check |

---

## Future Enhancements (Prioritized)

### P0 — Core Improvements
1. **PostgreSQL + SQLAlchemy** — Replace JSON flat-file with a real database
2. **JWT Authentication** — User accounts, persistent preferences
3. **WebSocket live alerts** — Real-time push without polling

### P1 — Feature Additions
4. **Geographic map view** — Leaflet.js map with alert pins
5. **Safe Circles** — Private encrypted status sharing with trusted contacts
6. **Email/SMS alerts** — Twilio/SendGrid for critical severity alerts
7. **Alert upvoting** — Community-driven verification system

### P2 — AI Enhancements
8. **Streaming responses** — Claude streaming API for faster UX
9. **Trend analysis** — "This type of scam is up 30% this week in your area"
10. **Personalized digests** — Based on user's past interactions and concerns

---

## Success Metrics Alignment

| Case Study Metric | How We Address It |
|---|---|
| **Anxiety Reduction** | AI digest tone is explicitly "calm and empowering"; noise is hidden by default |
| **Contextual Relevance** | Location-based filtering; digest scoped to user's area |
| **Trust & Privacy** | No real data collected; no location stored; transparent AI/fallback badges |
| **AI Application** | Three distinct AI features; graceful fallback on every one |
