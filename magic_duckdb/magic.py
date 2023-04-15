import logging
import argparse
from typing import Optional

from traitlets.config.configurable import Configurable
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.core.magic import (
    Magics,
    cell_magic,
    line_magic,
    magics_class,
    no_var_expand,
    needs_local_scope,
)
from IPython.core.getipython import get_ipython
from duckdb import ConnectionException, DuckDBPyConnection

from magic_duckdb.autocomplete.common import init_completers
from magic_duckdb.duckdb_mode import DuckDbMode


logger = logging.getLogger("magic_duckdb")

# Disable autocompletion initialization by setting this to False before loading extension
ENABLE_AUTOCOMPLETE = True
# dbwrapper: To override database logic, replace or monkeypatch this object
dbwrapper: DuckDbMode = DuckDbMode()
# database connection object created via -d (default), -cn (connection string) or -co (connection object)
connection: Optional[DuckDBPyConnection] = None


def _get_obj_from_name(name: str) -> Optional[object]:
    ip = get_ipython()
    return ip.ev(name) if ip is not None else None


@magics_class
class DuckDbMagic(Magics, Configurable):
    # selected via -t. None = Pandas.
    export_function = None

    def __init__(self, shell):
        Configurable.__init__(self, config=shell.config)
        Magics.__init__(self, shell=shell)

        # Add to configurable modules via %config
        self.shell.configurables.append(self)  # type: ignore

    def connect_by_objectname(self, connection_object):
        con: DuckDBPyConnection = _get_obj_from_name(connection_object)  # type: ignore
        if not isinstance(con, DuckDBPyConnection):
            raise ValueError(f"{connection_object} is not a DuckDBPyConnection")
        elif con is None:
            raise ValueError(f"Couldn't find {connection_object}")
        else:
            logger.info(f"Using existing connection: {connection_object}")
            global connection
            connection = con

    def format_wrapper(self, query):
        try:
            from magic_duckdb.extras.sqlformatter import formatsql

            return formatsql(query)
        except Exception as e:
            logger.exception("Error processing")
            raise e

    def ai_wrapper(self, chat: bool, prompt, query):
        try:
            from magic_duckdb.extras import sql_ai

            sql_ai.call_ai(connection, chat, prompt, query)
            return None  # suppress for now, need to figure out formatting
        except Exception as e:
            logger.exception("Error with AI")
            raise e

    @no_var_expand
    @needs_local_scope
    @line_magic("dql")
    @cell_magic("dql")
    @magic_arguments()
    @argument("-l", "--listtypes", help="List the available types", action="store_true")
    @argument(
        "-r",
        "--replace",
        help="Replace any {var}'s from environment",
        action="store_true",
    )
    @argument("-g", "--getcon", help="Return current connection", action="store_true")
    @argument(
        "-d", "--default_connection", help="Use default connection", action="store_true"
    )
    @argument("-f", "--format", help="Format (beautify) SQL input", action="store_true")
    @argument("-ai", help="Format (beautify) SQL input", action="store_true")
    @argument("-aichat", help="Format (beautify) SQL input", action="store_true")
    @argument(
        "-cn",
        "--connection_string",
        help="Connect to a database using the connection string, such as :memory: or file.db",
        nargs=1,
        type=str,
        action="store",
    )
    @argument(
        "-co",
        "--connection_object",
        help="Connect to a database using the connection object",
        nargs=1,
        type=str,
        action="store",
    )
    @argument(
        "-t",
        "--type",
        help="Set the default output type",
        nargs=1,
        type=str,
        action="store",
    )
    @argument(
        "-o",
        "--output",
        help="Write the output to the specified variable",
        nargs=1,
        type=str,
        action="store",
    )
    @argument(
        "-e",
        "--explain",
        help="Explain or Explain Analyze",
        nargs=1,
        type=str,
        action="store",
    )
    @argument("--tables", help="Return table names", action="store_true")
    @argument("rest", nargs=argparse.REMAINDER)
    def execute(self, line: str = "", cell: str = "", local_ns=None):
        global connection

        args = parse_argstring(self.execute, line)
        if args.replace:  # replace {vars} and reparse args
            ns = get_ipython().user_ns  # type: ignore
            line = line.format(**ns)  # type: ignore
            cell = cell.format(**ns) if cell is not None else None  # type: ignore
            args = parse_argstring(self.execute, line)

        rest = " ".join(args.rest)
        query = f"{rest}\n{cell}".strip()
        if "{" in query:
            logger.warning(
                "{ detected in text. Did you mean to use -r to format() {vars}?"
            )

        if args.listtypes:
            return dbwrapper.export_functions
        elif args.getcon:
            return connection
        elif args.format:
            return self.format_wrapper(query)
        elif args.ai:
            return self.ai_wrapper(False, rest, query)
        elif args.aichat:
            return self.ai_wrapper(False, rest, query)

        if args.default_connection:
            connection = dbwrapper.default_connection()
        if args.connection_object:
            self.connect_by_objectname(args.connection_object[0])
        if args.connection_string:
            connection = dbwrapper.connect(args.connection_string[0])
        if args.type:
            if args.type[0] in dbwrapper.export_functions:
                self.export_function = args.type[0]
            else:
                raise ValueError(
                    f"{args.type[0]} not found in {dbwrapper.export_functions}"
                )
        if args.explain:
            explain_function = args.explain[0]
            if explain_function not in dbwrapper.explain_functions:
                raise ValueError(
                    f"{explain_function} not found in {dbwrapper.explain_functions}"
                )
        else:
            explain_function = None

        logger.debug(f"Query = {query}, {len(query)}")

        if query is None or len(query) == 0:
            logger.debug("Nothing to execute")
            return

        if connection is None:
            logger.info("Setting connection to default_connection()")
            connection = dbwrapper.default_connection()

        try:
            if args.tables:
                return connection.get_table_names(query)

            o = dbwrapper.execute(
                query_string=query,
                connection=connection,
                export_function=self.export_function,
                explain_function=explain_function,
            )
            if args.output:
                self.shell.user_ns[args.output[0]] = o  # type: ignore
            return o
        except ConnectionException as e:
            logger.exception(
                f"Unable to connect, connection may already be closed {e}. Setting connection to None"
            )
            connection = None


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip = get_ipython()
    if ip is None:
        raise ValueError("No Ipython found")

    if ENABLE_AUTOCOMPLETE:
        init_completers(ip)

    ip.register_magics(DuckDbMagic)
