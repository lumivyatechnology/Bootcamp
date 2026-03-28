# 03 — Agent vs MCP Guide: Two Approaches to Building an Agentic AI System

> **Session:** 12:10–12:45 — Agentic AI: Agents and automation workflows, live demo
> **Session:** 12:45–1:15 — MCP: Model Context Protocol, scalable system design

This is the most important document. It shows the core distinction the bootcamp teaches: two different ways to wire tools into an AI agent.

---

## SECTION A — Direct Agent Approach (Approach A)

### Which Files Implement the Direct Agent

| File | Role |
|---|---|
| `src/main.py` | FastAPI entry point — creates the agent, registers it with CopilotKit |
| `src/main_cli.py` | CLI entry point — runs the same agent in a terminal loop |
| `src/analytics_agents/standalone_text_to_sql_agent.py` | The ReAct agent class — holds the prompt, tools, and LLM |
| `src/analytics_agents/tools/postgres_tool.py` | PostgreSQL tool implementation (3 tools) |
| `src/analytics_agents/tools/duckdb.py` | DuckDB tool implementation (alternative, same 3 tools) |
| `src/analytics_agents/tools/tool.py` | Abstract base class defining the tool interface |
| `src/config/dependencies.py` | Dependency injection — creates and caches the tool instances |
| `src/config/settings.py` | Pydantic Settings — loads env vars |
| `src/config/langfuse.py` | Langfuse observability callback |

### How Tools Are Hardcoded/Registered

The tools are **wired in at startup** through a direct import chain. There is no discovery — the code explicitly creates and injects the tools:

**Step 1:** `dependencies.py` creates a `PostgresTool` instance:
```python
@lru_cache
def get_db_tool() -> Tools:
    return get_postgres_tool()  # Returns PostgresTool with connection params from settings

db_tool = get_db_tool()  # Created at module import time
```

**Step 2:** `main.py` imports and uses it directly:
```python
from config.dependencies import db_tool

standalone_text_to_sql_agent = StandaloneTextToSQLAgent.from_groq(
    api_key=settings.GROQ_API_KEY,
    duckdb_tool=db_tool,       # <-- tools injected here, at startup
    temperature=0,
)
```

**Step 3:** Inside `from_groq()`, the tools are extracted:
```python
@classmethod
def from_llm(cls, duckdb_tool: Tools | list, llm: BaseChatModel):
    if isinstance(duckdb_tool, Tools):
        duckdb_tool = duckdb_tool.tools  # Calls .tools property → list of 3 StructuredTools
    return cls(duckdb_tool, llm)
```

**Step 4:** The agent is created with those tools baked in:
```python
@property
def agent(self):
    agent = create_agent(
        model=self.llm,
        tools=self.tools,           # <-- the 3 hardcoded tools
        system_prompt=self.PROMPT_TEMPLATE,
        checkpointer=InMemorySaver(),
    )
    return agent
```

### Request Lifecycle Step by Step (Direct Agent)

```
1. User types "What's the cheapest phone?" in the CopilotKit chat
         │
2. Browser sends POST to Next.js → /api/copilotkit
         │
3. route.ts forwards to FastAPI backend via LangGraphHttpAgent
         │
4. FastAPI receives request at /copilotkit endpoint
         │
5. CopilotKit invokes the LangGraph agent with the message
         │
6. Agent begins ReAct loop:
   │
   ├── 🧠 Thought: "I need to check what tables exist"
   ├── ⚡ Action: agent calls get_all_tables() 
   │              → PostgresTool.get_all_table() 
   │              → SQL: SELECT table_name FROM information_schema.tables
   │              → PostgreSQL returns table names
   ├── 👁️ Observation: "brands,cpu_models,operating_systems,phones,phone_specs"
   │
   ├── 🧠 Thought: "I need the phones table schema"
   ├── ⚡ Action: agent calls get_table_create_statement(table_name="phones")
   │              → PostgresTool.get_table_schema("phones")
   │              → SQL: SELECT column_name, data_type FROM information_schema.columns
   │              → PostgreSQL returns column definitions
   ├── 👁️ Observation: "CREATE TABLE phones (phone_id int, name text, price float, ...)"
   │
   ├── 🧠 Thought: "Now I can write the query"
   ├── ⚡ Action: agent calls execute_query("SELECT name, price FROM phones ORDER BY price LIMIT 1")
   │              → PostgresTool.execute_query()
   │              → SQL executed against PostgreSQL
   │              → Returns JSON result
   ├── 👁️ Observation: '[["Samsung Galaxy A05", 320.0]]'
   │
   └── ✅ Final Answer: "The cheapest phone is the Samsung Galaxy A05 at $320."
         │
7. Response streamed back through FastAPI → Next.js → Browser
```

### Pros of the Direct Approach
- **Simple to understand** — you can follow the code path from `main.py` to the tool in a straight line
- **Easy to debug** — tools are right there in the codebase, no network calls between agent and tools
- **Fast** — no overhead from MCP protocol, HTTP serialization, or service discovery
- **Good for prototyping** — get something working quickly with minimal setup

### Cons of the Direct Approach
- **Tight coupling** — the agent is married to the specific tool implementations; changing from PostgreSQL to DuckDB requires editing `dependencies.py`
- **Not extensible** — adding a new tool means changing the codebase, redeploying the agent
- **Hidden side effects** — tool implementations are buried inside the agent process; the LLM interacts with the database directly without any intermediate boundary
- **No standardized interface** — other systems can't discover or use these tools; they're internal to this Python process
- **Single point of failure** — if the tool crashes, it takes down the agent

---

## SECTION B — MCP Approach (Approach B)

### Which Files Implement MCP

| File | Role |
|---|---|
| `src/mcp_server/main.py` | MCP server — exposes 3 database tools over HTTP using FastMCP |
| `src/main_mcp.py` | MCP client — connects to the server, discovers tools, runs the agent |
| `src/analytics_agents/standalone_text_to_sql_agent.py` | Same agent class — but receives MCP tools instead of local tools |
| `src/config/dependencies.py` | Same dependency injection — used by the MCP server to access the database |

### How Tools Are Exposed Through MCP

**The MCP Server** (`src/mcp_server/main.py`) wraps the same database operations as standalone HTTP endpoints:

```python
from mcp.server.fastmcp import FastMCP
from config.dependencies import get_db_tool

mcp = FastMCP("DuckDB MCP Server")

@mcp.tool()
async def execute_query(query: str) -> str:
    """Execute a SQL query against the database and return results as JSON."""
    tool = get_db_tool()
    return tool.execute_query(query)

@mcp.tool()
async def get_all_tables() -> str:
    """Get a comma-separated list of all available tables in the database."""
    tool = get_db_tool()
    return tool.get_all_table()

@mcp.tool()
async def get_table_schema(table_name: str) -> str:
    """Get the CREATE TABLE statement (DDL) for a specific table."""
    tool = get_db_tool()
    return tool.get_table_schema(table_name)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")  # Starts on port 8000
```

Key differences from the direct approach:
- Each tool is a **decorated function** — MCP automatically generates the tool metadata (name, description, parameter schema) from the function signature and docstring
- The server runs as a **separate process** — it can be started, stopped, and scaled independently
- Tools are accessed via **HTTP** — any MCP-compatible client can discover and use them

### How the Agent Discovers and Calls Tools Through MCP

**The MCP Client** (`src/main_mcp.py`) doesn't hardcode any tools. Instead, it **discovers** them at runtime:

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from langchain_mcp_adapters.tools import load_mcp_tools

async with streamable_http_client(url="http://localhost:8000/mcp") as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # 🔑 KEY LINE: Discover tools dynamically from the server
        mcp_tools = await load_mcp_tools(session)
        
        # Create agent with discovered tools (not hardcoded ones)
        agent = StandaloneTextToSQLAgent.from_groq(
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            duckdb_tool=mcp_tools,  # <-- these came from the server, not from imports
        )
```

`load_mcp_tools(session)` calls the MCP server's `tools/list` endpoint, gets back the tool definitions, and wraps each one as a LangChain `StructuredTool` — bridged by `langchain-mcp-adapters`.

### Request Lifecycle Step by Step (MCP Approach)

```
TERMINAL 1: MCP Server running (make mcp_serve)
   └── Listening on http://localhost:8000/mcp

TERMINAL 2: MCP Client running (make run_mcp)

1. User types "What's the cheapest phone?" in the terminal
         │
2. Client connects to MCP server at localhost:8000/mcp
         │
3. Client calls session.initialize() — handshake with server
         │
4. Client calls load_mcp_tools(session) — DISCOVERS tools from server:
   │  Server responds with:
   │  ├── execute_query(query: str) → str
   │  ├── get_all_tables() → str  
   │  └── get_table_schema(table_name: str) → str
         │
5. Client creates StandaloneTextToSQLAgent with MCP-discovered tools
         │
6. Agent begins ReAct loop (same as Direct, but tools hit MCP server):
   │
   ├── 🧠 Thought: "I need to check what tables exist"
   ├── ⚡ Action: agent calls get_all_tables()
   │              → HTTP POST to MCP server → server calls PostgresTool → returns result
   ├── 👁️ Observation: "brands,cpu_models,operating_systems,phones,phone_specs"
   │
   ├── 🧠 Thought: "I need the phones table schema"
   ├── ⚡ Action: agent calls get_table_schema("phones")
   │              → HTTP POST to MCP server → server calls PostgresTool → returns result
   ├── 👁️ Observation: "CREATE TABLE phones (...)"
   │
   ├── 🧠 Thought: "Now I can write the query"
   ├── ⚡ Action: agent calls execute_query("SELECT ...")
   │              → HTTP POST to MCP server → server calls PostgresTool → returns result
   ├── 👁️ Observation: '[["Samsung Galaxy A05", 320.0]]'
   │
   └── ✅ Final Answer: "The cheapest phone is the Samsung Galaxy A05 at $320."
         │
7. Answer displayed in the terminal
```

### Pros of the MCP Approach
- **Standardized protocol** — any MCP-compatible client (Claude, custom agents, other systems) can use these tools without knowing the implementation details
- **Plug-and-play** — swap the database from PostgreSQL to MySQL by changing only the server; clients don't change at all
- **Decoupled** — server and client run as separate processes, can be deployed on different machines
- **Tool discovery** — clients don't need to know what tools exist in advance; they ask the server
- **Production-ready** — scales horizontally; multiple agent instances can share one MCP server
- **Explicit boundaries** — tool calls cross an HTTP boundary, making them auditable and observable
- **Composable** — can connect multiple MCP servers (database server + web search server + email server) to one agent

### Cons of the MCP Approach
- **More setup complexity** — need to run two processes (server + client) instead of one
- **Network overhead** — each tool call is an HTTP request/response cycle (adds latency)
- **More moving parts** — debugging requires checking both server and client logs
- **Requires MCP infrastructure** — the server needs to be running and healthy for the agent to work

---

## SECTION C — Side-by-Side Comparison

| Dimension | Direct Agent (Approach A) | MCP Agent (Approach B) |
|---|---|---|
| **Coupling** | Tight — tools imported directly into agent code | Loose — tools discovered over HTTP at runtime |
| **Tool Registration** | Hardcoded in `dependencies.py` at startup | Dynamic via `load_mcp_tools()` at connection time |
| **Extensibility** | Edit code + redeploy to add a tool | Add a `@mcp.tool()` function to the server — clients discover it automatically |
| **Network Boundary** | None — tools run in the same Python process | HTTP — tool calls cross a network boundary |
| **Observability** | Langfuse traces the agent, but tool internals are opaque | MCP protocol is explicit — every tool call is a logged HTTP request |
| **Startup Complexity** | One command: `make run_ui` | Two commands: `make mcp_serve` + `make run_mcp` |
| **Production Readiness** | Works for single-instance deploys | Built for multi-service architectures |
| **Client Flexibility** | Only this specific Python agent can use the tools | Any MCP client (Claude Desktop, other agents) can use the same tools |
| **Latency** | Fastest — direct function calls | Slightly slower — HTTP round-trips per tool call |
| **Failure Modes** | Tool crash = agent crash | Tool crash = agent gets an error and can retry |
| **Entry Point** | `src/main.py` (FastAPI) or `src/main_cli.py` (CLI) | `src/mcp_server/main.py` (server) + `src/main_mcp.py` (client) |
| **Frontend Integration** | Built-in via CopilotKit `/copilotkit` endpoint | Not yet — MCP client is CLI-only in this codebase |
| **Best For** | Learning, prototyping, simple deploys | Production, multi-agent systems, tool reuse |

---

## SECTION D — Demo Script

This is a step-by-step demo you can follow live. Run the Direct Agent first, then switch to the MCP version for the same query.

### Prerequisites (Do These Before the Demo)

1. PostgreSQL is running with the 5 normalized tables loaded
2. `.env` file is configured in `data_bot/analytics_agent/`
3. Both terminals are open and ready
4. Test both approaches work before going live

### Part 1: Direct Agent Demo (5 minutes)

**Step 1: Show the code (2 min)**

Open `src/main.py` and point out:
- Line where tools are imported: `from config.dependencies import db_tool`
- Line where agent is created: `StandaloneTextToSQLAgent.from_groq(..., duckdb_tool=db_tool, ...)`
- Say: *"See how the tools are imported directly? The agent knows exactly what tools it has because we hardcoded them."*

Open `src/config/dependencies.py` and point out:
- `db_tool = get_db_tool()` — the tool is created at import time
- Say: *"This tool is created once when the server starts. It's baked into the agent. If we wanted to add a new tool, we'd have to change this file and restart."*

**Step 2: Run the CLI version (3 min)**

```bash
cd data_bot/analytics_agent
make run_ui
```

Wait for the server to start (you'll see `Uvicorn running on http://0.0.0.0:3050`).

In a new terminal, or via the CopilotKit UI:

Open browser to `http://localhost:3000` (if UI is running) or use the CLI:
```bash
make run_cli   # (or: uv run --env-file .env src/main_cli.py)
```

Type this query:
```
What is the cheapest Samsung phone under $500?
```

**Narrate while waiting:**
> *"Right now the LLM is thinking. It's going through the ReAct loop — first it'll check what tables exist, then it'll look at the schema, then it'll write a SQL query. Watch the terminal logs..."*

Point out the server logs showing:
```
[*] Executing query: SELECT table_name FROM information_schema.tables...
[*] Fetching schema for table: phones
[*] Executing query: SELECT name, price FROM phones WHERE price < 500...
```

> *"There — three tool calls. get_all_tables, get_table_schema, execute_query. That's the ReAct pattern in action."*

### Part 2: MCP Agent Demo (5 minutes)

**Step 3: Show the MCP server code (1 min)**

Open `src/mcp_server/main.py` and say:
> *"Now here's the same three tools — but exposed through MCP. Notice how each tool is just a function decorated with `@mcp.tool()`. The server doesn't know or care who's calling these tools."*

**Step 4: Show the MCP client code (1 min)**

Open `src/main_mcp.py` and point out:
- `load_mcp_tools(session)` — *"This line discovers the tools at runtime. The client doesn't import any tool classes. It just asks the server: 'what tools do you have?'"*
- Say: *"Same agent, same LLM, same database — but now the tools come from a server, not from imports."*

**Step 5: Start the MCP server (1 min)**

In a new terminal:
```bash
cd data_bot/analytics_agent
make mcp_serve
```

You'll see: `Starting MCP server on http://localhost:8000/mcp`

**Step 6: Run the MCP client (2 min)**

In another terminal:
```bash
cd data_bot/analytics_agent
make run_mcp
```

Type the SAME query:
```
What is the cheapest Samsung phone under $500?
```

**Narrate the difference:**
> *"Same question. Same answer. But look at what's different: the tool calls are going over HTTP to the MCP server. The client didn't hardcode any tools — it discovered them. If I added a new tool to the server, this client would automatically be able to use it."*

### Part 3: The Punchline (1 min)

> *"So here's the key insight: in Approach A, the tools are part of the agent. In Approach B, the tools are a service the agent calls. It's the difference between a Swiss Army knife and a toolbox. The Swiss Army knife is convenient, but you can't add new tools. The toolbox is more setup, but you can add any tool you want — and anyone can use it."*

---

## Demo Risk Flags

| Risk | Impact | Mitigation |
|---|---|---|
| **MCP server not running when client tries to connect** | Client crashes with connection refused error | Start the server first. Keep the terminal visible so you can confirm it's running. |
| **Port 8000 already in use** | MCP server won't start | Check with `lsof -i :8000`. Kill existing process or change the port. |
| **MCP client fails to discover tools** | Agent has no tools, can't answer questions | Test the connection before the demo: `curl http://localhost:8000/mcp` should respond. |
| **Both approaches give different answers** | Confusing for audience — they should match | Both use the same database and same LLM. Slight wording differences are expected; data should be identical. |
| **MCP approach is noticeably slower** | Audience might question why you'd use MCP | Explain: *"Yes, it's slightly slower because of the HTTP round-trips. But in production, that trade-off buys you scalability, tool reuse, and decoupling."* |
| **`make run_mcp` exit code 2 (seen in terminal history)** | The MCP client has had issues running | Test beforehand. The `exit code 2` in the workspace suggests this has failed before. Check that `mcp` and `fastmcp` packages are installed: `uv pip install mcp fastmcp langchain-mcp-adapters`. |
| **Two demo terminals confuse the audience** | They lose track of which is the server, which is the client | Label your terminals clearly. Use different terminal backgrounds if possible. Narrate: *"This terminal is the server, this one is the client."* |
