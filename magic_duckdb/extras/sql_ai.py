#
#
# Futures:
# Use embeddings
# Maintain conversation context
from openai import OpenAI #
import logging
from typing import Tuple, Optional
import textwrap

logger = logging.getLogger("magic_duckdb")

OPENAI_KEY = None
print_prompts = False

__LAST_RESULT = None
COMPLETION_ENGINE = "gpt-3.5-turbo"
# COMPLETION_ENGINE = "gpt-4-32k-0314"

#CHATCOMPLETION_ENGINE = "gpt-4-0125-preview"

__OPENAI_CLIENT = None
def get_client():
    if OPENAI_KEY is None:
        raise ValueError(
            "Set the OPENAI_KEY before using. \nfrom magic_duckdb.extras import sql_ai\nsql_ai.OPENAI_KEY=yourkey"
        )

    global __OPENAI_CLIENT
    if __OPENAI_CLIENT is None:
        __OPENAI_CLIENT = OpenAI(api_key=OPENAI_KEY)

    return __OPENAI_CLIENT

def get_columns(connection) -> str:
    df = connection.sql(
        "select table_name, column_name, data_type from duckdb_columns"
    ).df()

    return df.to_csv(index=False)
    col_desc = []

    return ["column_name", "data_type"]

    for t in df["table_name"].unique():
        cols = [
            f"{v[0]} (type = {v[1]})"
            for v in df.loc[df["table_name"] == t, ["column_name", "data_type"]].values
        ]
        cols_desc = ",".join(cols)

        desc = f"Table {t} has the following columns and data types - {cols_desc}"
        col_desc.append(desc)

    return "\n".join(col_desc)


def get_schema(connection) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        if connection is None:
            return None, None, None

        t = connection.sql("PRAGMA show_tables")
        if t is None:  # no tables = None
            return None, None, None
        else:
            tables = t.df()

        if len(tables) == 0:
            tables = None
        else:
            tables = ", ".join(tables["name"].values)

        cols = get_columns(connection)

        constraints = connection.sql("select * from duckdb_constraints").df()

        if len(constraints) == 0:
            constraints = None
        else:
            constraints = constraints.to_csv()

        return tables, cols, constraints
    except Exception:
        logger.exception("Error getting schema")
        return None, None, None


def call_ai(connection, chat: bool, prompt, query):
    return ai_statement(
        connection=connection, prompt=prompt, statement=query
    )


def exec_ai_prompt(prompt: str, engine = None) -> str:
    
    client = get_client()

    completion = client.chat.completions.create(
        model=COMPLETION_ENGINE if engine is None else engine,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    message = completion.choices[0].message # response["choices"][0]["message"]["content"]  # type: ignore

    global __LAST_RESULT
    __LAST_RESULT = message
    result = message.content
    return result

def ai_statement(connection, prompt: str, statement: str):
    logger.info(f"Passing {prompt} statement to AI ): {statement}")
    # Prepare prompt
    tables, cols, constraints = get_schema(connection)

    prompt = f"{prompt}\nMy query is: {statement}\nMy database is DuckDB. DuckDB's SQL is similar to postgresql. DuckDB sql supports: select, from, join, where, group by, grouping sets, having, order by, limit, sample, unnest, with, window, qualify, values and filter. "
    context = f"I am writing SQL for a DuckDB database. My database's tables, columns and column data types are the following comma separated table: \n{cols}\n\nConstraints: {constraints}"

    full_prompt = context + "\nMy question is: " + prompt
    logger.debug(f"Num tokens: {len(prompt.split(' '))}")

    logger.info(f"Prompt = \n{full_prompt}")
    if print_prompts:
        print("-------------Prompt---------------")
        print(full_prompt)

    result = exec_ai_prompt(full_prompt)

    cell = textwrap.dedent(result)
    # Insert 4 spaces of indentation before each line
    cell = textwrap.indent(cell, " " * 4)

    print("-------------OpenAI Response---------------")
    print(cell)
    return cell
