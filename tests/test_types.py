from IPython.terminal.embed import InteractiveShellEmbed

from magic_duckdb import duckdb_mode


def create_shell() -> object:
    ipshell = InteractiveShellEmbed()
    ipshell.run_cell("%load_ext magic_duckdb")
    return ipshell


def test_types():
    # Not expected to occur, but should gracefully handle
    ipshell = create_shell()

    execution_result = ipshell.run_cell("%dql --listtypes")
    o = execution_result.result
    print(o)
    assert "df" in o
    for otype in o:
        execution_result2 = ipshell.run_cell(f"%dql -t {otype} PRAGMA version")
        assert execution_result2.error_in_exec is None

        outobj = execution_result2.result
        assert otype == "show" or outobj is not None


def test_explains():
    # Not expected to occur, but should gracefully handle
    ipshell = create_shell()

    for e in duckdb_mode.DuckDbMode.explain_functions:
        if "draw" not in e:
            er = ipshell.run_cell(f"%dql -e {e} select * from range(10)")
            assert er.error_in_exec is None
            o = er.result
            assert o is not None
