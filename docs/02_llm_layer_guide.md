# 02 — LLM Layer Guide: Language Models, Tool Calling & the ReAct Pattern

> **Session:** 11:35–12:10 — LLM: Intro to Large Language Models, Theory + Live Demo [YOUR SLOT]

---

## 1. How the LLM Is Configured in This Project

### Which Model and Provider

| Setting | Value |
|---|---|
| **Provider** | Groq (cloud inference platform) |
| **Model** | `qwen/qwen3-32b` (Qwen 3, 32-billion parameter model) |
| **Temperature** | `0` (deterministic — same input always produces same output) |
| **Framework** | LangChain + LangGraph |

### How the API Key Is Set Up

The API key is loaded from a `.env` file via Pydantic Settings:

```python
# src/config/settings.py
class Settings(BaseSettings):
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    # ... other settings
```

The settings are read from environment variables or a `.env` file in the `analytics_agent/` directory:
```bash
# .env
GROQ_API_KEY=gsk_your_key_here
```

### How the LLM Is Instantiated

From `src/analytics_agents/standalone_text_to_sql_agent.py`:

```python
@classmethod
def from_groq(cls, duckdb_tool: Tools | list, api_key: str, temperature: float):
    llm = ChatGroq(api_key=api_key, temperature=temperature, model="qwen/qwen3-32b")
    return cls.from_llm(duckdb_tool=duckdb_tool, llm=llm)
```

And it's called in `src/main.py`:

```python
standalone_text_to_sql_agent = StandaloneTextToSQLAgent.from_groq(
    api_key=settings.GROQ_API_KEY,
    duckdb_tool=db_tool,
    temperature=0,
)
```

### Alternative LLM Providers

The system supports multiple providers through factory methods:

| Method | Provider | Model |
|---|---|---|
| `from_groq()` | Groq | `qwen/qwen3-32b` |
| `from_azure_llm_config()` | Azure OpenAI | Configurable via `LLM_CONFIG` JSON |
| `from_perplexity()` | Perplexity AI | `sonar-reasoning-pro` |
| `from_llm()` | Any LangChain-compatible model | Custom |

This means **the agent is LLM-agnostic** — you can swap the brain without changing any other code.

---

## 2. The Three Tools Registered for the Agent

The agent has exactly **three tools** it can call. These are the only actions it can take in the world:

### Tool 1: `get_all_tables`

| Property | Value |
|---|---|
| **Name** | `get_all_tables` |
| **What it does** | Returns a comma-separated list of all table names in the database |
| **Parameters** | None (empty input) |
| **Returns** | String like `"brands,cpu_models,operating_systems,phones,phone_specs"` |
| **When the agent uses it** | First step — to understand what data is available |

**Code** (from `postgres_tool.py`):
```python
def get_all_table(self, *args, **kwargs) -> str:
    query = """
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' ORDER BY table_name;
    """
    tables = self.execute(query)
    return ",".join(t[0] for t in tables)
```

### Tool 2: `get_table_create_statement`

| Property | Value |
|---|---|
| **Name** | `get_table_create_statement` |
| **What it does** | Returns the CREATE TABLE DDL (schema) for a specific table |
| **Parameters** | `table_name: str` — the name of the table to inspect |
| **Returns** | String like `"CREATE TABLE phones (\n    phone_id integer NOT NULL,\n    name text,\n    price double precision,\n    ..."` |
| **When the agent uses it** | After seeing table names — to understand what columns exist |

**Code** (from `postgres_tool.py`):
```python
def get_table_schema(self, table_name: str, *args, **kwargs) -> str:
    query = f"""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    df = self.execute_df(query)
    return self._df_to_create_statement(df, table_name)
```

### Tool 3: `execute_query`

| Property | Value |
|---|---|
| **Name** | `execute_query` |
| **What it does** | Runs a SQL query against the database and returns results as JSON |
| **Parameters** | `query: str` — the SQL query to execute |
| **Returns** | JSON string of results (limited to 100 rows), e.g., `'[["Samsung Galaxy S25", 402.0], ...]'` |
| **When the agent uses it** | Once it knows the schema — to actually answer the question |

**Code** (from `postgres_tool.py`):
```python
def execute_query(self, query: str) -> str:
    try:
        data = self.execute(query)
        return json.dumps(data[:100], default=str)
    except Exception as e:
        return str(e)
```

### How Tools Are Registered

Each tool is wrapped as a LangChain `StructuredTool` with a name, description, function, and Pydantic schema for its inputs:

```python
@property
def tool_execute_query(self):
    return StructuredTool(
        name="execute_query",
        description="Execute SQL queries against Postgres.",
        func=self.execute_query,
        args_schema=ExecuteQueryInput,  # Pydantic model: { query: str }
        handle_tool_error=lambda e: f"Error executing query: {e}",
    )

@property
def tools(self):
    return [
        self.tool_execute_query,
        self.tool_get_all_table,
        self.tool_get_table_schema,
    ]
```

These tools are passed to the agent at creation time — the LLM reads their names and descriptions to decide which one to call.

---

## 3. Tracing a Real Query: "Recommend me a phone under $500 with good camera"

Here is exactly what happens inside the agent when a user asks this question:

### Round 1: Discover what's available

**🧠 Thought:** "I need to find out what tables are available in the database to answer a question about phones under $500 with good camera specs."

**⚡ Action:** Call `get_all_tables()`

**👁️ Observation:** `"brands,cpu_models,operating_systems,phones,phone_specs"`

### Round 2: Understand the phones table

**🧠 Thought:** "I need the schema for the 'phones' table to understand what columns are available, especially for price."

**⚡ Action:** Call `get_table_create_statement(table_name="phones")`

**👁️ Observation:**
```sql
CREATE TABLE phones (
    phone_id integer NOT NULL,
    name text,
    price double precision,
    brand_id integer,
    os_id integer,
    ratings_count integer,
    url text
);
```

### Round 3: Check specs table too

**🧠 Thought:** "For camera info, I might need to check the phone_specs table as well."

**⚡ Action:** Call `get_table_create_statement(table_name="phone_specs")`

**👁️ Observation:**
```sql
CREATE TABLE phone_specs (
    spec_id integer NOT NULL,
    phone_id integer,
    ram varchar,
    cpu_id integer,
    cpu_speed varchar
);
```

### Round 4: Write and execute the SQL

**🧠 Thought:** "The database doesn't have a specific camera column, but I can find phones under $500 with the best ratings (which often correlate with camera quality) and good specs (high RAM)."

**⚡ Action:** Call `execute_query(query="SELECT p.name, p.price, p.ratings_count, ps.ram FROM phones p JOIN phone_specs ps ON p.phone_id = ps.phone_id WHERE p.price < 500 ORDER BY p.ratings_count DESC LIMIT 5")`

**👁️ Observation:** `[["Samsung Galaxy S25 FE...", 402.0, 3896, "8 GB"], ["Samsung Galaxy S22 Ultra...", 387.0, 273, "12 GB"], ...]`

### Final Answer

**✅ Answer:** "Based on the data, here are the top phones under $500:
1. Samsung Galaxy S25 FE — $402, 3,896 ratings, 8 GB RAM
2. Samsung Galaxy S24 Ultra (Renewed) — $371, 94 ratings, 12 GB RAM
3. Samsung Galaxy S22 Ultra (Renewed) — $387, 273 ratings, 12 GB RAM

The Galaxy S25 FE is the most popular choice with the highest number of ratings..."

### Key Insight: The Agent Never Guesses

Notice: the agent doesn't have a "camera" column, so it adapts and uses ratings and specs as a proxy. It never makes up column names or data — it only uses what the schema tells it exists.

---

## 4. The ReAct Pattern: Where It Lives in the Code

### What Is ReAct?

**ReAct** = **Re**asoning + **Act**ing. Instead of the LLM just generating text, it follows a loop:

```
Thought → Action → Observation → (repeat until done) → Final Answer
```

### Where It's Defined

The ReAct pattern is implemented in two places:

**1. The System Prompt** (in `standalone_text_to_sql_agent.py`):

```python
PROMPT_TEMPLATE = """
You are an expert **Text-to-SQL ReAct Agent**...

### 🛠️ Tool Use and ReAct Format

You must follow the ReAct pattern: **Thought, Action, Observation.**

* **Thought:** Explain your reasoning. State what you are trying to achieve...
* **Action:** Call one of your available tools. The format is `ToolName[Input]`.
* **Observation:** The result of the tool execution.

Available Tools:
1. get_all_tables — Know which tables exist
2. get_table_schema — Inspect table columns, datatypes, structure
3. execute_query — Execute a SQL query

### 🛑 Constraints
* Do not hallucinate table or column names.
* Always attempt to run the query if the question can be answered with SQL.
* Final response must be the data itself, not the SQL.
"""
```

**2. The LangGraph Agent Creation** (also in `standalone_text_to_sql_agent.py`):

```python
@property
def agent(self):
    if self._agent is None:
        checkpointer = InMemorySaver()
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.PROMPT_TEMPLATE,
            checkpointer=checkpointer,
        )
        self._agent = agent
    return self._agent
```

`create_agent` from LangChain automatically implements the ReAct loop:
- It wraps the LLM in a graph that can call tools
- After each tool call, the result (observation) is fed back to the LLM
- The LLM decides whether to call another tool or produce a final answer
- `InMemorySaver` keeps conversation history so the agent can reference prior messages

### The Loop Visualized

```
User: "What's the cheapest Samsung phone?"
         │
         ▼
┌─────────────────────────────────┐
│ 🧠 THOUGHT                      │
│ "I need to check what tables    │
│  exist in the database"         │
│                                  │
│ ⚡ ACTION                        │
│ get_all_tables()                │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 👁️ OBSERVATION                   │
│ "brands,cpu_models,operating_   │
│  systems,phones,phone_specs"    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 🧠 THOUGHT                      │
│ "Now I need the phones schema"  │
│                                  │
│ ⚡ ACTION                        │
│ get_table_schema("phones")      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 👁️ OBSERVATION                   │
│ "CREATE TABLE phones (          │
│   phone_id integer, ..."        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 🧠 THOUGHT                      │
│ "I can now write the query"     │
│                                  │
│ ⚡ ACTION                        │
│ execute_query("SELECT name,     │
│  price FROM phones ORDER BY     │
│  price LIMIT 1")                │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 👁️ OBSERVATION                   │
│ [["Samsung Galaxy A05", 320.0]] │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ ✅ FINAL ANSWER                  │
│ "The cheapest Samsung phone is  │
│  the Galaxy A05 at $320."       │
└─────────────────────────────────┘
```

---

## 5. Key Talking Points

### Why an LLM Alone Fails Without Tool Calling

**Point 1: LLMs Don't Have Real-Time Data**
> "If you ask ChatGPT 'what's the cheapest Samsung phone on Amazon right now?' it gives you an answer based on its training data — which is months or years old. Our agent can actually query a live database and give you today's answer."

**Point 2: LLMs Hallucinate When They Don't Know**
> "Without tools, an LLM will confidently make up phone names, prices, and specs. With tool calling, the LLM is forced to check the database first. It can't invent data — it can only report what the query returns."

**Point 3: The LLM Is the Brain, Not the Hands**
> "Think of it this way: the LLM is brilliant at understanding your question and figuring out what SQL to write. But it can't actually run that SQL. The tools are its hands. Without hands, the brain is just thinking out loud."

### How Tool Calling Bridges the Gap

**Point 4: Tools Give LLMs Superpowers**
> "Tool calling turns a chatbot into an agent. A chatbot just responds. An agent can take actions: query databases, call APIs, search the web. The three tools in our system — get_all_tables, get_table_schema, execute_query — are enough for the LLM to answer any question about our phone data."

**Point 5: The Contract Is What Matters**
> "Each tool has a name, a description, and a schema. That's it. The LLM reads the description and decides when to use it. The description of `execute_query` says 'Execute SQL queries against Postgres.' — the LLM doesn't need to know how SQL works at the networking level. It just needs to know what the tool does and what to pass in."

---

## 6. Simple Analogy & 2-Minute Verbal Explanation

### The Analogy: The Smart Intern

> "Imagine you hire a brilliant intern who speaks every language, reads every textbook, and can write perfect SQL. But they've never been to your office. They don't know what databases you have, what tables exist, or what columns are called. If you ask them 'how many Samsung phones cost under $500?', they'll guess — and probably get it wrong.
>
> Now give them three tools: a list of all your databases, a way to look up table schemas, and a way to run queries. Suddenly, they can answer any question perfectly — not because they memorized the answer, but because they know how to look it up.
>
> That's tool calling. The LLM is the smart intern. The tools are the database access. The ReAct pattern is the intern's workflow: think about what I need → do something → see the result → repeat until I have the answer."

### 2-Minute Stage Explanation

> "Let me explain how this works in two minutes.
>
> A Large Language Model — like GPT or the Qwen model we're using — is incredibly good at understanding natural language. You can ask it 'find me a phone under $500 with good specs' and it understands exactly what you mean.
>
> But here's the problem: the LLM doesn't have access to our database. It doesn't know what phones we have, what they cost, or what their specs are. If it tries to answer without data, it'll hallucinate — make something up.
>
> So we give it tools. Three tools, specifically: one to list all tables in our database, one to read a table's structure, and one to run a SQL query. The LLM reads each tool's description and decides which one to use.
>
> The pattern is called ReAct — Reasoning plus Acting. The LLM thinks: 'I need to know what tables exist.' It acts: calls get_all_tables. It observes the result: 'phones, brands, phone_specs.' Then it thinks again: 'I need the phones schema.' Acts again. Observes again. And it keeps going until it has enough information to write the SQL query and give you a real, data-backed answer.
>
> That's the jump from chatbot to agent. A chatbot talks. An agent reasons, acts, and delivers."

---

## Demo Risk Flags

| Risk | Impact | Mitigation |
|---|---|---|
| **Groq API rate limit hit** | LLM calls return 429 errors, agent appears broken | Test beforehand. If rate-limited, switch to Azure or wait 60 seconds. Have a pre-recorded output as backup. |
| **Groq API key invalid** | Agent fails immediately | Double-check `.env` file. Have a backup key ready. |
| **Model `qwen/qwen3-32b` unavailable on Groq** | Agent can't start | Check Groq dashboard for model availability. Could switch to `llama-3.1-8b-instant` as fallback (change one line). |
| **LLM generates bad SQL** | Query fails, agent retries or returns error | This actually makes for a great demo moment — show the audience that the LLM is not perfect and needs guardrails. |
| **Agent takes too long to respond** | Audience loses attention during wait | Groq is fast (~2-3 second responses). If slow, narrate what's happening: "Right now the LLM is thinking..." |
| **`LLM_CONFIG` env var missing** | Pydantic Settings validation fails at startup | `LLM_CONFIG` is required by the Settings model — set `LLM_CONFIG={}` in `.env` even if not using Azure |
| **Agent returns SQL instead of plain English** | Confusing for non-technical audience | The system prompt says "Final response must be the data itself, not the SQL" — but occasionally the LLM slips. Just re-ask: "Can you explain that in plain English?" |
