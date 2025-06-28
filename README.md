# magic_duckdb

DuckDB Cell (%%dql) and Line (%dql) Magics for Jupyter and VSCode

## Motivation

magic_duckdb was created to:

- Provide simple cell/line magics with minimal code and zero dependencies
- Match performance of DuckDB python API
- Be a simple starting point to add other useful features with minimal complexity
- Bundle useful features, like using OpenAI to improve SQL, sql formatting (beautifying) and explain analyze graphics

### Why not the %sql magics (jupysql or ipython-sql)?

The goal of this project is to expose the native features of duckdb, with minimal dependencies, such as exporting to arrow tables or using DuckDB relation objects.

## Simplicity

The goal of this project was to provide minimal line & cell magics for DuckDB in Jupyter notebooks with minimal dependencies and as simply as possible.

The core code is concentrated in two places:

- magic.py: Barebones cell and line magic that parses arguments, and executes statements
- duckdb_mode.py: execute() calls the appropriate method based on the user selected output type.

Features that require additional dependencies, such as Jinja2 for the --jinja2 feature, are imported dynamically.

## Quick Start

```
%pip install magic_duckdb --upgrade --quiet
%load_ext magic_duckdb
%dql select * from range(100)
```

## Usage

```
Connection:
-cn <connection_string>: Create a new connection to a DuckDB. If passed without a query, this changes the global connection, otherwise used just for the current query.
    %dql -cn myfile.db
-co <connection_object>: Use an existing DuckDB Connection. If passed without a query, this changes the global connection, otherwise used just for the current query.
    con = duckdb.connect("somefile.db")
    %dql -co con
-d: Use the duckdb.default_connection. If passed without a query, this changes the global connection, otherwise used just for the current query.
-g | --getcon: Get the current connection
    con = %dql --getcon
--close: Close current connection

Modes:
-t <type> [default: df]: Selects the type for this request. If passed without a query, this changes the global default, otherwise used just for the current query.
-e <explain_mode>: Display the explain plan, or explain analyze, or AST

Options:
-l | --listtypes: Returns a list of available output types, for -t

-j | --jinja2: Process the SQL as a jinja template, using the user_ns environment.
    `%dql -j select * from {{var1}}`
-p | --params: Pass the specified parameter(s) as a SQL parameters
    `%dql -p obj1 select
-o <var>: Stores the resulting output in a variable named <var>
-tp <name> <value>: Pass a kwarg to the type function. Intended to be used to pass parameters to .show(). Must be passed on each call, not saved.
    `%dql -t show -tp max_rows 10 <query>`

Extras:
--tables: Returns tables used by the query
-f: Format the string using npx sql-formatter
Other:
-ai / -aichat: Route request to OpenAI
    %dql -ai Fix selct star frm mytable

```

See [notebooks](https://github.com/iqmo-org/magic_duckdb/tree/main/notebooks) for usage examples.

## Enabling Frame Scanning

To reference objects that are in the Jupyter notebook local scope, enable python_scan_all_frames. This is a DuckDB feature that searches the locals of the frame stack to find dataframes and other objects.
`%dql set python_scan_all_frames = True; `

## Modifying the MAGIC NAME from DQL to SQL

To use %sql and %%sql instead of the default dql, do the following (before loading the extension):

```py
import magic_duckdb
magic_duckdb.MAGIC_NAME = "sql"

%load_ext magic_duckdb
```

Using "sql" as the name may help the LSP automatically choose SQL syntax highlighting.

## Usage Details

- `%dql -t [df | arrow | pl | relation | show | df_markdown] <query>`: Equivalent to - `connection.sql(query).<type>()`. df_markdown requires `tabulate` package.
- `%dql -e [explain | explain_analyze_tree | explain_analyze_json | explain_analyze_draw | analyze | ast_json | ast_tree | ast_draw] <query>`:
  - `explain` is equivalent to `connection.sql(query).explain()`
  - `explain_analyze_*` options enable profiling (`PRAGMA enable_profiling`), and use `connection.sql(query).explain(type='analyze')`
  - `explain_analyze_draw` requires [graphviz](https://graphviz.org/) to be installed on your system, and "dot" or "dot.exe" must be in your PATH or added via `magic.explain_analyze_graphviz.dot_path = 'path_to_dot'`. The graphviz python module must also be installed: `pip install graphviz`
  - The AST options use [json_serialize_sql](https://github.com/duckdb/duckdb/discussions/6922) to describe the SQL. `ast_json` displays the raw json result, `ast_tree` displays an indented tree, and `ast_draw` uses graphviz to draw a graphical version of the tree
- `%dql --format <query>` uses [sql-formatter](https://github.com/sql-formatter-org/sql-formatter). This is a javascript library, so it needs to be installed separately, although it's executed via npx so should be fine as long as you have npx / node in your path.
- `%dql --tables <query>` returns the list of tables used by the query, equivalent to: `duckdb.get_table_names("SELECT * FROM xyz")`
- `%dql [-ai | -aichat] fix <query>` passes the current schema to OpenAI and askes OpenAI to "fix" the query. An OpenAI developer key is required.
- `%dql -r [readfile]` loads the query from the file path specified. Variable expansion is not supported at this time, file path must be a string.

```
            # to set openai key
            from magic_duckdb.extras import sql_ai
            sql_ai.OPENAI_KEY = openai_key
```

## Autocompletion: Work in Progress

There are two different Autocompletion implementations, one for MatcherAPIv2 and the other (pre-ipython 8.6.0) for MatcherAPIv1. The MatcherAPIv2 version is tried first, and if it fails, the MatcherAPIv1 version is loaded. MatcherAPIv1 will not match the entire results of a cell: it's limited to a line by line match.

- Phrase completion: `%dql create <tab>` will show common phrases, such as `CREATE OR REPLACE`
- Pragma completion: `%dql PRAGMA <tab>` will list available pragma's.
- Table completion: `%dql select * from <tab>` will list available tables and Pandas DataFrames. This is triggered by a list of keywords (ie: from) that are expected to be followed. See magic_duckdb.autocomplete.common for the keywords.
- Column completion: `%dql select tablename.<tab> from tablename` will list available tables and Pandas DataFrames for tablename.

Notes:

- VScode will autocomplete differently than Jupyter: For instance, VScode autocompletes on spaces, Jupyter on tabs.
- Column completion only matches table or dataframe names. It doesn't look up aliases or analyze subqueries.
- This is meant as a proof of concept. The next step is to leverage duckdb's existing work: [4921](https://github.com/duckdb/duckdb/pull/4921) and test cases here: [shell-test.py](https://github.com/Mytherin/duckdb/blob/5f75cb90b478434f0a1811af0695ea3a186a67a8/tools/shell/shell-test.py)
- https://jupyter-contrib-nbextensions.readthedocs.io/en/latest/nbextensions/hinterland/README.html: Enable code autocompletion menu for every keypress in a code cell, instead of only calling it with tab.

Autocompletion can be disabled with:

```
from magic_duckdb import magic
magic.ENABLE_AUTOCOMPLETE=False
%load_ext magic_duckdb
```

# Capturing output

Line Magics can be captured with assignment or -o:

```
# These are equivalent:
%dql -o varname <query>
varname = %dql <query>
```

Cell magics can only be captured with -o (var = %%dql doesn't work)

```
%%dql -o varname
<query>
```

To silence a cell, you can stack %%capture:

```
%%capture
%%iql -o bqldf
<query>
```

### Versions

> Python: 3.9.16 (main, Mar 8 2023, 10:39:24) [MSC v.1916 64 bit (AMD64)]
> DuckDB: library_version source_id
> 0 0.8.1-dev51 e84cc1acb8
> Pandas : 2.0.1
> jupysql 0.7.5

### Test Setup

See [benchmarking.ipynb](https://github.com/iqmo-org/magic_duckdb/blob/main/notebooks/benchmarking.ipynb) for the test code.

### Results

|     | name                      |      1 |   1000 | 1000000 | description                                         |
| --- | ------------------------- | -----: | -----: | ------: | --------------------------------------------------- |
| 0   | test_magicddb_pandas      |   3.47 |   4.11 |   291.0 | %dql -t df query                                    |
| 1   | test_duckdb_execute_df    |   3.80 |   3.39 |   281.0 | con.execute(query).df()                             |
| 2   | test_duckdb_execute_arrow |   3.91 |   4.04 |   128.0 | con.execute(query).arrow()                          |
| 3   | test_magicddb_arrow       |   4.10 |   5.38 |   127.0 | %dql -t arrow query                                 |
| 4   | test_duckdb_sql_df        |   6.93 |   7.94 |   318.0 | con.sql(query).df()                                 |
| 5   | test_jupysql              | 321.00 | 256.00 |   547.0 | %config SqlMagic.autopandas = True <br/> %sql query |

Copyright &copy; 2025 Iqmo Corporation
