# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Particle system for explosions and visual effects."""

import math
import random

from maxbloks.tankbattle import constants


class ParticleSystem:
    """Simple particle system for explosions and effects.

    Uses a pool of pre-allocated SRCALPHA surfaces to avoid
    creating a new surface for every particle every frame.
    """

    _POOL_SIZES = [2, 3, 4, 5, 6]  # Pre-allocated particle radii

    def __init__(self, pygame_module):
        self.pygame = pygame_module
        self.particles = []
        # Pre-allocate a pool of SRCALPHA surfaces at various sizes
        self._pool = {}
        for size in self._POOL_SIZES:
            diameter = size * 2
            surf = self.pygame.Surface((diameter, diameter), self.pygame.SRCALPHA)
            self._pool[size] = surf

    def _get_particle_surface(self, size):
        """Return a reusable surface for a particle of the given size.

        Falls back to creating a new one if the pool doesn't have
        the exact size, but the common sizes are pre-allocated.
        """
        if size in self._pool:
            return self._pool[size]
        # Rare: allocate for an unexpected size and cache it
        diameter = size * 2
        surf = self.pygame.Surface((diameter, diameter), self.pygame.SRCALPHA)
        self._pool[size] = surf
        return surf

    def emit_explosion(self, x, y, color, count=12, speed=80.0, lifetime=0.5):
        for _ in range(count):
            angle = random.random() * 360.0
            spd = speed * (0.3 + random.random() * 0.7)
            rad = math.radians(angle)
            vx = math.cos(rad) * spd
            vy = math.sin(rad) * spd
            life = lifetime * (0.5 + random.random() * 0.5)
            size = 2 + int(random.random() * 3)
            self.particles.append({
                "x": x, "y": y, "vx": vx, "vy": vy,
                "life": life, "max_life": life, "size": size, "color": color,
            })

    def emit_muzzle_flash(self, x, y, angle_deg):
        for i in range(5):
            spread = angle_deg + (random.random() - 0.5) * 30
            rad = math.radians(spread - 90)
            spd = 100 + random.random() * 60
            vx = math.cos(rad) * spd
            vy = math.sin(rad) * spd
            life = 0.1 + random.random() * 0.1
            self.particles.append({
                "x": x, "y": y, "vx": vx, "vy": vy,
                "life": life, "max_life": life, "size": 2,
                "color": (255, 255, 150),
            })

    def emit_smoke(self, x, y, count=3):
        for _ in range(count):
            vx = (random.random() - 0.5) * 20
            vy = -10 - random.random() * 30
            life = 0.4 + random.random() * 0.4
            size = 3 + int(random.random() * 4)
            self.particles.append({
                "x": x, "y": y, "vx": vx, "vy": vy,
                "life": life, "max_life": life, "size": size,
                "color": (100, 100, 100),
            })

    def update(self, dt):
        alive = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] > 0:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vx"] *= 0.95
                p["vy"] *= 0.95
                alive.append(p)
        self.particles = alive

    def draw(self, screen, camera_offset):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p["life"] / p["max_life"]))))
            sx = int(p["x"] - camera_offset[0])
            sy = int(p["y"] - camera_offset[1])
            if -10 < sx < constants.SCREEN_WIDTH + 10 and -10 < sy < constants.SCREEN_HEIGHT + 10:
                size = max(1, int(p["size"] * (p["life"] / p["max_life"])))
                color = p["color"]
                surf = self._get_particle_surface(size)
                surf.fill((0, 0, 0, 0))  # Clear the reusable surface
                self.pygame.draw.circle(surf, (*color, alpha), (size, size), size)
                screen.blit(surf, (sx - size, sy - size))
