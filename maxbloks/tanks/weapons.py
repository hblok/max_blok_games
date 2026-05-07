# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Weapon system with multiple weapon types and pickups."""

import pygame
import math
from typing import List, Optional

from maxbloks.tanks import position
from maxbloks.tanks import projectile as projectile_module


class WeaponType:
    """Enum for weapon types."""
    DEFAULT = "default"
    FASTER_SHOOTER = "faster_shooter"
    LASER = "laser"
    SPRAY_SHOOTER = "spray_shooter"
    BOMBS = "bombs"


class Weapon:
    """Base weapon class."""

    def __init__(self, config, projectile_config, colors):
        self.config = config
        self.projectile_config = projectile_config
        self.colors = colors
        self.weapon_type = WeaponType.DEFAULT
        self.fire_rate = config.fire_rate
        self.duration = 0

    def fire(self, pos: position.Position, angle: float,
             current_time: int) -> List[projectile_module.Projectile]:
        proj = projectile_module.Projectile(
            position.Position(pos.x, pos.y),
            angle,
            self.projectile_config,
            self.colors.projectile
        )
        proj.spawn_time = current_time
        return [proj]


class FasterShooter(Weapon):
    """Faster fire rate weapon."""

    def __init__(self, config, projectile_config, colors):
        super().__init__(config, projectile_config, colors)
        self.weapon_type = WeaponType.FASTER_SHOOTER
        self.fire_rate = max(50, config.fire_rate // 3)
        self.duration = config.weapon_duration


class SprayShooter(Weapon):
    """Shoots multiple projectiles in a spread."""

    def __init__(self, config, projectile_config, colors):
        super().__init__(config, projectile_config, colors)
        self.weapon_type = WeaponType.SPRAY_SHOOTER
        self.fire_rate = config.fire_rate
        self.duration = config.weapon_duration

    def fire(self, pos: position.Position, angle: float,
             current_time: int) -> List[projectile_module.Projectile]:
        projectiles: List[projectile_module.Projectile] = []
        for offset in [-20, -10, 0, 10, 20]:
            proj = projectile_module.Projectile(
                position.Position(pos.x, pos.y),
                angle + offset,
                self.projectile_config,
                self.colors.spray
            )
            proj.spawn_time = current_time
            projectiles.append(proj)
        return projectiles


class LaserBeam(pygame.sprite.Sprite):
    """Continuous laser beam sprite anchored to the tank barrel."""

    def __init__(self, colors, thickness: int = 8, length: int = 1000):
        super().__init__()
        self.colors = colors
        self.thickness = thickness
        self.length = length
        self.angle = 0.0

        self.start = position.Position(0.0, 0.0)
        self.end = position.Position(0.0, 0.0)

        self.base_image = pygame.Surface((self.thickness, self.length), pygame.SRCALPHA)
        pygame.draw.rect(self.base_image, self.colors.laser,
                         pygame.Rect(0, 0, self.thickness, self.length))
        pygame.draw.rect(self.base_image, pygame.Color(255, 180, 180, 160),
                         pygame.Rect(0, 0, self.thickness, self.length), 2)

        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(self.start.x), int(self.start.y)))

    def update_anchor(self, tank_pos: position.Position, tank_angle: float, barrel_offset: float):
        self.angle = tank_angle
        rad = math.radians(self.angle - 90.0)
        dir_x = math.cos(rad)
        dir_y = math.sin(rad)

        self.start = position.Position(
            tank_pos.x + dir_x * barrel_offset,
            tank_pos.y + dir_y * barrel_offset
        )
        self.end = position.Position(
            self.start.x + dir_x * self.length,
            self.start.y + dir_y * self.length
        )

        self.image = pygame.transform.rotate(self.base_image, -self.angle)
        mid_x = (self.start.x + self.end.x) * 0.5
        mid_y = (self.start.y + self.end.y) * 0.5
        self.rect = self.image.get_rect(center=(int(mid_x), int(mid_y)))

    def intersects_enemy(self, enemy) -> bool:
        ex = enemy.world_position.x
        ey = enemy.world_position.y
        sx = self.start.x
        sy = self.start.y
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y

        seg_len2 = dx * dx + dy * dy
        if seg_len2 <= 1e-6:
            dist = math.hypot(ex - sx, ey - sy)
            return dist <= enemy.collision_radius + self.thickness * 0.5

        t = ((ex - sx) * dx + (ey - sy) * dy) / seg_len2
        t = max(0.0, min(1.0, t))

        cx = sx + t * dx
        cy = sy + t * dy
        dist = math.hypot(ex - cx, ey - cy)
        return dist <= enemy.collision_radius + self.thickness * 0.5


class LaserWeapon(Weapon):
    """Continuous beam weapon controller."""

    def __init__(self, config, projectile_config, colors):
        super().__init__(config, projectile_config, colors)
        self.weapon_type = WeaponType.LASER
        self.fire_rate = config.fire_rate
        self.duration = config.weapon_duration
        self.beam: Optional[LaserBeam] = None

    def ensure_beam(self, projectiles_group: pygame.sprite.Group) -> LaserBeam:
        if self.beam is None or not self.beam.alive():
            self.beam = LaserBeam(self.colors, thickness=8, length=1000)
            projectiles_group.add(self.beam)
        return self.beam

    def update_beam(self, projectiles_group: pygame.sprite.Group,
                    tank_pos: position.Position, tank_angle: float, barrel_offset: float):
        beam = self.ensure_beam(projectiles_group)
        beam.update_anchor(tank_pos, tank_angle, barrel_offset)

    def deactivate_beam(self, projectiles_group: pygame.sprite.Group):
        if self.beam is not None:
            if self.beam.alive():
                self.beam.kill()
            self.beam = None


class BombProjectile(projectile_module.Projectile):
    """Explosive projectile that can land and act as a mine."""

    def __init__(self, pos: position.Position, angle: float, config, color: pygame.Color):
        super().__init__(pos, angle, config, color)
        self.explosion_radius = 80
        self.explosion_damage = config.damage * 2
        self.penetrating = False
        self.landed = False
        self.trigger_radius = max(self.collision_radius, 12)

        size = self.config.size * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (50, 50, 50), (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, (200, 200, 0), (size // 2, size // 2), size // 3)
        self.rect = self.image.get_rect(center=self.world_position.to_tuple())
        self.collision_radius = size // 2

    def land(self):
        """Transform the moving bomb into a stationary landmine."""
        self.landed = True
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        pygame.draw.circle(self.image, (255, 90, 0),
                           (self.rect.width // 2, self.rect.height // 2),
                           self.rect.width // 4, 2)

    def update_position(self):
        if self.landed:
            self.rect.center = self.world_position.to_tuple()
            return
        super().update_position()

    def is_expired(self, current_time: int) -> bool:
        return False


class BombWeapon(Weapon):
    """Weapon that fires bomb projectiles."""

    def __init__(self, config, projectile_config, colors):
        super().__init__(config, projectile_config, colors)
        self.weapon_type = WeaponType.BOMBS
        self.fire_rate = config.fire_rate * 2
        self.duration = config.weapon_duration

    def fire(self, pos: position.Position, angle: float,
             current_time: int) -> List[BombProjectile]:
        bomb = BombProjectile(
            position.Position(pos.x, pos.y),
            angle,
            self.projectile_config,
            self.colors.bomb
        )
        bomb.spawn_time = current_time
        return [bomb]


class WeaponPickup:
    """Collectible weapon pickup in the world."""

    def __init__(self, pos: position.Position, weapon_type: str, config, colors):
        self.world_position = pos
        self.weapon_type = weapon_type
        self.config = config
        self.colors = colors
        self.collision_radius = config.size

        size = config.size
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)

        color_map = {
            WeaponType.FASTER_SHOOTER: (255, 200, 0),
            WeaponType.LASER: (255, 0, 255),
            WeaponType.SPRAY_SHOOTER: (0, 255, 255),
            WeaponType.BOMBS: (255, 128, 0),
        }
        color = color_map.get(weapon_type, (200, 200, 200))

        pygame.draw.rect(self.image, (100, 100, 100), (size // 4, size // 4, size // 2, size // 2))
        pygame.draw.rect(self.image, color, (size // 4 + 2, size // 4 + 2, size // 2 - 4, size // 2 - 4))
        pygame.draw.circle(self.image, (255, 255, 255), (size // 2, size // 2), 3)

        self.rect = self.image.get_rect(center=self.world_position.to_tuple())

    def get_world_rect(self) -> pygame.Rect:
        return self.rect
