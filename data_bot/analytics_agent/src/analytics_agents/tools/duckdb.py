import duckdb
import json
import threading
import pandas as pd
from analytics_agents.tools.tool import Tools
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class ExecuteQueryInput(BaseModel):
    query: str = Field(..., description="The SQL query to be executed on the database.")


class GetTableSchemaInput(BaseModel):
    table_name: str = Field(
        ..., description="The name of the table to retrieve the Schema for."
    )


class EmptyInput(BaseModel):
    """No input parameters required."""

    pass


class TableInfo(BaseModel):
    name: str = Field(..., description="The name of the table.")
    path: str = Field(..., description="The file path of the table.")
    format: str = Field(
        ..., description="The format of the table (e.g., CSV, Parquet)."
    )


class DuckDBTool(Tools):
    def __init__(self, tables: list[TableInfo]):
        self._connection = None
        self.tables = tables
        self.db_lock = threading.Lock()

    def execute(self, query: str, *args, **kwargs):
        with self.db_lock:
            return self.connection.execute(query).fetchall()

    def execute_query(self, query: str) -> str:
        try:
            print("[*] Executing query: ", query)
            data = self.execute(query=query)
            return json.dumps(data[:100])
        except Exception as e:
            print("[!] Error while executing query: ", query)
            print("[!] Error: ", e)
            return str(e)

    def execute_df(self, query: str):
        with self.db_lock:
            return self.connection.execute(query).fetchdf()

    @property
    def connection(self):
        if self._connection is None:
            self._connection = duckdb.connect()
        return self._connection

    @staticmethod
    def _df_to_create_statement(df: pd.DataFrame, table_name: str) -> str:
        column_lines = []

        for _, row in df.iterrows():
            col_def = f"    {row['column_name']} {row['column_type']}"

            # NULL / NOT NULL
            if str(row["null"]).upper() == "NO":
                col_def += " NOT NULL"

            # DEFAULT value
            if row.get("default") not in (None, "None", ""):
                col_def += f" DEFAULT {row['default']}"

            # Extra (e.g., AUTO_INCREMENT)
            if row.get("extra") not in (None, "None", ""):
                col_def += f" {row['extra']}"

            # Key handling (Primary Key, Unique, etc.)
            if row.get("key") == "PRI":
                col_def += " PRIMARY KEY"

            col_def += ","
            column_lines.append(col_def)

        # Remove the last comma
        column_lines[-1] = column_lines[-1].rstrip(",")

        create_sql = f"CREATE TABLE {table_name} (\n" + "\n".join(column_lines) + "\n);"
        return create_sql

    def load_tables(self):
        for table in self.tables:
            query = f"""
            CREATE TABLE {table.name} AS SELECT * FROM read_{table.format}('{table.path}'); 
            """
            self.execute(query)

    def get_all_table(self, *args, **kwargs) -> str:
        tables = self.execute("SHOW TABLES")
        # Cleaning table names
        tables = [t[0] for t in tables]
        return ",".join(tables)

    def get_table_schema(self, table_name: str, *args, **kwargs) -> str:
        print("[*] Fetching Schema for table: ", table_name)
        column_info_df = self.execute_df(f"DESCRIBE SELECT * FROM {table_name};")
        # ddl = self.connection.execute(f"PRAGMA table_info('{table_name}');").fetchall()
        if column_info_df.empty:
            raise Exception(f"Table '{table_name}' does not exist.")

        try:
            ddl = self._df_to_create_statement(column_info_df, table_name)
        except Exception as e:
            print("[!] Table does not exist: ", table_name)
            print("[!] column_info: ", column_info_df)
            raise e
        return ddl

    @property
    def tool_get_all_table(self):
        return StructuredTool(
            name="get_all_tables",
            description="A tool to retrieve all table names present in database.",
            func=self.get_all_table,
            args_schema=EmptyInput,
            handle_tool_error=lambda e: f"Error fetching all tables: {e}",
        )

    @property
    def tool_get_table_schema(self):
        return StructuredTool(
            name="get_table_create_statement",
            description="A tool to retrieve the schema of a specific table present in database.",
            func=self.get_table_schema,
            args_schema=GetTableSchemaInput,
            handle_tool_error=lambda e: f"Error retriving schema: {e}",
        )

    @property
    def tool_execute_query(self):
        return StructuredTool(
            name="excute_query",
            description="A tool for executing SQL queries against a database.",
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
