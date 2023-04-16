# Autocompletion using iPython 8.6.0 or higher
# 8.6.0 introduced several enhancements to IPCompleter.
# An important change is being able to complete against the entire cell text
# for a cell magic. In v1 (pre 8.6.0), could only complete against the current line.

import re
from typing import List, Optional
from IPython.core.completer import IPCompleter

from magic_duckdb.autocomplete.common import (
    get_table_names,
    get_column_names,
    pragma_phrases,
    sql_phrases,
    sql_expects_tablename,
)
from IPython.core.completer import (
    SimpleMatcherResult,
    SimpleCompletion,
    context_matcher,
    CompletionContext,
)

import logging

logger = logging.getLogger(__name__)

pragma_before = re.compile(r"(?si).*pragma\s*")


class DqlCustomCompleter(IPCompleter):
    # In VSCode, text_until_cursor only returns the current line... not the entire cell/block. As far as I can tell, we'd need an extension for vscode, which seems like a bit too much work

    def __init__(self, *args, **kwargs):
        self.ipython = kwargs.get("shell")
        super().__init__(*args, **kwargs)

    all_phrases = sql_expects_tablename + sql_phrases + pragma_phrases
    lastword_pat = re.compile(r"(?si)(^|.*[\s])(\S+)\.")
    expects_table_pat = re.compile(r"(?si).*from")

    def convert_to_return(
        self, completions: List[str], matched_fragment: Optional[str] = None
    ) -> SimpleMatcherResult:
        simple_completions = [
            SimpleCompletion(text=t, type="duckdb") for t in completions
        ]

        # It took way too many hours to figure out that matched_fragment="" was needed here
        # Otherwise the results get suppressed
        r = SimpleMatcherResult(
            completions=simple_completions,
            suppress=True,
            matched_fragment=matched_fragment,
            ordered=True,
        )
        return r

    @context_matcher()  # type: ignore
    def line_completer(self, event: CompletionContext) -> SimpleMatcherResult:
        # if not %dql, returns nothing
        # if ends with a sql_expects_tablename phrase, then returns just table names
        # if ends in a period, checks to see if prefix is a tablename, and if so, returns column names
        # otherwise returns all sql phrases and tablenames
        # https://github.com/ipython/ipython/blob/a418f38c4f96de1755701041fe5d8deffbf906db/IPython/core/completer.py#L563

        try:
            # logger.info(event)
            logger.debug(f"{type(event)}, {self.ipython}, {event}")

            # return self.convert_to_return(["SELECT"], event.token)

            if hasattr(event, "full_text"):
                text = event.full_text
            else:
                logger.debug(f"No full_text, nothing to do {event}")
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
                token = ""

            line_after = text[4:].strip()

            logger.debug(f"{event}, {type(event)}")

            if token is not None and token.endswith("."):
                # VScode is ignoring or suppressing completions after a period.
                # get the word preceding the period
                tablename = token[:-1]
                logger.debug(tablename)

                # TODO: Deal with Aliases and SubQueries (xyz as abc)
                columns = get_column_names(self.ipython, tablename)
                logger.debug(f"Using columns {columns}")
                return self.convert_to_return(columns, matched_fragment="")

            # if the last phrase should be followed by a table name, return the list of tables
            elif self.expects_table_pat.match(line_after) is not None:
                names = get_table_names(self.ipython)
                if len(names) == 0:
                    names = ["No Tables or DataFrames Found"]
                logger.debug(f"Expects table name, returning {names}")

                return self.convert_to_return(names, matched_fragment=event.token)

            # default: return all phrases and tablenames
            allp = self.all_phrases + get_table_names(self.ipython)
            return self.convert_to_return(allp, event.token)

        except Exception:
            logger.exception(f"Error completing {event}")
            return self.convert_to_return([])


def init_completer(ipython):
    dql_completer = DqlCustomCompleter(
        shell=ipython, greedy=True
    )  # , attr_matches=True)

    # Development notes:
    # This took a while to figure out, partially because of the multiple APIs and signatures involved.
    #
    # What I learned:
    # The ipython (get_ipython) environment has a Completer object
    # Completer is an IPCompleter
    # You can extend this completer in several ways, including:
    # - Wrapping it
    # - Registering a custom_completer, of which there are several ways: add_hook, Completer.custom_completers.add_s and add_re, or customer_completers.insert
    #
    # ipython 8.6.0 introduced new a v2 version of the API, for completers decorated with @context_matcher(), this API uses a different signature
    # see ipython.core.completer for more info
    # The main advantage of v2 is getting the full cell text, not just current cell
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

    ipython.Completer.custom_completer_matcher = dql_completer.line_completer
    # ipython.Completer.custom_matchers.insert(0, dql_completer.line_completer)
    # ipython.use_jedi = False

    # ipython.Completer.suppress_competing_matchers = True
