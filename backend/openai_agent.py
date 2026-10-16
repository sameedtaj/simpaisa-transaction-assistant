
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from backend.prompts import build_sql_generation_prompt
from backend.guardrails import (
    validate_user_question,
    validate_generated_sql,
)
from backend.mcp_client import execute_readonly_sql


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing from .env")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


def clean_generated_sql(value: str) -> str:
    """
    Remove accidental Markdown formatting from GPT output.
    """

    if not value:
        return ""

    return (
        value
        .replace("```postgresql", "")
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )


async def generate_sql(user_question: str) -> str:
    """
    Generate SQL only after the input guardrail passes.
    """

    prompt = build_sql_generation_prompt(user_question)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Generate exactly one safe PostgreSQL SELECT query. "
                    "Return UNSAFE_SQL_REQUEST for modification requests. "
                    "Return NEED_DATE_RANGE when no usable date is provided."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    generated_text = response.choices[0].message.content or ""

    return clean_generated_sql(generated_text)


async def ask_database(user_question: str) -> dict:
    """
    Full application flow:

    User question
    -> input guardrail
    -> GPT SQL generation
    -> SQL output guardrail
    -> MCP Client
    -> MCP Server
    -> read-only PostgreSQL
    """

    # Guardrail 1: validate user question before spending GPT tokens.
    input_check = validate_user_question(user_question)

    if not input_check["valid"]:
        return {
            "success": False,
            "sql": None,
            "result": None,
            "answer": input_check["message"],
            "error": input_check["error"],
        }

    sql = await generate_sql(user_question)

    # Consistent fallback handling.
    if sql == "UNSAFE_SQL_REQUEST":
        return {
            "success": False,
            "sql": sql,
            "result": None,
            "answer": "This request is unsafe. Only SELECT queries are allowed.",
            "error": "UNSAFE_SQL_REQUEST",
        }

    if sql == "NEED_DATE_RANGE":
        return {
            "success": False,
            "sql": None,
            "result": None,
            "answer": (
                "Please provide a date range, month and year, day, year, "
                "or relative period such as last month."
            ),
            "error": "DATE_RANGE_REQUIRED",
        }

    # Guardrail 2: validate generated SQL before sending it to MCP.
    sql_check = validate_generated_sql(sql)

    if not sql_check["valid"]:
        return {
            "success": False,
            "sql": sql,
            "result": None,
            "answer": "The generated SQL failed the safety validation.",
            "error": sql_check["error"],
        }

    mcp_result = await execute_readonly_sql(sql)

    return {
        "success": True,
        "sql": sql,
        "result": mcp_result,
        "answer": None,
        "error": None,
    }
