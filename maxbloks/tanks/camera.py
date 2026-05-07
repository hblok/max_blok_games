# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
from maxbloks.tanks import position


class Camera:
    """Camera that follows the player and renders only visible portions of the world."""

    def __init__(self, viewport_width: int, viewport_height: int,
                 world_width: int, world_height: int):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.world_width = world_width
        self.world_height = world_height

        self.x = 0.0
        self.y = 0.0

    def update(self, target_pos: position.Position):
        """Update camera position to follow target (usually the player tank)."""
        self.x = target_pos.x - self.viewport_width / 2
        self.y = target_pos.y - self.viewport_height / 2
        self._clamp_to_world()

    def _clamp_to_world(self):
        self.x = max(0, min(self.x, self.world_width - self.viewport_width))
        self.y = max(0, min(self.y, self.world_height - self.viewport_height))

    def apply(self, entity_pos: position.Position) -> position.Position:
        """Convert world position to screen position."""
        screen_x = entity_pos.x - self.x
        screen_y = entity_pos.y - self.y
        return position.Position(screen_x, screen_y)

    def apply_rect(self, world_rect: pygame.Rect) -> pygame.Rect:
        """Convert world rect to screen rect."""
        return pygame.Rect(
            world_rect.x - int(self.x),
            world_rect.y - int(self.y),
            world_rect.width,
            world_rect.height
        )

    def is_visible(self, world_pos: position.Position, margin: int = 100) -> bool:
        return (world_pos.x >= self.x - margin and
                world_pos.x <= self.x + self.viewport_width + margin and
                world_pos.y >= self.y - margin and
                world_pos.y <= self.y + self.viewport_height + margin)

    def is_rect_visible(self, world_rect: pygame.Rect, margin: int = 100) -> bool:
        camera_rect = pygame.Rect(
            int(self.x) - margin,
            int(self.y) - margin,
            self.viewport_width + margin * 2,
            self.viewport_height + margin * 2
        )
        return world_rect.colliderect(camera_rect)

    def get_viewport_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y),
                           self.viewport_width, self.viewport_height)
