"""
Calendar route — today's briefing context.

GET /calendar/today — upcoming meetings today + open commitments relevant to them

Phase 1 stub: returns today's date with empty meetings and the user's open
commitments. Full Google Calendar integration is Phase 2.
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.deps import get_current_user
from src.database import get_client

logger = logging.getLogger(__name__)

router = APIRouter()


class UpcomingMeeting(BaseModel):
    id: str
    title: str
    start_time: str
    attendees: list[str]


class OpenCommitment(BaseModel):
    id: str
    text: str
    owner: str
    due_date: str | None
    conversation_title: str


class TodayBriefing(BaseModel):
    date: str
    upcoming_meetings: list[UpcomingMeeting]
    open_commitments: list[OpenCommitment]


@router.get(
    "/today",
    response_model=TodayBriefing,
    summary="Today's briefing: upcoming meetings and open commitments",
)
def get_today(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TodayBriefing:
    """Return today's context: upcoming meetings and open commitments.

    Phase 1: upcoming_meetings is always empty (Google Calendar sync is Phase 2).
    open_commitments returns the user's 20 most recent open commitments with
    conversation context.
    """
    user_id: str = current_user["sub"]
    raw_jwt: str = current_user["_raw_jwt"]
    db = get_client(raw_jwt)

    # Open commitments (most recently created, capped at 20)
    commitments_result = (
        db.table("commitments")
        .select("id, text, owner, due_date, conversation_id")
        .eq("user_id", user_id)
        .eq("status", "open")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    commitments = commitments_result.data or []

    conv_titles: dict[str, str] = {}
    if commitments:
        conv_ids = list({c["conversation_id"] for c in commitments})
        convs_result = (
            db.table("conversations")
            .select("id, title")
            .eq("user_id", user_id)
            .in_("id", conv_ids)
            .execute()
        )
        conv_titles = {c["id"]: c["title"] for c in (convs_result.data or [])}

    return TodayBriefing(
        date=date.today().isoformat(),
        upcoming_meetings=[],  # Phase 2: Google Calendar integration
        open_commitments=[
            OpenCommitment(
                id=c["id"],
                text=c["text"],
                owner=c["owner"],
                due_date=c.get("due_date"),
                conversation_title=conv_titles.get(c["conversation_id"], ""),
            )
            for c in commitments
        ],
    )
