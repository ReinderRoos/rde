local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- WSL
config.default_prog = { "wsl.exe", "-d", "Ubuntu" }

-- Font
config.font = wezterm.font("JetBrainsMono Nerd Font")
config.font_size = 12.5

-- Kleuren
config.color_scheme = "Catppuccin Mocha"

-- Scrollback
config.scrollback_lines = 50000

-- Tabbar
config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true
config.use_fancy_tab_bar = false

-- Venster
config.window_close_confirmation = "NeverPrompt"
config.adjust_window_size_when_changing_font_size = false

-- Cursor
config.default_cursor_style = "BlinkingBar"

return config