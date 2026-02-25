# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
entities.py — Player, Bullet, PowerUp, Particle data classes.

Each entity is a lightweight object with update() logic.
Drawing is handled by visual.py.
"""

from __future__ import annotations

import math
import random

from maxbloks.starfighter.settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT,
    FRICTION, ROTATION_SPEED, THRUST_POWER, MAX_SPEED,
    PLAYER_RADIUS, INVINCIBILITY_FRAMES,
    BULLET_SPEED, BULLET_LIFETIME, BULLET_RADIUS, MAX_BULLETS,
    HOMING_SPEED, HOMING_STEER, HOMING_LIFETIME, HOMING_MAX,
    BIGSHOT_SPEED, BIGSHOT_RADIUS, BIGSHOT_LIFETIME, BIGSHOT_MAX,
    FIRE_COOLDOWN_NORMAL, FIRE_COOLDOWN_RAPID, RAPID_MAX_BULLETS,
    SPREAD_ANGLE, SPEED_BOOST_MULT,
    POWERUP_LIFETIME, POWERUP_COLLECT_RADIUS, POWERUP_RADIUS,
    POWERUP_DURATION, SHIELD_HITS, SHIELD_INVINCIBILITY,
    PARTICLE_LIFETIME, PARTICLE_SPEED_MIN, PARTICLE_SPEED_MAX,
    PARTICLE_FRICTION,
    COLORS,
)
from maxbloks.starfighter.utils import (
    clamp_magnitude, wrap_position, normalize_angle,
    angle_to, random_range, circles_collide, distance,
)


# ======================================================================
# Player
# ======================================================================

class Player:
    """The player's ship."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -math.pi / 2   # facing up
        self.invincible = 0          # frames remaining
        self.fire_cooldown = 0
        self.radius = PLAYER_RADIUS

    @property
    def invincible_flash(self) -> bool:
        """True on frames where the ship should be hidden (blink)."""
        return self.invincible > 0 and (self.invincible // 4) % 2 == 0

    def update(self, rotate_left: bool, rotate_right: bool,
               thrust: bool, active_powerups: dict) -> None:
        """Advance one frame of player physics."""
        speed_mult = SPEED_BOOST_MULT if "speedboost" in active_powerups else 1.0
        max_spd = MAX_SPEED * speed_mult
        thrust_pow = THRUST_POWER * speed_mult

        # Rotation
        if rotate_left:
            self.angle -= ROTATION_SPEED
        if rotate_right:
            self.angle += ROTATION_SPEED

        # Thrust
        if thrust:
            self.vx += math.cos(self.angle) * thrust_pow
            self.vy += math.sin(self.angle) * thrust_pow

        # Clamp + friction
        self.vx, self.vy = clamp_magnitude(self.vx, self.vy, max_spd)
        self.vx *= FRICTION
        self.vy *= FRICTION

        # Move
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position(self.x, self.y,
                                       LOGICAL_WIDTH, LOGICAL_HEIGHT)

        # Invincibility countdown
        if self.invincible > 0:
            self.invincible -= 1

        # Fire cooldown
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def can_fire(self, bullets: list, active_powerups: dict) -> bool:
        """Check if the player can fire right now."""
        if self.fire_cooldown > 0:
            return False

        rapid = "rapidfire" in active_powerups
        homing = "homing" in active_powerups
        bigshot = "bigshot" in active_powerups

        if homing:
            count = sum(1 for b in bullets if b.homing)
            return count < HOMING_MAX
        if bigshot:
            count = sum(1 for b in bullets if b.big)
            return count < BIGSHOT_MAX

        max_b = RAPID_MAX_BULLETS if rapid else MAX_BULLETS
        return len(bullets) < max_b

    def fire(self, bullets: list, active_powerups: dict) -> None:
        """Create bullet(s) and set cooldown."""
        rapid = "rapidfire" in active_powerups
        homing = "homing" in active_powerups
        bigshot = "bigshot" in active_powerups
        spread = "spreadshot" in active_powerups

        cooldown = FIRE_COOLDOWN_RAPID if rapid else FIRE_COOLDOWN_NORMAL
        self.fire_cooldown = cooldown

        nose_x = self.x + math.cos(self.angle) * 20
        nose_y = self.y + math.sin(self.angle) * 20

        if homing:
            bullets.append(Bullet(
                nose_x, nose_y,
                math.cos(self.angle) * HOMING_SPEED,
                math.sin(self.angle) * HOMING_SPEED,
                life=HOMING_LIFETIME, radius=5,
                homing=True,
            ))
            return

        if bigshot:
            bullets.append(Bullet(
                nose_x, nose_y,
                math.cos(self.angle) * BIGSHOT_SPEED,
                math.sin(self.angle) * BIGSHOT_SPEED,
                life=BIGSHOT_LIFETIME, radius=BIGSHOT_RADIUS,
                big=True, pierce=True,
            ))
            return

        angles = [self.angle]
        if spread:
            angles = [
                self.angle - SPREAD_ANGLE,
                self.angle,
                self.angle + SPREAD_ANGLE,
            ]

        for a in angles:
            bullets.append(Bullet(
                nose_x, nose_y,
                math.cos(a) * BULLET_SPEED,
                math.sin(a) * BULLET_SPEED,
                life=BULLET_LIFETIME, radius=BULLET_RADIUS,
            ))

    def respawn(self) -> None:
        """Reset position after death."""
        self.x = LOGICAL_WIDTH / 2
        self.y = LOGICAL_HEIGHT / 2
        self.vx = 0.0
        self.vy = 0.0
        self.invincible = INVINCIBILITY_FRAMES


# ======================================================================
# Bullets
# ======================================================================

class Bullet:
    """A projectile (player or enemy)."""

    __slots__ = ("x", "y", "vx", "vy", "life", "radius",
                 "homing", "big", "pierce", "color")

    def __init__(self, x, y, vx, vy, life=60, radius=4,
                 homing=False, big=False, pierce=False,
                 color=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.radius = radius
        self.homing = homing
        self.big = big
        self.pierce = pierce
        self.color = color   # None → use default; set for enemy bullets

    def update(self, enemies=None) -> bool:
        """Advance one frame. Returns False if bullet should be removed."""
        if self.homing and enemies:
            self._steer_homing(enemies)

        self.x += self.vx
        self.y += self.vy
        self.life -= 1

        # Remove if expired or off-screen (bullets do NOT wrap)
        if self.life <= 0:
            return False
        if (self.x < -self.radius or self.x > LOGICAL_WIDTH + self.radius or
                self.y < -self.radius or self.y > LOGICAL_HEIGHT + self.radius):
            return False
        return True

    def _steer_homing(self, enemies) -> None:
        """Gently steer toward the nearest enemy."""
        nearest = None
        best_dist = float("inf")
        for e in enemies:
            d = distance(self.x, self.y, e.x, e.y)
            if d < best_dist:
                best_dist = d
                nearest = e
        if nearest is None:
            return

        desired = math.atan2(nearest.y - self.y, nearest.x - self.x)
        current = math.atan2(self.vy, self.vx)
        diff = normalize_angle(desired - current)
        steer = max(-HOMING_STEER, min(HOMING_STEER, diff))
        new_angle = current + steer
        self.vx = math.cos(new_angle) * HOMING_SPEED
        self.vy = math.sin(new_angle) * HOMING_SPEED


# ======================================================================
# Power-ups
# ======================================================================

class PowerUp:
    """A collectible power-up floating in space."""

    def __init__(self, x: float, y: float, powerup_type: str, color: tuple,
                 duration: int):
        self.x = x
        self.y = y
        self.vx = random_range(-0.3, 0.3)
        self.vy = random_range(-0.3, 0.3)
        self.powerup_type = powerup_type
        self.color = color
        self.duration = duration
        self.life = POWERUP_LIFETIME
        self.radius = POWERUP_RADIUS

    def update(self) -> bool:
        """Advance one frame. Returns False if expired."""
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position(self.x, self.y,
                                       LOGICAL_WIDTH, LOGICAL_HEIGHT)
        self.life -= 1
        return self.life > 0


# ======================================================================
# Particles
# ======================================================================

class Particle:
    """A visual-only particle for explosions."""

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color")

    def __init__(self, x: float, y: float, color: tuple):
        a = random.random() * math.pi * 2
        spd = random_range(PARTICLE_SPEED_MIN, PARTICLE_SPEED_MAX)
        self.x = x
        self.y = y
        self.vx = math.cos(a) * spd
        self.vy = math.sin(a) * spd
        self.life = PARTICLE_LIFETIME
        self.max_life = PARTICLE_LIFETIME
        self.color = color

    def update(self) -> bool:
        """Advance one frame. Returns False when dead."""
        self.x += self.vx
        self.y += self.vy
        self.vx *= PARTICLE_FRICTION
        self.vy *= PARTICLE_FRICTION
        self.life -= 1
        return self.life > 0