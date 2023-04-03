import pathlib
from subprocess import Popen, PIPE, STDOUT
import logging

logger = logging.getLogger("magic_duckdb")

language_mode = "postgresql"
indentStyle = "standard"
keywordCase = "upper"
linesBetweenQueries = 0
logicalOperatorNewline = "after"
denseOperators = "true"


def formatsql(query: str):
    logger.debug(f"Formatting {query}")
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

    p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT, shell=True)
    stdout_data = p.communicate(input=query.encode())[0]

    print(stdout_data.decode())
    return stdout_data.decode()
