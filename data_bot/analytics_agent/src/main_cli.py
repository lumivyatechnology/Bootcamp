import asyncio
import uuid

from analytics_agents.standalone_text_to_sql_agent import StandaloneTextToSQLAgent
from config import settings
from config.dependencies import db_tool
from config.langfuse import langfuse_callback

standalone_text_to_sql_agent = StandaloneTextToSQLAgent.from_groq(
    # llm_config=settings.LLM_CONFIG,
    api_key=settings.GROQ_API_KEY,
    db_tool=db_tool,
    temperature=0,
)
agent = standalone_text_to_sql_agent.agent


async def run_in_thread(question: str, thread_id: str):
    _input = {"messages": [{"role": "user", "content": question}]}
    result = await agent.ainvoke(
        _input, config={
            "configurable": {"thread_id": thread_id},
            "callbacks": [langfuse_callback],
        }
    )
    result = result["messages"][-1].content
    return result


async def run():
    thread_id = str(uuid.uuid4())
    while True:
        question = input("Enter your question: ")
        if question == "new":
            thread_id = str(uuid.uuid4())
        if question == "exit":
            break
        answer = await run_in_thread(question, thread_id)
        print(answer)

if __name__ == "__main__":
    asyncio.run(run())
