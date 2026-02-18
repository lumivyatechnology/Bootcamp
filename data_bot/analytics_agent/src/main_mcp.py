from config import settings

from analytics_agents.standalone_text_to_sql_agent import (
    StandaloneTextToSQLAgent,
)

from mcp import ClientSession
from mcp.client.streamable_http import StreamableHTTPTransport, streamable_http_client
from langchain_mcp_adapters.tools import load_mcp_tools
import uuid

import asyncio

# HTTP-based MCP transport
transport = StreamableHTTPTransport(
    url="http://localhost:8000/mcp",
)


async def run_text_to_sql_agent(question: str, thread_id: str = "user-123-session-1"):
    """
    Runs the Text-to-SQL agent using MCP DuckDB tools.

    This function is safe to call from:
    - FastAPI
    - CopilotKit AG-UI
    - Any async runtime
    """
    # read, write = await transport.open()
    async with streamable_http_client(url="http://localhost:8000/mcp") as (
        read,
        write,
        _,
    ):
        # async with transport as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Load MCP tools
            mcp_tools = await load_mcp_tools(session)
            # mcp_tools = mcp_tools.tools

            # Create agent
            agent = StandaloneTextToSQLAgent.from_groq(
                api_key=settings.GROQ_API_KEY,
                temperature=0,
                duckdb_tool=mcp_tools,
            )

            # Invoke agent (await if async)
            _input = {"messages": [{"role": "user", "content": question}]}
            result = await agent.agent.ainvoke(
                _input, config={"configurable": {"thread_id": thread_id}}
            )

            result = result["messages"][-1].content

        return result


async def test():
    res = await run_text_to_sql_agent(
        "What is the best phone in the market with respect to specs?"
    )
    print(res)


# asyncio.run(test())


async def run():
    thread_id = str(uuid.uuid4())
    while True:
        question = input("Enter your question: ")
        if question == "new":
            thread_id = str(uuid.uuid4())
        if question == "exit":
            break
        answer = await run_text_to_sql_agent(question, thread_id)
        print(answer)


asyncio.run(run())
