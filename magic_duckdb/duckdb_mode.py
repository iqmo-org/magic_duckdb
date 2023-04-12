import duckdb

from typing import Optional, List

from magic_duckdb.extras.explain_analyze_graphviz import draw_graphviz


def execute_db(query: str, con: duckdb.DuckDBPyConnection):
    """Simple wrapper to allow alternative implementations or wrappers to be inserted"""
    return con.sql(query)


class DuckDbMode:
    """Lightweight wrapper to separate duckdb specific logic from the Magic.
    Goal here is to expose all of DuckDB's goodness, but also make it easy to extend or replace this.
    """

    export_functions: List[str] = [
        "df",
        "arrow",
        "pl",
        "describe",
        "explain",
        "show",
        "relation",
        "explain_analyze_tree",
        "explain_analyze_json",
        "explain_analyze_draw",
        "analyze [alias for explain_analyze_draw]",
    ]

    def default_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.default_connection

    def connect(self, conn_string: str) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(conn_string)

    def explain_analyze(
        self, query_string: str, connection: duckdb.DuckDBPyConnection, export_function
    ):
        # query_tree

        if export_function == "explain_analyze_tree":
            execute_db("PRAGMA enable_profiling=query_tree", connection)
            r = execute_db(query_string, connection)
            t = r.explain(type="analyze")  # type: ignore
            return t
        elif export_function == "explain_analyze_json":
            execute_db("PRAGMA enable_profiling=json", connection)
            r = execute_db(query_string, connection)
            j = r.explain(type="analyze")  # type: ignore

            return j
        else:
            execute_db("PRAGMA enable_profiling=json", connection)
            r = execute_db(query_string, connection)
            j = r.explain(type="analyze")  # type: ignore
            return draw_graphviz(j)

    def execute(
        self,
        query_string: str,
        connection: Optional[duckdb.DuckDBPyConnection] = None,
        export_function: Optional[str] = None,
    ):
        if connection is None:
            connection = self.default_connection()

        if export_function is None:
            export_function = self.export_functions[0]

        if export_function.startswith("analyze"):
            export_function = "explain_analyze_draw"

        if "explain_analyze" in export_function:
            return self.explain_analyze(query_string, connection, export_function)
        else:
            try:
                r = execute_db(query_string, connection)
            except Exception as e:
                raise ValueError(f"Error executing {query_string} in DuckDB") from e

            if r is None:
                return None
            elif export_function == "relation":
                return r
            else:
                export_function = export_function
                f = getattr(r, export_function)
                return f()
