# 00 — Repository Overview: Complete Architectural Guide

> **Bootcamp:** "Build & Break Your First Agentic AI System in One Day" — Lumivya Technology

---

## 1. What This Repository Is

This repository contains a **full end-to-end agentic AI system** built around a single domain: **phone recommendations from Amazon listings**. It demonstrates the complete journey from raw web data to an AI-powered conversational interface, passing through every layer a production system needs: data engineering, AI/LLM reasoning, web integration, and horizontal scaling.

---

## 2. Folder Structure Explained

```
Bootcamp/
├── gettingstarted.md                  ← Setup guide: how to install tools and run each module
├── prerequisites.md                   ← System requirements & software versions for attendees
├── docs/
│   └── entire_project_description.md  ← Detailed technical documentation of the whole project
│
├── data_acquisition/                  ← MODULE 1: Web scraper (Amazon → raw CSV)
│   ├── scrapy.cfg                     ← Scrapy project config (tells Scrapy where settings live)
│   ├── samsung_phones_specs.csv       ← Raw scraped output (messy, unprocessed)
│   └── amazon_samsung/               ← The Scrapy project package
│       ├── __init__.py
│       ├── items.py                   ← Scrapy item definitions (placeholder, not heavily used)
│       ├── middlewares.py             ← Scrapy middleware hooks (default scaffolding)
│       ├── pipelines.py              ← Item pipeline (pass-through — items just flow to CSV)
│       ├── settings.py               ← Scrapy settings (concurrency, delays, user-agent rotation)
│       ├── samsung_phones_specs.csv   ← Copy of raw output inside the package
│       ├── normalization.ipynb        ← Jupyter notebook: raw CSV → normalized tables
│       └── spiders/
│           └── samsung_phones.py      ← THE spider: Selenium + Scrapy crawling Amazon
│
├── data_processing/                   ← MODULE 2: Normalization outputs
│   ├── normalization.ipynb            ← Jupyter notebook (may be a copy/variant of the one above)
│   └── dataset/                       ← Clean, normalized CSV files (5 tables)
│       ├── brands.csv                 ← Lookup: brand_id → brand_name
│       ├── operating_systems.csv      ← Lookup: os_id → os_name
│       ├── cpu_models.csv             ← Lookup: cpu_id → cpu_model
│       ├── phones.csv                 ← Main table: phone_id, name, price, foreign keys, url
│       └── phone_specs.csv            ← Specs table: ram, cpu_id, cpu_speed per phone
│
├── data_bot/                          ← MODULE 3: AI agent + web frontend
│   ├── analytics_agent/               ← Python backend (FastAPI + LangGraph agent)
│   │   ├── pyproject.toml             ← Python dependencies & project metadata
│   │   ├── Makefile                   ← Task runner (run_ui, mcp_serve, docker, etc.)
│   │   ├── Dockerfile                 ← Container image for the agent
│   │   ├── docker-compose.yaml        ← Multi-container orchestration (2 agents + nginx)
│   │   ├── README.md                  ← Project README
│   │   ├── DOCUMENTATION.md           ← Extended docs
│   │   ├── notes.txt / summary.txt    ← Dev notes and operational logs
│   │   ├── nginx/
│   │   │   ├── Dockerfile             ← Nginx container image
│   │   │   └── nginx.conf             ← Load balancer config (round-robin)
│   │   ├── src/
│   │   │   ├── main.py                ← FastAPI entry point (Approach A: direct agent + CopilotKit)
│   │   │   ├── main_cli.py            ← CLI entry point (Approach A: direct agent via terminal)
│   │   │   ├── main_mcp.py            ← MCP client entry point (Approach B: agent uses MCP tools)
│   │   │   ├── text_summarizer.py     ← Standalone text summarization demo
│   │   │   ├── config/
│   │   │   │   ├── __init__.py        ← Exports settings singleton
│   │   │   │   ├── settings.py        ← Pydantic Settings (all env vars)
│   │   │   │   ├── dependencies.py    ← Dependency injection (db_tool, user_input_tool)
│   │   │   │   └── langfuse.py        ← Langfuse observability setup
│   │   │   ├── analytics_agents/
│   │   │   │   ├── standalone_text_to_sql_agent.py  ← THE ReAct agent (LangGraph)
│   │   │   │   └── tools/
│   │   │   │       ├── tool.py        ← Abstract base class (Port interface)
│   │   │   │       ├── duckdb.py      ← DuckDB implementation (CSV-backed)
│   │   │   │       ├── postgres_tool.py ← PostgreSQL implementation (production)
│   │   │   │       └── user_input.py  ← Human-in-the-loop tool (CLI only)
│   │   │   └── mcp_server/
│   │   │       └── main.py            ← MCP server (Approach B: exposes tools over HTTP)
│   │   └── tests/
│   │       ├── conftest.py            ← Pytest fixtures (loads test data)
│   │       ├── agents/
│   │       │   └── test_standalone_text_to_sql_agent.py
│   │       └── tools/
│   │           ├── test_duckdb_tool.py
│   │           └── test_user_input_tool.py
│   │
│   └── ui/                            ← Next.js frontend (CopilotKit chat)
│       ├── package.json               ← Node.js dependencies
│       ├── next.config.ts             ← Next.js configuration
│       ├── tsconfig.json              ← TypeScript config
│       ├── eslint.config.mjs          ← Linting rules
│       ├── postcss.config.mjs         ← PostCSS (for Tailwind)
│       └── app/
│           ├── globals.css            ← Global styles (Tailwind imports)
│           ├── layout.tsx             ← Root layout: wraps app in <CopilotKit> provider
│           ├── page.tsx               ← Home page: renders <CopilotChat> component
│           ├── test.tsx               ← Simple counter test component (not connected to agent)
│           └── api/
│               └── copilotkit/
│                   └── route.ts       ← API route: bridges CopilotKit UI ↔ FastAPI agent backend
│
└── images/                            ← (Empty) placeholder for images
```

---

## 3. End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: DATA ACQUISITION                                                   │
│                                                                             │
│   Amazon.com ──► Selenium (renders JS) ──► Scrapy Spider ──► Raw CSV        │
│   (10 search      Chrome WebDriver         samsung_phones.py   samsung_     │
│    pages)                                                      phones_      │
│                                                                specs.csv    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: DATA PROCESSING                                                    │
│                                                                             │
│   Raw CSV ──► normalization.ipynb ──► 5 Normalized CSV files                │
│                    │                   (brands, operating_systems,           │
│                    │                    cpu_models, phones, phone_specs)     │
│                    │                                                        │
│                    └──► PostgreSQL (same 5 tables via SQLAlchemy)            │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: AI AGENT (Two Approaches)                                          │
│                                                                             │
│   APPROACH A (Direct):                                                      │
│   FastAPI (main.py) ──► StandaloneTextToSQLAgent ──► PostgresTool ──► DB    │
│                              │                                              │
│                              ▼                                              │
│                         Groq LLM (qwen3-32b)                                │
│                                                                             │
│   APPROACH B (MCP):                                                         │
│   MCP Client (main_mcp.py) ──► MCP Server (mcp_server/main.py) ──► DB      │
│                              │                                              │
│                              ▼                                              │
│                         Groq LLM (qwen3-32b)                                │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: WEB FRONTEND                                                       │
│                                                                             │
│   Browser ──► Next.js (page.tsx) ──► /api/copilotkit (route.ts)             │
│                <CopilotChat>            │                                    │
│                                         ▼                                   │
│                                   LangGraphHttpAgent                        │
│                                         │                                   │
│                                         ▼                                   │
│                                   FastAPI backend (:3050)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

### Data Layer
| Technology | Role |
|---|---|
| **Scrapy** | Web crawling framework — manages request scheduling, pipelines, and export |
| **Selenium + ChromeDriver** | Browser automation — renders Amazon's dynamic JavaScript content |
| **scrapy-fake-useragent** | Rotates User-Agent headers to reduce blocking by Amazon |
| **Pandas** | Data manipulation and transformation during normalization |
| **SQLAlchemy** | ORM used to push normalized data from the notebook into PostgreSQL |
| **PostgreSQL** | Production relational database storing the 5 normalized tables |

### AI/LLM Layer
| Technology | Role |
|---|---|
| **LangChain** | LLM framework — prompt templates, tool definitions, output parsers |
| **LangGraph** | Agentic workflow orchestration — manages the ReAct loop (Thought → Action → Observation) |
| **Groq + qwen/qwen3-32b** | Default LLM provider and model — fast inference, free tier available |
| **DuckDB** | In-memory SQL engine — alternative to PostgreSQL for local dev (reads CSV files directly) |
| **psycopg2** | PostgreSQL driver for Python — used by the PostgresTool |
| **Langfuse** | LLM observability — traces every call, tool execution, token usage, and latency |
| **FastMCP** | MCP server library — exposes database tools over the Model Context Protocol |
| **langchain-mcp-adapters** | Bridges MCP tools into LangChain's StructuredTool format |
| **Pydantic + Pydantic Settings** | Configuration management — validates env vars, defines tool schemas |

### Web Layer
| Technology | Role |
|---|---|
| **Next.js 16** | React framework (App Router) — serves the frontend + API route |
| **React 19** | UI rendering |
| **CopilotKit** | AI chat integration — `@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime` |
| **Tailwind CSS v4** | Utility-first styling |
| **TypeScript** | Type safety across the frontend |

### Infrastructure
| Technology | Role |
|---|---|
| **Docker** | Containerization — packages the agent into a reproducible image |
| **Docker Compose** | Multi-container orchestration — runs 2 agent replicas + nginx |
| **Nginx** | Reverse proxy + round-robin load balancer |
| **uv** | Fast Python package manager (replaces pip/poetry) |
| **pnpm** | Fast Node.js package manager |

---

## 5. Two Approaches to Building an Agentic AI System

### Approach A: Direct Agent (Hardcoded Tool Calling)

**Files involved:**
- `src/main.py` — FastAPI server, creates agent with tools directly injected
- `src/main_cli.py` — CLI version of the same agent
- `src/analytics_agents/standalone_text_to_sql_agent.py` — The ReAct agent
- `src/analytics_agents/tools/postgres_tool.py` — PostgreSQL tool (hardcoded)
- `src/analytics_agents/tools/duckdb.py` — DuckDB tool (alternative)
- `src/config/dependencies.py` — Wires tools into the agent at startup

**How it works:**
1. At startup, `dependencies.py` creates a `PostgresTool` instance
2. The tool's 3 methods (`execute_query`, `get_all_tables`, `get_table_schema`) are wrapped as LangChain `StructuredTool` objects
3. These tools are passed directly to `StandaloneTextToSQLAgent` constructor
4. The agent is registered with FastAPI via CopilotKit's `add_langgraph_fastapi_endpoint`
5. Tools are **hardcoded at build time** — the agent always has exactly these tools, no more, no less

### Approach B: MCP-Based Agent (Standardized Tool Discovery)

**Files involved:**
- `src/mcp_server/main.py` — MCP server (exposes tools over HTTP using FastMCP)
- `src/main_mcp.py` — MCP client (discovers and uses tools dynamically)
- `src/analytics_agents/standalone_text_to_sql_agent.py` — Same agent, but receives MCP tools

**How it works:**
1. The MCP server starts independently (`make mcp_serve`), exposing 3 tools over HTTP at `localhost:8000/mcp`
2. The MCP client connects, calls `session.initialize()`, then `load_mcp_tools(session)` to **discover tools at runtime**
3. Discovered tools are passed to the same `StandaloneTextToSQLAgent`
4. The agent works identically — but tools were discovered dynamically, not hardcoded
5. The server and client are **decoupled** — the server can be swapped, upgraded, or scaled independently

---

## 6. Environment Setup Checklist

Before any demo will work, these must be in place:

### Required Software
- Python >= 3.12 (with `uv` package manager)
- Node.js >= 20.9.0 (with `pnpm`)
- Docker + Docker Compose
- PostgreSQL running locally
- Google Chrome (for Selenium scraper)

### Required Environment Variables (`.env` in `data_bot/analytics_agent/`)
```bash
# LLM (pick one)
GROQ_API_KEY=gsk_...                    # Required for default Groq setup

# Database (required)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_db_name
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# Server
PORT=3050
HOST=0.0.0.0

# Observability (optional but recommended for demo)
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_ENVIRONMENT=bootcamp

# Azure OpenAI (only if using Azure — JSON string)
LLM_CONFIG={"azure_endpoint": "...", "api_key": "...", "api_version": "...", "model": "..."}
```

### Required for Frontend (`data_bot/ui/.env`)
```bash
AGENT_URL=http://localhost:3050    # Points to the FastAPI backend
```

### Setup Steps
1. **PostgreSQL**: Ensure it's running and the database exists with the 5 normalized tables loaded
2. **Backend**: `cd data_bot/analytics_agent && uv sync && make run_ui`
3. **Frontend**: `cd data_bot/ui && pnpm install && pnpm dev`
4. **MCP (optional)**: Terminal 1: `make mcp_serve` → Terminal 2: `make run_mcp`
5. **Load balancing (optional)**: `make loadbalance`

---

## Demo Risk Flags

| Risk | Impact | Mitigation |
|---|---|---|
| **PostgreSQL not running** | Agent fails immediately on any query | Check `pg_isready` before demo. Have DuckDB path ready as fallback (uncomment in `dependencies.py`) |
| **GROQ_API_KEY expired or rate-limited** | LLM calls fail, agent returns errors | Have a backup key. Groq free tier has request limits — test before demo |
| **`LLM_CONFIG` env var missing** | `Settings` validation fails, app won't start | Provide a dummy JSON value even if not using Azure: `LLM_CONFIG={}` |
| **Port 3050 already in use** | FastAPI won't start | Kill existing process: `lsof -i :3050` and stop it |
| **Port 3000 already in use** | Next.js dev server won't start | Kill existing process or use a different port |
| **No data in PostgreSQL tables** | Agent returns empty results, confusing for audience | Run normalization notebook to populate tables before demo |
| **AGENT_URL mismatch in frontend** | Chat sends requests to wrong backend | Default is `http://localhost:8123` but FastAPI runs on `3050` — set `AGENT_URL=http://localhost:3050` |
| **Docker not installed** | Load balancing demo fails | Pre-pull images and test `docker compose up` beforehand |
| **Selenium/Chrome version mismatch** | Scraper fails (but scraper is pre-run for demo) | Not critical if you have the CSV already — the scraper is shown conceptually |
