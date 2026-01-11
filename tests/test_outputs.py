from unittest.mock import patch

import pytest
from duckdb import ConnectionException
from IPython.terminal.embed import InteractiveShellEmbed  # noqa

from magic_duckdb.duckdb_mode import DuckDbMode
from magic_duckdb.magic import DuckDbMagic


def test_output_variable(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    m.execute(line="-o myvar select 42 as val")
    assert ipshell.user_ns["myvar"].iat[0, 0] == 42


def test_tables(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    result = m.execute(line="--tables select * from range(10)")
    assert result is not None


def test_type_param_int(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    with patch("magic_duckdb.magic.dbwrapper") as mock_wrapper:
        mock_wrapper.export_functions = ["df"]
        mock_wrapper.execute.return_value = None
        m.execute(line="-tp limit 10 select 1")
        _, kwargs = mock_wrapper.execute.call_args
        assert kwargs["export_kwargs"] == {"limit": 10}


def test_type_param_string(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    with patch("magic_duckdb.magic.dbwrapper") as mock_wrapper:
        mock_wrapper.export_functions = ["df"]
        mock_wrapper.execute.return_value = None
        m.execute(line="-tp name value select 1")
        _, kwargs = mock_wrapper.execute.call_args
        assert kwargs["export_kwargs"] == {"name": "value"}


def test_invalid_type(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    with pytest.raises(ValueError, match="not found"):
        m.execute(line="-t invalid_type select 1")


def test_invalid_explain(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    with pytest.raises(ValueError, match="not found"):
        m.execute(line="-e invalid_explain select 1")


def test_set_default_type_empty_query(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    m.execute(line="-t arrow")
    assert m.default_export_function == "arrow"


def test_connect_by_objectname_invalid_type(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    ipshell.user_ns["not_a_connection"] = "just a string"
    with pytest.raises(ValueError, match="not a DuckDBPyConnection"):
        m.connect_by_objectname("not_a_connection")


def test_connection_exception(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    m.execute(line="-d")
    with patch(
        "magic_duckdb.duckdb_mode.execute_db", side_effect=ConnectionException("test")
    ):
        m.execute(line="select 1")
    assert m.connection is None


def test_explain_analyze_draw(ipshell: InteractiveShellEmbed):
    pytest.importorskip("graphviz")
    m = DuckDbMagic(shell=ipshell)
    result = m.execute(line="-e explain_analyze_draw select * from range(10)")
    assert result is not None


def test_ast_draw(ipshell: InteractiveShellEmbed):
    pytest.importorskip("graphviz")
    m = DuckDbMagic(shell=ipshell)
    result = m.execute(line="-e ast_draw select * from range(10)")
    assert result is not None


def test_ast_tree(ipshell: InteractiveShellEmbed):
    m = DuckDbMagic(shell=ipshell)
    result = m.execute(line="-e ast_tree select * from range(10)")
    assert result is not None


def test_duckdb_mode_defaults():
    mode = DuckDbMode()
    result = mode.execute(
        query_string="select 42 as val", connection=None, export_function=None
    )
    assert result.iat[0, 0] == 42


def test_duckdb_mode_execute_exception():
    mode = DuckDbMode()
    with pytest.raises(Exception) as exc_info:
        mode.execute(query_string="select * from nonexistent_table_xyz")
    assert "query_string=" in str(exc_info.value.__notes__)


def test_invalid_ast_mode():
    mode = DuckDbMode()
    with pytest.raises(ValueError, match="Unexpected AST mode"):
        mode.explain_analyze(
            query_string="select 1",
            connection=mode.default_connection(),
            export_function="df",
            explain_function="ast_invalid",
        )
