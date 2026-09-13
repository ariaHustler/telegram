Exit code: 0
Wall time: 0.7 seconds
Output:
#!/usr/bin/env python3
"""Local MCP server for Telegram configuration, queues, Bot API, and MTProto."""
from __future__ import annotations

import asyncio
import json
import mimetypes
import os
import secrets
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("TELEGRAM_PLUGIN_DATA_DIR") or (Path.home() / ".telegram-plugin"))
DB_PATH = DATA_DIR / "telegram.db"
DEFAULT_CONFIG = {
    "default_surface": "chrome",
    "fallback_surfaces": ["iab", "desktop"],
    "default_language": "auto",
    "default_policy": "auto",
    "dry_run": True,
    "bot_token_env": "TELEGRAM_BOT_TOKEN",
    "api_id_env": "TELEGRAM_API_ID",
    "api_hash_env": "TELEGRAM_API_HASH",
    "phone_env": "TELEGRAM_PHONE",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS aliases(alias TEXT PRIMARY KEY, target TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'auto', updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS policies(target TEXT PRIMARY KEY, mode TEXT NOT NULL, allow_delete INTEGER NOT NULL DEFAULT 0, allowed_actions TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS drafts(id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, body TEXT NOT NULL, media_json TEXT NOT NULL DEFAULT '[]', status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS queue(id INTEGER PRIMARY KEY AUTOINCREMENT, draft_id INTEGER, target TEXT NOT NULL, body TEXT NOT NULL, media_json TEXT NOT NULL DEFAULT '[]', scheduled_at TEXT, transport TEXT NOT NULL DEFAULT 'auto', status TEXT NOT NULL DEFAULT 'queued', result_json TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, target TEXT, transport TEXT, dry_run INTEGER NOT NULL, request_json TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL);
    """)
    for key, value in DEFAULT_CONFIG.items():
        db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, json.dumps(value, ensure_ascii=False)))
    db.commit()
    return db


def setting(db: sqlite3.Connection, key: str) -> Any:
    row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else DEFAULT_CONFIG.get(key)


def resolve_target(db: sqlite3.Connection, target: str) -> str:
    row = db.execute("SELECT target FROM aliases WHERE alias=?", (target,)).fetchone()
    return row[0] if row else target


def effective_policy(db: sqlite3.Connection, target: str) -> dict[str, Any]:
    row = db.execute("SELECT * FROM policies WHERE target=?", (target,)).fetchone()
    if row:
        return {"mode": row["mode"], "allow_delete": bool(row["allow_delete"]), "allowed_actions": json.loads(row["allowed_actions"])}
    return {"mode": setting(db, "default_policy"), "allow_delete": False, "allowed_actions": ["read", "draft", "send", "edit", "forward", "upload", "schedule"]}


def audit(db: sqlite3.Connection, action: str, target: str | None, transport: str, dry: bool, request: dict, result: dict) -> None:
    db.execute("INSERT INTO audit(action,target,transport,dry_run,request_json,result_json,created_at) VALUES(?,?,?,?,?,?,?)",
               (action, target, transport, int(dry), json.dumps(request, ensure_ascii=False), json.dumps(result, ensure_ascii=False), now()))
    db.commit()


def bot_request(method: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in payload.items() if v is not None}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Telegram Bot API HTTP {exc.code}: {body[:1000]}") from exc


def bot_file_request(method: str, token: str, payload: dict[str, Any], field: str, path: Path) -> dict[str, Any]:
    boundary = "----codextelegram" + secrets.token_hex(12)
    chunks: list[bytes] = []
    for key, value in payload.items():
        if value is None:
            continue
        chunks.extend([f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n".encode(), str(value).encode("utf-8"), b"\r\n"])
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    chunks.extend([f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{path.name}\"\r\nContent-Type: {mime}\r\n\r\n".encode(), path.read_bytes(), b"\r\n", f"--{boundary}--\r\n".encode()])
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=b"".join(chunks), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Telegram Bot API HTTP {exc.code}: {body[:1000]}") from exc


async def mtproto_send(target: str, body: str) -> dict[str, Any]:
    try:
        from telethon import TelegramClient
    except ImportError as exc:
        raise RuntimeError("MTProto requires: python -m pip install -r scripts/requirements-optional.txt") from exc
    api_id = os.environ.get(str(DEFAULT_CONFIG["api_id_env"]))
    api_hash = os.environ.get(str(DEFAULT_CONFIG["api_hash_env"]))
    phone = os.environ.get(str(DEFAULT_CONFIG["phone_env"]))
    if not api_id or not api_hash:
        raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH are required")
    session = str(DATA_DIR / "mtproto-session")
    client = TelegramClient(session, int(api_id), api_hash)
    await client.start(phone=phone)
    try:
        message = await client.send_message(target, body)
        return {"ok": True, "message_id": message.id, "chat_id": getattr(message, "chat_id", None)}
    finally:
        await client.disconnect()


async def mtproto_send_file(target: str, path: Path, caption: str) -> dict[str, Any]:
    try:
        from telethon import TelegramClient
    except ImportError as exc:
        raise RuntimeError("MTProto requires: python -m pip install -r scripts/requirements-optional.txt") from exc
    api_id = os.environ.get(str(DEFAULT_CONFIG["api_id_env"])); api_hash = os.environ.get(str(DEFAULT_CONFIG["api_hash_env"])); phone = os.environ.get(str(DEFAULT_CONFIG["phone_env"]))
    if not api_id or not api_hash: raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH are required")
    client = TelegramClient(str(DATA_DIR / "mtproto-session"), int(api_id), api_hash)
    await client.start(phone=phone)
    try:
        message = await client.send_file(target, str(path), caption=caption)
        return {"ok": True, "message_id": message.id, "chat_id": getattr(message, "chat_id", None)}
    finally:
        await client.disconnect()


def schema(properties: dict, required: list[str] | None = None) -> dict:
    value = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        value["required"] = required
    return value


TOOLS = [
    {"name": "telegram_status", "description": "Inspect local Telegram plugin configuration and transport readiness without exposing secrets.", "inputSchema": schema({})},
    {"name": "telegram_config_set", "description": "Set a non-secret plugin preference.", "inputSchema": schema({"key": {"type": "string", "enum": list(DEFAULT_CONFIG)}, "value": {}}, ["key", "value"])},
    {"name": "telegram_alias_upsert", "description": "Create or update a stable alias for a user, group, or channel.", "inputSchema": schema({"alias": {"type": "string"}, "target": {"type": "string"}, "kind": {"type": "string", "enum": ["auto", "user", "group", "channel", "bot"]}}, ["alias", "target"])},
    {"name": "telegram_policy_set", "description": "Set per-target automation permissions.", "inputSchema": schema({"target": {"type": "string"}, "mode": {"type": "string", "enum": ["draft-only", "confirm-send", "auto"]}, "allow_delete": {"type": "boolean"}, "allowed_actions": {"type": "array", "items": {"type": "string"}}}, ["target", "mode"])},
    {"name": "telegram_draft_save", "description": "Save a multilingual Telegram draft and optional local media paths.", "inputSchema": schema({"target": {"type": "string"}, "body": {"type": "string"}, "media": {"type": "array", "items": {"type": "string"}}}, ["body"])},
    {"name": "telegram_queue_create", "description": "Queue a Telegram post or message for later processing.", "inputSchema": schema({"target": {"type": "string"}, "body": {"type": "string"}, "media": {"type": "array", "items": {"type": "string"}}, "scheduled_at": {"type": ["string", "null"]}, "transport": {"type": "string", "enum": ["auto", "bot", "mtproto", "chrome", "iab", "desktop"]}, "draft_id": {"type": ["integer", "null"]}}, ["target", "body"])},
    {"name": "telegram_queue_list", "description": "List queued, completed, or failed Telegram items.", "inputSchema": schema({"status": {"type": ["string", "null"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 200}})},
    {"name": "telegram_send", "description": "Send through Bot API or MTProto, or return an action plan for browser/desktop. Honors dry-run and per-target policy.", "inputSchema": schema({"target": {"type": "string"}, "body": {"type": "string"}, "transport": {"type": "string", "enum": ["bot", "mtproto", "chrome", "iab", "desktop"]}, "dry_run": {"type": "boolean"}, "confirmed": {"type": "boolean"}, "parse_mode": {"type": ["string", "null"], "enum": ["HTML", "MarkdownV2", None]}}, ["target", "body", "transport"])},
    {"name": "telegram_send_media", "description": "Send a local photo, video, audio, or document with an optional caption; supports dry-run and UI action plans.", "inputSchema": schema({"target": {"type": "string"}, "path": {"type": "string"}, "caption": {"type": "string"}, "media_type": {"type": "string", "enum": ["photo", "video", "audio", "document"]}, "transport": {"type": "string", "enum": ["bot", "mtproto", "chrome", "iab", "desktop"]}, "dry_run": {"type": "boolean"}, "confirmed": {"type": "boolean"}}, ["target", "path", "media_type", "transport"])},
    {"name": "telegram_queue_process", "description": "Process due queued items through API transports, honoring policy and dry-run.", "inputSchema": schema({"limit": {"type": "integer", "minimum": 1, "maximum": 100}, "dry_run": {"type": "boolean"}, "confirmed": {"type": "boolean"}})},
    {"name": "telegram_audit_list", "description": "Return recent Telegram operation audit records.", "inputSchema": schema({"limit": {"type": "integer", "minimum": 1, "maximum": 200}})},
]


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    db = connect()
    if name == "telegram_status":
        config = {row["key"]: json.loads(row["value"]) for row in db.execute("SELECT * FROM settings")}
        return {"database": str(DB_PATH), "config": config, "bot_ready": bool(os.environ.get(config["bot_token_env"])), "mtproto_ready": bool(os.environ.get(config["api_id_env"]) and os.environ.get(config["api_hash_env"])), "telethon_installed": _module_exists("telethon")}
    if name == "telegram_config_set":
        db.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (args["key"], json.dumps(args["value"], ensure_ascii=False))); db.commit()
        return {"ok": True, "key": args["key"], "value": args["value"]}
    if name == "telegram_alias_upsert":
        db.execute("INSERT INTO aliases(alias,target,kind,updated_at) VALUES(?,?,?,?) ON CONFLICT(alias) DO UPDATE SET target=excluded.target,kind=excluded.kind,updated_at=excluded.updated_at", (args["alias"], args["target"], args.get("kind", "auto"), now())); db.commit()
        return {"ok": True, **args}
    if name == "telegram_policy_set":
        actions = args.get("allowed_actions", ["read", "draft", "send", "edit", "forward", "upload", "schedule"])
        db.execute("INSERT INTO policies(target,mode,allow_delete,allowed_actions,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(target) DO UPDATE SET mode=excluded.mode,allow_delete=excluded.allow_delete,allowed_actions=excluded.allowed_actions,updated_at=excluded.updated_at", (args["target"], args["mode"], int(args.get("allow_delete", False)), json.dumps(actions), now())); db.commit()
        return {"ok": True, "target": args["target"], "policy": effective_policy(db, args["target"])}
    if name == "telegram_draft_save":
        stamp = now(); cur = db.execute("INSERT INTO drafts(target,body,media_json,created_at,updated_at) VALUES(?,?,?,?,?)", (args.get("target"), args["body"], json.dumps(args.get("media", []), ensure_ascii=False), stamp, stamp)); db.commit()
        return {"ok": True, "draft_id": cur.lastrowid}
    if name == "telegram_queue_create":
        target = resolve_target(db, args["target"]); stamp = now(); cur = db.execute("INSERT INTO queue(draft_id,target,body,media_json,scheduled_at,transport,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", (args.get("draft_id"), target, args["body"], json.dumps(args.get("media", []), ensure_ascii=False), args.get("scheduled_at"), args.get("transport", "auto"), stamp, stamp)); db.commit()
        return {"ok": True, "queue_id": cur.lastrowid, "target": target}
    if name == "telegram_queue_list":
        query = "SELECT * FROM queue"; params: list[Any] = []
        if args.get("status"): query += " WHERE status=?"; params.append(args["status"])
        query += " ORDER BY id DESC LIMIT ?"; params.append(args.get("limit", 50))
        return {"items": [{**dict(row), "media": json.loads(row["media_json"]), "result": json.loads(row["result_json"]) if row["result_json"] else None} for row in db.execute(query, params)]}
    if name == "telegram_audit_list":
        return {"items": [{**dict(row), "request": json.loads(row["request_json"]), "result": json.loads(row["result_json"])} for row in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (args.get("limit", 50),))]}
    if name == "telegram_queue_process":
        rows = db.execute("SELECT * FROM queue WHERE status='queued' AND (scheduled_at IS NULL OR scheduled_at<=?) ORDER BY id LIMIT ?", (now(), args.get("limit", 20))).fetchall()
        results = []
        for row in rows:
            transport = row["transport"]
            if transport not in ("bot", "mtproto"):
                results.append({"queue_id": row["id"], "ok": False, "reason": "UI transport requires an interactive surface"}); continue
            try:
                value = call_tool("telegram_send", {"target": row["target"], "body": row["body"], "transport": transport, "dry_run": args.get("dry_run", setting(db, "dry_run")), "confirmed": args.get("confirmed", False)})
                status = "queued" if value.get("dry_run") else "completed"
                db.execute("UPDATE queue SET status=?,result_json=?,updated_at=? WHERE id=?", (status, json.dumps(value, ensure_ascii=False), now(), row["id"])); db.commit()
                results.append({"queue_id": row["id"], **value})
            except Exception as exc:
                db.execute("UPDATE queue SET status='failed',result_json=?,updated_at=? WHERE id=?", (json.dumps({"error": str(exc)}, ensure_ascii=False), now(), row["id"])); db.commit()
                results.append({"queue_id": row["id"], "ok": False, "error": str(exc)})
        return {"processed": len(results), "items": results}
    if name == "telegram_send_media":
        target = resolve_target(db, args["target"]); transport = args["transport"]; path = Path(args["path"]).expanduser().resolve(); policy = effective_policy(db, target)
        if not path.is_file(): raise RuntimeError(f"Media file does not exist: {path}")
        if "upload" not in policy["allowed_actions"] or "send" not in policy["allowed_actions"]: raise RuntimeError("Upload/send is not allowed by the target policy")
        if policy["mode"] == "draft-only": raise RuntimeError("Target policy is draft-only")
        if policy["mode"] == "confirm-send" and not args.get("confirmed"): raise RuntimeError("Target policy requires confirmed=true")
        dry = bool(args.get("dry_run", setting(db, "dry_run"))); request = {"target": target, "path": str(path), "caption": args.get("caption", ""), "media_type": args["media_type"], "transport": transport}
        if dry: result = {"ok": True, "dry_run": True, "request": request, "bytes": path.stat().st_size, "policy": policy}
        elif transport == "bot":
            token = os.environ.get(str(setting(db, "bot_token_env")))
            if not token: raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
            method, field = {"photo": ("sendPhoto", "photo"), "video": ("sendVideo", "video"), "audio": ("sendAudio", "audio"), "document": ("sendDocument", "document")}[args["media_type"]]
            result = bot_file_request(method, token, {"chat_id": target, "caption": args.get("caption", "")}, field, path)
        elif transport == "mtproto": result = asyncio.run(mtproto_send_file(target, path, args.get("caption", "")))
        else: result = {"ok": True, "requires_ui": True, "surface": transport, **request, "instruction": "Use the matching browser/computer skill, verify destination, attach this exact file, verify preview and caption, then send under policy."}
        audit(db, "send_media", target, transport, dry, request, result)
        return result
    if name == "telegram_send":
        target = resolve_target(db, args["target"]); transport = args["transport"]; policy = effective_policy(db, target)
        if "send" not in policy["allowed_actions"]: raise RuntimeError("Send is not allowed by the target policy")
        if policy["mode"] == "draft-only": raise RuntimeError("Target policy is draft-only")
        if policy["mode"] == "confirm-send" and not args.get("confirmed"): raise RuntimeError("Target policy requires confirmed=true")
        dry = bool(args.get("dry_run", setting(db, "dry_run")))
        request = {"target": target, "body": args["body"], "transport": transport, "parse_mode": args.get("parse_mode")}
        if dry:
            result = {"ok": True, "dry_run": True, "request": request, "policy": policy}
        elif transport == "bot":
            token = os.environ.get(str(setting(db, "bot_token_env")))
            if not token: raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
            result = bot_request("sendMessage", token, {"chat_id": target, "text": args["body"], "parse_mode": args.get("parse_mode")})
        elif transport == "mtproto":
            result = asyncio.run(mtproto_send(target, args["body"]))
        else:
            result = {"ok": True, "requires_ui": True, "surface": transport, "target": target, "body": args["body"], "instruction": "Use the matching browser/computer skill, verify the resolved destination, compose, and send under the same policy."}
        audit(db, "send", target, transport, dry, request, result)
        return result
    raise RuntimeError(f"Unknown tool: {name}")


def _module_exists(name: str) -> bool:
    try:
        __import__(name); return True
    except ImportError:
        return False


def respond(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> None:
    connect().close()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")
            if method == "initialize":
                result = {"protocolVersion": request.get("params", {}).get("protocolVersion", "2025-06-18"), "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "telegram-local", "version": "0.1.0"}}
            elif method == "tools/list": result = {"tools": TOOLS}
            elif method == "tools/call":
                value = call_tool(request["params"]["name"], request["params"].get("arguments", {}))
                result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}], "structuredContent": value, "isError": False}
            elif method in ("notifications/initialized", "notifications/cancelled"):
                continue
            elif method == "ping": result = {}
            else: raise RuntimeError(f"Unsupported method: {method}")
            if req_id is not None: respond({"jsonrpc": "2.0", "id": req_id, "result": result})
        except Exception as exc:
            if 'req_id' in locals() and req_id is not None:
                respond({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(exc)}})


if __name__ == "__main__":
    main()

