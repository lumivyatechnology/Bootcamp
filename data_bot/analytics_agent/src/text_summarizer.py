import json
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from config import settings

# Load environment variables from .env file
load_dotenv()


class SummaryOutput(BaseModel):
    summary: str = Field(..., description="A concise summary of the provided text.")
    title: str = Field(..., description="A catchy title for the summary.")


class SummaryInput(BaseModel):
    text: str = Field(..., description="The text to be summarized.")


TEMPERATURE = 0.7

TEMPLATE = """
You are an expert text summarizer. Given the following text, provide a concise summary and a catchy title.

## Input:
{text}

## Output format:
{output_format_instruction}
"""


LLM_CONFIG = json.loads(os.getenv("LLM_CONFIG", '{}'))


def get_summarizer_chain(text: str) -> SummaryOutput:
    output_parser = PydanticOutputParser(pydantic_object=SummaryOutput)

    output_format_instructions = output_parser.get_format_instructions()

    print("[*] Output Format Instructions: ", output_format_instructions)

    prompt = PromptTemplate(
        template=TEMPLATE,
        input_variables=["text"],
        partial_variables={"output_format_instruction": output_format_instructions},
    )

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        temperature=TEMPERATURE,
        model="llama-3.1-8b-instant",
    )
    # llm = AzureChatOpenAI(**LLM_CONFIG, temperature=TEMPERATURE)

    print(
        "[*] Prompt: ",
        TEMPLATE.format(
            output_format_instruction=output_format_instructions, text=text
        ),
    )

    chain = prompt | llm | output_parser

    return chain


def summarize_text(text: str) -> SummaryOutput:
    summarizer_chain = get_summarizer_chain(text)

    summary = summarizer_chain.invoke({"text": text})

    return summary


def main():
    sample_text = (
        "Artificial Intelligence (AI) has rapidly evolved over the past decade, "
        "transforming various industries and aspects of daily life. From healthcare "
        "to finance, AI technologies are being leveraged to improve efficiency, "
        "accuracy, and decision-making processes. Machine learning algorithms, "
        "natural language processing, and computer vision are some of the key areas "
        "driving this revolution. As AI continues to advance, ethical considerations "
        "and regulatory frameworks are becoming increasingly important to ensure "
        "responsible development and deployment of these technologies."
    )

    summary = summarize_text(sample_text)

    print("\n\n[+] Output Summary: \n")

    print("[+] Summary Title: ", summary.title)
    print("[+] Summary: ", summary.summary)


if __name__ == "__main__":
    main()
