from pathlib import Path

import pytest
from nbclient import NotebookClient
from nbformat import read

NOTEBOOKS = Path(__file__).resolve().parent.parent / "notebooks"
notebooks = list(
    n
    for n in NOTEBOOKS.glob("*.ipynb")
    if n.name not in ("ai_examples.ipynb", "benchmarking.ipynb")
)


@pytest.mark.parametrize("nb_path", notebooks, ids=[p.name for p in notebooks])
@pytest.mark.asyncio
async def test_notebooks(nb_path: Path, tmp_path: Path):
    import os

    os.environ["TESTDBDIR"] = str(tmp_path)

    with nb_path.open() as f:
        nb = read(f, as_version=4)

    client = NotebookClient(nb)

    # run asynchronously, in the same interpreter as pytest
    await client.async_execute()
