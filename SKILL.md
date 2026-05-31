---
name: heat
description: "Run the Prosper Heat — an autonomous AI-scored sales contest. End-to-end playbook: heat engine, GAM verification, /hannavideo production, GHL Social Planner blast across FB/IG/LinkedIn/TikTok/Threads/Pinterest/Bluesky/YouTube, Telegram inbound for assets, Zelle-only payouts. Cadence: once per week. Slash: /heat."
argument-hint: "[round_number] e.g. '/heat 2' to fire Heat #2"
---

# /heat — the Prosper Heat playbook

**Locked by Craig 2026-05-31.** First successful run: Round 1, Friday 2026-05-30, 3:00–11:00 PM ET, scored solo by Hanna AI. Cadence going forward: **once per week**.

This skill is the complete technical and operational playbook for running the next Heat from cold start to ship.

---

## Architecture, one breath

```
Live homeowner leads (intake forms / SOL leads)
        ↓
Heat engine (Python daemon, launchd) → Redis state hash per rep
        ↓
iMessage responder pipes each rep's call/text/set into the engine
        ↓
Hourly digest writer (launchd cron) → ~/ClaudeCodexBridge/prosper-heat-digest-latest.txt
        ↓
Bell rings → engine stops → totals locked
        ↓
GAM verification round (Setmore Gmail + Google Calendar + bill check) → ground truth
        ↓
/hannavideo skill builds the winner reveal:
  Soul Cinema stills → Veo 3.1 PREVIEW motion → scoreboard cards → logo bumpers → Gemini Aoede VO → ffmpeg master
        ↓
GHL Social Planner blast: FB / IG (Reel) / LinkedIn / TikTok (Reel) / Threads / Pinterest / Bluesky / YouTube
        ↓
Telegram inbound (@prosper_hanna_mirror_bot) lets Craig drop additional assets from his phone any time
        ↓
Zelle DM to winners (private only, 803-556-7450, Zelle ONLY)
```

---

## Core components

### 1. Heat engine

- **Binary:** `/Users/craigstratton/bin/prosper-heat-engine.py` (Python)
- **Shell wrapper:** `~/bin/prosper-heat-engine.sh`
- **Hourly digest:** `~/bin/prosper-heat-hourly.sh`
- **launchd jobs:**
  - `io.prosper.heat-engine` — daemon, keeps engine alive
  - `io.prosper.heat-hourly` — fires the leaderboard digest every 30 min
- **State:** Redis (via `/Users/craigstratton/bin/redis-prosper` wrapper)
  - `prosper.lead.rep.<phone>` hash — per-rep score
  - `prosper.lead.active.<id>` hash — live lead bindings
- **Lead pool:** `~/ClaudeCodexBridge/prosper-heat-lead-pool.json`
- **Logs:** `/tmp/prosper-heat-engine.log`, `/tmp/prosper-heat-hourly.log`

### 2. Scoring rules

| Event | Points | Notes |
|---|---|---|
| Outbound call | +1 | logged by responder pipe |
| Outbound text | +1 | logged by responder pipe |
| Lead worked | +1 | any meaningful touch |
| Lead miss | -0.5 | abandoned without disposition |
| **Set (appointment booked)** | **+10** | unverified |
| **Set + electric bill received** | **+20** | bill-verified (gold standard) |

Phantom-set bug (fixed 2026-05-30 by Sam): engine was crediting SET on iMessage tapbacks like "Loved 'WINNER LOCKED'". The fix lives in `prosper-heat-engine.py` — parse only true SET commands matching `^SET <firstname> <day> <time>$`.

### 3. iMessage responder integration

- Bun TypeScript service at `~/.local/bin/bun src/responder.ts` (launchd `io.prosper.imessage-responder`)
- Watches `~/Library/Messages/chat.db`, calls gateway → Hanna's `claude-opus-4-7`
- Auto-replies to reps with engine prompts ("SET pending needs proof. Text: SET [FirstName] [Day] [Time]…")
- Drafts archive: `~/ClaudeCodexBridge/imessage-drafts/`
- Whitelist rule (Danny / ESP / draft-only lanes never auto-send — see `reference_craig_contacts.md`)

---

## Verification phase — GAM (the gold standard)

Every claimed SET must clear THREE checks before the prize ships:

```bash
GAM=/Users/craigstratton/bin/gamadv-xtd3/gam

# 1. Setmore Gmail confirmation
$GAM user <rep@prosper.energy> print messages query "setmore newer_than:1d"

# 2. Calendar mirror (some reps have separate Setmore calendars)
$GAM user <rep@prosper.energy> print events after <ISO> before <ISO>

# 3. Bill verification (forwarded electric/utility bill)
$GAM user <rep@prosper.energy> print messages query "bill OR utility OR kwh newer_than:1d"
```

If 1 + 3 both pass → bill-verified SET, score +20.
If only 1 → SET real, score +10.
If neither → push back to rep: "Send the Setmore confirmation email + the bill, or it doesn't count."

See sister skill `/gam` for the full Workspace ops doc.

---

## Video production — /hannavideo rail (mandatory)

**Free-first order of operations, locked rule:**

1. **Higgsfield ULTRA unlimited** — Soul Cinema for cinematic stills, Seedance 2.0 (Full Access from June 2 onward) for video.
2. **Google AI Studio direct** — Veo 3.1 PREVIEW (best Google video), Imagen 3/4, Gemini 2.5 multimodal.
3. **ElevenLabs Pro** — Hanna voice ID `MBOX74y6c3lQRInUUnKV` / Kayla `OFOPgozS9detM2RF0Rk4` (when key is unlocked from 1Password).
4. **Higgsfield credits** — only when 1+2 can't.
5. **ffmpeg / PIL** — composite + scoreboard cards + logo bumpers only, never for generation.

### Round-1 production stack (what shipped)

| Step | Tool | Output |
|---|---|---|
| Cinematic stills | Higgsfield Soul Cinema (UNLIMITED 365) | 3× 1152×2048 PNG references |
| Cinematic motion | Veo 3.1 PREVIEW via Gemini API `models/veo-3.1-generate-preview:predictLongRunning` | 3× 8s 720×1280 portrait MP4 |
| Logo opener + sign-off | PIL on the real Prosper Shield logo PNG | 1080×1350 brand bumpers with neon halo |
| Scoreboard reveals (1st / 2nd / 3rd / totals) | PIL on dark navy + neon gradient | 1080×1350 cards per scene |
| Voice over | Gemini 2.5 Flash Preview TTS, voice `Aoede` (warm female) | 64s 24kHz mono PCM → WAV |
| Music bed | ffmpeg synthesized 3-layer sine pad with lowpass + fade | 65s soft cinematic pad |
| Voice + bed mix | ffmpeg sidechain compressor (voice ducks pad) | 64s mixed track |
| Final master | ffmpeg xfade chain (0.7s crossfades, scene durations matched to VO) | 1080×1350 64s MP4 |

Master: `~/Desktop/PROSPER-HEAT-WINNERS-VIDEO-v5.mp4` (1.6 MB, H.264 CRF 18).

See sister skill `/hannavideo` for the complete rail spec + install.

---

## Social blast — GHL Social Planner (cracked schema)

**Endpoint:** `POST https://services.leadconnectorhq.com/social-media-posting/{LOCATION_ID}/posts`

**Required headers:**
```
Authorization: Bearer <GHL_API_KEY (PIT token)>
Version: 2021-07-28
Content-Type: application/json
```

**Required payload (the schema we cracked the hard way):**
```json
{
  "accountIds": ["<account_id>"],
  "summary": "<caption text>",
  "media": [{"url": "<video_url>", "type": "video/mp4"}],
  "status": "published",
  "type": "post",
  "userId": "<GHL user id>"
}
```

**Gotchas (do not repeat):**
- `type: "video"` → 422. Right value is the MIME — `"video/mp4"`.
- `status: "publish_now"` → 422. Right value is `"published"`.
- Missing `type` (post/reel) → 422.
- Missing `userId` → 422. Pull from `GET /users/?locationId=<LOC_ID>` (Craig = `YjzZOAWymxDJMX2NtG2t`).
- Missing `Version: 2021-07-28` header → 403 / Cloudflare WAF 1010.
- `thumbnailUrl` field on media → 422.

**Media upload (step 1 before the post):**
```
POST https://services.leadconnectorhq.com/medias/upload-file
Headers: Authorization, Version: 2021-07-28
multipart/form-data: locationId, file
Returns: {fileId, url}
```
Use the returned `url` in the post payload.

**Per-platform post type:**
- Facebook → `post`
- Instagram → `reel`
- LinkedIn → `post`
- TikTok → `reel`
- Threads → `post`
- Pinterest → `post`
- Bluesky → `post`
- YouTube → `post` (caveat: token expires; reconnect via GHL UI if 403)

**Account map** lives at `~/ClaudeCodexBridge/social/winner-announce-<date>/ghl-social-account-map.json` and is mirrored as `GHL_SOCIAL_ACCOUNT_MAP` in `~/.config/prosper/prosper.env`.

**Delete endpoint** (`DELETE /posts/<id>`) only removes the GHL planner record. It does NOT remove the actual post from the social platform. For that, use the platform's own Graph/API directly or have Craig delete from the platform's admin UI.

**URL reconstruction from postIds:**
- Facebook: `https://www.facebook.com/{page_id}/videos/{postId}`
- Instagram Reel: convert numeric `postId` → base64-shortcode → `https://www.instagram.com/reel/{shortcode}/`
- LinkedIn: `https://www.linkedin.com/feed/update/{urn}/`
- TikTok: `https://www.tiktok.com/@{handle}/video/{postId}`
- Threads: shortcode-encode like IG → `https://www.threads.com/@{handle}/post/{shortcode}`
- Pinterest: `https://www.pinterest.com/pin/{postId}/`
- Bluesky: parse the `at://did:plc:.../app.bsky.feed.post/<rkey>` → `https://bsky.app/profile/{handle}/post/{rkey}`

The shortcode encoder (Threads + IG):
```python
ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
def to_shortcode(n: int) -> str:
    s = ""
    while n > 0:
        s = ALPHA[n & 63] + s
        n >>= 6
    return s
```

---

## Telegram inbound — @prosper_hanna_mirror_bot

The full pipeline for Craig to drop assets (video, photo, text note) from his phone straight into the Hanna seat, **bypassing the Cowork chat upload constraint**.

### Components

- **Bot:** `@prosper_hanna_mirror_bot` (display: "Hanna Mirror AI")
- **Token:** `HANNA_TELEGRAM_BOT_TOKEN` env var (fallback hard-coded in script for resilience)
- **Whitelist:** `HANNA_TELEGRAM_ALLOWED` env var (default `7660965553` = Craig's chat ID)
- **Listener:** `/Users/craigstratton/ClaudeCodexBridge/bin/hanna-telegram-listener.py`
- **launchd plist:** `~/Library/LaunchAgents/io.prosper.hanna-telegram-listener.plist` (RunAtLoad + KeepAlive)
- **Inbox:** `~/ClaudeCodexBridge/social-inbox/INCOMING_<timestamp>_<kind>.<ext>` + `.meta.json` sidecar
- **Notify dir:** `~/ClaudeCodexBridge/_dispatch-notify/` — markdown files dropped here become visible to the Cowork seat
- **Log:** `~/.local/share/hanna-telegram-listener.log`
- **Offset file:** `~/.local/share/hanna-telegram-listener.offset` (Telegram update_id pointer for idempotency)

### Polling strategy

**Short-polling at 5s intervals** with `timeout=0` on `getUpdates`. Long-polling caused 409 Conflicts when the daemon restarted (Telegram holds the long-poll open server-side for up to 25s; a relaunch within that window races itself). Short-polling avoids the entire failure mode.

```python
LONG_POLL = 0
POLL_SECONDS = 5
url = f"{API}/getUpdates?offset={offset}&timeout={LONG_POLL}&allowed_updates=%5B%22message%22%5D"
```

### Supported media kinds

| Telegram object | Inbox extension | Notes |
|---|---|---|
| `video` | `.mp4` | preferred |
| `video_note` | `.mp4` | round selfie video |
| `animation` | `.mp4` | GIF |
| `document` (mime video/*) | from file_name | when sent "as file" |
| `document` (mime image/*) | from file_name | image-as-file |
| `photo` (largest variant) | `.jpg` | photo picker |
| `text` | none | dropped as `_dispatch-notify/INBOUND_NOTE_<ts>.md` |

### Sidecar metadata schema

Every download writes a `.meta.json` next to the file:
```json
{
  "received_at": "ISO8601 UTC",
  "from": "Craig",
  "chat_id": 7660965553,
  "kind": "video|photo|document_video|...",
  "telegram_file_id": "BAACAgIA...",
  "telegram_file_size": 28419233,
  "caption": "any user caption",
  "message_id": 322,
  "downloaded_bytes": 28419233,
  "local_path": "/Users/craigstratton/ClaudeCodexBridge/social-inbox/INCOMING_...mp4"
}
```

### 409 Conflict recovery

If launchd shows the listener up but logs spam "HTTPError: 409 Conflict":

```bash
# 1. Force-stop our listener
launchctl unload -w ~/Library/LaunchAgents/io.prosper.hanna-telegram-listener.plist

# 2. Clear any webhook (mutually exclusive with getUpdates)
TG_TOKEN="<the bot token>"
curl -X POST "https://api.telegram.org/bot${TG_TOKEN}/deleteWebhook?drop_pending_updates=true"

# 3. Wait ~30s for any stale long-poll to time out server-side
sleep 30

# 4. Reload
launchctl load -w ~/Library/LaunchAgents/io.prosper.hanna-telegram-listener.plist
```

If still 409s after that, search the wider fleet for another process polling the same token. Telegram bot tokens are globally exclusive for `getUpdates`.

### Outbound from Hanna → Craig

The bot can also push status alerts to Craig:
```python
requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
              json={"chat_id": chat_id, "text": text}, timeout=10)
```
Used by the latency-watch script (`~/ClaudeCodexBridge/prosper-responder-latency-watch.sh`) and the listener itself (acknowledges every inbound video).

---

## Zelle payout rule — HARD STOP

**All Prosper rep payouts go through Zelle ONLY. No exceptions.**

- Company Zelle number: **803-556-7450**
- Direction: rep **SENDS a request** to 803-556-7450 from their Zelle app. Craig accepts the request and the money fires back.
- ❌ NO Venmo. NO Cash App. NO PayPal. NO wires. NO checks.
- ❌ NEVER use `+18435567450` — that's a typo from a prior session, wrong area code.

If a rep pushes back asking for a different method, reinforce: **"Zelle only. 803-556-7450. That's the only method we use."**

If a rep says they don't have Zelle: **"Most banks have it in their app. Download takes about 60 seconds."**

The Zelle line goes via **private DM**, never in the public social post.

See memory `reference_prosper_zelle_payout_rule.md` for the full rule.

---

## Weekly cadence (the new rule)

**Heat runs once per week.** Craig locked this 2026-05-31 immediately after Round 1.

Suggested cadence:
- **Run window:** Friday afternoon, 3-11 PM ET (matches Round 1's proven format)
- **Pool size:** ~80 unique fresh leads per heat (Round 1 had 83)
- **Reps:** all opted-in reps on the floor
- **Prize ladder:** $300 / $200 / $100 for 1st / 2nd / 3rd
- **Bell:** 11 PM ET → engine stops → verification round begins immediately
- **Announce:** Saturday morning ET, public blast + private DMs

---

## Round-N runbook (copy-paste checklist)

### Pre-Heat (day-of, before 3 PM ET)
- [ ] Refresh the lead pool: `~/ClaudeCodexBridge/prosper-heat-lead-pool.json`
- [ ] Verify heat-engine launchd job is loaded: `launchctl list | grep heat`
- [ ] Verify imessage-responder is alive
- [ ] Send opt-in nudge to all reps still PENDING
- [ ] Confirm Higgsfield ULTRA credits sane (`show_plans_and_credits`)
- [ ] Confirm Gemini API key works (Aoede test)
- [ ] Confirm GHL PIT + `GHL_SOCIAL_ACCOUNT_MAP` env loaded
- [ ] Confirm Telegram listener is green (`tail ~/.local/share/hanna-telegram-listener.log`)

### Live window (3-11 PM ET)
- [ ] Engine fires hourly digest into reps' group every 30 min
- [ ] Cowork seat posts in-pane shoutouts per hour
- [ ] Verify each claimed SET as it arrives (GAM Setmore check live)

### Bell (11 PM ET)
- [ ] Stop engine: `launchctl unload io.prosper.heat-engine`
- [ ] Lock final totals (Redis read + JSON snapshot)
- [ ] Run full GAM verification round on top 3 (Setmore + Calendar + bill for each)

### Production (next morning)
- [ ] Generate Soul Cinema stills (3 references) → Veo 3.1 PREVIEW (3 clips)
- [ ] Build scoreboard PNGs (1st, 2nd, 3rd, totals)
- [ ] Build logo opener + sign-off PNGs
- [ ] Gemini Aoede TTS the script (~64s)
- [ ] ffmpeg assemble master + audio bed sidechain mix
- [ ] Confirm with Craig

### Blast
- [ ] Upload master to GHL via `/medias/upload-file`
- [ ] POST to GHL Social Planner for each platform with correct schema
- [ ] Pull URLs back from `/posts/list` and confirm each lands

### Payout
- [ ] Private DM each winner with the Zelle line (NEVER in public post)
- [ ] Watch for incoming Zelle requests on 803-556-7450
- [ ] Craig fires each one back

### Cleanup
- [ ] Archive lead pool + scoreboard digest to `~/ClaudeCodexBridge/heat-history/<round-date>/`
- [ ] Update `MEMORY.md` index entry

---

## File map

```
/Users/craigstratton/
├── bin/
│   ├── prosper-heat-engine.py
│   ├── prosper-heat-engine.sh
│   ├── prosper-heat-hourly.sh
│   ├── gamadv-xtd3/gam
│   └── redis-prosper
├── ClaudeCodexBridge/
│   ├── bin/
│   │   └── hanna-telegram-listener.py
│   ├── skills/heat/SKILL.md          # THIS FILE
│   ├── skills/hannavideo/SKILL.md    # sister
│   ├── skills/gam/SKILL.md           # sister
│   ├── social/winner-announce-<date>/
│   │   ├── captions.json
│   │   ├── ghl-social-account-map.json
│   │   └── COPY-FINAL-WINNER.md
│   ├── social-blast/prosper-blast.py
│   ├── social-inbox/                 # Telegram drops land here
│   ├── _dispatch-notify/             # Hanna seat sees notifications here
│   └── heat-history/<round-date>/
└── Library/LaunchAgents/
    ├── io.prosper.heat-engine.plist
    ├── io.prosper.heat-hourly.plist
    ├── io.prosper.imessage-responder.plist
    └── io.prosper.hanna-telegram-listener.plist
```

---

## Cross-references
- [[reference-hannavideo-skill]] — `/hannavideo` free-first media routing
- [[reference-gam-skill-default-for-google]] — `/gam` Google Workspace rail
- [[feedback-use-subscription-unlimited-first]] — parent rule (sub-tier first)
- [[reference-prosper-zelle-payout-rule]] — Zelle-only payout HARD rule
- [[feedback-social-always-has-visual]] — visuals always required
- [[reference-craig-contacts]] — rep identity registry

---

**Author:** Hanna, 2026-05-31. Locked after Prosper Heat Round 1 shipped end-to-end across 8 platforms with verified payouts.
