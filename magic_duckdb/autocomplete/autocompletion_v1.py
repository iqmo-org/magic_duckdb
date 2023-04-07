# autocompletion for pre-iPython 8.6.0
# the main limitation here is
from magic_duckdb.autocomplete.common import (
    get_table_names,
    get_column_names,
    sql_expects_tablename,
)

import logging

logger = logging.getLogger("magic_duckdb")


def line_completer(ipython, event):
    # v1 (pre 8.6.0 iPython) only passes the current line, not the entire text. So, line magics are fine but cell magics aren't

    try:
        logger.debug(event)
        command = event.command
        if command != "%dql" and command != "%%dql":
            return

        line = event.line
        symbol = event.symbol
        # text_until_cursor = event.text_until_cursor

        if symbol == "" and line[-1] == " ":
            last_word = line.split(" ")[-2]
            logger.info(last_word)

            if last_word.upper() in sql_expects_tablename:
                return get_table_names(ipython)
        elif symbol[-1] == ".":
            tablename = symbol[:-1]

            columns = get_column_names(ipython, tablename)
            logger.debug(f"Using columns {columns}, {type(columns)}")

            # To complete a word, the current symbol needs to be prefixed
            # To suggest the next word, just return the next word
            results = [f"{symbol}{col}" for col in columns]
            logger.info(results)
            return results

        logger.info(event)
    except Exception:
        logger.exception(f"Error: {event}")


def init_completer(ipython):
    ipython.set_hook("complete_command", line_completer, re_key="[%]+dql.*")
