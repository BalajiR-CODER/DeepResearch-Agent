# 🔬 DeepResearch Agent

An AI-powered research agent that takes any question, autonomously searches the web, reads sources, and produces a structured markdown report with citations — in under 60 seconds.

---

## Demo

> **Input:** "What are the latest developments in India's semiconductor industry?"

> **Output:** A structured markdown report with executive summary, numbered sections, inline citations, and a sources list — automatically generated from live web sources.

![DeepResearch Agent Screenshot](docs/screenshot.png)

---

## What It Does

1. **Plans** — Breaks your question into 3–4 targeted sub-queries using Gemini 2.5 Flash
2. **Searches** — Queries DuckDuckGo for each sub-query
3. **Reads** — Scrapes and extracts content from top results
4. **Writes** — Synthesizes findings into a structured report with inline citations

---

## Architecture

```
User Question
      ↓
Query Planner (Gemini 2.5 Flash)
      ↓
┌─────────────────────────────┐
│         Agent Loop          │
│  Search → Scrape → Next     │  ×N sub-queries
└─────────────────────────────┘
      ↓
Report Writer (Gemini 2.5 Flash)
      ↓
Structured Markdown Report
```

Built with **LangGraph** — each step (planner, search, scrape, writer) is a node in a stateful graph with conditional routing.

---

## Tech Stack

| Layer | Tool |
|---|---|
| LLM | Gemini 2.5 Flash |
| Agent Framework | LangGraph |
| Web Search | DuckDuckGo (via `duckduckgo-search`) |
| Web Scraping | BeautifulSoup + requests |
| Backend API | FastAPI |
| Frontend | Streamlit |
| Language | Python 3.12 |

**Cost: $0** — all free-tier tools.

---

## Project Structure

```
deep-research-agent/
├── backend/
│   ├── __init__.py
│   ├── app.py          # FastAPI routes
│   ├── agent.py        # LangGraph agent (planner → search → scrape → writer)
│   ├── tools.py        # DuckDuckGo search + BeautifulSoup scraper
│   └── config.py       # Environment config
├── frontend/
│   └── streamlit_app.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quickstart

### 1. Clone and set up environment

```bash
git clone https://github.com/yourusername/deep-research-agent.git
cd deep-research-agent
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-2.5-flash
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

### 3. Run the backend

```bash
uvicorn backend.app:app --reload
```

Backend runs at `http://localhost:8000`

### 4. Run the frontend

```bash
# In a new terminal
streamlit run frontend/streamlit_app.py
```

Frontend runs at `http://localhost:8501`

---

## API Reference

### `POST /research`

Run the research agent on a query.

**Request:**
```json
{
  "query": "What are the latest developments in India's semiconductor industry?"
}
```

**Response:**
```json
{
  "report": "# India's Semiconductor Industry\n\n## Executive Summary\n..."
}
```

### `GET /`

Health check.

```json
{
  "message": "DeepResearch Agent API running"
}
```

---

## Requirements

```
langgraph==0.2.34
langchain==0.3.0
langchain-google-genai==2.1.4
duckduckgo-search==6.2.1
beautifulsoup4==4.12.3
fastapi==0.115.0
uvicorn==0.30.6
streamlit==1.39.0
python-dotenv==1.0.1
requests==2.32.3
pydantic==2.9.2
```

---

## How the Agent Works

### LangGraph State Machine

The agent is a stateful graph with 5 nodes:

```
planner → search → scrape → next → (conditional)
                                       ├── search  (if more sub-queries remain)
                                       └── writer  (if all sub-queries done)
```

**State** tracks the query, list of sub-queries, current index, search results, scraped content, and final report across all nodes.

### Scrape Fallback

If a URL returns a 403, times out, or is JS-rendered, the agent falls back to the DuckDuckGo snippet for that source — ensuring every sub-query contributes content to the final report even when scraping fails.

---

## Key Design Decisions

**Why LangGraph over a simple loop?**
LangGraph provides explicit state management and conditional routing. The graph structure makes it easy to add new nodes (e.g. a fact-checker agent, a summariser) without rewriting control flow.

**Why DuckDuckGo?**
No API key required, no rate limit issues on free tier, and `duckduckgo-search` is a stable Python wrapper. Suitable for portfolio and demo use.

**Why Gemini 2.5 Flash?**
Fast, free on AI Studio, and handles both structured output (JSON sub-queries) and long-form writing (research reports) well in a single model.

---

## Limitations

- Scraping is blocked by some sites (paywalls, JS-heavy pages) — mitigated by snippet fallback
- Report quality depends on DDG result quality for niche queries
- No persistent memory between sessions
- Single-user; no auth or rate limiting on the API

---

## Future Improvements

- [ ] Stream the report token-by-token to the frontend
- [ ] Add a fact-checker agent node to flag uncertain claims
- [ ] Support PDF export of the generated report
- [ ] Add Redis caching for repeated queries
- [ ] Deploy to Railway / Render with Docker

---

## Author

**Balaji R** — AI Engineer | Bangalore
[LinkedIn](https://https://linkedin.com/in/balaji-r-06b68b289/) ·[GitHub](https://github.com/BalajiR-CODER)

---

## License

MIT