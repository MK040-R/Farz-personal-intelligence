# Roadmap: Farz

## Overview

The backend intelligence pipeline is fully built (Phase 0a, 0, Phase 1 Waves 1-3). What remains is surfacing that intelligence to users. This roadmap covers four delivery phases: the frontend web app (built by Codex), topic arc and commitment surfaces (new backend + API), connection detection (new backend + API), and calendar-driven pre-meeting briefs (new backend + scheduler). When all four phases are complete, a user can walk into any meeting fully briefed by their own history — automatically.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Frontend Web App** - Codex builds the Next.js UI that surfaces all existing backend capabilities to users
- [ ] **Phase 2: Topic Arcs and Commitment Tracker** - Backend computes topic timelines; user can track open commitments across meetings
- [ ] **Phase 3: Connection Graph** - Backend detects meeting connections; user can see which meetings share topics or entities
- [ ] **Phase 4: Calendar Sync and Pre-Meeting Briefs** - Google Calendar integration triggers automated briefs before each meeting

## Phase Details

### Phase 1: Frontend Web App
**Goal**: Users can access Farz through a web browser, log in, import their meetings, and interact with all intelligence the backend already produces
**Depends on**: Nothing (backend is already complete; this surfaces it)
**Requirements**: FRONT-01, FRONT-02, FRONT-03, FRONT-04, FRONT-05, FRONT-06
**Success Criteria** (what must be TRUE):
  1. User can open the web app, click "Sign in with Google," and land on their dashboard without any backend errors
  2. User can trigger Drive retro-import from the UI and watch a live progress indicator update as meetings are indexed
  3. User can browse a paginated list of all their imported meetings and click one to see its extracted topics and commitments
  4. User can click any topic or commitment entry and see the exact source quote with speaker name and timestamp highlighted
  5. User can type a natural-language question in a search box and receive ranked meeting segment results with source citations
**Plans**: TBD

Plans:
- [ ] 01-01: Auth flow and dashboard shell (Google OAuth callback, session cookie, empty state)
- [ ] 01-02: Onboarding and import UI (Drive import trigger, live progress via polling /onboarding/import/status)
- [ ] 01-03: Meeting list and conversation detail views (topics, commitments, citations)
- [ ] 01-04: Semantic search UI (question input, ranked results, citation display)

### Phase 2: Topic Arcs and Commitment Tracker
**Goal**: Users can see how subjects evolved across meetings over time, and can manage open commitments in one consolidated view
**Depends on**: Phase 1
**Requirements**: TARC-01, TARC-02, CMMT-01, CMMT-02
**Success Criteria** (what must be TRUE):
  1. User can navigate to a topic and see a chronological timeline of every meeting where that topic appeared, with dates and brief context per entry
  2. User can click any timeline entry and jump to the exact transcript segment that produced it
  3. User can open a commitments view showing all open commitments across all meetings, filterable by assignee and showing deadline where extracted
  4. User can mark a commitment as resolved and see it removed from the open commitments list immediately
**Plans**: TBD

Plans:
- [ ] 02-01: Topic Arc backend — compute and store topic_arcs and topic_arc_conversation_links from existing topics + conversations data
- [ ] 02-02: Topic Arc API endpoint — GET /topics/{id}/arc returning timeline with segment citations
- [ ] 02-03: Commitment tracker API — GET /commitments with filters, PATCH /commitments/{id} mark-resolved (stub exists, needs full implementation)
- [ ] 02-04: Topic arc and commitment UI surfaces in the frontend (coordinate with Codex)

### Phase 3: Connection Graph
**Goal**: Users can see which meetings are connected by shared topics or entities, and understand exactly what links them
**Depends on**: Phase 2
**Requirements**: CONN-01, CONN-02
**Success Criteria** (what must be TRUE):
  1. User can open a meeting and see a list of other meetings that share topics or entities with it
  2. Each connection entry clearly states what links the two meetings (shared entity name, topic label, or commitment thread) — not just a list of meeting titles
  3. The /conversations/{id}/connections endpoint returns real data (currently a stub returning [])
**Plans**: TBD

Plans:
- [ ] 03-01: Connection detection backend — Celery task or on-demand computation comparing topic/entity overlap across conversations, writing to connections and connection_linked_items tables
- [ ] 03-02: Connections API endpoint — complete the stub at GET /conversations/{id}/connections with real data and linked item explanations
- [ ] 03-03: Connection UI surface — meeting connection display within conversation detail view (coordinate with Codex)

### Phase 4: Calendar Sync and Pre-Meeting Briefs
**Goal**: Users receive a complete, cited pre-meeting brief automatically before each calendar event — no manual action required
**Depends on**: Phase 3
**Requirements**: CAL-01, CAL-02, BRIEF-01, BRIEF-02, BRIEF-03
**Success Criteria** (what must be TRUE):
  1. Google Calendar events are auto-linked to imported meetings by time-window matching — user sees the calendar event name on each meeting that corresponds to it
  2. Upcoming meetings are read from Google Calendar; a brief is generated and ready 10-15 minutes before each event starts
  3. The brief contains relevant topic context, open commitments, and connected meeting references — all three components present
  4. Every claim or fact in a brief links back to a specific transcript segment the user can click to verify
  5. The /calendar/today endpoint returns real upcoming meetings (currently a stub returning [])
**Plans**: TBD

Plans:
- [ ] 04-01: Google Calendar sync backend — read calendar events via Google Calendar API, match to conversations by time window, write links to conversations table (drive_file_id or new calendar_event_id column)
- [ ] 04-02: Brief generation Celery task — compose brief from topic_arcs + commitments + connections scoped to the meeting's participants and topic overlap; use claude-opus-4-6 sparingly
- [ ] 04-03: Brief scheduler — Celery Beat job or cron that reads upcoming events and fires brief generation at T-12 minutes
- [ ] 04-04: Brief API and citation surface — GET /briefs/{id}, citation links to segment IDs, brief display in frontend (coordinate with Codex)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Frontend Web App | 0/4 | Not started | - |
| 2. Topic Arcs and Commitment Tracker | 0/4 | Not started | - |
| 3. Connection Graph | 0/3 | Not started | - |
| 4. Calendar Sync and Pre-Meeting Briefs | 0/4 | Not started | - |
