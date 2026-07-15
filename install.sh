#!/usr/bin/env bash
set -euo pipefail

RDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "RDE installeren vanuit: $RDE_DIR"

mkdir -p "$HOME/.local/scripts"

ln -sfn "$RDE_DIR/tmux/tmux.conf" "$HOME/.tmux.conf"
ln -sfn "$RDE_DIR/scripts/proj" "$HOME/.local/scripts/proj"
chmod +x "$RDE_DIR/scripts/proj"

BASH_LOAD_LINE='if [ -f "$HOME/rde/bash/rde.sh" ]; then source "$HOME/rde/bash/rde.sh"; fi'

touch "$HOME/.bashrc"

if ! grep -Fqx "$BASH_LOAD_LINE" "$HOME/.bashrc"; then
    printf '\n# Load Reinder Development Environment\n%s\n' \
        "$BASH_LOAD_LINE" >> "$HOME/.bashrc"
fi

if command -v cmd.exe >/dev/null 2>&1; then
    WINDOWS_HOME="$(
        cmd.exe /c echo %USERPROFILE% 2>/dev/null |
        tr -d '\r' |
        xargs wslpath
    )"

    if [ -d "$WINDOWS_HOME" ]; then
        cp -f "$RDE_DIR/wezterm/wezterm.lua" \
            "$WINDOWS_HOME/.wezterm.lua"
        echo "WezTerm-configuratie geplaatst in $WINDOWS_HOME"
    fi
fi

echo "RDE-installatie voltooid."
echo "Open een nieuwe shell of voer uit: source ~/.bashrc"
