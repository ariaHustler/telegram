# Configuration and rollout

The MCP server stores SQLite data under `%LOCALAPPDATA%\Codex\telegram-plugin` by default. Override the directory with `TELEGRAM_PLUGIN_DATA_DIR`.

Rollout sequence:

1. Inspect status.
2. Define aliases.
3. Define explicit per-target policies.
4. Rehearse with global dry-run enabled.
5. Verify Browser/Chrome/Desktop destination selection without sending.
6. Verify Bot API identity and MTProto login separately.
7. Disable dry-run only for targets whose policies and identities were validated.
8. Inspect the audit trail after the first live operation.

The database contains configuration, aliases, policies, drafts, queues, and audit metadata. It must not contain Bot tokens, API hashes, passwords, cookies, or verification codes.
