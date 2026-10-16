
import re
from typing import Optional


UNSAFE_REQUEST_PATTERNS = [
    r"\bdelete\b",
    r"\bupdate\b",
    r"\binsert\b",
    r"\bdrop\b",
    r"\balter\b",
    r"\btruncate\b",
    r"\bcreate\b",
    r"\breplace\b",
    r"\bmerge\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\bremove\b.*\btransaction",
    r"\bmodify\b.*\bdata",
]


MONTH_NAMES = (
    "january|february|march|april|may|june|"
    "july|august|september|october|november|december|"
    "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
)


def detect_unsafe_request(question: str) -> bool:
    """
    Detect user requests that attempt to modify database data.
    """

    normalized = question.strip().lower()

    return any(
        re.search(pattern, normalized, flags=re.IGNORECASE)
        for pattern in UNSAFE_REQUEST_PATTERNS
    )


def has_valid_date_reference(question: str) -> bool:
    """
    Return True when the question contains an explicit usable date period.

    Accepted:
    - June 2026
    - 2026-06-01
    - 2026-06-01 to 2026-06-30
    - today
    - yesterday
    - last month
    - this month
    - current month
    - last 7 days
    """

    normalized = question.strip().lower()

    relative_date_patterns = [
        r"\btoday\b",
        r"\byesterday\b",
        r"\bthis month\b",
        r"\bcurrent month\b",
        r"\blast month\b",
        r"\bthis year\b",
        r"\bcurrent year\b",
        r"\blast year\b",
        r"\blast\s+\d+\s+days?\b",
        r"\blast\s+\d+\s+months?\b",
    ]

    if any(re.search(pattern, normalized) for pattern in relative_date_patterns):
        return True

    # ISO date such as 2026-06-01
    if re.search(r"\b20\d{2}-\d{2}-\d{2}\b", normalized):
        return True

    # Month plus year, such as June 2026
    if re.search(
        rf"\b(?:{MONTH_NAMES})\b[\s,/-]*\b20\d{{2}}\b",
        normalized,
        flags=re.IGNORECASE,
    ):
        return True

    # Year-level request, such as "transactions in 2026"
    if re.search(r"\b(?:in|for|during)\s+20\d{2}\b", normalized):
        return True

    return False


def validate_user_question(question: str) -> dict:
    """
    Input guardrail executed before GPT.
    """

    if not question or not question.strip():
        return {
            "valid": False,
            "error": "EMPTY_QUESTION",
            "message": "Question cannot be empty.",
        }

    if len(question.strip()) > 1000:
        return {
            "valid": False,
            "error": "QUESTION_TOO_LONG",
            "message": "Question is too long.",
        }

    if detect_unsafe_request(question):
        return {
            "valid": False,
            "error": "UNSAFE_SQL_REQUEST",
            "message": "Only read-only database questions are allowed.",
        }

    if not has_valid_date_reference(question):
        return {
            "valid": False,
            "error": "DATE_RANGE_REQUIRED",
            "message": (
                "Please provide a date range, month and year, day, year, "
                "or relative period such as last month."
            ),
        }

    return {
        "valid": True,
        "error": None,
        "message": None,
    }


FORBIDDEN_SQL_KEYWORDS = [
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
    "revoke",
]

ALLOWED_TABLE = "collection_data26_sample"


def validate_generated_sql(sql: str) -> dict:
    """
    Output guardrail executed after GPT and before MCP.
    """

    if not sql or not sql.strip():
        return {
            "valid": False,
            "error": "EMPTY_SQL",
        }

    clean_sql = sql.strip()
    lower_sql = clean_sql.lower()

    if clean_sql in {"UNSAFE_SQL_REQUEST", "NEED_DATE_RANGE"}:
        return {
            "valid": False,
            "error": clean_sql,
        }

    if not lower_sql.startswith("select"):
        return {
            "valid": False,
            "error": "ONLY_SELECT_ALLOWED",
        }

    # Prevent stacked/multiple statements.
    statements = [
        part.strip()
        for part in clean_sql.split(";")
        if part.strip()
    ]

    if len(statements) != 1:
        return {
            "valid": False,
            "error": "MULTIPLE_SQL_STATEMENTS_NOT_ALLOWED",
        }

    for keyword in FORBIDDEN_SQL_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", lower_sql):
            return {
                "valid": False,
                "error": f"FORBIDDEN_SQL_KEYWORD:{keyword}",
            }

    if not re.search(
        rf"\bfrom\s+(?:public\.)?{re.escape(ALLOWED_TABLE)}\b",
        lower_sql,
    ):
        return {
            "valid": False,
            "error": "UNAUTHORIZED_TABLE",
        }

    if '"Created Date"' not in clean_sql:
        return {
            "valid": False,
            "error": "DATE_FILTER_REQUIRED",
        }

    if "select *" in lower_sql and not re.search(r"\blimit\s+\d+\b", lower_sql):
        return {
            "valid": False,
            "error": "LIMIT_REQUIRED_FOR_DETAIL_QUERY",
        }

    limit_match = re.search(r"\blimit\s+(\d+)\b", lower_sql)

    if limit_match and int(limit_match.group(1)) > 1000:
        return {
            "valid": False,
            "error": "LIMIT_EXCEEDS_1000",
        }

    return {
        "valid": True,
        "error": None,
    }
