Exit code: 0
Wall time: 0.8 seconds
Output:
# Content package contract

Required fields:

- `target`: alias, username, or numeric chat ID
- `body`: final Unicode text
- `language`: BCP 47 language tag or `auto`
- `transport`: `bot`, `mtproto`, `chrome`, `iab`, or `desktop`
- `scheduled_at`: ISO-8601 timestamp with offset, or null
- `media`: ordered absolute local paths
- `source_provenance`: source URLs or local artifact paths when applicable
- `acceptance`: exact checks required after publication

Acceptance checks:

- Destination identity matches.
- Text, numbers, links, hashtags, mentions, and symbols match the approved package.
- RTL/LTR segments render correctly.
- Media order, crop, duration, audio, subtitles, and caption are correct.
- API response includes a successful message identifier or the published UI state is visible.

