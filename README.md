# magic_duckdb

iPython Cell %%dql and Line %dql magics for DuckDB, for both Jupyter and VSCode

## Quick Start

```
%pip install magic_duckdb --upgrade --quiet
%load_ext magic_duckdb
%dql select * from range(100)
```

## Usage:

```
Connection:
-cn <connection_string>: Create a new connection to a DuckDB.
    %dql -cn myfile.db
-co <connection_object>: Use an existing DuckDB Connection.
    con = duckdb.connect("somefile.db")
    %dql -co con
-d: Use the duckdb.default_connection
--getcon: Get the current connection
    con = %dql --getcon

Types:
--listtypes: Returns a list of available output types
-t <type> [default: df]: Selects the type for this and all future requests.

Other:
-ai / -aichat: Route request to OpenAI
    %%dql -ai Fix my sql
    ....

-r: Replace {var} with variable strings from the environment
    var1 = "some string"
    %dql -r select * from {var1} join table
```

See notebooks/examples.ipynb for complete usage examples.

## Motivation

magic_duckdb was created to:

- Expose duckdb's functionality with minimal overhead and complexity
- Make it easier to use duckdb in Jupyter notebooks
- Bundle useful features, like using OpenAI to improve SQL, sql formatting (beautifying) and explain analyze graphics
- Provide a starting point to add other useful features with minimal complexity

### Why not other projects like Jupysql or ipython-sql?

The %sql magics are great, but are intended for breadth (supporting many types of databases), not depth (deep integration and optimizations for specific databases). As shown below (Performance Comparison), this breadth comes at a performance cost.

## Simplicity

The goal of this project was to provide a minimal line & cell magics for DuckDB in Jupyter notebooks with minimal dependencies and as simply as possible.

The code is concentrated in two files with under 300 lines of code. Goal is to keep this code short and simple.

- magic.py: Barebones cell and line magic that parses arguments, and executes statements
- duckdb_mode.py: execute() calls the appropriate method based on the user selected output type.

There are also separate files for drawing explain analyze graphs and formatting (beautifying) SQL.

## Fun Stuff / Extras

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

Graphing Dependency / Why GraphViz? GraphViz was quick, simple, and has the best layout engines available. [D2](https://github.com/terrastruct/d2) is a promising option but in either case, requires an external dependency, but I tried to find a comparable pure Python library and failed.

## %dql -t format [experimental]

SQL Formatting uses [sql-formatter](https://github.com/sql-formatter-org/sql-formatter). This is a javascript library, so it needs to be installed separately, although it's executed via npx so should be fine as long as you have npx / node in your path.

It does not have a duckdb language, so the PostgreSQL language is used. It's been good enough, but some queries might not format well until/unless they add a duckdb mode.

SQL Formatter Dependency / Why SQL Formatter and not something pure Python? The comparable Python projects seem idle / no longer maintained.

## Autocompletion: Work in Progress

There's two different Autocompletion implementations, one for MatcherAPIv2 and the other (pre-ipython 8.6.0) for MatcherAPIv1. The MatcherAPIv2 version is tried first, and if it fails, the MatcherAPIv1 version is loaded. MatcherAPIv1 will not match the entire results of a cell: it's limited to a line by line match.

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
