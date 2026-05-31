#!/usr/bin/env python3
"""Hanna Telegram inbound listener — Prosper social blast pipeline.

Polls @prosper_hanna_mirror_bot for new updates every 5 seconds.
Whitelists Craig's chat ID (7660965553) only — drops everything else.
Downloads any video into ~/ClaudeCodexBridge/social-inbox/ with a timestamped
filename, writes a small JSON metadata sidecar, and notifies Hanna via a
ClaudeCodexBridge "incoming.notify" file so the Cowork seat sees it instantly.

Authored 2026-05-31 by Hanna. Owner: support@prosper.energy.
"""
from __future__ import annotations
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config — load secrets from ~/.config/prosper/prosper.env or fallback inline
# ---------------------------------------------------------------------------
ENV_PATH = Path.home() / ".config" / "prosper" / "prosper.env"


def load_env() -> dict:
    env = dict(os.environ)
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip("'").strip('"'))
    return env


ENV = load_env()
TG_TOKEN = ENV.get("HANNA_TELEGRAM_BOT_TOKEN") or "8799770266:AAGAy7j-QjQJv87t7QHwv4dTM8nKTeR7vEo"
ALLOWED_CHAT_IDS = {int(x) for x in (ENV.get("HANNA_TELEGRAM_ALLOWED", "7660965553")).split(",") if x.strip()}

INBOX = Path.home() / "ClaudeCodexBridge" / "social-inbox"
OFFSET_FILE = Path.home() / ".local" / "share" / "hanna-telegram-listener.offset"
LOG_FILE = Path.home() / ".local" / "share" / "hanna-telegram-listener.log"
NOTIFY_DIR = Path.home() / "ClaudeCodexBridge" / "_dispatch-notify"

for p in (INBOX, OFFSET_FILE.parent, LOG_FILE.parent, NOTIFY_DIR):
    p.mkdir(parents=True, exist_ok=True)

API = f"https://api.telegram.org/bot{TG_TOKEN}"
FILE_API = f"https://api.telegram.org/file/bot{TG_TOKEN}"

POLL_SECONDS = 5
LONG_POLL = 0  # short-poll only — avoids 409 conflicts with any other token holder


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}\n"
    sys.stderr.write(line)
    sys.stderr.flush()
    try:
        with LOG_FILE.open("a") as f:
            f.write(line)
    except Exception:
        pass


def read_offset() -> int:
    try:
        return int(OFFSET_FILE.read_text().strip())
    except Exception:
        return 0


def write_offset(n: int) -> None:
    OFFSET_FILE.write_text(str(n))


def tg_get_updates(offset: int) -> list:
    url = f"{API}/getUpdates?offset={offset}&timeout={LONG_POLL}&allowed_updates=%5B%22message%22%5D"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as r:
        body = json.loads(r.read().decode())
    if not body.get("ok"):
        raise RuntimeError(f"getUpdates not ok: {body}")
    return body.get("result", [])


def tg_get_file_path(file_id: str) -> str:
    url = f"{API}/getFile?file_id={urllib.parse.quote(file_id)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        body = json.loads(r.read().decode())
    if not body.get("ok"):
        raise RuntimeError(f"getFile not ok: {body}")
    return body["result"]["file_path"]


def tg_send_message(chat_id: int, text: str) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        f"{API}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            r.read()
    except Exception as e:
        log(f"sendMessage error: {e}")


def download_to(url: str, dest: Path) -> int:
    with urllib.request.urlopen(url, timeout=300) as r, dest.open("wb") as f:
        n = 0
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
            n += len(chunk)
    return n


def handle_message(msg: dict) -> None:
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if chat_id not in ALLOWED_CHAT_IDS:
        log(f"DROP: chat_id {chat_id} not in whitelist")
        return

    from_user = msg.get("from", {}).get("first_name", "Unknown")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Find any media payload
    payload = None
    kind = None
    ext = "bin"

    if "video" in msg:
        payload = msg["video"]
        kind = "video"
        ext = "mp4"
    elif "video_note" in msg:
        payload = msg["video_note"]
        kind = "video_note"
        ext = "mp4"
    elif "animation" in msg:
        payload = msg["animation"]
        kind = "animation"
        ext = "mp4"
    elif "document" in msg:
        doc = msg["document"]
        mime = (doc.get("mime_type") or "").lower()
        if "video" in mime or doc.get("file_name", "").lower().endswith((".mp4", ".mov", ".m4v")):
            payload = doc
            kind = "document_video"
            ext = (doc.get("file_name", "").rsplit(".", 1)[-1] or "mp4").lower()
        elif "image" in mime:
            payload = doc
            kind = "document_image"
            ext = (doc.get("file_name", "").rsplit(".", 1)[-1] or "jpg").lower()
    elif "photo" in msg and msg["photo"]:
        # Telegram sends an array of size variants; pick the biggest
        payload = max(msg["photo"], key=lambda p: p.get("file_size", 0))
        kind = "photo"
        ext = "jpg"

    if payload and "file_id" in payload:
        file_id = payload["file_id"]
        file_size = payload.get("file_size", 0)
        try:
            file_path = tg_get_file_path(file_id)
            url = f"{FILE_API}/{file_path}"
            dest = INBOX / f"INCOMING_{ts}_{kind}.{ext}"
            n = download_to(url, dest)
            sidecar = dest.with_suffix(dest.suffix + ".meta.json")
            sidecar.write_text(json.dumps({
                "received_at": datetime.now(timezone.utc).isoformat(),
                "from": from_user,
                "chat_id": chat_id,
                "kind": kind,
                "telegram_file_id": file_id,
                "telegram_file_size": file_size,
                "caption": msg.get("caption", ""),
                "message_id": msg.get("message_id"),
                "downloaded_bytes": n,
                "local_path": str(dest),
            }, indent=2))
            log(f"SAVED {kind} {dest.name} ({n:,} bytes) from {from_user}")
            # Notify Hanna seat via dispatch-notify file
            notify_path = NOTIFY_DIR / f"INBOUND_VIDEO_{ts}.md"
            caption_note = msg.get("caption", "(no caption)")
            notify_path.write_text(
                f"# Inbound social asset from Craig\n\n"
                f"**File:** `{dest}`\n"
                f"**Kind:** {kind}\n"
                f"**Size:** {n:,} bytes\n"
                f"**Caption:** {caption_note}\n"
                f"**Received:** {datetime.now().isoformat()}\n\n"
                f"Hanna: open the file, write platform-tuned captions, preview to Craig, fire on go.\n"
            )
            tg_send_message(chat_id,
                f"✅ Got it. {kind} saved as {dest.name}. Writing the caption now — preview coming to Cowork.")
        except Exception as e:
            log(f"ERR downloading {file_id}: {e}")
            tg_send_message(chat_id, f"⚠️ Download failed: {e}")
    else:
        # Text-only message — relay to Hanna seat as a note
        text = msg.get("text", "")
        if text:
            note_path = NOTIFY_DIR / f"INBOUND_NOTE_{ts}.md"
            note_path.write_text(
                f"# Telegram note from Craig\n\n"
                f"**From:** {from_user}\n**Received:** {datetime.now().isoformat()}\n\n"
                f"---\n\n{text}\n"
            )
            log(f"NOTE saved: {text[:60]}")
            tg_send_message(chat_id, "✅ Got it. Relayed to Hanna in Cowork.")


def main() -> int:
    log(f"START — whitelist={ALLOWED_CHAT_IDS} inbox={INBOX}")
    offset = read_offset()
    while True:
        try:
            updates = tg_get_updates(offset)
            for u in updates:
                offset = max(offset, u["update_id"] + 1)
                msg = u.get("message")
                if not msg:
                    continue
                handle_message(msg)
            if updates:
                write_offset(offset)
            time.sleep(POLL_SECONDS)
        except urllib.error.HTTPError as e:
            log(f"HTTPError: {e.code} {e.reason} — sleeping {POLL_SECONDS}s")
            time.sleep(POLL_SECONDS)
        except Exception as e:
            log(f"loop error: {e!r}")
            time.sleep(POLL_SECONDS * 2)


if __name__ == "__main__":
    sys.exit(main() or 0)
