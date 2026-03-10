# Farz - Interface Design System

## Direction: "The Private Office"

> A private workspace for serious operators. Dark forest foundations, warm cream text, and one gold accent for signal. Quiet authority, dense clarity, no visual theatrics.

---

## Product Context

**Who this is for:** Working professionals (PMs, team leads, founders, cross-functional operators) who context-switch across meetings and need reliable recall.

**What they must do:** Recover decisions, prepare for upcoming meetings, track commitments, and follow long-running topics without rereading raw transcripts.

**How it should feel:** Deliberate, trusted, and focused. The interface should read like an executive briefing surface, not a consumer productivity app.

---

## Design Direction

### Color

Dark forest base, cream ink, single gold accent. Accent is the only chromatic signal.

| Token                    | Value                         | Usage |
| ------------------------ | ----------------------------- | ----- |
| `--bg-base`              | `#0A1510`                     | App background; near-black forest canvas |
| `--bg-surface`           | `#101D17`                     | Primary cards, panels, sidebar surfaces |
| `--bg-surface-raised`    | `#14231C`                     | Overlays, dropdowns, raised surfaces |
| `--bg-control`           | `#0E1A14`                     | Inputs, search bars, text areas |
| `--ink-primary`          | `#F0EDE4`                     | Primary text and headings |
| `--ink-secondary`        | `#CEC7B8`                     | Secondary labels and helper copy |
| `--ink-tertiary`         | `#AFA894`                     | Metadata, timestamps, low-emphasis details |
| `--ink-muted`            | `#7E786A`                     | Disabled text, placeholders |
| `--accent`               | `#C9A84C`                     | Focus state, links, citations, active controls |
| `--accent-subtle`        | `rgba(201, 168, 76, 0.16)`    | Subtle accent backgrounds and chips |
| `--accent-hover`         | `#D6B867`                     | Hover/active variant of accent |
| `--border-standard`      | `rgba(240, 237, 228, 0.18)`   | Default container separation |
| `--border-soft`          | `rgba(240, 237, 228, 0.10)`   | Quiet grouping dividers |
| `--border-emphasis`      | `rgba(201, 168, 76, 0.55)`    | Active/selected outlines |
| `--shadow-card`          | `none`                        | No shadows; depth comes from borders only |
| `--shadow-raised`        | `none`                        | No shadows on overlays |
| `--semantic-open`        | `#C9A84C`                     | Open/attention state (same accent family) |
| `--semantic-resolved`    | `#9E9888`                     | Resolved/de-emphasized neutral state |
| `--semantic-destructive` | `#B5AE9C`                     | Destructive actions via neutral contrast + copy/icon |

### Typography

Use **Plus Jakarta Sans** for interface language and **JetBrains Mono** for transcript/data surfaces.

| Role                     | Font              | Weight | Size    | Notes |
| ------------------------ | ----------------- | ------ | ------- | ----- |
| Page headings            | Plus Jakarta Sans | 700    | 22-28px | Letter spacing `-0.01em` |
| Card titles              | Plus Jakarta Sans | 600    | 15px    | Tight, compact headings |
| Body                     | Plus Jakarta Sans | 400    | 14px    | Line height 1.6 |
| Labels / section headers | Plus Jakarta Sans | 500    | 11px    | Uppercase, `0.06em` tracking |
| Data / timestamps        | JetBrains Mono    | 400    | 12px    | Tabular style, `--ink-tertiary` |
| Transcript               | JetBrains Mono    | 400    | 12.5px  | High readability for long text blocks |

### Depth Strategy

**Borders only. No shadows.**

Depth is established by contrast between surfaces and explicit border hierarchy.

- `--bg-base` anchors the canvas
- `--bg-surface` and `--bg-surface-raised` layer structure
- `--border-standard`, `--border-soft`, and `--border-emphasis` define hierarchy
- Controls rely on border and ink contrast, not glow or shadow

### Spacing

Base unit: **4px**.

| Scale | Value | Usage |
| ----- | ----- | ----- |
| `xs`  | 4px   | Tight inline spacing, icon gaps |
| `sm`  | 8px   | Small control interiors |
| `md`  | 16px  | Card and input padding |
| `lg`  | 20px  | Related content groups |
| `xl`  | 32px  | Major section separation |
| `2xl` | 48px  | Page-level breathing room |

### Border Radius

Slightly restrained radius values to keep the surface professional.

| Scale  | Value | Usage |
| ------ | ----- | ----- |
| `sm`   | 6px   | Chips, compact badges |
| `md`   | 10px  | Cards, inputs, buttons |
| `lg`   | 14px  | Drawers and overlays |
| `pill` | 999px | Status pills |

---

## Signature Element - The Arc Thread

The **Topic Arc** is the visual signature of Farz. It should read as an evidence trail, not decoration.

- Thread: 1.5px line using `--accent` (reduced opacity between points)
- Active node: full `--accent`
- Inactive node: `--bg-surface` fill with `--border-standard` ring
- Usage: Search result timelines and any arc-based context view

---

## Navigation

Dark surface sidebar, restrained contrast, precise active state.

- Background: `--bg-surface`
- Width: 220px
- Active item: `--accent` text + `--accent-subtle` fill + `--border-emphasis`
- Default item: `--ink-secondary`; hover to `--ink-primary`
- Logo: Plus Jakarta Sans 700, `--ink-primary`

Primary nav: Dashboard, Search, Meetings, Commitments, Insights.

---

## Key Component Patterns

### Meeting Card

- Surface: `--bg-surface`, `1px` `--border-standard`, radius `md`
- Title: `--ink-primary`, Plus Jakarta Sans 600, 15px
- Metadata: `--ink-tertiary`, JetBrains Mono 12px
- "Brief ready" chip: `--accent-subtle` background, `--accent` text, `pill` radius
- Topic chips: `--accent-subtle` + `--accent`, no additional colors

### Commitment Item

- Left rail: 3px `--accent`
- Commitment text: `--ink-primary`, 14px
- Attribution/date: `--ink-tertiary`, JetBrains Mono 12px
- Status states:
  - open uses `--semantic-open`
  - resolved uses `--semantic-resolved`
  - destructive actions use neutral `--semantic-destructive` plus explicit copy/icon

### Search / Topic Arc Result

- Arc thread and nodes follow signature element spec
- Arc point container: `--bg-surface`, `1px` `--border-standard`, 20px padding
- Citation line: `--ink-tertiary`, JetBrains Mono 12px
- Jump links and focus states: `--accent` / `--accent-hover`
- Status note: bordered block with `--accent-subtle` fill

### Pre-Meeting Brief

- Hero section: `--bg-surface`, `1px` `--border-emphasis`, top edge accent allowed
- Section separators: `--border-soft` with generous vertical spacing
- Agenda and commitment blocks: compact structure, no ornamental styling

---

## What This Is Not

- No light-mode surfaces or white-first visual hierarchy
- No multi-accent palette
- No shadow-led elevation
- No gradients, glow effects, or decorative flourishes
- No saturated semantic green/red system
- No loose, playful, or consumer-style spacing patterns
- No monospace for non-data/non-transcript content
