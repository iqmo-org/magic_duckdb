import re
from typing import List, Optional
from IPython.core.completer import IPCompleter

from magic_duckdb import magic
from magic_duckdb.logging_init import init_logging

logger = init_logging()


def get_table_names() -> List[str]:
    # TODO: Cache?
    try:
        if magic.connection is not None:
            tables = magic.connection.sql("show tables")
            if tables is None:
                return []
            else:
                return list(tables.df()["name"])
        else:
            return []
    except Exception:
        logger.debug("Unable to get table names")
        return []


def get_column_names(tablename: str) -> List[str]:
    # TODO: Cache?
    try:
        if magic.connection is not None:
            columns = magic.connection.sql(f"pragma table_info('{tablename}')")
            if columns is None:
                return []
            else:
                names = list(columns.df().astype(str)["name"])
                # logger.debug(names)
                return names
        else:
            return []
    except Exception:
        logger.debug("Unable to get column names")
        return []


pragma_before = re.compile(r"(?si).*pragma\s*")


class DqlCustomCompleter(IPCompleter):
    # In VSCode, text_until_cursor only returns the current line... not the entire cell/block. As far as I can tell, we'd need an extension for vscode, which seems like a bit too much work

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    pragmas = []

    sql_expects_tablename = [
        "UNION",
        "UNION ALL",
        "UNION ALL BY NAME",
        "UNION BY NAME",
        "JOIN",
        "INNER JOIN",
        "LEFT JOIN",
        "RIGHT JOIN",
        "FULL JOIN",
        "LEFT OUTER JOIN",
        "RIGHT OUTER JOIN",
        "FROM",
        "INTO",
    ]

    sql_phrases = [
        "PRAGMA",
        "SELECT",
        "WHERE",
        "GROUP BY",
        "ORDER BY",
        "LIMIT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "ALTER",
        "DROP",
        "TRUNCATE",
        "TABLE",
        "DATABASE",
        "INDEX",
        "VIEW",
        "FUNCTION",
        "PROCEDURE",
        "TRIGGER",
        "AND",
        "OR",
        "NOT",
        "BETWEEN",
        "LIKE",
        "IN",
        "NULL",
        "IS",
        "EXISTS",
        "COUNT",
        "SUM",
        "MIN",
        "MAX",
        "AVG",
        "DISTINCT",
        "AS",
        "CREATE TABLE",
        "CREATE OR REPLACE TABLE",
        "CREATE TABLE IF NOT EXISTS",
        "CREATE VIEW",
    ]

    pragma_phrases = [
        "PRAGMA version",
        "PRAGMA database_list",
        "PRAGMA database_size",
        "PRAGMA show_tables",
        "PRAGMA show_tables_expanded",
        "PRAGMA table_info('",
        "PRAGMA functions",
        "PRAGMA collations",
        "PRAGMA enable_progress_bar",
        "PRAGMA disable_progress_bar",
        "PRAGMA enable_profiling",
        "PRAGMA disable_profiling",
        "PRAGMA disable_optimizer",
        "PRAGMA enable_optimizer",
        "PRAGMA enable_verification",
        "PRAGMA disable_verification",
        "PRAGMA verify_parallelism",
        "PRAGMA disable_verify_parallelism",
        "PRAGMA force_index_join",
        "PRAGMA force_checkpoint",
    ]

    all_phrases = sql_expects_tablename + sql_phrases + pragma_phrases
    lastword_pat = re.compile(r"(?si)(^|.*[\s])(\S+)\.")
    expects_table_pat = re.compile(r"(?si).*from")

    def line_completer(self, event) -> Optional[List[str]]:
        # if not %dql, returns nothing
        # if ends with a sql_expects_tablename phrase, then returns just table names
        # if ends in a period, checks to see if prefix is a tablename, and if so, returns column names
        # otherwise returns all sql phrases and tablenames

        try:
            command = event.command
            text = event.text_until_cursor
            # symbol = event.symbol
            # line = event.line
            line_after = text[4:].strip()

            if command != "%dql":
                # Should never occur
                logger.info(f"Unexpected command {command}")
                return None

            logger.debug(f"{event}, {type(event)}")

            if line_after[-1] == ".":

                # VScode is ignoring or suppressing completions after a period.
                # get the word preceding the period
                m = self.lastword_pat.match(line_after)
                if m is not None:
                    tablename = m.group(2)
                    columns = get_column_names(tablename)
                    return columns

                else:
                    # logger.debug("Matching failure: {line_after}")
                    return []

            # if the last phrase should be followed by a table name, return the list of tables
            elif self.expects_table_pat.match(line_after) is not None:
                # logger.debug("Expects table name")
                return get_table_names()

            # default: return all phrases and tablenames
            return self.all_phrases + get_table_names()
        except Exception:
            logger.exception(f"Error completing {event}")
            return []


def init_completer(ipython):

    dql_completer = DqlCustomCompleter(shell=ipython, greedy=True, attr_matches=True)

    # Development notes:
    # add_s or add_re calls with two parameters:
    # callable(self, event)
    # The event contains: 2023-04-02 07:14:42,857 - magic_duckdb - INFO - namespace(line='%dql asda', symbol='asda', command='%dql', text_until_cursor='%dql asda')

    # set_custom_completer was an alternative method of adding, which seemed inconsistent within VScode... but it passed three parameters:
    # self, ipcompleter, linebuffer, cursor_pos
    #
    # the third method was add_hook('custom_complete'...)
    # which is a synonym for add_s or add_re
    # https://ipython.readthedocs.io/en/stable/api/generated/IPython.core.completer.html
    # https://raw.githubusercontent.com/ipython/ipython/main/IPython/core/completer.py
    # https://ipython.org/ipython-doc/rel-0.12.1/api/generated/IPython.utils.strdispatch.html#IPython.utils.strdispatch.StrDispatch.s_matches
    # https://github.com/ipython/ipython/blob/9663a9adc4c87490f1dc59c8b6f32cdfd0c5094a/IPython/core/tests/test_completer.py

    ipython.Completer.custom_completers.add_s(
        "%dql", dql_completer.line_completer, priority=0
    )
    # ipython.Completer.suppress_competing_matchers = True
    # ip.Completer.custom_completers.add_re(r'(?si).*dql.*', dql_completer.complete)
    # ip.set_custom_completer(dql_completer.complete, 0)
