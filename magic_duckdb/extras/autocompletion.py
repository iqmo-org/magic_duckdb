import re
from typing import List, Optional
from IPython.core.completer import IPCompleter

from magic_duckdb import magic
from IPython.core.completer import (
    SimpleMatcherResult,
    SimpleCompletion,
    context_matcher,
    CompletionContext,
)
import logging

logger = logging.getLogger("magic_duckdb")


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

    def convert_to_return(
        self, completions: List[str], matched_fragment: Optional[str] = None
    ):

        completions = [SimpleCompletion(text=t, type="duckdb") for t in completions]

        # It took way too many hours to figure out that matched_fragment="" was needed here
        # Otherwise the results get suppressed
        r = SimpleMatcherResult(
            completions=completions,
            suppress=True,
            matched_fragment=matched_fragment,
            ordered=True,
        )
        return r

    @context_matcher()  # forces v2 api
    def line_completer(self, event: CompletionContext) -> SimpleMatcherResult:
        # if not %dql, returns nothing
        # if ends with a sql_expects_tablename phrase, then returns just table names
        # if ends in a period, checks to see if prefix is a tablename, and if so, returns column names
        # otherwise returns all sql phrases and tablenames
        # https://github.com/ipython/ipython/blob/a418f38c4f96de1755701041fe5d8deffbf906db/IPython/core/completer.py#L563

        try:

            logger.info(f"{type(event)}")

            if hasattr(event, "full_text"):
                text = event.full_text
            else:
                logger.info("No full_text, nothing to do")
                return self.convert_to_return([])

            if not text.startswith("%dql") and not text.startswith("%%dql"):
                return self.convert_to_return([])

            # if hasattr(event, "command"):
            #    command = event.command
            # else:
            #    logger.info(f"{event}")
            #    #command = None

            if hasattr(event, "token"):
                token = event.token
            else:
                logger.info(f"{event}")
                token = ""

            line_after = text[4:].strip()

            logger.debug(f"{event}, {type(event)}")

            if token is not None and token.endswith("."):
                # VScode is ignoring or suppressing completions after a period.
                # get the word preceding the period
                tablename = token[:-1]

                columns = get_column_names(tablename)
                logger.debug(f"Using columns {columns}")
                return self.convert_to_return(columns, matched_fragment="")

            # if the last phrase should be followed by a table name, return the list of tables
            elif self.expects_table_pat.match(line_after) is not None:
                # logger.debug("Expects table name")
                names = get_table_names()
                return self.convert_to_return(names)

            # default: return all phrases and tablenames
            allp = self.all_phrases + get_table_names()
            return self.convert_to_return(allp)

        except Exception:
            logger.exception(f"Error completing {event}")
            return self.convert_to_return([])


def init_completer(ipython):

    dql_completer = DqlCustomCompleter(shell=ipython, greedy=True, attr_matches=True)

    # Development notes:
    # This took a while to figure out, partially because of the multiple APIs and signatures involved.
    # Read the links below to better understand how this all really works.
    #
    # add_s or add_re calls with two parameters:
    # callable(self, event)
    # The event contains: 2023-04-02 07:14:42,857 - magic_duckdb - INFO - namespace(line='%dql asda', symbol='asda', command='%dql', text_until_cursor='%dql asda')
    #
    # set_custom_completer was an alternative method of adding, which seemed inconsistent within VScode... but it passed three parameters:
    # self, ipcompleter, linebuffer, cursor_pos
    #
    # the third method was add_hook('custom_complete'...)
    # which is a synonym for add_s or add_re
    #
    # https://github.com/ipython/ipython/pull/13745
    # https://ipython.readthedocs.io/en/stable/api/generated/IPython.core.completer.html
    # https://raw.githubusercontent.com/ipython/ipython/main/IPython/core/completer.py
    # https://ipython.org/ipython-doc/rel-0.12.1/api/generated/IPython.utils.strdispatch.html#IPython.utils.strdispatch.StrDispatch.s_matches
    # https://github.com/ipython/ipython/blob/9663a9adc4c87490f1dc59c8b6f32cdfd0c5094a/IPython/core/tests/test_completer.py
    #
    # Also, annoyingly, VScode inserts some completions in: https://stackoverflow.com/questions/72824819/vscode-autocomplete-intellisense-in-jupyter-notebook-when-starting-string-lit

    # ipython.Completer.custom_completers.add_s(
    #    "%dql", dql_completer.line_completer, priority=-1
    # )

    # ipython.Completer.suppress_competing_matchers = True
    # ip.Completer.custom_completers.add_re(r'(?si).*dql.*', dql_completer.complete)
    # ip.set_custom_completer(dql_completer.complete, 0)

    ipython.Completer.custom_matchers.insert(0, dql_completer.line_completer)
    ipython.use_jedi = False

    # ipython.Completer.suppress_competing_matchers = True
