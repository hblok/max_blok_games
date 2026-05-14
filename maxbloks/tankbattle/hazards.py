# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Arena environmental hazards for TankBattle."""

import dataclasses
import enum
import logging
import math
import random

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import utils

logger = logging.getLogger(__name__)


class HazardType(enum.Enum):
    """Types of environmental hazards."""

    ICE_PATCH = "ice_patch"
    MUD_SWAMP = "mud_swamp"
    CONVEYOR_BELT = "conveyor_belt"
    TELEPORTER = "teleporter"
    LANDMINE = "landmine"
    TURRET = "turret"


@dataclasses.dataclass
class IcePatch:
    """Low-friction zone causing tanks to slide and drift."""

    tile_x: int
    tile_y: int
    is_alive: bool = True

    @property
    def position(self):
        """Return tile position."""
        return self.tile_x, self.tile_y

    def get_friction_modifier(self):
        """Return friction multiplier (0.3 = very slippery)."""
        return 0.3


@dataclasses.dataclass
class MudSwamp:
    """High-friction terrain that slashes maximum movement speed in half."""

    tile_x: int
    tile_y: int
    is_alive: bool = True

    @property
    def position(self):
        """Return tile position."""
        return self.tile_x, self.tile_y

    def get_speed_modifier(self):
        """Return speed multiplier (0.5 = half speed)."""
        return 0.5


@dataclasses.dataclass
class ConveyorBelt:
    """Moving tile that pushes tanks or projectiles in specific directions."""

    tile_x: int
    tile_y: int
    direction_x: float  # Normalized direction vector
    direction_y: float
    push_speed: float = 80.0  # Pixels per second
    is_alive: bool = True

    @property
    def position(self):
        """Return tile position."""
        return self.tile_x, self.tile_y

    def get_push_velocity(self):
        """Return push velocity vector."""
        return self.direction_x * self.push_speed, self.direction_y * self.push_speed


@dataclasses.dataclass
class Teleporter:
    """Sci-fi portal linking two distant points on the map."""

    tile_x: int
    tile_y: int
    target_tile_x: int
    target_tile_y: int
    cooldown: float = 0.0  # Seconds before can teleport again
    is_alive: bool = True

    @property
    def position(self):
        """Return tile position."""
        return self.tile_x, self.tile_y

    @property
    def target_position(self):
        """Return target world position."""
        return utils.tile_to_world(self.target_tile_x, self.target_tile_y)

    def update(self, dt):
        """Update cooldown."""
        self.cooldown = max(0.0, self.cooldown - dt)

    def can_teleport(self):
        """Check if teleporter is ready."""
        return self.cooldown <= 0.0

    def teleport(self):
        """Trigger teleport and set cooldown."""
        self.cooldown = 2.0  # 2 second cooldown


@dataclasses.dataclass
class Landmine:
    """Neutral, pre-placed explosive hazard hidden inside destructible soft obstacles."""

    tile_x: int
    tile_y: int
    trigger_radius: float = 32.0
    damage: int = 3
    is_armed: bool = False
    arm_timer: float = 1.5
    is_alive: bool = True

    @property
    def position(self):
        """Return world position."""
        return utils.tile_to_world(self.tile_x, self.tile_y)

    def update(self, dt):
        """Arm mine after delay."""
        if not self.is_armed:
            self.arm_timer = max(0.0, self.arm_timer - dt)
            if self.arm_timer == 0.0:
                self.is_armed = True
                logger.debug("Landmine at (%d, %d) armed", self.tile_x, self.tile_y)

    def check_trigger(self, tanks):
        """Return detonated tanks and kill mine when triggered."""
        if not self.is_armed or not self.is_alive:
            return []
        hit_tanks = []
        for tank in tanks:
            if tank.is_alive and utils.circles_collide(self.position, self.trigger_radius, tank.position, constants.TANK_HITBOX_RADIUS):
                tank.damage(self.damage)
                hit_tanks.append(tank)
        if hit_tanks:
            self.is_alive = False
        return hit_tanks


@dataclasses.dataclass
class TurretBullet:
    """Projectile fired by a turret."""

    x: float
    y: float
    vx: float
    vy: float
    damage: int = 2
    radius: float = 4.0
    lifetime: float = 4.0
    is_alive: bool = True

    @property
    def position(self):
        """Return bullet position."""
        return self.x, self.y

    def update(self, dt, arena):
        """Move and interact with arena boundaries/obstacles."""
        if not self.is_alive:
            return
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.is_alive = False
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        normal = arena.boundary_normal(self.position, self.radius)
        obstacle = arena.obstacle_at_world(self.x, self.y)
        if obstacle is not None and not obstacle.is_destroyed:
            if obstacle.type == entities.ObstacleType.SOFT:
                obstacle.is_destroyed = True
                self.is_alive = False
                return
            normal = arena.tile_collision_normal(self.position, obstacle)
        if normal is not None:
            self.is_alive = False


@dataclasses.dataclass
class Turret:
    """Automated neutral defense shooting at whichever tank gets too close."""

    tile_x: int
    tile_y: int
    engage_distance: float = 250.0
    fire_cooldown: float = 0.0
    fire_interval: float = 1.5
    damage: int = 2
    bullet_speed: float = 200.0
    hp: int = constants.TURRET_HP
    is_alive: bool = True

    @property
    def position(self):
        """Return world position."""
        return utils.tile_to_world(self.tile_x, self.tile_y)

    def take_damage(self, amount):
        """Apply damage to the turret; destroys it when HP reaches zero."""
        if not self.is_alive:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.is_alive = False
            logger.debug("Turret at (%d, %d) destroyed", self.tile_x, self.tile_y)

    def update(self, dt, tanks, game):
        """Update turret logic and fire at nearby tanks."""
        if not self.is_alive:
            return None

        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

        # Find nearest alive tank
        alive_tanks = [t for t in tanks if t.is_alive]
        if not alive_tanks:
            return None

        target = min(alive_tanks, key=lambda t: utils.distance(self.position, t.position))
        dist = utils.distance(self.position, target.position)

        if dist > self.engage_distance:
            return None

        # Fire if cooldown ready
        if self.fire_cooldown <= 0.0:
            self.fire_cooldown = self.fire_interval
            return self._fire_at(target)

        return None

    def _fire_at(self, target):
        """Create a bullet aimed at the target."""
        world_x, world_y = self.position
        dx = target.x - world_x
        dy = target.y - world_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return None

        vx = (dx / dist) * self.bullet_speed
        vy = (dy / dist) * self.bullet_speed

        return TurretBullet(
            x=world_x,
            y=world_y,
            vx=vx,
            vy=vy,
            damage=self.damage,
        )