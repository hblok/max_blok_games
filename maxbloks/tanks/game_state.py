# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import IntEnum


class GameState(IntEnum):
    """Possible game states."""
    PLAYING = 1
    GAME_OVER = 2
    VICTORY = 3


class GameStats:
    """Track game statistics."""

    def __init__(self):
        self.score = 0
        self.enemies_killed = 0
        self.shots_fired = 0

    def reset(self):
        self.score = 0
        self.enemies_killed = 0
        self.shots_fired = 0

    def enemy_killed(self):
        self.enemies_killed += 1
        self.score += 100

    def shot_fired(self):
        self.shots_fired += 1
