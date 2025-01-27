from IPython.terminal.embed import InteractiveShellEmbed
import pytest

def create_shell() -> object:
    ipshell = InteractiveShellEmbed()
    ipshell.run_cell("%load_ext magic_duckdb")
    return ipshell


def test_read_exists():
    ipshell = create_shell()
    er = ipshell.run_cell("%dql -r tests/test_query_file.sql")  
    
    assert er.error_in_exec is None
    assert len(er.result) == 10


def test_read_jinja():
    ipshell = create_shell()
    ipshell.run_cell("RANGELEN = 15")

    er = ipshell.run_cell("%dql -j -r tests/test_query_jinja.sql")  
    
    assert er.error_in_exec is None
    assert len(er.result) == 15


def test_read_doesnt_exist():
    ipshell = create_shell()

    er = ipshell.run_cell("%dql -r thisfile_doesnt_exist.sql")
    
    assert isinstance(er.error_in_exec, FileNotFoundError)