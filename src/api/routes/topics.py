"""
Topics routes.

GET /topics           — list all topics across all conversations (newest conversation first)
GET /topics/{id}      — single topic with key quotes and source conversations
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_user
from src.database import get_client

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class TopicSummary(BaseModel):
    id: str
    label: str
    conversation_count: int
    latest_date: str | None


class TopicDetail(BaseModel):
    id: str
    label: str
    summary: str
    status: str
    key_quotes: list[str]
    conversation_id: str
    conversation_title: str
    meeting_date: str


# ---------------------------------------------------------------------------
# GET /topics
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[TopicDetail],
    summary="List all topics across all conversations",
)
def list_topics(
    limit: int = 100,
    offset: int = 0,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[TopicDetail]:
    """Return all topics for the current user, newest conversation first.

    Each topic includes its source conversation title and date for context.
    """
    user_id: str = current_user["sub"]
    raw_jwt: str = current_user["_raw_jwt"]
    db = get_client(raw_jwt)

    # Fetch topics joined with conversation metadata via two queries
    # (supabase-py doesn't support JOINs — fetch conversations separately)
    topics_result = (
        db.table("topics")
        .select("id, label, summary, status, key_quotes, conversation_id, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    topics = topics_result.data or []
    if not topics:
        return []

    # Fetch conversation metadata for all referenced conversations
    conv_ids = list({t["conversation_id"] for t in topics})
    convs_result = (
        db.table("conversations")
        .select("id, title, meeting_date")
        .eq("user_id", user_id)
        .in_("id", conv_ids)
        .execute()
    )
    conv_map = {c["id"]: c for c in (convs_result.data or [])}

    return [
        TopicDetail(
            id=t["id"],
            label=t["label"],
            summary=t["summary"],
            status=t["status"],
            key_quotes=t.get("key_quotes") or [],
            conversation_id=t["conversation_id"],
            conversation_title=conv_map.get(t["conversation_id"], {}).get("title", ""),
            meeting_date=conv_map.get(t["conversation_id"], {}).get("meeting_date", ""),
        )
        for t in topics
    ]


# ---------------------------------------------------------------------------
# GET /topics/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/{topic_id}",
    response_model=TopicDetail,
    summary="Get a single topic with its source conversation",
)
def get_topic(
    topic_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TopicDetail:
    """Return a single topic with its key quotes and source conversation."""
    user_id: str = current_user["sub"]
    raw_jwt: str = current_user["_raw_jwt"]
    db = get_client(raw_jwt)

    topic_result = (
        db.table("topics")
        .select("id, label, summary, status, key_quotes, conversation_id")
        .eq("id", topic_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not topic_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    t = topic_result.data[0]

    conv_result = (
        db.table("conversations")
        .select("id, title, meeting_date")
        .eq("id", t["conversation_id"])
        .eq("user_id", user_id)
        .execute()
    )
    conv = conv_result.data[0] if conv_result.data else {}

    return TopicDetail(
        id=t["id"],
        label=t["label"],
        summary=t["summary"],
        status=t["status"],
        key_quotes=t.get("key_quotes") or [],
        conversation_id=t["conversation_id"],
        conversation_title=conv.get("title", ""),
        meeting_date=conv.get("meeting_date", ""),
    )
