from analytics_agents.tools.tool import Tools


class TestDuckDBTool:
    def test_table_load(self, duckdb_tool: Tools):
        assert duckdb_tool is not None

    def test_execute_query(self, duckdb_tool: Tools):
        data = duckdb_tool.execute("SELECT COUNT(*) FROM customers;")

        print("[+] Customers Count: ", data)

    def test_execute_query_32(self, duckdb_tool: Tools):
        data = duckdb_tool.execute_query("SELECT * FROM customers;")

        print("[+] Customers Count: ", data)

    def test_get_all_tables(self, duckdb_tool: Tools):
        tables = duckdb_tool.get_all_table()

        print("[+] All Tables: ", tables)

    def test_get_table_ddl(self, duckdb_tool: Tools):
        ddl = duckdb_tool.get_table_schema("customers")

        print("[+] Customers DDL: ", ddl)

    def test_get_table_ddl_non_existent(self, duckdb_tool: Tools):
        try:
            _ = duckdb_tool.get_table_schema("non_existent_table")
        except Exception as e:
            print("[+] Caught Exception as expected for non-existent table:", e)
