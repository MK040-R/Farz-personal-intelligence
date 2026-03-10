"""
Conversations routes — list and detail views.

GET /conversations            — paginated list of the user's conversations
GET /conversations/{id}       — full conversation detail with topics, commitments,
                                entities, and transcript segments
GET /conversations/{id}/connections — Phase 2 stub; always returns empty list
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


class ConversationSummary(BaseModel):
    id: str
    title: str
    source: str
    meeting_date: str
    duration_seconds: int | None
    status: str  # "processing" | "indexed"


class TopicOut(BaseModel):
    id: str
    label: str
    summary: str
    status: str
    key_quotes: list[str]


class CommitmentOut(BaseModel):
    id: str
    text: str
    owner: str
    due_date: str | None
    status: str


class EntityOut(BaseModel):
    id: str
    name: str
    type: str
    mentions: int


class SegmentOut(BaseModel):
    id: str
    speaker_id: str
    start_ms: int
    end_ms: int
    text: str


class ConversationDetail(BaseModel):
    conversation: ConversationSummary
    topics: list[TopicOut]
    commitments: list[CommitmentOut]
    entities: list[EntityOut]
    segments: list[SegmentOut]
    connections: list[Any]  # Phase 2 — always empty in Phase 1


# ---------------------------------------------------------------------------
# GET /conversations
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[ConversationSummary],
    summary="List all conversations for the current user",
)
def list_conversations(
    limit: int = 50,
    offset: int = 0,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[ConversationSummary]:
    """Return a paginated list of conversations, newest first.

    Each item includes the conversation's current processing status
    (``processing`` until AI extraction completes, then ``indexed``).
    """
    user_id: str = current_user["sub"]
    raw_jwt: str = current_user["_raw_jwt"]
    db = get_client(raw_jwt)

    result = (
        db.table("conversations")
        .select("id, title, source, meeting_date, duration_seconds, status")
        .eq("user_id", user_id)
        .order("meeting_date", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return [
        ConversationSummary(
            id=row["id"],
            title=row["title"],
            source=row["source"],
            meeting_date=row["meeting_date"],
            duration_seconds=row.get("duration_seconds"),
            status=row.get("status", "processing"),
        )
        for row in (result.data or [])
    ]


# ---------------------------------------------------------------------------
# GET /conversations/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get full detail for a single conversation",
)
def get_conversation(
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ConversationDetail:
    """Return a conversation with its topics, commitments, entities, and segments.

    Topics, commitments, and entities are only present once extraction completes
    (conversation.status == 'indexed'). While status is 'processing', those lists
    are empty.
    """
    user_id: str = current_user["sub"]
    raw_jwt: str = current_user["_raw_jwt"]
    db = get_client(raw_jwt)

    # --- Conversation ---
    conv_result = (
        db.table("conversations")
        .select("id, title, source, meeting_date, duration_seconds, status")
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not conv_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    conv = conv_result.data[0]

    # --- Topics ---
    topics_result = (
        db.table("topics")
        .select("id, label, summary, status, key_quotes")
        .eq("conversation_id", conversation_id)
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )

    # --- Commitments ---
    commitments_result = (
        db.table("commitments")
        .select("id, text, owner, due_date, status")
        .eq("conversation_id", conversation_id)
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )

    # --- Entities ---
    entities_result = (
        db.table("entities")
        .select("id, name, type, mentions")
        .eq("conversation_id", conversation_id)
        .eq("user_id", user_id)
        .order("mentions", desc=True)
        .execute()
    )

    # --- Transcript segments ---
    segments_result = (
        db.table("transcript_segments")
        .select("id, speaker_id, start_ms, end_ms, text")
        .eq("conversation_id", conversation_id)
        .eq("user_id", user_id)
        .order("start_ms")
        .execute()
    )

    return ConversationDetail(
        conversation=ConversationSummary(
            id=conv["id"],
            title=conv["title"],
            source=conv["source"],
            meeting_date=conv["meeting_date"],
            duration_seconds=conv.get("duration_seconds"),
            status=conv.get("status", "processing"),
        ),
        topics=[
            TopicOut(
                id=t["id"],
                label=t["label"],
                summary=t["summary"],
                status=t["status"],
                key_quotes=t.get("key_quotes") or [],
            )
            for t in (topics_result.data or [])
        ],
        commitments=[
            CommitmentOut(
                id=c["id"],
                text=c["text"],
                owner=c["owner"],
                due_date=c.get("due_date"),
                status=c["status"],
            )
            for c in (commitments_result.data or [])
        ],
        entities=[
            EntityOut(
                id=e["id"],
                name=e["name"],
                type=e["type"],
                mentions=e["mentions"],
            )
            for e in (entities_result.data or [])
        ],
        segments=[
            SegmentOut(
                id=s["id"],
                speaker_id=s["speaker_id"],
                start_ms=s["start_ms"],
                end_ms=s["end_ms"],
                text=s["text"],
            )
            for s in (segments_result.data or [])
        ],
        connections=[],  # Phase 2
    )


# ---------------------------------------------------------------------------
# GET /conversations/{id}/connections  — Phase 2 stub
# ---------------------------------------------------------------------------


@router.get(
    "/{conversation_id}/connections",
    summary="Get connections for a conversation (Phase 2 stub)",
)
def get_connections(
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, list[Any]]:
    """Phase 2 stub — connections are not yet implemented.

    Returns an empty list so the frontend can code against the agreed shape.
    The conversation existence is verified so 404 is still returned for
    unknown IDs.
    """
    user_id: str = current_user["sub"]
    raw_jwt: str = current_user["_raw_jwt"]
    db = get_client(raw_jwt)

    exists = (
        db.table("conversations")
        .select("id")
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not exists.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return {"connections": []}
