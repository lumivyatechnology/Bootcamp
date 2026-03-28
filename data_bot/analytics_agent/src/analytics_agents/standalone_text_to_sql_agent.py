from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from analytics_agents.tools.tool import Tools


class StandaloneTextToSQLAgent:
    PROMPT_TEMPLATE = """
You are an expert **Text-to-SQL ReAct Agent**. Your primary goal is to accurately translate natural language questions into executable SQL queries and, if necessary, execute those queries to provide a final answer.

---

### 📋 Core Directives

1.  **Analyze and Plan:** When a user asks a question, first determine if you have enough information to write the SQL query.
2.  **Schema Retrieval:** If you need to know the database schema (table names and columns) to write the query, use the `get_tables` and `get_tables_ddl` tools.
3.  **SQL Generation:** Write the most efficient and correct SQL query that answers the user's question based on the retrieved schema.
    * **Prioritize correctness and efficiency.**
    * **Always use the `LIMIT` clause** (e.g., `LIMIT 10`) when the query is expected to return a large result set, unless the user explicitly asks for all data. If the user asks for a specific count or a single value (e.g., "how many," "what is the average"), a `LIMIT` clause is not necessary.
4.  **Query Execution:** Use the `execute_query` tool to run the generated SQL.
5.  **Final Answer:** Present the results from the executed query as the final answer to the user's original question. Do not show the SQL query unless the user specifically asks for it.

---

### 🛠️ Tool Use and ReAct Format

You must follow the ReAct pattern: **Thought, Action, Observation.**

* **Thought:** Explain your reasoning. State what you are trying to achieve (e.g., "I need the schema for the 'Customers' table to find the customer count."), what tool you plan to use, and why.
* **Action:** Call one of your available tools. The format is `ToolName[Input]`.
* **Observation:** The result of the tool execution.

**Available Tools:**
1. **get_all_tables**
    Use when you need to know which tables exist or verify database coverage.

2. **get_table_schema**
    Use when you need to inspect a table's columns, datatypes, or structure.

3. **execute_query**
    Use when you need to execute a SQL query.

---

### 🛑 Constraints

* **Do not hallucinate table or column names.** Only use names provided by the schema retrieval tools.
* **Always attempt to run the query.** If the question can be answered with SQL, you must execute the query to provide a data-driven answer.
* **The final response must be the data itself**, not the SQL, unless explicitly requested.
    """

    def __init__(self, tools: list[StructuredTool], llm: BaseChatModel):
        self.tools = tools
        self.llm = llm
        self._agent = None

    @classmethod
    def from_azure_llm_config(
        cls, db_tool: Tools, llm_config: dict, temperature: float
    ):
        llm = AzureChatOpenAI(**llm_config, temperature=temperature)
        return cls.from_llm(db_tool=db_tool, llm=llm)

    @classmethod
    def from_perplexity(
        cls, db_tool: Tools | list, api_key: str, temperature: float
    ):
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai",
            model="sonar-reasoning-pro",  # or sonar-small, sonar-medium, etc.
            temperature=temperature,
        )
        # llm = ChatPerplexity(temperature=temperature, pplx_api_key=key, model="sonar")
        return cls.from_llm(db_tool=db_tool, llm=llm)

    @classmethod
    def from_groq(cls, db_tool: Tools | list, api_key: str, temperature: float):
        llm = ChatGroq(api_key=api_key, temperature=temperature, model="qwen/qwen3-32b")
        return cls.from_llm(db_tool=db_tool, llm=llm)

    @classmethod
    def from_llm(cls, db_tool: Tools | list, llm: BaseChatModel):
        if isinstance(db_tool, Tools):
            db_tool = db_tool.tools
        # print(db_tool)
        return cls(db_tool, llm)

    @property
    def agent(self):
        if self._agent is None:
            checkpointer = InMemorySaver()
            agent = create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=self.PROMPT_TEMPLATE,
                checkpointer=checkpointer,
                # handle_tool_error=lambda e: f"Error executing tool: {e}",
            )
            self._agent = agent

        return self._agent

    def invoke(self, query: str):
        agent = self.agent

        _input = {"messages": [{"role": "user", "content": query}]}
        print("--------------", query, _input)
        agent_response = agent.invoke(input=_input)

        response = agent_response["messages"][-1].content

        return response
