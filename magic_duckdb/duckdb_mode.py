import duckdb

from typing import Optional, List, Dict, Tuple
import json
from magic_duckdb.extras.explain_analyze_graphviz import draw_graphviz
from magic_duckdb.extras.ast_graphviz import ast_draw_graphviz, ast_tree
from IPython.display import Markdown


def execute_db(
    *, query: str, con: duckdb.DuckDBPyConnection, execute: bool = False, params=None
):
    """Simple wrapper to allow alternative implementations or wrappers to be inserted
    execute = False: returns a Relation object"""

    if execute or params is not None:
        return con.execute(query, parameters=params)
    else:
        return con.sql(query)


class DuckDbMode:
    """Lightweight wrapper to separate duckdb specific logic from the Magic.
    Goal here is to expose all of DuckDB's goodness, but also make it easy to extend or replace this.
    """

    export_functions: List[str] = [
        "df",
        "df_markdown",
        "arrow",
        "pl",
        "describe",
        "show",
        "relation",
    ]

    explain_functions: List[str] = [
        "explain",
        "explain_analyze_tree",
        "explain_analyze_json",
        "explain_analyze_draw",
        "analyze",
        "ast_json",
        "ast_draw",
        "ast_tree",
    ]

    def default_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.default_connection

    def connect(self, conn_string: str) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(conn_string)

    def explain_analyze(
        self,
        query_string: str,
        connection: duckdb.DuckDBPyConnection,
        export_function,
        explain_function,
    ):
        # query_tree

        if explain_function == "explain_analyze_tree" or explain_function == "analyze":
            execute_db(
                query="PRAGMA enable_profiling=query_tree", con=connection, execute=True
            )
            r = execute_db(query=query_string, con=connection, execute=False)
            t = r.explain(type="analyze")  # type: ignore
            print(t)
            return t
        elif explain_function == "explain_analyze_json":
            execute_db(
                query="PRAGMA enable_profiling=json", con=connection, execute=True
            )
            r = execute_db(query=query_string, con=connection, execute=False)
            j = r.explain(type="analyze")  # type: ignore
            return j
        elif explain_function == "explain_analyze_draw":
            execute_db(
                query="PRAGMA enable_profiling=json", con=connection, execute=True
            )
            r = execute_db(query=query_string, con=connection, execute=False)
            j = r.explain(type="analyze")  # type: ignore
            return draw_graphviz(j)
        elif explain_function == "explain":
            r = execute_db(query=query_string, con=connection, execute=False)
            j = r.explain()  # type: ignore
            print(j)
            return j
        elif explain_function.startswith("ast"):
            r = connection.execute(
                "select json_serialize_sql($1::varchar)", [query_string]
            )
            df = r.df()
            json_str = df.iat[0, 0]
            json_obj = json.loads(json_str)
            if explain_function == "ast_json":
                return json_obj
            elif explain_function == "ast_draw":
                return ast_draw_graphviz(json_obj)
            elif explain_function == "ast_tree":
                return ast_tree(json_obj)
            else:
                raise ValueError(f"Unexpected AST mode {explain_function}")

        else:
            raise ValueError(f"Unexpected explain mode {explain_function}")

    def execute(
        self,
        query_string: str,
        connection: Optional[duckdb.DuckDBPyConnection] = None,
        export_function: Optional[str] = None,
        explain_function: Optional[str] = None,
        params: Optional[List[object]] = None,
        export_kwargs: Dict[str, object] = {}
    ) -> Tuple[object, bool]:
        if connection is None:
            connection = self.default_connection()

        if export_function is None:
            export_function = self.export_functions[0]

        if explain_function is not None:
            return self.explain_analyze(
                query_string, connection, export_function, explain_function
            )
        else:
            try:
                if export_function in ["show", "describe", "relation"]:
                    # Result must be a relation, not a connection
                    execute = False
                else:
                    execute = True
                r = execute_db(
                    query=query_string, con=connection, params=params, execute=execute
                )
            except Exception as e:
                raise ValueError(f"Error executing {query_string} in DuckDB") from e

            if r is None or ("relation" == export_function):
                return r
            else:
                if export_function == "df_markdown":
                    md = r.df().to_markdown(index=False)
                    mdd = Markdown(md)
                    return mdd
                    
                else:
                    export_function = export_function
                    f = getattr(r, export_function)
                    
                    return f(**export_kwargs)
