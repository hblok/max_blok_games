# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path


class GamePaths:
    """Manages paths to game assets."""

    def __init__(self):
        self.root = Path(__file__).parent
        self.assets = self.root / "assets"
        self.sprites = self.assets / "sprites"
        self.sounds = self.assets / "sounds"
        self.fonts = self.assets / "fonts"

    def get_sprite_path(self, filename: str) -> Path:
        return self.sprites / filename

    def get_sound_path(self, filename: str) -> Path:
        return self.sounds / filename

    def get_font_path(self, filename: str) -> Path:
        return self.fonts / filename
