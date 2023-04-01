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

from typing import Optional

# dbwrapper: To override database logic, replace or monkeypatch this object
dbwrapper: DuckDbMode = DuckDbMode()

# Disables extra print statements
debug_msgs = True


def _get_obj_from_name(name: str) -> Optional[object]:
    ip = get_ipython()
    if ip is None:
        print("No ipython found")
        return None
    else:
        return ip.ev(name)


@magics_class
class DuckDbMagic(Magics, Configurable):
    # database connection object
    # created via -d (default), -cn (connection string) or -co (connection object)
    connection: Optional[DuckDBPyConnection] = None

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
                    return self.connection

                # handle commands with no options
                elif cmd == "-d":
                    self.connection = dbwrapper.default_connection()
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
                        if debug_msgs:
                            print(f"Using existing connection: {connection_object}")
                    self.connection = con
                    line = everything_after_cmd_option
                elif cmd == "-cn":
                    connection_string = cmd_option
                    if debug_msgs:
                        print(f"Connecting to {connection_string}")
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

        # Done handling arguments, run the statement(s)... if there is one
        if line is None and cell is not None and len(cell) > 0:
            query = cell
        else:
            query = line

        if query is None or len(query) == 0:
            return

        if self.connection is None:
            if debug_msgs:
                print("Setting connection to default_connection()")
            self.connection = dbwrapper.default_connection()
        try:
            return dbwrapper.execute(
                query_string=query,
                connection=self.connection,
                export_function=self.export_function,
            )
        except ConnectionException as e:
            print(
                f"Unable to connect, connection may already be closed {e}. Setting connection to None"
            )
            self.connection = None


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(DuckDbMagic)
