# Telegram Plugin for Codex

A local Codex plugin for multilingual Telegram operations, content automation,
per-target policies, Telegram Web, Telegram Desktop, Bot API, and MTProto.

## Capabilities

- Read, search, summarize, draft, translate, send, edit, and forward messages.
- Work with private chats, groups, channels, files, images, video, audio, and documents.
- Save drafts and manage a persistent SQLite publication queue.
- Apply `draft-only`, `confirm-send`, or `auto` policies per destination.
- Use Chrome, the Codex in-app browser, Telegram Desktop, Bot API, or MTProto.
- Keep API credentials outside the repository.

## Components

- `.codex-plugin/plugin.json`: Codex plugin manifest.
- `.mcp.json`: local MCP server registration.
- `scripts/telegram_mcp.py`: MCP tools, SQLite storage, Bot API, and MTProto integration.
- `skills/telegram-operate`: conversation and media operations.
- `skills/telegram-content-pipeline`: content packaging, queueing, and publication.
- `skills/telegram-policy-admin`: aliases, policies, credentials, and audit configuration.

## Authentication

On Windows, the plugin reads credentials from Windows Credential Manager and
falls back to protected environment bindings. It never requires credentials to
be committed to the repository or entered into a Codex conversation.

Expected variable names:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_PHONE
```

Install the optional MTProto dependency:

```powershell
python -m pip install -r scripts/requirements-optional.txt
```

Store the BotFather token securely (the prompt hides input):

```powershell
python scripts/store_credential.py TELEGRAM_BOT_TOKEN
```

Use `telegram_bot_identity` to validate it, then send `/start` to the bot and
use `telegram_bot_updates` to discover the private chat ID.

Local state defaults to `%LOCALAPPDATA%\Codex\telegram-plugin` and remains
outside the plugin repository.

## Verification

The GitHub Actions workflow validates:

- Python syntax
- all bundled Codex skills
- the Codex plugin manifest
- MCP initialization and tool discovery
- dry-run text and media operations
- absence of common Telegram credential and session artifacts

## Documentation

Persian documentation is available in [docs/README.fa.md](docs/README.fa.md).

## License

Copyright (c) 2026 Aria Hustler. All rights reserved. See [LICENSE](LICENSE).
