# Analytics Agent Project Documentation

## 1. Project Overview

This project implements a sophisticated analytics agent designed to answer complex questions by breaking them down into smaller, manageable sub-problems. It leverages a graph-based architecture using **LangGraph** to orchestrate a series of specialized agents.

The core functionalities include:
- **Planning:** Decomposing a user's query into a multi-step execution plan.
- **Text-to-SQL:** Converting natural language questions into SQL queries.
- **Execution:** Running SQL queries against an in-memory **DuckDB** database.
- **Self-Correction:** Re-planning and refining steps based on execution errors or user feedback.
- **Answer Synthesis:** Compiling results from multiple steps into a final, coherent answer.

The project also includes examples of running the agent as a standalone service with a UI (via CopilotKit) and as a client connecting to a Multi-Agent Communication Protocol (**MCP**) server.

## 2. Installation & Usage

### Prerequisites

- Python 3.12+
- `uv` (a fast Python package installer and resolver)

### Setup

1.  **Install Dependencies:** Install all required production dependencies.
    ```bash
    uv sync
    ```

2.  **Install Development Dependencies:** To install additional packages for development (e.g., testing tools), run:
    ```bash
    uv sync --dev
    ```

### Environment Variables

The application relies on several environment variables for configuration. You can set these in a `.env` file in the project root.

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `PORT` | Port for the FastAPI server | No | `3050` |
| `HOST` | Host for the FastAPI server | No | `0.0.0.0` |
| `DEBUG` | Enable debug mode | No | `False` |
| `RELOAD` | Enable auto-reload for development | No | `True` |
| `DATA_BASE_PATH` | Base path for the database files | No | `.` |
| `DATA_BASE_PATH_TEST` | Base path for the test database files | No | `.` |
| `LLM_CONFIG` | Configuration dictionary for Azure OpenAI (if using Azure) | Yes (if using Azure) | - |
| `OPENAI_API_KEY` | OpenAI API Key (if using OpenAI) | Yes (if using OpenAI) | - |
| `GROQ_API_KEY` | Groq API Key (if using Groq) | Yes (if using Groq) | - |
| `GEMINI_KEY` | Google Gemini API Key (if using Gemini) | Yes (if using Gemini) | - |
| `PERPLEXITY_KEY` | Perplexity API Key (if using Perplexity) | Yes (if using Perplexity) | - |
| `LANGFUSE_SECRET_KEY` | Langfuse Secret Key for observability | No | - |
| `LANGFUSE_PUBLIC_KEY` | Langfuse Public Key for observability | No | - |
| `LANGFUSE_BASE_URL` | Langfuse Base URL | No | - |
| `LANGFUSE_ENVIRONMENT` | Langfuse Environment name | No | - |

**Note:** `LLM_CONFIG` should be a valid JSON string or dictionary when defined in python, containing configuration for the LLM provider (typically Azure OpenAI).

### How to Run

The project uses a `Makefile` to simplify common tasks.

-   **`make run_ui`**
    -   **Description:** Runs the main FastAPI application located in `src/main.py`. This exposes the analytics agent through an API compatible with CopilotKit, allowing it to be integrated with a user interface.
    -   **Command:** `uv run --env-file .env src/main.py`

-   **`make run_mcp`**
    -   **Description:** Runs the MCP client example from `src/main_mcp.py`. This script demonstrates how the agent can connect to and interact with an MCP server.
    -   **Command:** `uv run --env-file .env src/main_mcp.py`

-   **`make mcp_serve`**
    -   **Description:** Starts the MCP server defined in `src/mcp_server/main.py`. This server is required for the `run_mcp` client to connect to.
    -   **Command:** `uv run --env-file .env src/mcp_server/main.py`

-   **`make mcp_inspector`**
    -   **Description:** Runs the `fastmcp` inspector, a development tool used for debugging and monitoring the MCP server.
    -   **Command:** `fastmcp dev src/mcp_server/main.py`

-   **`make run_summarizer`**
    -   **Description:** Runs a utility script for text summarization located at `src/text_summarizer.py`.
    -   **Command:** `uv run --env-file .env src/text_summarizer.py`

## 3. Codebase & Agent Documentation

### `StandaloneTextToSQLAgent`

-   **Files:** `src/analytics_agents/standalone_text_to_sql_agent.py`
-   **Purpose:** These agents translate natural language questions and plan steps into executable SQL queries.
-   **Role:** They use the database schema and the context of the plan to generate accurate SQL. The `TextToSQLAgent` is designed to work within the main graph, while the `StandaloneTextToSQLAgent` can be used as a more direct, self-contained Text-to-SQL engine that follows a ReAct (Reasoning-Action) pattern.

## 4. Tools

The agents are equipped with tools to interact with their environment. The primary tool is for database interaction.

### DuckDB Tool (`src/analytics_agents/tools/duckdb.py`)

-   **Purpose:** Provides the necessary functions for agents to interact with the DuckDB database.
-   **Key Functions:**
    -   `get_all_table()`: Retrieves the names of all tables in the database.
    -   `get_table_schema(table_name: str)`: Returns the `CREATE TABLE` statement for a given table, allowing agents to understand its structure.
    -   `execute_query(query: str)`: Executes a SQL query against the database and returns the result.
