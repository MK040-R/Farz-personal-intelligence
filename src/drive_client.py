"""
Google Drive client — lists and exports Google Meet transcript documents.

Google Meet saves a transcript Google Doc to the "Meet Recordings" folder in Drive
whenever transcription is enabled for a meeting. This module lists those docs and
exports their plain text content for the ingest pipeline.

No audio or video files are involved at any point.

Rules enforced here:
- Transcript text is returned to the caller in memory and never written to disk.
- Token refresh is a separate explicit call — never silently retried.

Async functions are used for FastAPI route handlers.
Sync functions are used inside Celery tasks.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel

from src.config import settings

logger = logging.getLogger(__name__)

_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"  # noqa: S105

_TRANSCRIPT_MIME_TYPE = "application/vnd.google-apps.document"


class DriveTranscript(BaseModel):
    file_id: str
    name: str
    created_time: datetime
    size_bytes: int | None = None


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


async def refresh_access_token(refresh_token: str) -> str:
    """Exchange a Google refresh token for a fresh access token (async)."""
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            _TOKEN_ENDPOINT,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    response.raise_for_status()
    data = response.json()
    token: str | None = data.get("access_token")
    if not token:
        raise ValueError("Token refresh response missing access_token")
    return token


def refresh_access_token_sync(refresh_token: str) -> str:
    """Exchange a Google refresh token for a fresh access token (sync, for Celery tasks)."""
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            _TOKEN_ENDPOINT,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    response.raise_for_status()
    data = response.json()
    token: str | None = data.get("access_token")
    if not token:
        raise ValueError("Token refresh response missing access_token")
    return token


# ---------------------------------------------------------------------------
# Drive listing (async — used by FastAPI routes)
# ---------------------------------------------------------------------------


async def _get_meet_folder_ids(
    client: httpx.AsyncClient,
    access_token: str,
) -> list[str]:
    """Return the Drive folder IDs for all folders named 'Meet Recordings'.

    Google Meet automatically saves transcripts to a folder with this name.
    Returns an empty list if no such folder exists yet.
    """
    meet_folder_query = (
        "mimeType='application/vnd.google-apps.folder'"
        " and name='Meet Recordings' and trashed=false"
    )
    params = {
        "q": meet_folder_query,
        "fields": "files(id)",
        "pageSize": "10",
    }
    response = await client.get(
        _DRIVE_FILES_URL,
        params=params,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code == 401:
        raise PermissionError("Google access token is invalid or expired")
    response.raise_for_status()
    return [f["id"] for f in response.json().get("files", [])]


async def list_meet_transcripts(
    access_token: str,
    lookback_days: int = 365,
) -> list[DriveTranscript]:
    """List Google Meet transcript documents from Drive created in the last lookback_days.

    Searches only inside 'Meet Recordings' folders for Google Doc files (the transcript
    documents that Google Meet saves automatically when transcription is enabled).

    Args:
        access_token: A valid Google access token with drive.readonly scope.
        lookback_days: How far back to look (default 365 days).

    Returns:
        List of DriveTranscript objects. Empty if none found.

    Raises:
        PermissionError: If the token is invalid or expired.
        httpx.HTTPStatusError: On other HTTP errors.
    """
    since = datetime.now(tz=UTC) - timedelta(days=lookback_days)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient(timeout=30.0) as client:
        folder_ids = await _get_meet_folder_ids(client, access_token)

        if folder_ids:
            parent_clause = " or ".join(f"'{fid}' in parents" for fid in folder_ids)
            query = (
                f"mimeType='{_TRANSCRIPT_MIME_TYPE}'"
                f" and ({parent_clause})"
                f" and createdTime >= '{since_str}'"
                f" and trashed=false"
            )
        else:
            # No Meet Recordings folder yet — fall back to name pattern
            query = (
                f"mimeType='{_TRANSCRIPT_MIME_TYPE}'"
                f" and name contains 'Meet'"
                f" and createdTime >= '{since_str}'"
                f" and trashed=false"
            )

        params = {
            "q": query,
            "fields": "files(id,name,createdTime,size)",
            "orderBy": "createdTime desc",
            "pageSize": "100",
        }

        response = await client.get(
            _DRIVE_FILES_URL,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code == 401:
        raise PermissionError("Google access token is invalid or expired")
    response.raise_for_status()

    files: list[dict[str, Any]] = response.json().get("files", [])
    transcripts: list[DriveTranscript] = []
    for f in files:
        try:
            transcripts.append(
                DriveTranscript(
                    file_id=f["id"],
                    name=f["name"],
                    created_time=datetime.fromisoformat(f["createdTime"].replace("Z", "+00:00")),
                    size_bytes=int(f["size"]) if f.get("size") else None,
                )
            )
        except (KeyError, ValueError) as exc:
            logger.warning("Skipping malformed Drive file entry: %s", exc)

    logger.debug(
        "Drive listing: %d transcripts found (lookback=%d days, folder_filter=%s)",
        len(transcripts),
        lookback_days,
        bool(folder_ids),
    )
    return transcripts


# ---------------------------------------------------------------------------
# Transcript export (sync — used by Celery ingest task)
# ---------------------------------------------------------------------------


def export_transcript_sync(access_token: str, file_id: str) -> str:
    """Export a Google Meet transcript Google Doc as plain text.

    Args:
        access_token: A valid Google access token with drive.readonly scope.
        file_id: The Google Drive file ID of the transcript Google Doc.

    Returns:
        Plain text content of the transcript.

    Raises:
        PermissionError: If the token is invalid or expired.
        httpx.HTTPStatusError: On other HTTP errors.
    """
    url = f"{_DRIVE_FILES_URL}/{file_id}/export"
    with httpx.Client(timeout=60.0) as client:
        response = client.get(
            url,
            params={"mimeType": "text/plain"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code == 401:
        raise PermissionError("Google access token is invalid or expired for transcript export")
    response.raise_for_status()

    text = response.text
    logger.info("Exported transcript %d chars for Drive file %s", len(text), file_id)
    return text
