# Reinder Development Environment

# Eigen scripts en lokaal geïnstalleerde programma's
export PATH="$HOME/.local/scripts:$HOME/.local/bin:$PATH"

# Aliassen
alias gs='git status'
alias gl='git log --oneline --graph --decorate'
alias ..='cd ..'
alias ...='cd ../..'
alias fd='fdfind'
alias cat='batcat'
alias lg='lazygit'

# Editor
export EDITOR=vim
export VISUAL=vim

# Zoxide
if command -v zoxide >/dev/null 2>&1; then
    eval "$(zoxide init bash)"
fi

# Start of heropen tmux voor interactieve shells
if command -v tmux >/dev/null 2>&1 &&
   [[ $- == *i* ]] &&
   [ -z "${TMUX:-}" ]; then
    exec tmux new-session -A -s main
fi
