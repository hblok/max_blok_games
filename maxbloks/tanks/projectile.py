# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
import math
from maxbloks.tanks import position


class Projectile(pygame.sprite.Sprite):
    """Projectile fired by the tank."""

    def __init__(self, pos: position.Position, angle: float, config, color: pygame.Color):
        super().__init__()
        self.world_position = pos
        self.angle = angle
        self.config = config
        self.color = color
        self.spawn_time = 0
        self.collision_radius = config.size // 2
        self.penetrating = False

        rad_angle = math.radians(angle)
        self.velocity_x = math.sin(rad_angle) * config.speed
        self.velocity_y = -math.cos(rad_angle) * config.speed

        self._create_projectile_image()
        self.rect = self.image.get_rect(center=self.world_position.to_tuple())

    def _create_projectile_image(self):
        size = self.config.size
        self.image = pygame.Surface((size, size))
        self.image.fill((255, 0, 255))
        self.image.set_colorkey((255, 0, 255))

        pygame.draw.circle(self.image, self.color, (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, (255, 255, 255), (size // 2, size // 2), size // 3)

    def update_position(self):
        self.world_position.x += self.velocity_x
        self.world_position.y += self.velocity_y
        self.rect.center = self.world_position.to_tuple()

    def is_expired(self, current_time: int) -> bool:
        return current_time - self.spawn_time > self.config.lifetime

    def is_off_world(self, world_width: int, world_height: int) -> bool:
        return (self.world_position.x < 0 or self.world_position.x > world_width or
                self.world_position.y < 0 or self.world_position.y > world_height)
