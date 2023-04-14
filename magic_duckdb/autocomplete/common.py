import logging
from typing import List

from magic_duckdb import magic
from pandas import DataFrame

logger = logging.getLogger("magic_duckdb")

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


def get_table_names(ipython) -> List[str]:
    try:
        user_keys = [k for k, v in ipython.user_ns.items() if isinstance(v, DataFrame)]

        if magic.connection is not None:
            tables = magic.connection.sql("show tables")
            if tables is None:
                return user_keys
            else:
                return list(tables.df()["name"]) + user_keys
        else:
            logger.info(user_keys)
            return user_keys
    except Exception:
        logger.exception("Unable to get table names")
        return []


def get_column_names(ipython, tablename: str) -> List[str]:
    try:
        # check if an object
        # o = ipython.ev(tablename)
        o = ipython.user_ns.get(tablename)
        if o is None and magic.connection is not None:
            columns = magic.connection.sql(f"pragma table_info('{tablename}')")
            if columns is None:
                logger.debug("None columns")
                return []
            else:
                names = list(columns.df().astype(str)["name"])
                logger.debug(f"Column names {names}")
                return names
        elif o is not None:
            if isinstance(o, DataFrame):
                return list(o.columns)
            else:
                logger.debug(f"{tablename} in namespace, but not a DataFrame {type(o)}")
                return []
        else:
            return []
    except Exception:
        logger.exception("Unable to get column names")
        return []


def init_completers(ip):
    try:
        from magic_duckdb.autocomplete.autocompletion_v2 import init_completer

        init_completer(ipython=ip)
    except Exception:
        logger.debug(
            "Unable to initialize autocompletion_v2. iPython 8.6.0+ is required. Trying v1 completer"
        )
        try:
            from magic_duckdb.autocomplete.autocompletion_v2 import init_completer

            init_completer(ipython=ip)
        except Exception:
            logger.debug("Unable to initialize autocompletion_v1")
