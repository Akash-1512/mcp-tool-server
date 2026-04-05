from __future__ import annotations

import json
import logging
import pathlib
import sqlite3

from mcp_server.exceptions import SQLQueryForbiddenError, ToolExecutionError

logger = logging.getLogger(__name__)

# LOCAL DEMO — SQLite local file, zero cost
_DB_PATH = pathlib.Path(__file__).parent.parent.parent / "data" / "enterprise.db"


def get_db_connection() -> sqlite3.Connection:
    """Return a SQLite connection with Row factory enabled.

    Row factory means rows are accessible by column name:
        row["name"] instead of row[0]

    Raises ToolExecutionError if the database file does not exist.
    Run 'make seed-db' to generate it from data/seed.sql.
    """
    if not _DB_PATH.exists():
        raise ToolExecutionError(
            tool_name="sql_query_tool",
            message=(f"Database not found at {_DB_PATH}. " "Run 'make seed-db' to generate it."),
        )
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    # FIXME: concurrent tool calls may hit SQLite read lock under load.
    # Enable WAL mode for better read concurrency:
    #   conn.execute("PRAGMA journal_mode=WAL")
    # Not enabled yet — needs load testing first.
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# [PRODUCTION] Azure SQL — uncomment to enable
# Requires: AZURE_SQL_CONNECTION_STRING in .env
# ─────────────────────────────────────────────────────────────────────────────
# import pyodbc
# def get_db_connection() -> pyodbc.Connection:
#     connection_string = os.getenv("AZURE_SQL_CONNECTION_STRING")
#     if not connection_string:
#         raise ToolExecutionError(
#             tool_name="sql_query_tool",
#             message="AZURE_SQL_CONNECTION_STRING not set in environment",
#         )
#     return pyodbc.connect(connection_string)

# ─── Query Validation ─────────────────────────────────────────────────────────

_FORBIDDEN_STATEMENTS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"}


def _validate_select_only(query: str) -> None:
    """Reject any SQL statement that is not a SELECT.

    Checks the first non-whitespace keyword — does not attempt full SQL
    parsing. Sufficient for demo security; production would use a proper
    SQL parser or parameterised views.
    """
    first_keyword = query.strip().split()[0].upper()
    if first_keyword in _FORBIDDEN_STATEMENTS:
        raise SQLQueryForbiddenError(received_statement=query)
    if first_keyword != "SELECT":
        raise SQLQueryForbiddenError(received_statement=query)


# ─── Handler ─────────────────────────────────────────────────────────────────


async def handle_sql_query(arguments: dict) -> str:
    """Execute a read-only SQL SELECT against the IT asset management database.

    Called by the MCP dispatch endpoint when tool name is 'sql_query_tool'.
    Returns results as a JSON string — a list of row objects.

    Raises:
        ToolExecutionError: if 'query' argument missing, DB not found,
                            or SQLite raises an error during execution.
        SQLQueryForbiddenError: if the statement is not a SELECT.
    """
    sql_query = arguments.get("query")
    if not sql_query or not sql_query.strip():
        raise ToolExecutionError(
            tool_name="sql_query_tool",
            message="Required argument 'query' is missing or empty",
        )

    _validate_select_only(sql_query)

    logger.info("sql_query_tool executing: %s", sql_query[:120])

    try:
        conn = get_db_connection()
        try:
            cursor = conn.execute(sql_query)
            columns = [description[0] for description in cursor.description]
            sql_query_result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()
    except sqlite3.OperationalError as e:
        raise ToolExecutionError(
            tool_name="sql_query_tool",
            message=f"SQLite operational error: {e}",
        ) from e
    except sqlite3.DatabaseError as e:
        raise ToolExecutionError(
            tool_name="sql_query_tool",
            message=f"SQLite database error: {e}",
        ) from e

    logger.info("sql_query_tool returned %d rows", len(sql_query_result))
    return json.dumps(sql_query_result, default=str)
