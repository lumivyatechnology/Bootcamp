import json
import threading
import psycopg2
import pandas as pd

from analytics_agents.tools.tool import Tools
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class ExecuteQueryInput(BaseModel):
    query: str = Field(..., description="The SQL query to be executed on the database.")


class GetTableSchemaInput(BaseModel):
    table_name: str = Field(
        ..., description="The name of the table to retrieve the schema for."
    )


class EmptyInput(BaseModel):
    """No input parameters required."""

    pass


class PostgresTool(Tools):
    def __init__(self, connection_params: dict):
        """
        connection_params example:
        {
            "host": "localhost",
            "port": 5432,
            "dbname": "mydb",
            "user": "postgres",
            "password": "secret"
        }
        """
        self._connection = None
        self.connection_params = connection_params
        self.db_lock = threading.Lock()

    @property
    def connection(self):
        if self._connection is None:
            self._connection = psycopg2.connect(**self.connection_params)
            self._connection.autocommit = True
        return self._connection

    def execute(self, query: str):
        with self.db_lock:
            with self.connection.cursor() as cur:
                cur.execute(query)
                if cur.description:
                    return cur.fetchall()
                return []

    def execute_query(self, query: str) -> str:
        try:
            print("[*] Executing query:", query)
            data = self.execute(query)
            return json.dumps(data[:100], default=str)
        except Exception as e:
            print("[!] Error executing query:", query)
            print("[!] Error:", e)
            return str(e)

    def execute_df(self, query: str) -> pd.DataFrame:
        with self.db_lock:
            return pd.read_sql_query(query, self.connection)

    def get_all_table(self, *args, **kwargs) -> str:
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        tables = self.execute(query)
        return ",".join(t[0] for t in tables)

    def get_table_schema(self, table_name: str, *args, **kwargs) -> str:
        print("[*] Fetching schema for table:", table_name)

        query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = '{table_name}'
        ORDER BY ordinal_position;
        """

        df = self.execute_df(query)

        if df.empty:
            raise Exception(f"Table '{table_name}' does not exist.")

        return self._df_to_create_statement(df, table_name)

    @staticmethod
    def _df_to_create_statement(df: pd.DataFrame, table_name: str) -> str:
        columns = []

        for _, row in df.iterrows():
            col = f"    {row['column_name']} {row['data_type']}"

            if row["is_nullable"] == "NO":
                col += " NOT NULL"

            # if row["column_default"]:
            #     col += f" DEFAULT {row['column_default']}"

            columns.append(col)

        return f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"

    @property
    def tool_get_all_table(self):
        return StructuredTool(
            name="get_all_tables",
            description="Retrieve all table names present in the Postgres database.",
            func=self.get_all_table,
            args_schema=EmptyInput,
            handle_tool_error=lambda e: f"Error fetching tables: {e}",
        )

    @property
    def tool_get_table_schema(self):
        return StructuredTool(
            name="get_table_create_statement",
            description="Retrieve CREATE TABLE statement for a Postgres table.",
            func=self.get_table_schema,
            args_schema=GetTableSchemaInput,
            handle_tool_error=lambda e: f"Error retrieving schema: {e}",
        )

    @property
    def tool_execute_query(self):
        return StructuredTool(
            name="execute_query",
            description="Execute SQL queries against Postgres.",
            func=self.execute_query,
            args_schema=ExecuteQueryInput,
            handle_tool_error=lambda e: f"Error executing query: {e}",
        )

    @property
    def tools(self):
        return [
            self.tool_execute_query,
            self.tool_get_all_table,
            self.tool_get_table_schema,
        ]
