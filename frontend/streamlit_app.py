
import json
from typing import Any

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

REQUEST_TIMEOUT = 120


st.set_page_config(
    page_title="SIMPAISA Database Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state() -> None:
    """Initialize Streamlit chat history."""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "show_sql" not in st.session_state:
        st.session_state.show_sql = True


def check_backend_health() -> tuple[bool, str]:
    """Check whether the FastAPI backend is available."""

    try:
        response = requests.get(
            HEALTH_ENDPOINT,
            timeout=5,
        )

        if response.status_code == 200:
            return True, "Backend connected"

        return False, f"Backend returned status {response.status_code}"

    except requests.RequestException:
        return False, "Backend is not running"


def call_chat_api(question: str) -> dict[str, Any]:
    """Send the user question to the existing FastAPI backend."""

    response = requests.post(
        CHAT_ENDPOINT,
        json={"question": question},
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


def parse_result(result: Any) -> Any:
    """
    Convert the backend result into a Python object.

    Your current backend may return the MCP result as an escaped JSON string.
    This function handles both strings and already-structured objects.
    """

    if result is None:
        return None

    if isinstance(result, (dict, list)):
        return result

    if isinstance(result, str):
        cleaned_result = result.strip()

        if not cleaned_result:
            return None

        try:
            return json.loads(cleaned_result)
        except json.JSONDecodeError:
            return result

    return result


def extract_data(parsed_result: Any) -> Any:
    """Extract the data property from the MCP response when available."""

    if isinstance(parsed_result, dict):
        if "data" in parsed_result:
            return parsed_result["data"]

    return parsed_result


def display_result(result: Any) -> None:
    """Display query results using the most appropriate Streamlit component."""

    parsed_result = parse_result(result)
    data = extract_data(parsed_result)

    if data is None:
        st.info("No result was returned.")
        return

    if isinstance(data, list):
        if len(data) == 0:
            st.info("No records found for this question.")
            return

        if all(isinstance(row, dict) for row in data):
            dataframe = pd.DataFrame(data)

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(f"Rows returned: {len(data):,}")
            return

    if isinstance(data, dict):
        columns = st.columns(min(len(data), 4))

        for index, (key, value) in enumerate(data.items()):
            columns[index % len(columns)].metric(
                label=key.replace("_", " ").title(),
                value=value,
            )

        return

    if isinstance(data, str):
        st.write(data)
        return

    st.json(data)


def display_assistant_message(message: dict[str, Any]) -> None:
    """Display a stored assistant response."""

    if message.get("error"):
        st.error(message.get("answer") or message["error"])
        return

    if message.get("answer"):
        st.markdown(message["answer"])

    display_result(message.get("result"))

    sql = message.get("sql")

    if sql and st.session_state.show_sql:
        with st.expander("View generated SQL", expanded=False):
            st.code(sql, language="sql")


def render_sidebar() -> None:
    """Render controls and application information."""

    with st.sidebar:
        st.title("Database Assistant")

        backend_ok, backend_message = check_backend_health()

        if backend_ok:
            st.success(backend_message)
        else:
            st.error(backend_message)
            st.caption(
                "Start FastAPI using:\n\n"
                "`python -m uvicorn backend.app:app --reload`"
            )

        st.divider()

        st.toggle(
            "Show generated SQL",
            key="show_sql",
        )

        if st.button(
            "Clear conversation",
            use_container_width=True,
        ):
            st.session_state.messages = []
            st.rerun()

        st.divider()

        st.subheader("Example questions")

        examples = [
            "Give me successful transaction count for June 2026",
            "Give me total amount for June 2026",
            "Show successful transaction count by operator for June 2026",
            "Give me transaction details for mobile number 3097524704 in June 2026",
        ]

        for example in examples:
            if st.button(
                example,
                key=f"example_{example}",
                use_container_width=True,
            ):
                st.session_state.pending_question = example
                st.rerun()

        st.divider()

        st.caption(
            "Read-only AI analytics assistant\n\n"
            "FastAPI + OpenAI + MCP + PostgreSQL"
        )


def render_header() -> None:
    """Render the main application header."""

    st.title("SIMPAISA Transaction Assistant")

    st.markdown(
        """
Ask transaction-related questions in natural language.

The assistant safely converts your question into read-only PostgreSQL,
executes it through MCP, and displays the result.
"""
    )

    st.divider()


def process_question(question: str) -> None:
    """Call the API and store the answer in chat history."""

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your question and retrieving data..."):
            try:
                response = call_chat_api(question)

                assistant_message = {
                    "role": "assistant",
                    "success": response.get("success", False),
                    "answer": response.get("answer"),
                    "sql": response.get("sql"),
                    "result": response.get("result"),
                    "error": response.get("error"),
                }

                display_assistant_message(assistant_message)
                st.session_state.messages.append(assistant_message)

            except requests.Timeout:
                error_message = {
                    "role": "assistant",
                    "error": "The request timed out. Please try a smaller date range.",
                    "answer": None,
                    "result": None,
                    "sql": None,
                }

                st.error(error_message["error"])
                st.session_state.messages.append(error_message)

            except requests.ConnectionError:
                error_message = {
                    "role": "assistant",
                    "error": (
                        "The FastAPI backend is not running. "
                        "Start it before using the frontend."
                    ),
                    "answer": None,
                    "result": None,
                    "sql": None,
                }

                st.error(error_message["error"])
                st.session_state.messages.append(error_message)

            except requests.HTTPError as exc:
                error_message = {
                    "role": "assistant",
                    "error": f"Backend error: {exc}",
                    "answer": None,
                    "result": None,
                    "sql": None,
                }

                st.error(error_message["error"])
                st.session_state.messages.append(error_message)

            except Exception as exc:
                error_message = {
                    "role": "assistant",
                    "error": f"Unexpected error: {exc}",
                    "answer": None,
                    "result": None,
                    "sql": None,
                }

                st.error(error_message["error"])
                st.session_state.messages.append(error_message)


def main() -> None:
    """Run the Streamlit application."""

    initialize_session_state()
    render_sidebar()
    render_header()

    for message in st.session_state.messages:
        role = message.get("role")

        with st.chat_message(role):
            if role == "user":
                st.markdown(message.get("content", ""))
            else:
                display_assistant_message(message)

    pending_question = st.session_state.pop("pending_question", None)

    question = st.chat_input(
        "Ask a question about transactions..."
    )

    final_question = pending_question or question

    if final_question:
        with st.chat_message("user"):
            st.markdown(final_question)

        process_question(final_question)


if __name__ == "__main__":
    main()
