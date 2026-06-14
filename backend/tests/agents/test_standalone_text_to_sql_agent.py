import pytest

from analytics_agents.standalone_text_to_sql_agent import StandaloneTextToSQLAgent
from analytics_agents.tools.tool import Tools


class TestTextToSQLAgent:
    @pytest.mark.parametrize(
        "query, temperature",
        [
            # ("How many customers are there in the customers table?", 1),
            # ("Give me all the table create statements", 1),
            ("Give me customer with most orders", 1)
            # ("Give the table create statements of 'customers', 'geolocation'", 1),
            # ("How many rows are there in students table", 0.7)
        ],
    )
    def test_text_to_sql_agent(
        self, db_tool: Tools, llm_config: dict, query: str, temperature: float
    ):
        text_to_sql_agent = StandaloneTextToSQLAgent.from_azure_llm_config(
            db_tool, llm_config, temperature
        )
        agent = text_to_sql_agent.agent

        _input = {"messages": [{"role": "user", "content": query}]}
        agent_response = agent.invoke(input=_input)

        response = agent_response["messages"][-1].content

        print("[+] TextToSQL Agent Test Completed.")
        print("[+] AI Agent response: ", response)
