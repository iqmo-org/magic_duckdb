# magic_duckdb

Simple Cell / Line Magic for DuckDB for Jupyter.

## Quick Start

```
%pip install magic_duckdb
%load_ext magic_duckdb
%dql select * from range(100)
```

# Motivation

magic_duckdb was created to:

- Expose duckdb's functionality with minimal overhead and complexity
- Make it easier to use duckdb in Jupyter notebooks
- Bundle useful features, like sql formatting (beautifying) and explain analyze graphics
- Provide a starting point to add other useful features with minimal complexity

## Why not other projects like Jupysql or ipython-sql?

The %sql magics are great, but are intended for breadth (supporting many types of databases), not depth (deep integration and optimizations for specific databases). As shown below (Performance Comparison), this breadth comes at a performance cost.

# Simplicity

The goal of this project was to provide a minimal line & cell magics for DuckDB in Jupyter notebooks with minimal dependencies and as simply as possible.

The code is concentrated in two files, totalling around 200 lines of code:

- magic.py: Barebones cell and line magic that parses arguments, and executes statements
- duckdb_mode.py: execute() calls the appropriate method based on the user selected output type.

There are also separate files for drawing explain analyze graphs and formatting (beautifying) SQL.

## Data Formats

The following formats are supported:

```
%dql --listtypes
> ['df', 'arrow', 'pl', 'describe', 'explain', 'show', 'relation', 'explain_analyze_tree', 'explain_analyze_json', 'explain_analyze_draw', 'format_sql', 'analyze [alias for explain_analyze_draw]']
%dql -t arrow
```

## %dql -t [df | arrow | pl | relation | show | explain]

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

## %dql -t analyze [experimental - requires 0.7.2+]

analyze (or explain_analyze_draw) generates an graphical version of the JSON tree created by explain_analyze_json. This version handles large, complex trees well and is easily modified or otherwise extended.

[graphviz](https://graphviz.org/) must be installed on your system, and "dot" or "dot.exe" must be in your PATH. If it's installed, but not in PATH, set the path with:

```
magic.explain_analyze_graphviz.dot_path = 'path_to_dot'
```

### Why GraphViz?

GraphViz was quick, simple, and has the best layout engines available. I tried to find a comparable pure-Python library and failed.

## %dql -t format [experimental]

SQL Formatting uses https://github.com/sql-formatter-org/sql-formatter. This is a javascript library, so it needs to be installed separately.

It does not have a duckdb language, so the PostgreSQL language is used. It's been good enough, but some queries might not format well until/unless they add a duckdb mode.

Why SQL Formatter and not something pure Python? The comparable Python projects seem idle / no longer maintained.

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

# TODOs

- Replace the command parsing with CmdParser
- Pretty print the Explain and Analyze outputs

## Copyright (c) 2023 Iqmo Corporation
