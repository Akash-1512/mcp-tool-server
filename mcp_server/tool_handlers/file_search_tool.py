from __future__ import annotations

import json
import logging
import pathlib

from mcp_server.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)

# LOCAL DEMO — local filesystem, zero cost
_FILES_DIR = pathlib.Path(__file__).parent.parent.parent / "data" / "files"

# ─────────────────────────────────────────────────────────────────────────────
# [PRODUCTION] Azure Blob Storage — uncomment to enable
# Requires: AZURE_BLOB_CONNECTION_STRING, AZURE_BLOB_CONTAINER_NAME in .env
# ─────────────────────────────────────────────────────────────────────────────
# from azure.storage.blob import BlobServiceClient
# import os
# def _get_blob_client():
#     return BlobServiceClient.from_connection_string(
#         os.getenv("AZURE_BLOB_CONNECTION_STRING")
#     ).get_container_client(os.getenv("AZURE_BLOB_CONTAINER_NAME"))


# ─── Handler ──────────────────────────────────────────────────────────────────


async def handle_file_search(arguments: dict) -> str:
    """Search data/files/ for files matching a keyword in name or content.

    Searches all files in the files directory case-insensitively.
    Returns a JSON list of match objects, each with:
        - file_name: name of the matching file
        - matched_lines: list of lines containing the keyword
        - preview: first 200 chars of first matching line

    Raises:
        ToolExecutionError: if keyword is missing/empty or files dir not found
    """
    keyword = arguments.get("keyword")
    if not keyword or not keyword.strip():
        raise ToolExecutionError(
            tool_name="file_search_tool",
            message="Required argument 'keyword' is missing or empty",
        )

    if not _FILES_DIR.exists():
        raise ToolExecutionError(
            tool_name="file_search_tool",
            message=f"Files directory not found at {_FILES_DIR}",
        )

    keyword_lower = keyword.strip().lower()
    logger.info("file_search_tool searching for keyword: '%s'", keyword)

    file_search_results = []

    for file_path in sorted(_FILES_DIR.iterdir()):
        if not file_path.is_file():
            continue

        filename_match = keyword_lower in file_path.name.lower()

        try:
            file_content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            logger.warning("Could not read file %s: %s", file_path.name, e)
            continue

        matched_lines = [
            line.strip() for line in file_content.splitlines() if keyword_lower in line.lower()
        ]

        if filename_match or matched_lines:
            preview = (
                matched_lines[0][:200] if matched_lines else f"Filename match: {file_path.name}"
            )
            file_search_results.append(
                {
                    "file_name": file_path.name,
                    "file_path": str(
                        file_path.relative_to(pathlib.Path(__file__).parent.parent.parent)
                    ),
                    "matched_lines": matched_lines[:5],
                    "preview": preview,
                }
            )

    logger.info(
        "file_search_tool found %d matching files for keyword '%s'",
        len(file_search_results),
        keyword,
    )

    if not file_search_results:
        return json.dumps([])

    return json.dumps(file_search_results)
