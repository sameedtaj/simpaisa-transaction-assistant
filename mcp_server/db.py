
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def validate_sql(query: str):
    q = query.strip().lower()

    forbidden = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace",
        "merge",
        "grant",
        "revoke"
    ]

    if not q.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    for word in forbidden:
        pattern = r"\\b" + word + r"\\b"
        if re.search(pattern, q):
            raise ValueError(
                f"Blocked forbidden SQL keyword: {word}"
            )


def run_select_query(query: str):

    validate_sql(query)

    with engine.connect() as conn:

        result = conn.execute(text(query))

        rows = result.mappings().all()

        return [dict(row) for row in rows]


if __name__ == "__main__":

    print(
        run_select_query(
            "SELECT COUNT(*) AS total_rows FROM collection_data26_sample;"
        )
    )
