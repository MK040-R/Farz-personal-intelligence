"""
Shared helpers for conversation ↔ calendar event linking.

These utilities are used by both read routes and background tasks so the
matching logic stays consistent while heavy sync work can move off the request
path.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.calendar_client import CalendarEvent

MATCH_WINDOW_SECONDS = 8 * 60 * 60


def parse_iso_datetime(value: Any) -> datetime | None:
    """Parse an ISO-like datetime value into a timezone-aware datetime."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def best_match_event(
    conversation_time: datetime,
    events: list[CalendarEvent],
    used_event_ids: set[str],
) -> CalendarEvent | None:
    """Return the nearest unused calendar event within the allowed window."""
    best: tuple[float, CalendarEvent] | None = None
    for event in events:
        if event.event_id in used_event_ids:
            continue
        distance_seconds = abs((conversation_time - event.start_time).total_seconds())
        if distance_seconds > MATCH_WINDOW_SECONDS:
            continue
        if best is None or distance_seconds < best[0]:
            best = (distance_seconds, event)
    return best[1] if best else None


def sync_conversation_calendar_links(
    db: Any,
    user_id: str,
    conversations: list[dict[str, Any]],
    events: list[CalendarEvent],
) -> int:
    """Link conversations to the nearest calendar events and return link count."""
    if not conversations or not events:
        return 0

    parsed_conversations: list[tuple[str, datetime]] = []
    for row in conversations:
        conversation_id = row.get("id")
        if not isinstance(conversation_id, str) or not conversation_id.strip():
            continue
        meeting_date = parse_iso_datetime(row.get("meeting_date"))
        if meeting_date is None:
            continue
        parsed_conversations.append((conversation_id, meeting_date))

    parsed_conversations.sort(key=lambda item: item[1])

    linked_count = 0
    used_event_ids: set[str] = set()
    for conversation_id, meeting_date in parsed_conversations:
        match = best_match_event(meeting_date, events, used_event_ids)
        if match is None:
            continue

        (
            db.table("conversations")
            .update({"calendar_event_id": match.event_id})
            .eq("user_id", user_id)
            .eq("id", conversation_id)
            .execute()
        )
        used_event_ids.add(match.event_id)
        linked_count += 1

    return linked_count
