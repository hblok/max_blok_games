# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Tuple, Optional
import pygame
import math

from maxbloks.tanks import projectile as projectile_module
from maxbloks.tanks import position
from maxbloks.tanks import constants


class Tank(pygame.sprite.Sprite):
    """Player-controlled tank entity with detailed visual design and smooth orientation."""

    def __init__(self, pos: position.Position, config, colors):
        super().__init__()
        self.config = config
        self.world_position = pos
        self.angle = 0.0
        self.health = config.max_health
        self.last_fire_time = 0
        self.colors = colors

        self.rotation_speed = getattr(self.config, "rotation_speed", 60.0)
        self._last_rot_ms = pygame.time.get_ticks()

        self._create_surface()
        self.rect = self.image.get_rect(center=self.world_position.to_tuple())
        self.collision_radius = config.size / 2.5

    def _create_surface(self):
        size = self.config.size
        self.original_image = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        track_width = size // 5
        track_height = size * 3 // 4
        track_y = center - track_height // 2

        pygame.draw.rect(self.original_image, self.colors.tank_tracks,
                         (2, track_y, track_width, track_height))
        pygame.draw.rect(self.original_image, self.colors.tank_details,
                         (2, track_y, track_width, track_height), 2)

        pygame.draw.rect(self.original_image, self.colors.tank_tracks,
                         (size - track_width - 2, track_y, track_width, track_height))
        pygame.draw.rect(self.original_image, self.colors.tank_details,
                         (size - track_width - 2, track_y, track_width, track_height), 2)

        body_width = size * 2 // 3
        body_height = size // 2
        body_rect = pygame.Rect(
            center - body_width // 2,
            center - body_height // 2,
            body_width,
            body_height
        )
        pygame.draw.rect(self.original_image, self.colors.tank_body, body_rect)
        pygame.draw.rect(self.original_image, self.colors.tank_details, body_rect, 2)

        turret_radius = size // 4
        pygame.draw.circle(self.original_image, self.colors.tank_body, (center, center), turret_radius)
        pygame.draw.circle(self.original_image, self.colors.tank_details, (center, center), turret_radius, 2)

        barrel_width = 6
        barrel_length = size // 2
        barrel_rect = pygame.Rect(
            center - barrel_width // 2,
            center - barrel_length,
            barrel_width,
            barrel_length
        )
        pygame.draw.rect(self.original_image, self.colors.tank_barrel, barrel_rect)
        pygame.draw.rect(self.original_image, pygame.Color(50, 50, 50), barrel_rect, 1)

        hatch_size = turret_radius // 2
        pygame.draw.circle(self.original_image, self.colors.tank_details, (center, center), hatch_size)

        pygame.draw.line(self.original_image, pygame.Color(100, 200, 100),
                         (center, center - body_height // 2 - 2),
                         (center, center - body_height // 2 - 8), 3)

        self.image = self.original_image.copy()

    def update_movement(self, axis_x: float, axis_y: float, deadzone: float):
        """Update tank movement based on joystick input."""
        if abs(axis_x) < deadzone and abs(axis_y) < deadzone:
            return

        adjusted_x, adjusted_y = self._apply_diagonal_boost(axis_x, axis_y)
        self._update_rotation(adjusted_x, adjusted_y)
        self._move_forward()

    def _apply_diagonal_boost(self, axis_x: float, axis_y: float) -> Tuple[float, float]:
        magnitude = math.sqrt(axis_x * axis_x + axis_y * axis_y)

        if magnitude < 0.01:
            return axis_x, axis_y

        is_diagonal = abs(axis_x) > 0.3 and abs(axis_y) > 0.3
        if is_diagonal:
            boost = self.config.diagonal_sensitivity
            normalized_x = axis_x / magnitude
            normalized_y = axis_y / magnitude
            boosted_magnitude = min(magnitude * boost, 1.0)
            return normalized_x * boosted_magnitude, normalized_y * boosted_magnitude

        return axis_x, axis_y

    def _update_rotation(self, axis_x: float, axis_y: float):
        """Gradually orient the tank to face joystick direction."""
        target_angle = math.degrees(math.atan2(axis_y, axis_x)) + 90.0

        now_ms = pygame.time.get_ticks()
        dt = max(0.0, (now_ms - getattr(self, "_last_rot_ms", now_ms)) / 1000.0)
        self._last_rot_ms = now_ms

        diff = (target_angle - self.angle + 180.0) % 360.0 - 180.0

        max_step = self.rotation_speed * dt
        if abs(diff) <= max_step:
            self.angle = target_angle
        else:
            self.angle += max_step if diff > 0.0 else -max_step

        self.angle %= 360.0
        self._rotate_image()

    def _move_forward(self):
        rad = math.radians(self.angle - 90)
        self.world_position.x += math.cos(rad) * self.config.speed
        self.world_position.y += math.sin(rad) * self.config.speed

    def _rotate_image(self):
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=self.world_position.to_tuple())

    def constrain_to_world(self, world_width: int, world_height: int):
        margin = self.config.size // 2
        self.world_position.x = max(margin, min(world_width - margin, self.world_position.x))
        self.world_position.y = max(margin, min(world_height - margin, self.world_position.y))
        self.rect.center = self.world_position.to_tuple()

    def resolve_obstacle_collision(self, pushback: position.Position):
        self.world_position.x += pushback.x
        self.world_position.y += pushback.y
        self.rect.center = self.world_position.to_tuple()

    def can_fire(self, current_time: int, fire_rate: int) -> bool:
        return current_time - self.last_fire_time >= fire_rate

    def fire(self, current_time: int, weapon_manager):
        """Fire using the weapon manager."""
        fire_rate = weapon_manager.get_fire_rate()

        if not self.can_fire(current_time, fire_rate):
            return []

        self.last_fire_time = current_time

        barrel_offset = self.config.size * 0.4
        rad_angle = math.radians(self.angle)
        barrel_x = self.world_position.x + barrel_offset * math.sin(rad_angle)
        barrel_y = self.world_position.y - barrel_offset * math.cos(rad_angle)

        return weapon_manager.fire(
            position.Position(barrel_x, barrel_y),
            self.angle,
            current_time
        )

    def take_damage(self, damage: int):
        self.health = max(0, self.health - damage)

    def heal(self, amount: int):
        self.health = min(self.config.max_health, self.health + amount)

    def is_alive(self) -> bool:
        return self.health > 0
