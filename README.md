# magic_duckdb

iPython Cell %%dql and Line %dql magics for DuckDB, for both Jupyter and VSCode

## Quick Start

```
%pip install magic_duckdb
%load_ext magic_duckdb
%dql select * from range(100)
```

## Usage:

```
Connection:
-cn <connection_string>: Create a new connection to a DuckDB. Example: %dql -cn :memory:
-co <connection_object>: Use an existing DuckDB Connection. Example: %dql -co con
-d: Use the duckdb.default_connection
--getcon: Get the current connection, regardless of how it was created

Types:
--listtypes: Returns a list of available output types. Pandas df is the default type.
-t <type>: Selects the type for this and all future requests.
```

See notebooks/examples.ipynb for complete usage examples.

## Motivation

magic_duckdb was created to:

- Expose duckdb's functionality with minimal overhead and complexity
- Make it easier to use duckdb in Jupyter notebooks
- Bundle useful features, like sql formatting (beautifying) and explain analyze graphics
- Provide a starting point to add other useful features with minimal complexity

### Why not other projects like Jupysql or ipython-sql?

The %sql magics are great, but are intended for breadth (supporting many types of databases), not depth (deep integration and optimizations for specific databases). As shown below (Performance Comparison), this breadth comes at a performance cost.

## Simplicity

The goal of this project was to provide a minimal line & cell magics for DuckDB in Jupyter notebooks with minimal dependencies and as simply as possible.

The code is concentrated in two files with under 300 lines of code. Goal is to keep this code short and simple.

- magic.py: Barebones cell and line magic that parses arguments, and executes statements
- duckdb_mode.py: execute() calls the appropriate method based on the user selected output type.

There are also separate files for drawing explain analyze graphs and formatting (beautifying) SQL.

## Fun Stuff

- SQL Formatter: Using the javascript sql-formatter project. Requires node/npx.
- Graphical Explain Analyze: Formats complex explain analyze results using Graphviz. Requires both graphviz python module and graphviz binaries in your PATH.
- AI Suggestions and Fixing: -ai and -aichat route the requests to OpenAI. Requires an OpenAI developer key.

## Data Formats

The following formats are supported:

```
%dql --listtypes
> ['df', 'arrow', 'pl', 'describe', 'explain', 'show', 'relation', 'explain_analyze_tree', 'explain_analyze_json', 'explain_analyze_draw', 'format_sql', 'analyze [alias for explain_analyze_draw]']
%dql -t arrow
```

### %dql -t [df | arrow | pl | relation | show | explain]

Executes and returns the appropriate method for the type:

```
connection.sql(query).<type>()
```

## %dql -t [explain_analyze_tree | explain_analyze_json]

```
connection.sql("PRAGMA enable_profiling=[json | query_tree]")
r = connection.sql(query_string)
t = r.explain(type= "analyze")
return t
```

### %dql -t analyze [experimental - requires 0.7.2+]

analyze (or explain_analyze_draw) generates an graphical version of the JSON tree created by explain_analyze_json. This version handles large, complex trees well and is easily modified or otherwise extended.

[graphviz](https://graphviz.org/) must be installed on your system, and "dot" or "dot.exe" must be in your PATH. If it's installed, but not in PATH, set the path with:

```
magic.explain_analyze_graphviz.dot_path = 'path_to_dot'
```

Graphing Dependency / Why GraphViz? GraphViz was quick, simple, and has the best layout engines available. I tried to find a comparable pure-Python library and failed.

## %dql -t format [experimental]

SQL Formatting uses https://github.com/sql-formatter-org/sql-formatter. This is a javascript library, so it needs to be installed separately.

It does not have a duckdb language, so the PostgreSQL language is used. It's been good enough, but some queries might not format well until/unless they add a duckdb mode.

SQL Formatter Dependency / Why SQL Formatter and not something pure Python? The comparable Python projects seem idle / no longer maintained.

## Autocompletion: Work in Progress

There's a rough implementation of an autocompleter that can be enabled prior to loading the extension.

This is really a proof of concept at getting the plumbing to work. The actual autocompletion should probably leverage duckdb's existing work: [4921](https://github.com/duckdb/duckdb/pull/4921) and test cases here: [shell-test.py](https://github.com/Mytherin/duckdb/blob/5f75cb90b478434f0a1811af0695ea3a186a67a8/tools/shell/shell-test.py)

```
from magic_duckdb import magic
magic.ENABLE_AUTOCOMPLETE=True
%load_ext magic_duckdb
```

Completions:

- Common phrases, such as PRAGMAs and SQL phrases like CREATE OR REPLACE TABLE
- Table names from the current duckdb connection
- Column names: Column names are suggested when a tablename is followed by a period. Aliases are not discovered, so exact table names (ie; tablenamexyz.) will be looked up.

Limitations:

- Line magics %dql only, not yet for %%dql cell magics
- Case sensitive: it'll autocomplete CREA<tab>, but not CREA<tab>

Gotchas:

- Autocompletion uses the iPython 8.2.x signatures, so won't work in older iPython installs.
- VSCode behaves differently than Jupyter: Jupyter autocompletes on Tab, VSCode defaults to spaces.
- VSCode also seems to insert certain autocompletions outside of the ipython stack, not allowing an autocompleter to override certain completions.

# Performance Comparison

The jupysql/sql-alchemy/duckdb-engine %sql magic was surprisingly slow when compared to magic_duckdb or duckdb. I didn't spend a lot of time evaluating this, so please do your own evaluation: my priority was keeping magic_duckdb simple by using duckdb directly.

## Versions

- SQLAlchemy 1.4.47
- DuckDb: 0.7.2dev1256
- duckdb-engine: 0.7.0
- jupysql: 0.6.6

## 1 million rows

```
# Test setup
# Create a semi-large dataframe
from pandas import DataFrame
import numpy as np
simpledf = DataFrame(np.random.randn(1000000,20))
```

```
%load_ext simplemagic
%timeit odf = %dql select * from simpledf
```

> 288 ms ± 24.7 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

```
# %pip install duckdb duckdb_engine jupysql
%load_ext sql
%sql duckdb:///:memory:
%config SqlMagic.autopandas = True

%timeit odf = %sql select * from simpledf
```

> 6.69 s ± 806 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

## 1 Row

magic_duckdb:

> 7.84 ms ± 330 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

jupysql:

> 7.29 ms ± 126 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

<br/>
Copyright (c) 2023 Iqmo Corporation
