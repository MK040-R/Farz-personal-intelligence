"""
Index stats route.

GET /index/stats — return counts and last-updated timestamp from the user's index
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_user
from src.database import get_client

logger = logging.getLogger(__name__)

router = APIRouter()


class IndexStats(BaseModel):
    conversation_count: int
    topic_count: int
    commitment_count: int
    entity_count: int
    last_updated_at: str | None


@router.get(
    "/stats",
    response_model=IndexStats,
    summary="Return counts and last-updated time from the user's index",
)
def get_index_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> IndexStats:
    """Return aggregate counts for the current user's intelligence index.

    Counts are maintained incrementally by background workers — they reflect
    the state at the time of last extraction, not a live COUNT(*).
    entity_count is computed live (small table, fast query).
    """
    user_id: str = current_user["sub"]
    raw_jwt: str = current_user["_raw_jwt"]
    db = get_client(raw_jwt)

    index_result = (
        db.table("user_index")
        .select("conversation_count, topic_count, commitment_count, last_updated")
        .eq("user_id", user_id)
        .execute()
    )
    if not index_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found. Please sign in again.",
        )
    idx = index_result.data[0]

    # entity_count is not stored in user_index — compute it live
    entity_result = (
        db.table("entities")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    entity_count = entity_result.count or 0

    return IndexStats(
        conversation_count=idx.get("conversation_count", 0),
        topic_count=idx.get("topic_count", 0),
        commitment_count=idx.get("commitment_count", 0),
        entity_count=entity_count,
        last_updated_at=idx.get("last_updated"),
    )
