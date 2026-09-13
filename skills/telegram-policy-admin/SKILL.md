---
name: telegram-policy-admin
description: Configure and inspect Telegram plugin aliases, destinations, automation permissions, dry-run behavior, browser priority, Bot API and MTProto environment-variable bindings, audit records, and local data settings. Use when setting up Telegram access, changing per-chat safety policy, diagnosing transport readiness, or managing operational configuration.
---

# Telegram Policy Administration

## Initialize

1. Call `telegram_status` to create and inspect the local database.
2. On Windows, store secrets with `python scripts/store_credential.py NAME`; input is hidden and saved in Windows Credential Manager. Environment variables remain a fallback. Default names are `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_PHONE`.
3. Install the optional Telethon dependency only when MTProto is required: `python -m pip install -r scripts/requirements-optional.txt` from the plugin root.
4. Keep `dry_run=true` through initial browser, Bot API, and MTProto rehearsals.
5. Validate a BotFather token with `telegram_bot_identity`. After the user sends `/start` to the bot, use `telegram_bot_updates` with `include_text=false` to discover the private chat ID.

## Manage aliases

Use `telegram_alias_upsert` to map a stable human-readable alias to a username, numeric chat ID, or other transport-specific target. Confirm target identity in Telegram before enabling automatic sending.

## Manage policies

Use `telegram_policy_set` with one of:

- `draft-only`: read and create drafts; block sends.
- `confirm-send`: require `confirmed=true` for each send.
- `auto`: permit unattended actions listed in `allowed_actions`.

Deletion remains disabled unless `allow_delete=true`. Even then, execute deletion only when the user's current instruction explicitly identifies the deletion scope.

## Configure surfaces

Use `telegram_config_set` for `default_surface`, `fallback_surfaces`, `default_language`, `default_policy`, `dry_run`, and credential environment-variable names. Do not store actual tokens, hashes, phone verification codes, passwords, cookies, or browser session data.

## Audit and recovery

Use `telegram_audit_list` to trace MCP operations. A failed send is not safe to retry until the transport response or Telegram UI proves whether the original request created a message. Prefer idempotent queue records and retain message identifiers.

Read [references/configuration.md](references/configuration.md) for storage paths and rollout sequence.
