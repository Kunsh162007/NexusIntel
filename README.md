# NexusIntel AI

**The Unified, Autonomous Deep-Web Intelligence Matrix**

> One system that monitors the live web and routes AI agents to the friction points across GTM, Finance, and Security — in real time, without waiting to be told where to look.

**Hackathon:** Web Data UNLOCKED — Bright Data AI × Web Data Weekend  
**Tracks:** GTM Intelligence · Finance & Market Intelligence · Security & Compliance  
**Partner Challenges:** AI/ML API · Cognee · TriggerWare.ai · Kiro

---

## What It Does

NexusIntel AI tears down the walls between three enterprise teams that almost never share a data layer.

Traditional agents wait to be told where to look. **NexusIntel decides for itself.**

The **Auto-Focus Engine** continuously pings a watchlist of live web sources, detects semantic anomalies using embedding comparison, and autonomously dispatches deep-dive agents to investigate. Findings are stored in a shared **Cognee** knowledge graph, surfaced as **Critical Insight Briefs** in the relevant track dashboard, and actioned via **TriggerWare.ai** webhooks — all without human intervention.

### Architecture

```
Live Public Web
       ↓
Bright Data Retrieval Layer
(Web Unlocker · SERP API · Web Scraper API · Scraping Browser · MCP Server)
       ↓
Auto-Focus Engine (anomaly detection + agent dispatch)
  powered by: AI/ML API (LLM reasoning)
       ↓                    ↓                    ↓
  GTM Track          Finance Track        Security Track
  (competitors,       (alt-data,           (threats,
   pricing,           filings, risk)        leaks, compliance)
   hiring)
       ↘                  ↓                  ↙
         Cognee Graph Memory (shared cross-track knowledge)
                           ↓
               TriggerWare.ai (webhooks → CRM / Slack)
                           ↓
            Voice Layer (Speechmatics STT + Web Speech TTS)
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Git

### 1. Clone

```bash
git clone https://github.com/your-username/nexusintel-ai.git
cd nexusintel-ai
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and fill in your API keys (see "API Keys" section below)
```

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
python main.py
# → Running on http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
# → Running on http://localhost:5173
```

Open **http://localhost:5173** — you'll see the NexusIntel dashboard.

### 5. Try the demo (no API keys required)

In the **Auto-Focus Status** card, click one of the demo scenario buttons:
- **Price Cut** — simulates a competitor slashing prices
- **Data Breach** — simulates a credential leak detection
- **Filing Alert** — simulates a cross-track SEC filing anomaly

Each demo fires a Critical Insight Brief into the relevant track dashboard in real time.

---

## API Keys Needed

| Service | Purpose | How to get | Cost |
|---------|---------|------------|------|
| **Bright Data** | Web Unlocker, SERP, Scraper, Browser | [brightdata.com](https://brightdata.com) → Create zones | $250 hackathon credit (code: `unlocked`) |
| **AI/ML API** | LLM reasoning, embeddings | [aimlapi.com](https://aimlapi.com) → API Keys | $10 hackathon credit |
| **Cognee** | Knowledge graph memory | [cognee.ai](https://cognee.ai) | Partner access |
| **TriggerWare.ai** | Webhook action layer | [triggerware.ai](https://triggerware.ai) | Partner access |
| **Speechmatics** | Voice STT | [speechmatics.com](https://speechmatics.com) | $200 credit (code: `WEBDATAHACK200`) |

> **Minimum viable setup:** Only `AIML_API_KEY` + Bright Data credentials are strictly required for the full live experience. Everything else has a graceful fallback.

### Bright Data credentials explained

In `.env`:
```
BRIGHT_DATA_CUSTOMER_ID=hl_xxxxxxxx     # Your customer ID from dashboard
BRIGHT_DATA_UNLOCKER_PASSWORD=xxx       # Password for your Web Unlocker zone
BRIGHT_DATA_SERP_PASSWORD=xxx           # Password for your SERP zone (optional)
```

Find these in: **Bright Data Dashboard → Proxies & Scraping → Your Zone → Access Parameters**

---

## Docker Deployment

```bash
cp .env.example .env
# Fill in .env

docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## Deploy to Railway (Recommended for Demo URL)

1. Push to GitHub
2. Create a new Railway project → "Deploy from GitHub repo"
3. Add two services: one pointing to `Dockerfile.backend`, one to `Dockerfile.frontend`
4. Set environment variables from your `.env` in Railway dashboard
5. Railway provides a public HTTPS URL — use this as your demo URL for submission

---

## Deploy to AWS with Kiro

1. Open this project in **Kiro** (AWS IDE)
2. Kiro auto-detects the Docker Compose setup
3. Use Kiro's deployment wizard to push to ECS/App Runner
4. Set env vars in Kiro's environment panel

---

## Feature Walkthrough

### Auto-Focus Engine
The engine runs a background loop every 5 minutes (configurable). For each URL in the watchlist:
1. Fetches content via Bright Data Web Unlocker
2. Computes an embedding of the page text
3. Compares to the stored baseline embedding (cosine similarity)
4. If similarity drops below threshold → **anomaly detected**
5. Dispatches a LangChain agent with Bright Data tools to investigate
6. AI/ML API generates a structured **Critical Insight Brief**
7. Stores in Cognee knowledge graph
8. Fires TriggerWare webhook
9. Broadcasts to all connected WebSocket clients

### Multi-Track Deep Switch
Click any of the three track tabs to switch the entire workspace:
- **GTM** — competitor analysis, hiring signals, web intelligence search
- **Finance** — pricing anomaly scanner, SEC filings, alternative data
- **Security** — threat scanner, credential checker, regulatory tracker

### Voice Interface
Click the **Voice** button → speak a command → Speechmatics transcribes → NexusIntel acts:
- *"Switch to security"* → switches track
- *"Give me a briefing"* → reads latest insight aloud (browser TTS)
- *"Search Salesforce"* → triggers a search

### Cross-Track Memory (Cognee)
When a GTM insight detects a competitor layoff, it's stored in Cognee. When the Finance track later analyzes that competitor's earnings, the stored GTM context is retrieved and linked — turning isolated observations into connected intelligence.

---

## Project Structure

```
nexusintel-ai/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # All configuration / env vars
│   ├── models.py               # Pydantic data models
│   ├── engine/
│   │   ├── auto_focus.py       # Autonomous monitoring engine
│   │   ├── agents.py           # LangChain agents + Bright Data tools
│   │   └── bright_data.py      # Bright Data API client (all 5 products)
│   ├── memory/
│   │   └── knowledge_graph.py  # Cognee integration
│   ├── actions/
│   │   └── triggers.py         # TriggerWare.ai webhook dispatch
│   ├── voice/
│   │   └── speech.py           # Speechmatics STT + command parsing
│   └── routes/                 # FastAPI route modules per track
├── frontend/
│   └── src/
│       ├── App.jsx             # Root component
│       ├── components/         # Track dashboards, insight cards, voice
│       ├── hooks/              # WebSocket hook
│       └── store/              # Zustand global state
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── .env.example
```

---

## Hackathon Compliance

- [x] Uses Bright Data (5 products: Web Unlocker, SERP, Web Scraper API, Scraping Browser, MCP Server pattern)
- [x] Covers all 3 tracks: GTM · Finance · Security
- [x] Partner: AI/ML API — LLM reasoning + embeddings
- [x] Partner: Cognee — cross-track knowledge graph
- [x] Partner: TriggerWare.ai — event-driven webhook actions
- [x] Partner: Kiro — AWS deployment target
- [x] Public GitHub repository
- [x] MIT License
- [x] Original work

---

## License

MIT
