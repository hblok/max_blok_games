# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import enum


class GameState(enum.Enum):
    """Game state machine states."""

    MENU = "menu"
    LOBBY = "lobby"
    CONNECTING = "connecting"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    PAUSED = "paused"
    ROUND_OVER = "round_over"
    MATCH_OVER = "match_over"
