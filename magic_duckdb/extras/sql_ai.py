#
#
# Futures:
# Use embeddings
# Maintain conversation context
import openai  # type: ignore
import logging
from typing import Tuple, Optional
import textwrap

logger = logging.getLogger("magic_duckdb")

OPENAI_KEY = None
print_prompts = False
COMPLETION_ENGINE = "text-davinci-002"
# COMPLETION_ENGINE = "gpt-4-32k-0314"

CHATCOMPLETION_ENGINE = "gpt-3.5-turbo"


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
        connection=connection, prompt=prompt, statement=query, chat=chat
    )


def ai_statement(connection, prompt: str, statement: str, chat: bool = False):
    logger.info(f"Passing {prompt} statement to AI (chat={chat}): {statement}")
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

    if OPENAI_KEY is None:
        raise ValueError(
            "Set the OPENAI_KEY before using. \nfrom magic_duckdb.extras import sql_ai\nsql_ai.OPENAI_KEY=yourkey"
        )
    else:
        openai.api_key = OPENAI_KEY

    if chat:
        response = openai.ChatCompletion.create(
            model=CHATCOMPLETION_ENGINE,
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            max_tokens=193,
            temperature=0,
        )
        result = response["choices"][0]["message"]["content"]  # type: ignore

    else:
        response = openai.Completion.create(
            engine=COMPLETION_ENGINE,
            prompt=full_prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5,
        )

        result = response.choices[0].text.strip()  # type: ignore

    cell = textwrap.dedent(result)
    # Insert 4 spaces of indentation before each line
    cell = textwrap.indent(cell, " " * 4)

    print("-------------OpenAI Response---------------")
    print(cell)
    return cell
