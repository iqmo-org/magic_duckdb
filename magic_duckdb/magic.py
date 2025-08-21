import argparse
import logging
from pathlib import Path
from typing import Dict, Optional

# from IPython.core.getipython import get_ipython
from duckdb import ConnectionException, DuckDBPyConnection
from IPython.core.magic import (
    Magics,
    cell_magic,
    line_magic,
    magics_class,
    needs_local_scope,
    no_var_expand,
)
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from traitlets.config.configurable import Configurable

from . import MAGIC_NAME
from .duckdb_mode import DuckDbMode
from .extras import jinja_template

logger = logging.getLogger("magic_duckdb")

# dbwrapper: To override database logic, replace or monkeypatch this object
dbwrapper: DuckDbMode = DuckDbMode()


def _get_obj_from_name(shell, name: str) -> Optional[object]:
    return shell.ev(name) if shell is not None else None


@magics_class
class DuckDbMagic(Magics, Configurable):
    # selected via -t. None = Pandas.
    default_export_function = None
    # database connection object created via -d (default), -cn (connection string) or -co (connection object)
    connection: Optional[DuckDBPyConnection] = None

    def __init__(self, shell, attr_matches: bool = True):
        Configurable.__init__(self, config=shell.config)
        Magics.__init__(self, shell=shell)

        # Add to configurable modules via %config
        self.shell.configurables.append(self)  # type: ignore

    def connect_by_objectname(self, connection_object):
        con: DuckDBPyConnection = _get_obj_from_name(self.shell, connection_object)  # type: ignore
        if not isinstance(con, DuckDBPyConnection):
            raise ValueError(f"{connection_object} is not a DuckDBPyConnection")
        elif con is None:
            raise ValueError(f"Couldn't find {connection_object}")
        else:
            logger.info("Using existing connection: %s", connection_object)

            self.connection = con

    def format_wrapper(self, query: str):
        try:
            from magic_duckdb.extras.sqlformatter import formatsql

            return formatsql(query)
        except Exception as e:
            logger.exception("Error processing")
            raise e

    def ai_wrapper(self, chat: bool, prompt: str, query: str):
        try:
            from magic_duckdb.extras import sql_ai

            sql_ai.call_ai(self.connection, chat, prompt, query)
            return None  # suppress for now, need to figure out formatting
        except Exception as e:
            logger.exception("Error with AI")
            raise e

    @no_var_expand
    @needs_local_scope
    @line_magic(MAGIC_NAME)
    @cell_magic(MAGIC_NAME)
    @magic_arguments()
    @argument("-l", "--listtypes", help="List the available types", action="store_true")
    @argument("-g", "--getcon", help="Return current connection", action="store_true")
    @argument(
        "-d", "--default_connection", help="Use default connection", action="store_true"
    )
    @argument("-f", "--format", help="Format (beautify) SQL input", action="store_true")
    @argument("-ai", help="OpenAI", action="store_true")
    @argument("-aichat", help="OpenAI Chat", action="store_true")
    @argument(
        "-cn",
        "--connection_string",
        help="Connect to a database using the connection string, such as :memory: or file.db",
        nargs=1,
        type=str,
        action="store",
    )
    @argument(
        "-r",
        "--readfile",
        help="Read SQL from a file",
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
        help="Explain or Explain Analyze or AST",
        nargs=1,
        type=str,
        action="store",
    )
    @argument("--tables", help="Return table names", action="store_true")
    @argument("--close", help="Close database connection", action="store_true")
    @argument("-j", "--jinja2", help="Apply Jinja2 Template", action="store_true")
    @argument(
        "-p",
        "--param",
        dest="queryparams",
        help="Params from user_ns",
        action="append",
    )
    @argument(
        "-tp",
        "--type_param",
        dest="type_param",
        nargs=2,
        help="Params to pass to the Output Type function, given as a name/value pair",
        action="append",
    )
    @argument("rest", nargs=argparse.REMAINDER)
    def execute(self, line: str = "", cell: str = "", local_ns=None):
        cell = "" if cell is None else cell
        line = "" if line is None else line
        user_ns: Dict[str, object] = self.shell.user_ns  # type: ignore

        args = parse_argstring(self.execute, line)

        rest = " ".join(args.rest)

        if args.readfile:
            sql_file_path = Path(args.readfile[0])
            query = sql_file_path.read_text()
        else:
            query = f"{rest}\n{cell}".strip()

        if args.jinja2:
            query = jinja_template.apply_template(query, user_ns)

        if args.listtypes:
            return dbwrapper.export_functions
        elif args.getcon:
            return self.connection
        elif args.format:
            return self.format_wrapper(query)
        elif args.ai:
            return self.ai_wrapper(False, rest, query)
        elif args.aichat:
            return self.ai_wrapper(False, rest, query)
        elif args.close:
            if self.connection is not None:
                try:
                    self.connection.close()
                finally:
                    self.connection = None

        export_kwargs = {}

        if args.type_param:
            for n, v in args.type_param:
                if str(v).isdigit():
                    v = int(v)
                export_kwargs[n] = v

        thisconnection = None
        if args.default_connection:
            thisconnection = dbwrapper.default_connection()
        if args.connection_object:
            thisconnection = self.connect_by_objectname(args.connection_object[0])
        if args.connection_string:
            thisconnection = dbwrapper.connect(args.connection_string[0])

        if args.type and args.type[0] not in dbwrapper.export_functions:
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

        logger.debug("Query = %s", query)
        if query is None or len(query) == 0:
            if args.type:
                # print("Default format changed: {args.type[0]}")
                self.default_export_function = args.type[0]
            if thisconnection is not None:
                # print(f"Default connection changed: ", "default_connection()" if args.default_connection else args.connection_object[0] if args.connection_object else args.connection_string)
                self.connection = thisconnection
            logger.debug("Nothing to execute")
            return

        if thisconnection is None:
            if self.connection is None:
                # print("Default connection changed: default_connection()")
                self.connection = dbwrapper.default_connection()
            thisconnection = self.connection

        try:
            if args.queryparams:
                queryparams = [user_ns[p] for p in args.queryparams]
            else:
                queryparams = None

            if args.tables:
                return thisconnection.get_table_names(query)  # type: ignore

            o = dbwrapper.execute(
                query_string=query,
                connection=thisconnection,
                export_function=(
                    args.type[0] if args.type else self.default_export_function
                ),
                explain_function=explain_function,
                params=queryparams,
                export_kwargs=export_kwargs,
            )
            if args.output:
                user_ns[args.output[0]] = o

            return o

        except ConnectionException:
            logger.exception(
                "Unable to connect, connection may already be closed. Setting connection to None"
            )
            self.connection = None
