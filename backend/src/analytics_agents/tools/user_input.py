from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class UserOpinionInput(BaseModel):
    question: str = Field(
        ..., description="The SQL query to be executed on the DuckDB database."
    )


class UserInputTool:
    """Tool for receiving user input."""

    def get_user_opinion(self, question: str, *args, **kwargs) -> str:
        print("[+] Question by agent: ", question)
        opinion = input("[+] Enter your opinion: ")
        return opinion

    @property
    def tools(self) -> list[StructuredTool]:
        return [
            StructuredTool(
                name="user_opinion",
                description="A tool for asking the user for their opinion on a specific question.",
                func=self.get_user_opinion,
                args_schema=UserOpinionInput,
                handle_tool_error=lambda e: f"Error executing query: {e}",
            ),
        ]
