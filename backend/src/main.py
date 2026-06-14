import uvicorn
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="analytics_agent",
        description="Analytics agent that have access to phone data",
        graph=agent,  # the graph object from your langgraph import
        config={"callbacks": [langfuse_callback]},
    ),
    path="/copilotkit",  # the endpoint you'd like to serve your agent on
)


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


def main():
    """Run the uvicorn server."""
    uvicorn.run(
        "main:app",  # the path to your FastAPI file, replace this if its different
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )


if __name__ == "__main__":
    main()
