## HITL Admin Panel Logic — Backend Integration Brief

### Purpose
- **Goal**: Enable human-in-the-loop (HITL) handling of conversations flagged by the bot or rules, with clear state transitions, realtime updates, and auditability.

### Data model used by the UI
- **Conversations**: `status`, `priority`, `assigned_admin_id`, `last_message_at`, intended flags `human_handling`, `rag_enabled`, optional `escalation_reason`, `escalation_timestamp`.
- **Messages**: `sender_type` (`user`|`bot`|`human`), `requires_human` (flag raised by bot/rules), `human_replied` (set when admin replies), `metadata`.
- **Admin actions**: Audit rows for admin operations (e.g., reply, assign/release human, control toggles).

### Realtime behavior
- UI subscribes to `messages` and `conversations` for live updates.
- Conversations page implements robust event-specific handlers and polling fallbacks; HITL page refetches on change.

### HITL page logic (Admin focus)
- **View**: Lists conversations needing human attention (filter by `human_handling` or `status = 'escalated'`).
- **Assign/Release**: Toggle `human_handling` and switch `status` (`escalated` ↔ `active`); set/clear `assigned_admin_id`.
- **Human reply**: Insert a `human` message (set `human_replied = true`, `requires_human = false`), then reset conversation back to bot (`human_handling = false`, `status = 'active'`, update `last_message_at`).
- **Outbound**: HITL page only records replies in DB; it does not send to the end user directly.

### Conversations page logic (Full monitor)
- **Filters/search**: `all`/`active`/`escalated`/`resolved`, search by `user_id`.
- **Human reply**: Insert `human` message, set conversation to `active`, send reply to end user (current implementation uses an internal API to Facebook Messenger), log to `admin_actions`.
- **Assign/Release**: Same intent as HITL page (escalated ↔ active); should use `human_handling` for consistency.
- **Resilience**: Event-specific realtime handlers plus per-conversation and global polling fallbacks.

### Key HITL concepts
- **Message-level trigger**: Bot/backend sets `requires_human = true` on a message to pull conversation into HITL.
- **Conversation-level control**: `human_handling` indicates active human control; `assigned_admin_id` tracks owner; `status` cycles through `active`/`escalated`/`resolved`/`closed`.
- **Return-to-bot**: A human reply sets `human_replied` and resets conversation to `active` so the bot resumes.
- **Auditability**: All admin actions should be appended to `admin_actions`.
- **RAG control (planned)**: Toggle `rag_enabled` per conversation; adjust `priority` as needed.

### Inconsistencies to resolve
- **Schema vs UI fields**: UI references `human_handling`, `rag_enabled`, `escalation_*` but these are not yet in the current schema.
- **Field naming**: Keep `requires_human` at message-level only; use `human_handling` at conversation-level (remove any conversation-level `requires_human`).
- **RLS**: Current policies are read-only. Writes must go via secure server/service role or admin-aware RLS.
- **Mock API**: Some HITL components call a service that currently returns mock data; backend endpoints should replace these.

### Minimal backend contract
- **Schema updates (conversations)**
  - Add: `human_handling BOOLEAN NOT NULL DEFAULT false`, `rag_enabled BOOLEAN NOT NULL DEFAULT true`, `escalation_reason TEXT NULL`, `escalation_timestamp TIMESTAMPTZ NULL`.
  - Keep: `status`, `priority`, `assigned_admin_id`, `last_message_at`.
- **Messages**
  - Use `requires_human` and `human_replied` to drive HITL; optional `confidence_score` and `metadata` for context.
- **Realtime**
  - Ensure replication/WAL is enabled for `messages` and `conversations` so clients receive live events.
- **Endpoints**
  - Health: `GET /admin/health`.
  - Lists: `GET /admin/conversations` (filters), `GET /admin/conversations/escalated`, `GET /admin/conversations/active`.
  - Conversation status: `GET /admin/conversation/{conversation_id}/status`.
  - Messages: `GET /admin/conversation/{conversation_id}/messages`.
  - Control: `POST /admin/conversation/control` with `action` in `{assign_human, release_human, disable_rag, enable_rag, close_conversation}`; update state and write `admin_actions`.
  - Priority: `PUT /admin/conversation/{conversation_id}/priority`.
  - Mark message: `POST /admin/message/{message_id}/mark-human-replied`.

### Action → state mapping
- **assign_human**: `human_handling = true`, `status = 'escalated'`, `assigned_admin_id = <admin>`, optionally set `escalation_reason/timestamp`.
- **release_human**: `human_handling = false`, `status = 'active'`, `assigned_admin_id = null`.
- **disable_rag / enable_rag**: Toggle `rag_enabled`.
- **close_conversation**: `status = 'closed'`.
- **human reply**: Insert `human` message with `human_replied = true` and `requires_human = false`; set conversation `human_handling = false`, `status = 'active'`, update `last_message_at`.

### Security and audit
- Prefer server-owned writes (service role) or admin-aware RLS policies.
- Log all admin actions to `admin_actions` with `admin_id`, `action_type`, `conversation_id`, and `details`.

### Outbound messaging
- If backend will own outbound sending to channels (e.g., Messenger), provide an endpoint the UI can call and return delivery status so the UI reflects success/failure.

### Integration checklist
- Add missing conversation columns and backfill defaults.
- Implement endpoints listed above and replace mock responses.
- Unify UI and backend on `human_handling` (conversation-level) and `requires_human` (message-level).
- Ensure Supabase realtime streams are active for target tables.
- Enforce secure writes and append to `admin_actions` for every state change.
