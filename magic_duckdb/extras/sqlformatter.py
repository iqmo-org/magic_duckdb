import logging
import pathlib
from subprocess import PIPE, STDOUT, Popen

logger = logging.getLogger("magic_duckdb")

language_mode = "postgresql"
indentStyle = "standard"  # noqa: N816
keywordCase = "upper"  # noqa: N816
linesBetweenQueries = 0  # noqa: N816
logicalOperatorNewline = "after"  # noqa: N816
denseOperators = "true"  # noqa: N816


def formatsql(query: str):
    logger.debug("Formatting: %s", query)
    config = f'"keywordCase": "{keywordCase}", "indentStyle": "{indentStyle}", "linesBetweenQuerys": {linesBetweenQueries}, "logicalOperatorNewline": "{logicalOperatorNewline}", "denseOperators": "{denseOperators}"'
    config = "{" + config + "}"

    pathlib.Path("format_config.json").write_text(config)

    cmd = [
        "npx",
        "sql-formatter",
        "-l",
        language_mode,
        "--config",
        "format_config.json",
    ]

    p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT, shell=True)  # noqa: S602
    stdout_data = p.communicate(input=query.encode())[0]

    print(stdout_data.decode())  # noqa: T201
    return stdout_data.decode()
