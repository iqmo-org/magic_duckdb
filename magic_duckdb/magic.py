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

from magic_duckdb.duckdb_mode import DuckDbMode


logger = logging.getLogger("magic_duckdb")

# dbwrapper: To override database logic, replace or monkeypatch this object
dbwrapper: DuckDbMode = DuckDbMode()

ENABLE_AUTOCOMPLETE = False

connection: Optional[DuckDBPyConnection] = None


def _get_obj_from_name(name: str) -> Optional[object]:
    ip = get_ipython()
    return ip.ev(name) if ip is not None else None


@magics_class
class DuckDbMagic(Magics, Configurable):
    # database connection object
    # created via -d (default), -cn (connection string) or -co (connection object)

    # selected via -t. None = Pandas.
    export_function = None

    def __init__(self, shell):
        Configurable.__init__(self, config=shell.config)
        Magics.__init__(self, shell=shell)

        # Add ourself to the list of module configurable via %config
        self.shell.configurables.append(self)  # type: ignore

    def connect_by_objectname(self, connection_object):
        con: DuckDBPyConnection = _get_obj_from_name(connection_object)  # type: ignore
        if not isinstance(con, DuckDBPyConnection):
            raise ValueError(f"{connection_object} is not a DuckDBPyConnection")
        if con is None:
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
    @argument("-l", "--listtype", help="List the available types", action="store_true")
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
    @argument("rest", nargs=argparse.REMAINDER)
    def execute(self, line: str = "", cell: str = "", local_ns=None):
        global connection

        args = parse_argstring(self.execute, line)
        # Grab rest of line
        rest = " ".join(args.rest)
        query = f"{rest}\n{cell}".strip()

        logger.debug(f"Query = {query}, {len(query)}")
        if args.listtype:
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
            export_function = args.type[0]
            if export_function in dbwrapper.export_functions:
                self.export_function = export_function
            else:
                raise ValueError(
                    f"{export_function} not found in {dbwrapper.export_functions}"
                )

        if query is None or len(query) == 0:
            logger.debug("Nothing to execute")
            return

        if connection is None:
            logger.info("Setting connection to default_connection()")
            connection = dbwrapper.default_connection()

        try:
            o = dbwrapper.execute(
                query_string=query,
                connection=connection,
                export_function=self.export_function,
            )
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
        try:
            from magic_duckdb.extras.autocompletion import init_completer

            init_completer(ipython=ip)
        except Exception:
            logger.exception(
                "Unable to initialize autocompletion. iPython 8.x is required."
            )

    ip.register_magics(DuckDbMagic)
