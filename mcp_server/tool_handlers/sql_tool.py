from __future__ import annotations

import json
import logging
import os
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
            message=(
                f"Database not found at {_DB_PATH}. "
                "Run 'make seed-db' to generate it."
            ),
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