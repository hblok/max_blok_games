# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Entity model objects for TankBattle."""

import dataclasses
import enum

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import utils


class WeaponType(enum.Enum):
    """Available weapon modes."""

    PRIMARY = "primary"
    SPREAD_SHOT = "spread_shot"
    ROCKET = "rocket"
    RAPID_FIRE = "rapid_fire"
    RICOCHET = "ricochet"
    MINE_LAYER = "mine_layer"


class PowerUpType(enum.Enum):
    """Power-up pickup types."""

    HEALTH = "health"
    SPREAD_SHOT = "spread_shot"
    ROCKET = "rocket"
    RAPID_FIRE = "rapid_fire"
    RICOCHET = "ricochet"
    MINE_LAYER = "mine_layer"


class ObstacleType(enum.Enum):
    """Obstacle types."""

    HARD_ROCK = "hard_rock"
    SOFT = "soft"


@dataclasses.dataclass
class Tank:
    """Top-down tank with independent body and turret orientation."""

    x: float
    y: float
    body_angle: float = 0.0
    turret_angle: float = 0.0
    hp: int = constants.TANK_MAX_HP
    speed: float = constants.TANK_SPEED
    rotation_speed: float = constants.TANK_ROTATION_SPEED
    active_weapon: WeaponType = WeaponType.PRIMARY
    weapon_timer: float = 0.0
    weapon_shots: int = 0
    is_alive: bool = True
    hit_flash_timer: float = 0.0
    fire_cooldown: float = 0.0
    player_id: int = 1

    @property
    def position(self):
        """Return the tank world position."""
        return self.x, self.y

    def reset(self, x_value, y_value, angle):
        """Reset tank for a new round."""
        self.x = x_value
        self.y = y_value
        self.body_angle = angle
        self.turret_angle = angle
        self.hp = constants.TANK_MAX_HP
        self.active_weapon = WeaponType.PRIMARY
        self.weapon_timer = 0.0
        self.weapon_shots = 0
        self.is_alive = True
        self.hit_flash_timer = 0.0
        self.fire_cooldown = 0.0

    def rotate_body(self, direction, dt):
        """Rotate body by signed direction."""
        self.body_angle = utils.normalize_angle(
            self.body_angle + direction * self.rotation_speed * dt
        )

    def set_turret_from_vector(self, x_value, y_value):
        """Aim turret from a non-neutral right-stick vector."""
        if x_value != 0.0 or y_value != 0.0:
            self.turret_angle = utils.vector_to_angle(x_value, y_value)

    def move(self, forward_amount, dt, arena):
        """Move forward/backward, reverting if blocked."""
        old_x = self.x
        old_y = self.y
        vx_value, vy_value = utils.angle_to_vector(self.body_angle)
        self.x += vx_value * self.speed * forward_amount * dt
        self.y += vy_value * self.speed * forward_amount * dt
        self.x = utils.clamp(self.x, constants.TANK_HITBOX_RADIUS, constants.WORLD_WIDTH - constants.TANK_HITBOX_RADIUS)
        self.y = utils.clamp(self.y, constants.TANK_HITBOX_RADIUS, constants.WORLD_HEIGHT - constants.TANK_HITBOX_RADIUS)
        if arena.collides_with_solid(self.position, constants.TANK_COLLISION_RADIUS):
            self.x = old_x
            self.y = old_y

    def update(self, dt):
        """Advance timers."""
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        if self.active_weapon != WeaponType.PRIMARY:
            self.weapon_timer = max(0.0, self.weapon_timer - dt)
            if self.weapon_timer == 0.0 or self.weapon_shots == 0:
                self.clear_weapon()

    def damage(self, amount):
        """Apply damage and trigger hit flash."""
        if not self.is_alive:
            return
        self.hp = max(0, self.hp - amount)
        self.hit_flash_timer = constants.TANK_HIT_FLASH_TIME
        if self.hp == 0:
            self.is_alive = False

    def heal(self, amount):
        """Restore HP up to the maximum."""
        if self.is_alive:
            self.hp = min(constants.TANK_MAX_HP, self.hp + amount)

    def apply_powerup(self, power_type):
        """Apply a health or weapon pickup."""
        if power_type == PowerUpType.HEALTH:
            self.heal(constants.HEALTH_PACK_RESTORE)
            return
        self.active_weapon = WeaponType(power_type.value)
        self.weapon_timer = constants.WEAPON_DURATION
        if power_type == PowerUpType.SPREAD_SHOT:
            self.weapon_shots = constants.SPREAD_SHOT_LIMIT
        elif power_type == PowerUpType.ROCKET:
            self.weapon_shots = constants.ROCKET_LIMIT
        elif power_type == PowerUpType.RICOCHET:
            self.weapon_shots = constants.RICOCHET_LIMIT
        elif power_type == PowerUpType.MINE_LAYER:
            self.weapon_shots = constants.MINE_LIMIT
        else:
            self.weapon_shots = -1

    def clear_weapon(self):
        """Revert to primary weapon."""
        self.active_weapon = WeaponType.PRIMARY
        self.weapon_timer = 0.0
        self.weapon_shots = 0

    def can_fire(self):
        """Return True when cooldown allows firing."""
        return self.fire_cooldown <= 0.0 and self.is_alive

    def consume_shot(self):
        """Consume temporary shot and set cooldown."""
        if self.active_weapon == WeaponType.RAPID_FIRE:
            self.fire_cooldown = constants.RAPID_FIRE_COOLDOWN
        else:
            self.fire_cooldown = constants.PRIMARY_FIRE_COOLDOWN
        if self.weapon_shots > 0:
            self.weapon_shots -= 1


@dataclasses.dataclass
class Bullet:
    """Projectile fired by a tank."""

    x: float
    y: float
    vx: float
    vy: float
    damage: int
    owner: Tank
    max_bounces: int = 0
    bounces_remaining: int = 0
    radius: float = constants.BULLET_RADIUS
    lifetime: float = constants.BULLET_MAX_LIFETIME
    is_alive: bool = True
    weapon_type: WeaponType = WeaponType.PRIMARY

    @property
    def position(self):
        """Return bullet position."""
        return self.x, self.y

    @classmethod
    def from_angle(cls, x_value, y_value, angle, speed, damage, owner, weapon_type=WeaponType.PRIMARY, bounces=0):
        """Create a bullet from an angle."""
        dx_value, dy_value = utils.angle_to_vector(angle)
        return cls(
            x_value,
            y_value,
            dx_value * speed,
            dy_value * speed,
            damage,
            owner,
            bounces,
            bounces,
            constants.BULLET_RADIUS,
            constants.BULLET_MAX_LIFETIME,
            True,
            weapon_type,
        )

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
            if obstacle.type == ObstacleType.SOFT:
                obstacle.is_destroyed = True
                self.is_alive = False
                return
            normal = arena.tile_collision_normal(self.position, obstacle)
        if normal is not None:
            if self.bounces_remaining > 0:
                self.vx, self.vy = utils.reflect_velocity((self.vx, self.vy), normal)
                self.bounces_remaining -= 1
                self.x = utils.clamp(self.x, self.radius, constants.WORLD_WIDTH - self.radius)
                self.y = utils.clamp(self.y, self.radius, constants.WORLD_HEIGHT - self.radius)
            else:
                self.is_alive = False


@dataclasses.dataclass
class Mine:
    """Delayed-arming proximity mine."""

    x: float
    y: float
    owner: Tank
    armed: bool = False
    trigger_radius: float = constants.MINE_TRIGGER_RADIUS
    arm_timer: float = constants.MINE_ARM_TIME
    is_alive: bool = True

    @property
    def position(self):
        """Return mine position."""
        return self.x, self.y

    def update(self, dt):
        """Arm mine after delay."""
        if not self.armed:
            self.arm_timer = max(0.0, self.arm_timer - dt)
            if self.arm_timer == 0.0:
                self.armed = True

    def check_trigger(self, tanks):
        """Return detonated tanks and kill mine when triggered."""
        if not self.armed or not self.is_alive:
            return []
        hit_tanks = []
        for tank in tanks:
            if tank.is_alive and utils.circles_collide(self.position, self.trigger_radius, tank.position, constants.TANK_HITBOX_RADIUS):
                tank.damage(constants.MINE_DAMAGE)
                hit_tanks.append(tank)
        if hit_tanks:
            self.is_alive = False
        return hit_tanks


@dataclasses.dataclass
class PowerUp:
    """Collectible power-up."""

    x: float
    y: float
    type: PowerUpType
    identifier: int
    pulse_timer: float = 0.0
    is_alive: bool = True

    @property
    def position(self):
        """Return power-up position."""
        return self.x, self.y

    def update(self, dt):
        """Advance pulsing animation timer."""
        self.pulse_timer += dt * constants.POWERUP_PULSE_SPEED

    def collect_if_touching(self, tank):
        """Apply pickup to tank if overlapping."""
        if self.is_alive and utils.circles_collide(self.position, constants.POWERUP_COLLISION_RADIUS, tank.position, constants.TANK_HITBOX_RADIUS):
            tank.apply_powerup(self.type)
            self.is_alive = False
            return True
        return False


@dataclasses.dataclass
class Obstacle:
    """Tile obstacle."""

    tile_x: int
    tile_y: int
    type: ObstacleType
    is_destroyed: bool = False

    @property
    def position(self):
        """Return tile position."""
        return self.tile_x, self.tile_y

    def restore(self):
        """Restore soft obstacle."""
        if self.type == ObstacleType.SOFT:
            self.is_destroyed = False
