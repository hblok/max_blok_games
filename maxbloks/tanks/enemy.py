# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
import math
from maxbloks.tanks import position


class Enemy(pygame.sprite.Sprite):
    """Enemy that chases the player."""

    def __init__(self, pos: position.Position, config, color: pygame.Color, speed_multiplier: float = 1.0):
        super().__init__()
        self.world_position = pos
        self.config = config
        self.color = color
        self.speed = config.base_speed * speed_multiplier
        self.health = config.health
        self.collision_radius = config.size // 2

        self._create_enemy_image()
        self.rect = self.image.get_rect(center=self.world_position.to_tuple())

    def _create_enemy_image(self):
        size = self.config.size
        self.image = pygame.Surface((size, size))
        self.image.fill((255, 0, 255))
        self.image.set_colorkey((255, 0, 255))

        pygame.draw.circle(self.image, self.color, (size // 2, size // 2), size // 2)

        eye_offset = size // 4
        eye_size = size // 6
        pygame.draw.circle(self.image, (0, 0, 0),
                           (size // 2 - eye_offset, size // 2 - eye_offset), eye_size)
        pygame.draw.circle(self.image, (0, 0, 0),
                           (size // 2 + eye_offset, size // 2 - eye_offset), eye_size)

    def update_ai(self, target_position: position.Position):
        """Move enemy toward target position."""
        dx = target_position.x - self.world_position.x
        dy = target_position.y - self.world_position.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > 0:
            self.world_position.x += (dx / distance) * self.speed
            self.world_position.y += (dy / distance) * self.speed
            self.rect.center = self.world_position.to_tuple()

    def take_damage(self, amount: int):
        self.health -= amount

    def is_alive(self) -> bool:
        return self.health > 0

    def resolve_obstacle_collision(self, pushback: position.Position):
        self.world_position.x += pushback.x
        self.world_position.y += pushback.y
        self.rect.center = self.world_position.to_tuple()
