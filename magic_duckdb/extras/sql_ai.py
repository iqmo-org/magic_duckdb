import openai  # type: ignore
import logging
import functools
from typing import Tuple, Optional
import textwrap

logger = logging.getLogger("magic_duckdb")

openai_key = None
print_prompts = False


@functools.lru_cache(32)
def get_schema(connection) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if connection is None:
        return None, None, None

    tables = connection.sql("PRAGMA show_tables").df()

    if len(tables) == 0:
        tables = None
    else:
        tables = tables["name"].values

    cols = connection.sql("select * from duckdb_columns").df()
    if len(cols) == 0:
        cols = None
    else:
        cols = cols.to_csv()

    constraints = connection.sql("select * from duckdb_constraints").df()

    if len(constraints) == 0:
        constraints = None
    else:
        constraints = constraints.to_csv()

    return tables, cols, constraints


def call_ai(connection, cmd, prompt, query):
    if cmd == "-aichat":
        chat = True
    else:
        chat = False

    query
    return fix_statement(
        connection=connection, prompt=prompt, statement=query, chat=chat
    )


def fix_statement(connection, prompt: str, statement: str, chat: bool = False):

    logger.info(f"Passing {prompt} statement to AI (chat={chat}): {statement}")
    # Prepare prompt
    tables, cols, constraints = get_schema(connection)

    prompt = f"{prompt} my SQL\nMy query is: {statement}\nDuckdb is similar to postgresql. My database has the following tables: {tables}\nAnd column metadata: \n {cols}\n\nMy database has the following constraints: {constraints}"

    logger.debug(f"Num tokens: {len(prompt.split(' '))}")

    logger.info(f"Prompt = \n{prompt}")
    if print_prompts:
        print("-------------Prompt---------------")
        print(prompt)
    if openai_key is None:
        raise ValueError(
            "Set the AI_KEY before using. \nfrom magic_duckdb.extras import sql_ai\nsql_ai.openai_key=yourkey"
        )
    else:
        openai.api_key = openai_key

    if chat:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=193,
            temperature=0,
        )
        result = response["choices"][0]["message"]["content"]

    else:
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5,
        )

        result = response.choices[0].text.strip()

    cell = textwrap.dedent(result)
    # Insert 4 spaces of indentation before each line
    cell = textwrap.indent(cell, " " * 4)

    print("-------------OpenAI Response---------------")
    print(cell)
    return cell
