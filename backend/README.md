# Analytics Agent Playground

This repository contains a playground for building and testing analytics agents.

## Getting Started

1. Install dependencies: `uv sync` && `uv sync --dev`
2. Run the main application: `python main.py`
3. Run the main application using MCP: `python main_mcp.py`
4. Run the tests: `uv run --env-file .env pytest tests/agents/test_analytics_agent_graph.py -s -k test_text_to_sql_agent`

## Overview

The main components are:

- `main.py`: Entry point for the application.
- `main_mcp.py`: Entry point for the application using MCP.
- `src/`: Source code for the analytics agents and tools.
- `tests/`: Tests for the agents and tools.
- `data/`: Sample data for the agents to use.

## Usage

The main application in `main.py` runs a sample analytics agent graph. You can modify this file to experiment with different agent configurations.

The core agent logic is in `src/analytics_agents/analytics_agent_graph.py`. This file defines the LangGraph graph that orchestrates the different agent components.

The individual agent components are in the `src/analytics_agents/` directory. These include agents for planning, text-to-SQL generation, and output classification.

The tools used by the agents are in `src/analytics_agents/tools/`. This includes a DuckDB tool for running SQL queries.

## Documentation

For more detailed documentation, including environment variable configuration and architecture details, please refer to [DOCUMENTATION.md](DOCUMENTATION.md).
