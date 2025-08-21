import os
from pathlib import Path

import pytest
from IPython.terminal.embed import InteractiveShellEmbed  # noqa # type: ignore

# ensure subprocesses (like nbclient kernels) get coverage started
os.environ["COVERAGE_PROCESS_START"] = str(
    Path(__file__).resolve().parent / ".coveragerc"
)


@pytest.fixture
def ipshell(tmp_path) -> InteractiveShellEmbed:
    # prevent contention for a single shared in memory database
    # db = tmp_path / "test.db"
    # magic.connection = duckdb.connect(db)

    ipshell = InteractiveShellEmbed()  # noqa
    ipshell.run_cell("%load_ext magic_duckdb")
    ipshell.run_cell("%load_ext magic_duckdb")
    return ipshell
