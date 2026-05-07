# AI Browser Automation Agent

A production-minded MVP of an AI-powered browser automation agent. Understands natural language instructions and executes browser-based workflows across Google Sheets, Drive, Colab, Gmail, and generic web apps.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                     │
│  CommandInput │ ExecutionLog │ BrowserPreview │ History       │
└──────────────────────┬───────────────────────────────────────┘
                       │ REST + SSE
┌──────────────────────▼───────────────────────────────────────┐
│                    Backend (FastAPI)                          │
│  /executions  │  /workflows  │  /automations  │  /stream     │
└──────┬────────────────┬──────────────────────────────────────┘
       │                │
┌──────▼──────┐  ┌──────▼──────────────────────────────────────┐
│  Planner    │  │  Executor Agent (Playwright)                 │
│  (GPT-4.1)  │  │  click / type / extract / screenshot        │
└──────┬──────┘  └──────┬──────────────────────────────────────┘
       │                │
┌──────▼────────────────▼─────────────────────────────────────┐
│  State Manager + Memory Layer (SQLite)                       │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- OpenAI API key

### 1. Clone and configure

```bash
git clone <repo-url>
cd pinterest-content-automation
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

### 2. Run with Docker (recommended)

```bash
docker-compose up --build
```

Open http://localhost:3000

### 3. Run manually

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Example Prompts

```
"Go to https://drive.google.com, find the latest spreadsheet, copy Sheet1 contents, 
 open Google Colab, create a new notebook named 'Data Import', paste the content, and save."

"Open https://docs.google.com/spreadsheets/d/YOUR_ID and extract all data from the first sheet"

"Navigate to https://colab.research.google.com, create a new notebook, 
 add a markdown cell saying 'Hello World', then save it"

"Go to Gmail, open the latest unread email and extract the subject line"
```

## Project Structure

```
project-root/
├── backend/          # FastAPI application
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── routers/
├── agents/           # AI planning + browser execution
│   ├── planner.py    # GPT-4.1 powered step planner
│   ├── executor.py   # Playwright action executor
│   └── orchestrator.py
├── tools/            # Reusable browser tool registry
│   ├── registry.py
│   ├── browser_tools.py
│   └── google_tools.py
├── memory/           # State + workflow memory
│   ├── state_manager.py
│   └── memory_layer.py
├── workflows/        # Example workflow definitions
│   └── examples/
├── frontend/         # Next.js dashboard
├── tests/            # Unit + integration tests
├── docker/           # Dockerfiles
├── logs/             # Runtime logs
└── screenshots/      # Captured screenshots
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/executions` | Start a new automation execution |
| GET | `/api/executions` | List execution history |
| GET | `/api/executions/{id}` | Get execution details |
| GET | `/api/executions/{id}/steps` | Get individual step results |
| GET | `/api/executions/{id}/stream` | SSE stream of live progress |
| POST | `/api/workflows` | Save a workflow |
| GET | `/api/workflows` | List saved workflows |
| POST | `/api/automations` | Save an automation template |
| GET | `/api/automations` | List automation templates |
| GET | `/health` | Health check |

## Environment Variables

See `.env.example` for all configuration options.

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

## Security Notes

- Never commit `.env` files
- OAuth tokens are stored encrypted in SQLite
- Confirmation steps gate destructive browser actions
- Browser sessions run in sandboxed Chromium contexts
