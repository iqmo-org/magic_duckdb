# magic_duckdb cell & line magics

[magic_duckdb](https://github.com/iqmo-org/magic_duckdb) provides a %dql cell magic and %%dql line magic for VScode & Jupyter notebooks.

It is a lightweight wrapper around DuckDB's Python API with no additional dependencies.

Autocomplete is a work-in-progress. There are also some experimental (disabled by default) features for -ai/-aichat, and sql formatting via -format. More information is available on [magic_duckdb](https://github.com/iqmo-org/magic_duckdb).

# Quick Start

## Installation

```
%pip install magic_duckdb # --upgrade
%load_ext magic_duckdb

# Print DuckDB version
%dql PRAGMA version
```

## Usage

As a line magic

```
%dql <options> <statement(s)>
```

As a cell magic

```
%%dql <options>
statement(s)
```

## Options

### Connection

- -d: [Default] Use [duckdb.defaultconnection](https://duckdb.org/docs/api/python/reference/#duckdb.default_connection) and return Pandas DataFrames using [`connection.sql("...").df()`](https://duckdb.org/docs/api/python/reference/#duckdb.df)
- -cn <value>: Connect via `duckdb.connect(value)` and use this for subsequent requests
- -co <variable>: `%dql -co conn` will set the internal dql conneciton to the object named conn.

### Output Types

- `-t [df (default) | arrow | pl | describe | explain | show | relation]`: Outputs data in teh specified type. The type selected is used for all subsequent calls.

### Helpers

- -o <variable>: Convenience function to store the result in variable
- -r: Format the string with Python format(), using the user namespace. {var}'s will be replaced with the content of var. Note that this is _not_ an f-string: code inside the {}'s are not executed. This is the same as ".format(...)".

## Examples

```
# Change output from Pandas df to Arrow:
%dql -t arrow

# Execute two statements, separated by semicolon
%dql CREATE TABLE abc as SELECT * FROM range(10); CREATE TABLE xyz as SELECT * FROM range(10)

# Execute a single statement
df1 = %dql SELECT * FROM xyz

# Execute a statement, storing output in df2
%dql -o df2 SELECT * FROM abc
```

Uses a cell amgic to create two tables and execute a query. The object from the last statement is stored in `df3`.

```
%%dql -t df -o df3
CREATE TABLE abc as SELECT * FROM range(10);
CREATE TABLE xyz as SELECT * FROM range(10);
SELECT * FROM abc union all SELECT * FROM xyz
```

Uses %%capture magic to silence the display output. This is useful at suppressing display of intermediate data.

```
%%capture
%%dql -t df -o df_out
SELECT * FROM abc
```

Format the string:

```
--Cell 1--
var1 = "abcd"

--Cell 2--
%%dql -r
CREATE TABLE {var1} as SELECT * FROM range(10)
;
SELECT * FROM {var1}
```
