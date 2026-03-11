# Requirements: Farz

**Defined:** 2026-03-11
**Core Value:** A working professional can ask "What did we decide about X?" and get an accurate, cited answer across all their past meetings — without doing anything manually.

## Already Complete

Phases 0a, 0, and Phase 1 Waves 1–3 are built and verified. These requirements are done:

- ✓ Google OAuth login, session management, RLS-enforced auth
- ✓ Google Drive retro-import pipeline (enumerate, ingest, idempotency)
- ✓ Deepgram transcription via Drive streaming (audio never stored)
- ✓ TranscriptSegment storage (speaker_id, start_ms, end_ms, text)
- ✓ LLM extraction: topics, commitments, entities with segment citations
- ✓ pgvector embeddings (1536-dim) on transcript_segments
- ✓ Semantic search endpoint (POST /search, cosine similarity, user-scoped)
- ✓ API routes: auth, conversations, topics, commitments, search, onboarding, health
- ✓ 38 unit tests passing, CI running

## v1 Requirements

Requirements for the remaining MVP scope. Each maps to a roadmap phase.

### Frontend

- [ ] **FRONT-01**: User can log in via Google OAuth from the web app
- [ ] **FRONT-02**: User can trigger Google Drive retro-import and see live progress (% indexed)
- [ ] **FRONT-03**: User can browse a list of all their indexed meetings
- [ ] **FRONT-04**: User can open a meeting and see the extracted topics and commitments for that meeting
- [ ] **FRONT-05**: User can click any topic or commitment to see the exact source quote with speaker name and timestamp
- [ ] **FRONT-06**: User can type a question and get semantically matched meeting segments with source citations

### Topic Arc

- [ ] **TARC-01**: User can view a timeline showing how a topic evolved across multiple meetings in chronological order
- [ ] **TARC-02**: Each entry in the Topic Arc timeline links to its source transcript segment

### Connections

- [ ] **CONN-01**: User can see which meetings are connected by shared topics or entities
- [ ] **CONN-02**: Each connection shows what links the meetings (shared entity, topic, or commitment thread)

### Briefs

- [ ] **BRIEF-01**: User receives a pre-meeting brief 10–15 minutes before a calendar event starts
- [ ] **BRIEF-02**: The brief includes relevant topic context, open commitments, and related meeting connections
- [ ] **BRIEF-03**: Every claim in a brief links back to a source transcript segment

### Commitments

- [ ] **CMMT-01**: User can view all open commitments across all meetings, with assignee and deadline where available
- [ ] **CMMT-02**: User can mark a commitment as resolved

### Calendar

- [ ] **CAL-01**: Google Calendar sync auto-links imported meetings to calendar events by time window
- [ ] **CAL-02**: Upcoming meetings are read from Google Calendar to trigger brief generation at T-12 minutes

## v2 Requirements

Deferred — not in current roadmap.

### Desktop

- **DESK-01**: Native Mac/Windows desktop app (Electron) captures system audio without a bot
- **DESK-02**: Real-time Deepgram streaming WebSocket integration for live transcription

### Additional Integrations

- **INTG-01**: Gmail integration (gmail.readonly scope) for email context in briefs
- **INTG-02**: Slack integration for cross-channel conversation context

### Scale & Infrastructure

- **INFRA-01**: Migrate from Render.com to AWS ECS + RDS + ElastiCache
- **INFRA-02**: pgvector ivfflat/hnsw ANN index for sub-200ms p95 search at scale
- **INFRA-03**: Formal DPA with Anthropic and OpenAI before external user onboarding

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile app | Web-first; mobile is post-MVP |
| Bot-based recording (Fireflies/Otter model) | Privacy constraint — no bots, ever |
| Admin panel with user content visibility | Architectural constraint — no admin reads user data |
| Soft-delete / deleted_at columns | Architectural constraint — hard-delete only, always |
| Manual file upload endpoint | Retro-import delivers instant history; manual upload adds friction with no benefit |
| Electron desktop app | Phase 3 — intelligence layer must be validated first |
| SOC 2 / GDPR / UAE ADGM compliance | Phase 3+ concern |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FRONT-01 | Phase 1 — Frontend Web App | Pending |
| FRONT-02 | Phase 1 — Frontend Web App | Pending |
| FRONT-03 | Phase 1 — Frontend Web App | Pending |
| FRONT-04 | Phase 1 — Frontend Web App | Pending |
| FRONT-05 | Phase 1 — Frontend Web App | Pending |
| FRONT-06 | Phase 1 — Frontend Web App | Pending |
| TARC-01 | Phase 2 — Topic Arcs and Commitment Tracker | Pending |
| TARC-02 | Phase 2 — Topic Arcs and Commitment Tracker | Pending |
| CMMT-01 | Phase 2 — Topic Arcs and Commitment Tracker | Pending |
| CMMT-02 | Phase 2 — Topic Arcs and Commitment Tracker | Pending |
| CONN-01 | Phase 3 — Connection Graph | Pending |
| CONN-02 | Phase 3 — Connection Graph | Pending |
| BRIEF-01 | Phase 4 — Calendar Sync and Pre-Meeting Briefs | Pending |
| BRIEF-02 | Phase 4 — Calendar Sync and Pre-Meeting Briefs | Pending |
| BRIEF-03 | Phase 4 — Calendar Sync and Pre-Meeting Briefs | Pending |
| CAL-01 | Phase 4 — Calendar Sync and Pre-Meeting Briefs | Pending |
| CAL-02 | Phase 4 — Calendar Sync and Pre-Meeting Briefs | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-11*
*Last updated: 2026-03-11 after roadmap creation*
