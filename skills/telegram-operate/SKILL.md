Exit code: 0
Wall time: 0.9 seconds
Output:
---
name: telegram-operate
description: Operate Telegram conversations, groups, channels, files, and media through Telegram Web, Telegram Desktop, Bot API, or MTProto. Use when Codex must search or read Telegram, summarize conversations, draft or translate replies, send/edit/forward/delete messages, or upload/download Telegram media.
---

# Telegram Operations

## Select the transport

1. Honor an explicitly named surface: Chrome, in-app Browser, Telegram Desktop, Bot API, or MTProto.
2. Otherwise use Chrome first, then the in-app Browser, then Telegram Desktop.
3. Prefer Bot API for bot-owned destinations and repeatable server-side actions.
4. Prefer MTProto for authenticated user-account operations that Telegram Web cannot perform reliably.
5. Use `telegram_status` before API operations and never expose credential values.

For Browser or Chrome, read and follow the corresponding installed browser skill before interacting. For Telegram Desktop, read and follow Computer Use. Do not switch away from an explicitly requested surface.

## Resolve and authorize

1. Resolve aliases through the MCP tools or the visible Telegram search UI.
2. Match both the displayed name and stable username or numeric ID when available.
3. Load the target policy. Treat `draft-only`, `confirm-send`, and `auto` as binding.
4. Require an explicit user instruction for destructive operations even when the policy allows automation.
5. Never infer permission to contact additional people, groups, or channels.

## Read and search

Use visible Telegram UI state for Web/Desktop searches. Do not inspect cookies, storage, session files, passwords, or hidden browser state. Report the covered chats, time range, filters, and unread boundary with summaries. Preserve exact quotations only when needed.

## Compose and send

1. Draft in the conversation language; preserve RTL direction and exact names, numbers, links, mentions, and formatting.
2. Validate the resolved destination and attachment paths.
3. For API sends, call `telegram_send` with the required transport. Pass `confirmed=true` only after the relevant confirmation exists.
4. For UI sends, call `telegram_send` first to obtain the action plan, then execute it on the matching surface.
5. Distinguish typed text from a sent message. Confirm completion only from a visible sent bubble or an API success with message ID.

## Files and media

Verify local path, media type, file size, caption, destination, and upload completion. Keep downloaded files outside the plugin directory. Do not claim conversion or delivery until the output exists and Telegram shows completion.

## Audit

Use `telegram_audit_list` for API/MCP operations. For browser and desktop operations, state the destination, operation, and visible completion evidence without recording message content unnecessarily.

Read [references/transport-matrix.md](references/transport-matrix.md) when selecting among multiple valid transports.

