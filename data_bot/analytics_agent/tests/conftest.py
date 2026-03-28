import json
import os

import pytest
from dotenv import load_dotenv

from analytics_agents.tools.duckdb import DuckDBTool, TableInfo
from analytics_agents.tools.tool import Tools
from analytics_agents.tools.user_input import UserInputTool
from utils.answer_saver import AnswerSaver


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv(dotenv_path=".env")


@pytest.fixture(scope="session")
def llm_config():
    llm_config = json.loads(os.getenv("LLM_CONFIG"))
    return llm_config


TABLES = [
    {"name": "customers", "path": "olist_customers_dataset.csv", "format": "csv"},
    {"name": "geolocation", "path": "olist_geolocation_dataset.csv", "format": "csv"},
    {"name": "order_items", "path": "olist_order_items_dataset.csv", "format": "csv"},
    {
        "name": "order_payments",
        "path": "olist_order_payments_dataset.csv",
        "format": "csv",
    },
    {
        "name": "order_reviews",
        "path": "olist_order_reviews_dataset.csv",
        "format": "csv",
    },
    {"name": "orders", "path": "olist_orders_dataset.csv", "format": "csv"},
    {"name": "products", "path": "olist_products_dataset.csv", "format": "csv"},
    {"name": "sellers", "path": "olist_sellers_dataset.csv", "format": "csv"},
    {
        "name": "product_category_translation",
        "path": "product_category_name_translation.csv",
        "format": "csv",
    },
]

# TABLES = [
#     {"name": "brands", "path": "brands.csv", "format": "csv"},
#     {"name": "cpu_models", "path": "cpu_models.csv", "format": "csv"},
#     {"name": "operating_systems", "path": "operating_systems.csv", "format": "csv"},
#     {"name": "phones", "path": "phones.csv", "format": "csv"},
#     {"name": "phone_specs", "path": "phone_specs.csv", "format": "csv"},
# ]


@pytest.fixture(scope="session")
def user_input_tool():
    return UserInputTool()


@pytest.fixture(scope="session")
def answer_saver():
    directory = "data/answers"
    answer_saver = AnswerSaver(directory=directory)
    return answer_saver
