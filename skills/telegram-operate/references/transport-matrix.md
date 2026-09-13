Exit code: 0
Wall time: 0.8 seconds
Output:
# Transport matrix

| Transport | Best use | Authentication | Main limitation |
|---|---|---|---|
| Chrome | Existing signed-in user session and rich Telegram Web UI | Existing Chrome session | UI selectors and loading state |
| In-app Browser | Isolated signed-in web workflow inside Codex | Existing in-app session | Separate session from Chrome |
| Desktop | Native-only functions and OS-level file workflows | Existing desktop session | Visual automation is slower |
| Bot API | Reliable bot messaging and channel automation | `TELEGRAM_BOT_TOKEN` | Bot permissions and Bot API scope |
| MTProto | User-account automation and broader Telegram API access | `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, optional `TELEGRAM_PHONE` | First-run login and session lifecycle |

Use only environment variable names in configuration. Store MTProto session data in the configured local data directory, never in the plugin source.

