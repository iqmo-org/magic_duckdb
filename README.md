# magic_duckdb

DuckDB Cell (%%dql) and Line (%dql) Magics for Jupyter and VSCode

## Motivation

magic_duckdb was created to:

- Provide simple cell/line magics with minimal code and zero dependencies
- Match performance of DuckDB python API
- Be a simple starting point to add other useful features with minimal complexity
- Bundle useful features, like using OpenAI to improve SQL, sql formatting (beautifying) and explain analyze graphics

### Why not the %sql magics (jupysql or ipython-sql)?

The %sql magics are great, but they do carry a lot of dependencies and incur a significant performance overhead (see Performance Comparison below). They also don't provide certain DuckDB specific features, like exporting directly to arrow(), controlling the DuckDB connections, or

## Simplicity

The goal of this project was to provide a minimal line & cell magics for DuckDB in Jupyter notebooks with minimal dependencies and as simply as possible.

The code is concentrated in two files with under 300 lines of code. Goal is to keep this code short and simple.

- magic.py: Barebones cell and line magic that parses arguments, and executes statements
- duckdb_mode.py: execute() calls the appropriate method based on the user selected output type.

There are also separate files for drawing explain analyze graphs and formatting (beautifying) SQL.

## Quick Start

```
%pip install magic_duckdb --upgrade --quiet
%load_ext magic_duckdb
%dql select * from range(100)
```

## Usage

```
Connection:
-cn <connection_string>: Create a new connection to a DuckDB.
    %dql -cn myfile.db
-co <connection_object>: Use an existing DuckDB Connection.
    con = duckdb.connect("somefile.db")
    %dql -co con
-d: Use the duckdb.default_connection
-g | --getcon: Get the current connection
    con = %dql --getcon
--close: Close current connection

Modes:
-t <type> [default: df]: Selects the type for this and all future requests.
-e <explain_mode>: Display the explain plan, or explain analyze, or AST

Options:
-l | --listtypes: Returns a list of available output types, for -t
-r: Replace {var} with variable strings from the environment using .format(). Note: not a f-string: {var} is not evaluated.
    var1 = "table1"
    %dql -r select * from {var1}, table2
-o <var>: Stores the resulting output in a variable named <var>

Extras:
--tables: Returns tables used by the query
-f: Format the string using npx sql-formatter
Other:
-ai / -aichat: Route request to OpenAI
    %dql -ai Fix selct star frm mytable

```

See [notebooks](https://github.com/iqmo-org/magic_duckdb/tree/main/notebooks) for usage examples.

## Usage Details

- `%dql -t [df | arrow | pl | relation | show] <query>`: Equivalent to - `connection.sql(query).<type>()`
- `%dql -e [explain | explain_analyze_tree | explain_analyze_json | explain_analyze_draw | analyze | ast_json | ast_tree | ast_draw] <query>`:
  - `explain` is equivalent to `connection.sql(query).explain()`
  - `explain_analyze_*` options enable profiling (`PRAGMA enable_profiling`), and use `connection.sql(query).explain(type='analyze')`
  - `explain_analyze_draw` requires [graphviz](https://graphviz.org/) to be installed on your system, and "dot" or "dot.exe" must be in your PATH or added via `magic.explain_analyze_graphviz.dot_path = 'path_to_dot'`. The graphviz python module must also be installed: `pip install graphviz`
  - The AST options use [json_serialize_sql](https://github.com/duckdb/duckdb/discussions/6922) to describe the SQL. `ast_json` displays the raw json result, `ast_tree` displays an indented tree, and `ast_draw` uses graphviz to draw a graphical version of the tree
- `%dql --format <query>` uses [sql-formatter](https://github.com/sql-formatter-org/sql-formatter). This is a javascript library, so it needs to be installed separately, although it's executed via npx so should be fine as long as you have npx / node in your path.
- `%dql --tables <query>` returns the list of tables used by the query, equivalent to: `duckdb.get_table_names("SELECT * FROM xyz")`
- `%dql [-ai | -aichat] fix <query>` passes the current schema to OpenAI and askes OpenAI to "fix" the query. An OpenAI developer key is required.

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

# Performance Comparison

The jupysql/sql-alchemy/duckdb-engine %sql magic was surprisingly slow when compared to magic_duckdb or duckdb. I didn't spend a lot of time evaluating this, so please do your own evaluation: my priority was keeping magic_duckdb simple by using duckdb directly.

### Versions

- SQLAlchemy 2.0.9
- DuckDb: 0.7.2dev1671
- duckdb-engine: 0.7.0
- jupysql: 0.7.0

### Test Setup

See [benchmarking.ipynb](https://github.com/iqmo-org/magic_duckdb/blob/main/notebooks/benchmarking.ipynb) for the test code.

### Results

| # Rows | duckdb (baseline) | magic_duckdb (%dql) | jupysql+SQLAlchemy (%sql) |
| :----- | ----------------: | ------------------: | ------------------------: |
| 10M    |            3.03 s |              2.91 s |                    50.2 s |
| 1M     |            310 ms |              302 ms |                    5.44 s |
| 100K   |             56 ms |               53 ms |                    844 ms |
| 10K    |             10 ms |               10 ms |                    413 ms |
| 1K     |             12 ms |               11 ms |                    388 ms |
| 1      |            7.5 ms |              7.8 ms |                    363 ms |

Copyright &copy; 2023 Iqmo Corporation
