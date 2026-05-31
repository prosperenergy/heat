# heat

**The Prosper Heat playbook — autonomous AI-scored sales contest, end-to-end.**

`heat` is the canonical operational + technical skill for running the Prosper Heat: an autonomous sales contest scored live by Hanna AI, verified against Setmore Gmail + Google Calendar + electric-bill proof, then announced with a /hannavideo-produced winner reveal and blasted across every connected social platform via GHL Social Planner. Winners receive their prize via Zelle ONLY to **803-556-7450**.

## What's in here

- **`SKILL.md`** — the full playbook: architecture, scoring rules, GAM verification flow, video production stack, GHL Social Planner schema (the one we cracked the hard way), Telegram inbound listener wiring, Zelle payout rule, weekly cadence, round-N runbook checklist.
- **`README.md`** — this overview.
- **`hanna-telegram-listener.py`** — the Telegram inbound script that turns Craig's phone into a one-tap asset drop for the Hanna seat. Polls `@prosper_hanna_mirror_bot` at 5s, downloads videos / photos / docs / notes to `~/ClaudeCodexBridge/social-inbox/` with sidecar metadata, emits dispatch-notify markdowns for the Cowork seat.
- **`io.prosper.hanna-telegram-listener.plist`** — launchd job (RunAtLoad + KeepAlive).
- **`fire_ghl_social_planner.py`** — reference implementation of the cracked GHL POST schema (type=video/mp4, status=published, userId required, post type per platform).
- **`install.sh`** — one-liner installer.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/prosperenergy/heat/main/install.sh | bash
```

## What this skill produced (Round 1, 2026-05-30)

- 8-hour autonomous sales contest run solo by Hanna AI (3 PM-11 PM ET)
- 83-lead pool, 88 active assignments, 3-way race
- Final: Scott 180 ($300) / Garett 167 ($200) / Mo 149 ($100)
- 7 Setmore appointments verified live in Garett's Gmail via GAM
- 64-second cinematic reveal video produced via Soul Cinema + Veo 3.1 PREVIEW + Gemini Aoede TTS + ffmpeg
- Public blast fired to **8 platforms** through GHL Social Planner: Facebook (Prosper Shield + Solar Program pages), Instagram (Reel), LinkedIn (Prosper Solar Energy company page), TikTok (Reel), Threads, Pinterest, Bluesky, YouTube (note: YouTube token expired and failed)
- Private Zelle DMs to all three winners (803-556-7450)

## Sister skills

- **`/hannavideo`** — free-first media routing rail (Higgsfield → Google AI Studio → ElevenLabs → credits → ffmpeg). Required by every Heat for the winner reveal video.
- **`/gam`** — Google Workspace ops via gamadv-xtd3. Required for Setmore Gmail verification (the gold standard for confirming a real appointment was set).

## License

Internal Prosper Energy / Prosper Shield. Not for external redistribution.
