#!/usr/bin/env bash
set -euo pipefail

RDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "RDE installeren vanuit: $RDE_DIR"

# Benodigde mappen
mkdir -p "$HOME/.local/scripts"
mkdir -p "$HOME/.config/lazygit"

# tmux-configuratie
ln -sfn \
    "$RDE_DIR/tmux/tmux.conf" \
    "$HOME/.tmux.conf"

# Projectlaunchers
ln -sfn \
    "$RDE_DIR/scripts/work" \
    "$HOME/.local/scripts/work"

if [ -f "$RDE_DIR/scripts/proj" ]; then
    ln -sfn \
        "$RDE_DIR/scripts/proj" \
        "$HOME/.local/scripts/proj"

    chmod +x "$RDE_DIR/scripts/proj"
fi

chmod +x "$RDE_DIR/scripts/work"
chmod +x "$RDE_DIR/work.py"

# Lazygit-configuratie
ln -sfn \
    "$RDE_DIR/lazygit/config.yml" \
    "$HOME/.config/lazygit/config.yml"

# RDE Bash-configuratie laden
BASH_LOAD_LINE='if [ -f "$HOME/rde/bash/rde.sh" ]; then source "$HOME/rde/bash/rde.sh"; fi'

touch "$HOME/.bashrc"

if ! grep -Fqx "$BASH_LOAD_LINE" "$HOME/.bashrc"; then
    printf '\n# Load Reinder Development Environment\n%s\n' \
        "$BASH_LOAD_LINE" >> "$HOME/.bashrc"
fi

# Algemene Git-configuratie laden
GIT_CONFIG_PATH="$RDE_DIR/git/gitconfig"

if [ -f "$GIT_CONFIG_PATH" ]; then
    if ! git config --global --get-all include.path 2>/dev/null |
        grep -Fxq "$GIT_CONFIG_PATH"; then
        git config --global --add include.path "$GIT_CONFIG_PATH"
    fi
fi

# WezTerm-configuratie naar Windows kopiëren
if command -v cmd.exe >/dev/null 2>&1 &&
   command -v wslpath >/dev/null 2>&1; then

    WINDOWS_HOME_RAW="$(
        cmd.exe /c echo %USERPROFILE% 2>/dev/null |
        tr -d '\r'
    )"

    if [ -n "$WINDOWS_HOME_RAW" ]; then
        WINDOWS_HOME="$(wslpath "$WINDOWS_HOME_RAW")"

        if [ -d "$WINDOWS_HOME" ] &&
           [ -f "$RDE_DIR/wezterm/wezterm.lua" ]; then

            cp -f \
                "$RDE_DIR/wezterm/wezterm.lua" \
                "$WINDOWS_HOME/.wezterm.lua"

            echo "WezTerm-configuratie geplaatst in: $WINDOWS_HOME"
        fi
    fi
fi

echo
echo "RDE-installatie voltooid."
echo "Voer nu uit:"
echo
echo "  source ~/.bashrc"
echo "  hash -r"
echo "  tmux source-file ~/.tmux.conf"
