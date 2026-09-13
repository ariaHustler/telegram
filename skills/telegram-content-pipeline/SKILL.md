---
name: telegram-content-pipeline
description: Create, transform, schedule, queue, and publish multilingual Telegram channel or group content with text, captions, images, video, audio, documents, and subtitles. Use for editorial calendars, recurring Telegram posts, content repurposing, media preparation, scheduled publication, and post-publication verification.
---

# Telegram Content Pipeline

## Build the content package

1. Identify objective, audience, target, content language, CTA, publishing window, and source assets.
2. Produce the text and media as a versioned package. Preserve factual claims, source links, mentions, and RTL typography.
3. Verify Telegram limits and formatting against current official documentation when limits materially affect the output.
4. Save intermediate text with `telegram_draft_save`; store media at stable absolute paths outside the plugin.

## Queue and publish

1. Resolve the destination alias and load its policy.
2. Create a queue record with `telegram_queue_create`, including ISO-8601 schedule and transport.
3. Use Bot API or MTProto for unattended automation. Use Chrome, the in-app Browser, or Desktop when the requested operation depends on the UI.
4. Keep global `dry_run=true` until the workflow has passed a complete rehearsal.
5. At publish time, validate destination, final text, media order, caption, schedule, and policy; then call `telegram_send` or execute the UI plan.

## Verify

Treat queued, typed, uploaded, published, and verified as different states. Mark success only after an API message ID or visible published post exists. Check media playback/download, caption integrity, link targets, RTL order, and scheduled time zone.

## Repurpose

Adapt content to Telegram rather than mechanically copying it. Retain the canonical claim set while changing hook, structure, length, formatting, and media crop for the destination audience. Record source provenance when the content is research-based.

Read [references/content-contract.md](references/content-contract.md) for the package schema and acceptance checks.
