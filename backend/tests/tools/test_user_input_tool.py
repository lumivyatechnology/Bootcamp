
import pytest
from analytics_agents.tools.user_input import UserInputTool

class TestUserInputTool:
    @pytest.mark.parametrize(
            "question", 
            [
                ("What is your opinion things happening in your life?", 1),
            ]
    )
    def test_user_opinion(self, user_input_tool: UserInputTool, question):
        opinion = user_input_tool.get_user_opinion(question)
        print(f"[+] Users Opinion: {opinion}")

