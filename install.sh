#!/usr/bin/env bash
# heat skill installer — Prosper fleet
set -e
REPO_RAW="https://raw.githubusercontent.com/prosperenergy/heat/main"
TARGETS=(
  "$HOME/.claude/skills/heat"
  "$HOME/.codex/skills/heat"
  "$HOME/.agents/skills/heat"
  "$HOME/ClaudeCodexBridge/skills/heat"
)
for D in "${TARGETS[@]}"; do
  mkdir -p "$D"
  curl -fsSL "$REPO_RAW/SKILL.md" -o "$D/SKILL.md"
  echo "installed: $D/SKILL.md"
done
# Commands
for D in "$HOME/.claude/commands" "$HOME/.codex/commands" "$HOME/.agents/commands"; do
  mkdir -p "$D"
  curl -fsSL "$REPO_RAW/heat.command.md" -o "$D/heat.md"
done

# Optional: install the Telegram listener if not present
LISTENER="$HOME/ClaudeCodexBridge/bin/hanna-telegram-listener.py"
if [ ! -f "$LISTENER" ]; then
  mkdir -p "$HOME/ClaudeCodexBridge/bin"
  curl -fsSL "$REPO_RAW/hanna-telegram-listener.py" -o "$LISTENER"
  chmod +x "$LISTENER"
  echo "installed: $LISTENER"
fi

# Optional: install the launchd plist if not present
PLIST="$HOME/Library/LaunchAgents/io.prosper.hanna-telegram-listener.plist"
if [ ! -f "$PLIST" ]; then
  curl -fsSL "$REPO_RAW/io.prosper.hanna-telegram-listener.plist" -o "$PLIST"
  echo "installed: $PLIST"
  launchctl load -w "$PLIST"
  echo "loaded Telegram listener launchd job"
fi

echo "✅ heat skill installed — slash command /heat is live"
echo "📚 Read $HOME/.claude/skills/heat/SKILL.md for the full playbook"
