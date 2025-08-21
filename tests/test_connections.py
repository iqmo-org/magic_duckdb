from IPython.terminal.embed import InteractiveShellEmbed  # noqa #type: ignore

from magic_duckdb.magic import DuckDbMagic


def test_none_inputs(ipshell: InteractiveShellEmbed):
    # Not expected to occur, but should gracefully handle
    m = DuckDbMagic(shell=ipshell)

    result = m.execute(line="-cn :memory:", cell=None)

    result = m.execute(line="-d PRAGMA version", cell=None)
    assert result is not None

    result = m.execute(line=None, cell="PRAGMA version")
    assert result is not None

    result = m.execute(line="", cell="PRAGMA version")
    assert result is not None


def test_cn_file(ipshell: InteractiveShellEmbed):
    # Not expected to occur, but should gracefully handle
    m = DuckDbMagic(shell=ipshell)

    filename = "test.db"

    m.execute(line=f"-cn {filename}")
    df = m.execute("PRAGMA database_list")

    assert len(df) == 1
    assert df.at[0, "file"].endswith(filename)


def test_co_file(ipshell: InteractiveShellEmbed, tmp_path):
    # Not expected to occur, but should gracefully handle
    m = DuckDbMagic(shell=ipshell)

    fname = "test.db"
    fpath = tmp_path / fname
    ipshell.user_ns["filename"] = fpath

    ipshell.run_cell("import duckdb")
    ipshell.run_cell("fcon = duckdb.connect(filename)")

    m.execute(line="-co fcon")
    df = m.execute(line="PRAGMA database_list")

    assert len(df) == 1

    assert df.at[0, "file"].endswith(fname)

    o = m.execute(line="-g")
    df2 = o.execute("PRAGMA database_list").df()
    assert df2.at[0, "file"].endswith(fname)


def test_close(ipshell: InteractiveShellEmbed, tmp_path):
    m = DuckDbMagic(shell=ipshell)

    # No exception here
    m.execute(line="--close")

    fname = "test.db"
    fpath = tmp_path / fname

    m.execute(line=f"-cn {fpath}")
    df = m.execute(line="PRAGMA database_list")

    assert len(df) == 1
    assert df.at[0, "file"].endswith(fname)

    m.execute(line="--close")
    df2 = m.execute(line="PRAGMA database_list")
    assert df2.at[0, "name"] == "memory"
