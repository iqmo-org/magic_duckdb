import duckdb
from pandas import DataFrame
import numpy as np
from magic_duckdb import magic
from magic_duckdb.extras.autocompletion import DqlCustomCompleter
from types import SimpleNamespace


def simple_autocomplete_tests():
    with duckdb.connect() as con:

        some_tablename = "tablenamereallylong"
        # create some tables
        simpledf = DataFrame(np.random.randn(10, 20))  # type: ignore # noqa

        con.sql(f"CREATE OR REPLACE TABLE {some_tablename} as select * from simpledf")
        con.sql("create table sometablename2 as select * from range(10) t(my_column_1)")
        con.sql(
            "create table longtablenameishardtomakeup as select * from range(10) t(d)"
        )
        con.sql("show tables").df()

        # test autocompletion
        magic.connection = con
        completer = DqlCustomCompleter()

        # completer finds the table names
        event = SimpleNamespace(
            line="%dql s", symbol="s", command="%dql", text_until_cursor="%dql s"
        )
        results = completer.line_completer(event)
        # display(results)
        assert results is not None
        assert some_tablename in [r.text for r in results["completions"]]
        assert "SELECT" in [r.text for r in results["completions"]]

        event = SimpleNamespace(
            line="%dql s",
            symbol="s",
            command="%dql",
            text_until_cursor="%dql select * from",
        )
        results = completer.line_completer(event)
        assert results is not None
        assert some_tablename in [r.text for r in results["completions"]]
        assert "SELECT" not in [r.text for r in results["completions"]]

        # Tablename doesn't exist
        event = SimpleNamespace(
            line="%dql s",
            symbol="s",
            command="%dql",
            text_until_cursor="%dql select blah.",
        )
        results = completer.line_completer(event)
        assert results is not None
        assert len(results) == 0

        event = SimpleNamespace(
            line="%dql tablenamereallylong.",
            symbol="tablenamereallylong.",
            command="%dql",
            text_until_cursor="%dql  tablenamereallylong.",
        )
        results = completer.line_completer(event)
        assert results is not None
        assert "19" in [r.text for r in results["completions"]]

        event = SimpleNamespace(
            line="%dql select tablenamereallylong. from tablenamereallylong",
            symbol="tablenamereallylong.",
            command="%dql",
            text_until_cursor="%dql select sometablename2.",
        )
        results = completer.line_completer(event)
        assert results is not None
        assert "my_column_1" in [r.text for r in results["completions"]]

        event = SimpleNamespace(
            line="%dql s",
            symbol="s",
            command="%dql",
            text_until_cursor=f"%dql select {some_tablename}.",
        )
        results = completer.line_completer(event)
        assert results is not None
        assert "19" in [r.text for r in results["completions"]]
        # Tablename doesn't exist
