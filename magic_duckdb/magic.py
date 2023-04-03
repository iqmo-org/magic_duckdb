import re
from traitlets.config.configurable import Configurable
from IPython.core.magic_arguments import magic_arguments
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
from magic_duckdb.autocompletion import init_completer
from typing import Optional
import logging

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

    pattern = re.compile(r"(?si)\s*(\-\S+)(\s+(\S+))?(\s+(.*))?\s*")

    @no_var_expand
    @needs_local_scope
    @line_magic("dql")
    @cell_magic("dql")
    @magic_arguments()
    def execute(
        self, line: Optional[str] = None, cell: Optional[str] = None, local_ns=None
    ):
        global connection

        # Handle arguments
        # TODO: Replace this with argparser or equivalent.
        if line is not None:
            # If arguments (-something) passed, then handle them
            m = self.pattern.match(line)
            if m is not None:  # a command was found
                cmd = m.group(1)
                everything_after_cmd = m.group(2)
                cmd_option = m.group(3)
                everything_after_cmd_option = (
                    m.group(5) if len(m.groups()) >= 5 else None
                )

                # handle explicits
                if cmd == "--listtypes":
                    return dbwrapper.export_functions
                elif cmd == "--getcon":
                    return connection

                # handle commands with no options
                elif cmd == "-d":
                    connection = dbwrapper.default_connection()
                    line = everything_after_cmd

                # handle commands with options
                elif cmd == "-co":
                    connection_object = cmd_option
                    con: DuckDBPyConnection = _get_obj_from_name(connection_object)  # type: ignore
                    if not isinstance(con, DuckDBPyConnection):
                        raise ValueError(
                            f"{connection_object} is not a DuckDBPyConnection"
                        )

                    if con is None:
                        raise ValueError(f"Couldn't find {connection_object}")
                    else:
                        logger.info(f"Using existing connection: {connection_object}")
                    connection = con
                    line = everything_after_cmd_option
                elif cmd == "-cn":
                    connection_string = cmd_option
                    logger.info(f"Connecting to {connection_string}")
                    con = dbwrapper.connect(connection_string)
                    line = everything_after_cmd_option
                elif cmd == "-t":
                    export_function = cmd_option
                    if export_function in dbwrapper.export_functions:
                        self.export_function = export_function
                    else:
                        raise ValueError(
                            f"{export_function} not found in {dbwrapper.export_functions}"
                        )

                    line = everything_after_cmd_option

        query = cell if (cell is not None and len(cell) == 0) else line

        if query is None or len(query) == 0:
            logger.debug("Nothing to execute")
            return

        if connection is None:
            logger.info("Setting connection to default_connection()")
            connection = dbwrapper.default_connection()
        try:
            return dbwrapper.execute(
                query_string=query,
                connection=connection,
                export_function=self.export_function,
            )
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
        init_completer(ipython=ip)

    ip.register_magics(DuckDbMagic)
