# 🛡️ Community Guardian — Intelligent Community Safety & Digital Wellness Platform

> A Palo Alto Networks New Grad SWE Take-Home Case Study Submission

---

## 📽️ Video Demo

🎥 **[Watch the 5–7 minute demo here](#)** ← *(Video link will be added before final submission)*

---

## Candidate Information

| Field | Value |
|---|---|
| **Candidate Name** | *(Maloth Niha)* |
| **Scenario Chosen** | Scenario 3 — Intelligent Community Safety & Digital Wellness |
| **Estimated Time Spent** | ~5.5 hours |
| **College** | IIT Hyderabad |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- An Anthropic API key ([get one here](https://console.anthropic.com))

### Backend Setup

```bash
cd backend

# Install dependencies
py -m pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the backend
py -m uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the React app
npm start

```
If Node.js is not installed, install the LTS version from nodejs.org first.

The app will open at `http://localhost:3000`

### Run Commands (Full Stack)

```bash
# Terminal 1 — Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm start
```

### Test Commands

```bash
cd backend

# Run all tests
pytest tests/test_alerts.py -v

# Run with coverage
pytest tests/test_alerts.py -v --tb=short
```

---

## 🤖 AI Disclosure

| Question | Answer |
|---|---|
| **Did you use an AI assistant?** | Yes — Claude (Anthropic) and GitHub Copilot for code suggestions |
| **How did you verify suggestions?** | Every function was manually reviewed, tested end-to-end, and validated against the API. AI-generated logic was cross-checked against FastAPI docs and Pydantic v2 validator syntax. Tests were run to confirm correctness. |
| **Example of a suggestion rejected/changed** | Copilot initially suggested using `@validator` (Pydantic v1 syntax) for input validation. I changed it to `@field_validator` with `@classmethod` (Pydantic v2), which is the correct modern approach. The AI also suggested a more complex multi-file state management system for the React frontend — I simplified it to `useState` hooks in a single `App.js` to stay within the timebox and reduce complexity. |

---

## ⚙️ Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| **Backend** | FastAPI (Python) | Fast, async, auto-generates Swagger docs, excellent Pydantic integration |
| **AI** | Anthropic Claude API (`claude-opus-4-5`) | Best-in-class reasoning for noise filtering and safety summarization |
| **AI Fallback** | Rule-based keyword matching | Ensures app works 100% without API key |
| **Frontend** | React 18 | Component-based, fast to iterate, great ecosystem |
| **Data** | JSON flat-file | Simple, portable, no database setup required for prototype |
| **Tests** | pytest + FastAPI TestClient | Standard Python testing, easy to read |

---

## 🏗️ Architecture & Design

```
community-guardian/
├── backend/
│   ├── main.py              # FastAPI app, CORS, router registration
│   ├── ai_service.py        # All Claude API calls + rule-based fallbacks
│   ├── routers/
│   │   ├── alerts.py        # CRUD for safety alerts (Create/Read/Update/Delete)
│   │   ├── digest.py        # AI-generated safety digest for a location
│   │   └── checklist.py     # AI-generated action checklists per threat type
│   ├── tests/
│   │   └── test_alerts.py   # 10 tests: happy path + edge cases
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.js           # Main React app (all components)
│   │   └── App.css          # Dark cybersecurity theme
│   └── public/
│       └── index.html
├── data/
│   ├── sample_alerts.json   # Synthetic alert dataset (8 records)
│   └── sample_users.json    # Synthetic safe circle users
└── README.md
```

### Core End-to-End Flow

```
User opens app
    → DigestBanner fetches AI safety summary for their neighborhood
    → Alerts list loads, AI filters noise (venting/irrelevant posts)
    → User can: Create alert | Filter/Search | Mark verified | Get Checklist
    → Checklist modal: AI generates 5-step action plan per threat type
```

### AI Integration

Three AI capabilities are implemented, each with a rule-based fallback:

| Feature | AI Behavior | Fallback Behavior |
|---|---|---|
| **Noise Filtering** | Claude analyzes each alert and marks venting/irrelevant posts as noise | Keyword matching (ugh, lol, hate, pizza, etc.) |
| **Safety Digest** | Claude generates a calm, location-specific safety summary | Rule-based count + severity aggregation |
| **Threat Checklist** | Claude generates a personalized 5-step action plan | Pre-written templates per threat category |

**Fallback trigger:** If `ANTHROPIC_API_KEY` is missing or the API call throws any exception, the system transparently switches to rule-based logic. Every response includes an `ai_powered: true/false` flag so the UI can display which mode is active.

---

## ⚖️ Tradeoffs & Prioritization

### What I cut to stay within 4–6 hours

- **No database** — used JSON flat-file instead of SQLite/PostgreSQL. In production, this would be a proper DB with indexed queries.
- **No authentication** — Safe Circles feature is designed in the synthetic data but not wired up in the UI. Adding JWT auth would take another hour.
- **No real-time updates** — WebSocket support for live alert streaming was skipped in favor of a manual refresh button.
- **No map view** — A geographic map of alerts (Leaflet.js) was planned but deprioritized since the core AI flow was more important to demonstrate.

### What I'd build next with more time

1. **WebSocket live alerts** — Push new alerts to all connected users in real time
2. **Safe Circles UI** — Private encrypted status sharing with trusted contacts
3. **Location-based filtering** — GPS-aware alerts using browser geolocation
4. **User authentication** — JWT-based login so users have persistent profiles
5. **PostgreSQL + Alembic** — Replace JSON flat-file with a real database and migrations
6. **Alert upvoting** — Community verification via thumbs up/down rather than manual admin action
7. **Email/SMS notifications** — Twilio or SendGrid integration for critical alerts

### Known Limitations

- **Data persistence** — Alert data resets if `sample_alerts.json` is overwritten. In production, use a database.
- **AI latency** — Claude API calls take 1–3 seconds. A loading state is shown, but response streaming would improve UX.
- **No input sanitization for XSS** — React handles this naturally, but the backend should add HTML sanitization for production.
- **Flat-file concurrency** — Concurrent writes to JSON could cause race conditions under load. Use a DB for any production use.
- **AI hallucination risk** — Claude's output is parsed as JSON. If the model returns malformed JSON, the fallback activates. This is handled in try/catch blocks.

---

## 🧪 Test Coverage

| Test | Type | What it validates |
|---|---|---|
| `test_health_check` | Happy path | API is reachable |
| `test_get_all_alerts_returns_list` | Happy path | GET /alerts returns correct schema |
| `test_create_valid_alert` | Happy path | Valid POST creates alert + returns 201 |
| `test_get_digest` | Happy path | Digest has required fields + valid status |
| `test_generate_checklist_digital_threat` | Happy path | Checklist has ≥3 steps + title |
| `test_filter_alerts_by_category` | Happy path | Category filter works correctly |
| `test_update_alert_verified_status` | Happy path | PATCH correctly updates verified flag |
| `test_create_alert_empty_text` | Edge case | Empty text returns 422 |
| `test_create_alert_text_too_short` | Edge case | Text < 10 chars returns 422 |
| `test_get_nonexistent_alert` | Edge case | Non-existent ID returns 404 |
| `test_update_nonexistent_alert` | Edge case | PATCH non-existent returns 404 |
| `test_invalid_severity_in_update` | Edge case | Invalid severity rejected |
| `test_checklist_invalid_threat_type` | Edge case | Invalid threat type returns 422 |
| `test_alert_text_too_long` | Edge case | Text > 1000 chars returns 422 |
| `test_noise_filtered_by_default` | Edge case | Noise alerts hidden by default |

---

## 🔒 Security & Responsible AI

- **No API keys committed** — `.env` is gitignored; `.env.example` provided
- **Synthetic data only** — No real personal data; no web scraping
- **AI fallback always active** — System never fails silently; degrades gracefully
- **Pydantic input validation** — All inputs validated server-side before processing
- **Privacy-first design** — No user tracking, no location data stored
- **Calm UX tone** — AI output is tuned to be empowering, not fear-inducing (aligns with Responsible AI pillar)
- **AI transparency** — Every response shows whether it was AI-powered or rule-based

---

## 📊 Sample Data

`data/sample_alerts.json` contains 8 synthetic alerts covering:
- ✅ Verified phishing email alert (high severity)
- ✅ Verified ransomware warning (critical)
- ✅ Verified car break-ins (medium)
- ✅ IRS phone scam targeting elderly (high)
- ⚠️ Unverified suspicious activity (low)
- ⚠️ Unverified streetlight outage (low)
- 🔇 Noise: neighbor venting (filtered by AI)
- 🔇 Noise: irrelevant community post (filtered by AI)
