# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Rendering helpers for TankBattle with polished visual effects.

Performance optimizations over the original implementation:
  - SpriteCache pre-builds turret surfaces (no per-frame allocation).
  - ParticleSystem reuses a small pool of SRCALPHA surfaces instead
    of creating a new surface for every particle every frame.
  - Powerup rendering uses a cached set of pre-scaled surfaces at
    discrete pulse phases instead of calling transform.scale every
    frame.
  - Hit-flash and ricochet-glow surfaces are cached once.
  - Tile building uses batch pygame.draw calls instead of per-pixel
    set_at() loops.
"""

import math
import random
import time

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import utils


class SpriteCache:
    """Pre-render and cache surfaces that don't change between frames."""

    def __init__(self, pygame_module):
        self.pygame = pygame_module
        self._cache = {}
        self._build_terrain_tile()
        self._build_hard_rock_tile()
        self._build_soft_obstacle_tile()
        self._build_tank_surfaces()
        self._build_turret_surfaces()
        self._build_bullet_surface()
        self._build_rocket_surface()
        self._build_mine_surface()
        self._build_powerup_surfaces()
        self._build_powerup_pulse_frames()
        self._build_hit_flash_surface()
        self._build_ricochet_glow_surface()
        self._build_destroyed_hull_surface()

    # ------------------------------------------------------------------
    # Tile builders — using batch draw calls instead of per-pixel set_at
    # ------------------------------------------------------------------

    def _build_terrain_tile(self):
        size = constants.TILE_SIZE
        tile = self.pygame.Surface((size, size))
        tile.fill(constants.COLOR_BG)
        # Subtle noise via small scattered dots instead of per-pixel loop
        rng = random.Random(42)
        base_r, base_g, base_b = constants.COLOR_BG
        for _ in range(40):
            px = rng.randrange(size)
            py = rng.randrange(size)
            noise = rng.randint(-6, 6)
            color = (
                max(0, min(255, base_r + noise)),
                max(0, min(255, base_g + noise)),
                max(0, min(255, base_b + noise // 2)),
            )
            self.pygame.draw.circle(tile, color, (px, py), 1)
        # A few darker spots for variety
        darker = (max(0, base_r - 8), max(0, base_g - 8), base_b)
        for _ in range(12):
            px = rng.randrange(size)
            py = rng.randrange(size)
            self.pygame.draw.circle(tile, darker, (px, py), 1)
        self._cache["terrain_tile"] = tile

    def _build_hard_rock_tile(self):
        size = constants.TILE_SIZE
        tile = self.pygame.Surface((size, size))
        tile.fill(constants.COLOR_HARD)
        # Surface detail using draw calls instead of per-pixel set_at
        hr, hg, hb = constants.COLOR_HARD
        rng = random.Random(7)
        for _ in range(20):
            px = rng.randrange(1, size - 1)
            py = rng.randrange(1, size - 1)
            variation = rng.randint(-6, 6)
            color = (
                max(0, min(255, hr + variation)),
                max(0, min(255, hg + variation)),
                max(0, min(255, hb + variation)),
            )
            self.pygame.draw.circle(tile, color, (px, py), 1)
        highlight = tuple(min(255, c + 30) for c in constants.COLOR_HARD)
        shadow = tuple(max(0, c - 25) for c in constants.COLOR_HARD)
        self.pygame.draw.line(tile, highlight, (0, 0), (size - 1, 0), 1)
        self.pygame.draw.line(tile, highlight, (0, 0), (0, size - 1), 1)
        self.pygame.draw.line(tile, shadow, (size - 1, 1), (size - 1, size - 1), 1)
        self.pygame.draw.line(tile, shadow, (1, size - 1), (size - 1, size - 1), 1)
        self.pygame.draw.rect(tile, shadow, (0, 0, size, size), 1)
        self._cache["hard_rock_tile"] = tile

    def _build_soft_obstacle_tile(self):
        size = constants.TILE_SIZE
        tile = self.pygame.Surface((size, size))
        tile.fill(constants.COLOR_SOFT)
        # Surface detail
        sr, sg, sb = constants.COLOR_SOFT
        rng = random.Random(13)
        for _ in range(15):
            px = rng.randrange(1, size - 1)
            py = rng.randrange(1, size - 1)
            variation = rng.randint(-4, 4)
            color = (
                max(0, min(255, sr + variation)),
                max(0, min(255, sg + variation)),
                max(0, min(255, sb + variation // 2)),
            )
            self.pygame.draw.circle(tile, color, (px, py), 1)
        darker_soft = tuple(max(0, c - 20) for c in constants.COLOR_SOFT)
        for crack_y in range(4, size - 2, 7):
            start_x = (crack_y * 3) % (size // 2)
            self.pygame.draw.line(tile, darker_soft, (start_x, crack_y),
                                  (min(start_x + 8, size - 1), crack_y + 2), 1)
        highlight = tuple(min(255, c + 25) for c in constants.COLOR_SOFT)
        shadow = tuple(max(0, c - 20) for c in constants.COLOR_SOFT)
        self.pygame.draw.line(tile, highlight, (0, 0), (size - 1, 0), 1)
        self.pygame.draw.line(tile, highlight, (0, 0), (0, size - 1), 1)
        self.pygame.draw.line(tile, shadow, (size - 1, 1), (size - 1, size - 1), 1)
        self.pygame.draw.line(tile, shadow, (1, size - 1), (size - 1, size - 1), 1)
        self._cache["soft_obstacle_tile"] = tile

    # ------------------------------------------------------------------
    # Tank body surfaces
    # ------------------------------------------------------------------

    def _build_tank_surfaces(self):
        for color_key, base_color in [("green", constants.COLOR_GREEN), ("red", constants.COLOR_RED)]:
            body_w = constants.TANK_BODY_WIDTH
            body_h = constants.TANK_BODY_HEIGHT
            total_size = max(body_w, body_h) + 16
            surface = self.pygame.Surface((total_size, total_size), self.pygame.SRCALPHA)
            cx, cy = total_size // 2, total_size // 2
            dark_color = tuple(max(0, c - 50) for c in base_color)
            mid_color = tuple(max(0, c - 25) for c in base_color)
            light_color = tuple(min(255, c + 40) for c in base_color)
            track_w = (body_w - 6) // 2
            track_h = body_h + 4
            left_track_rect = (cx - body_w // 2 - 1, cy - track_h // 2, track_w, track_h)
            right_track_rect = (cx + body_w // 2 - track_w + 1, cy - track_h // 2, track_w, track_h)
            self.pygame.draw.rect(surface, dark_color, left_track_rect, border_radius=2)
            self.pygame.draw.rect(surface, dark_color, right_track_rect, border_radius=2)
            for track_rect in [left_track_rect, right_track_rect]:
                for tread_y in range(track_rect[1] + 3, track_rect[1] + track_rect[3] - 2, 5):
                    self.pygame.draw.line(surface, (0, 0, 0, 120),
                                          (track_rect[0] + 1, tread_y),
                                          (track_rect[0] + track_rect[2] - 1, tread_y), 1)
            body_rect = (cx - body_w // 2, cy - body_h // 2, body_w, body_h)
            self.pygame.draw.rect(surface, base_color, body_rect, border_radius=3)
            inner_rect = (cx - body_w // 2 + 3, cy - body_h // 2 + 3, body_w - 6, body_h - 6)
            self.pygame.draw.rect(surface, mid_color, inner_rect, border_radius=2)
            self.pygame.draw.rect(surface, dark_color, body_rect, 2, border_radius=3)
            highlight_line = (cx - body_w // 2 + 3, cy - body_h // 2 + 2)
            self.pygame.draw.line(surface, light_color,
                                  (body_rect[0] + 4, body_rect[1] + 2),
                                  (body_rect[0] + body_rect[2] - 4, body_rect[1] + 2), 1)
            turret_w = constants.TANK_TURRET_WIDTH
            turret_h = constants.TANK_BODY_HEIGHT
            turret_rect = (cx - turret_w // 2, cy - turret_h // 2, turret_w, turret_h)
            self.pygame.draw.rect(surface, base_color, turret_rect, border_radius=2)
            self.pygame.draw.rect(surface, dark_color, turret_rect, 1, border_radius=2)
            self.pygame.draw.line(surface, light_color,
                                  (turret_rect[0] + 2, turret_rect[1] + 1),
                                  (turret_rect[0] + turret_rect[2] - 2, turret_rect[1] + 1), 1)
            hatch_x = cx + turret_w // 2 + 2
            hatch_y = cy - 4
            self.pygame.draw.rect(surface, dark_color, (hatch_x, hatch_y, 8, 8), border_radius=2)
            self.pygame.draw.rect(surface, mid_color, (hatch_x + 1, hatch_y + 1, 6, 6), border_radius=1)
            muzzle_w = turret_w + 4
            muzzle_h = 4
            muzzle_rect = (cx - muzzle_w // 2, cy - turret_h // 2 - muzzle_h, muzzle_w, muzzle_h)
            self.pygame.draw.rect(surface, dark_color, muzzle_rect, border_radius=1)
            shadow_surface = self.pygame.Surface((total_size, total_size), self.pygame.SRCALPHA)
            shadow_body = (body_rect[0] + 3, body_rect[1] + 3, body_rect[2], body_rect[3])
            self.pygame.draw.rect(shadow_surface, (0, 0, 0, 40), shadow_body, border_radius=3)
            final = self.pygame.Surface((total_size, total_size), self.pygame.SRCALPHA)
            final.blit(shadow_surface, (0, 0))
            final.blit(surface, (0, 0))
            self._cache[f"tank_{color_key}"] = final
            self._cache[f"tank_{color_key}_size"] = total_size

    # ------------------------------------------------------------------
    # Turret surfaces — cached at init instead of created every frame
    # ------------------------------------------------------------------

    def _build_turret_surfaces(self):
        """Pre-render turret surfaces for each tank color.

        These are blitted and rotated each frame, but the base
        surface is created only once.
        """
        for color_key, base_color in [("green", constants.COLOR_GREEN), ("red", constants.COLOR_RED)]:
            dark_color = tuple(max(0, c - 50) for c in base_color)
            mid_color = tuple(max(0, c - 25) for c in base_color)
            light_color = tuple(min(255, c + 40) for c in base_color)
            size = 48
            surface = self.pygame.Surface((size, size), self.pygame.SRCALPHA)
            cx, cy = size // 2, size // 2
            turret_w = constants.TANK_TURRET_WIDTH
            turret_h = constants.TANK_BODY_HEIGHT
            barrel_rect = (cx - turret_w // 2, cy - turret_h // 2, turret_w, turret_h)
            self.pygame.draw.rect(surface, base_color, barrel_rect, border_radius=2)
            self.pygame.draw.rect(surface, dark_color, barrel_rect, 1, border_radius=2)
            self.pygame.draw.line(surface, light_color,
                                  (barrel_rect[0] + 2, barrel_rect[1] + 1),
                                  (barrel_rect[0] + barrel_rect[2] - 2, barrel_rect[1] + 1), 1)
            muzzle_w = turret_w + 4
            muzzle_h = 5
            muzzle_rect = (cx - muzzle_w // 2, cy - turret_h // 2 - muzzle_h, muzzle_w, muzzle_h)
            self.pygame.draw.rect(surface, dark_color, muzzle_rect, border_radius=1)
            self.pygame.draw.rect(surface, mid_color,
                                  (cx - turret_w // 2 - 1, cy - 6, turret_w + 2, 12),
                                  border_radius=3)
            self.pygame.draw.rect(surface, dark_color,
                                  (cx - turret_w // 2 - 1, cy - 6, turret_w + 2, 12),
                                  1, border_radius=3)
            self._cache[f"turret_{color_key}"] = surface

    # ------------------------------------------------------------------
    # Projectile and item surfaces
    # ------------------------------------------------------------------

    def _build_bullet_surface(self):
        size = 12
        surface = self.pygame.Surface((size, size), self.pygame.SRCALPHA)
        center = size // 2
        self.pygame.draw.circle(surface, (255, 255, 200, 180), (center, center), 4)
        self.pygame.draw.circle(surface, (255, 255, 255), (center, center), 2)
        self._cache["bullet"] = surface

    def _build_rocket_surface(self):
        size = 16
        surface = self.pygame.Surface((size, size), self.pygame.SRCALPHA)
        center = size // 2
        self.pygame.draw.polygon(surface, (220, 100, 30),
                                 [(center, 0), (center - 3, center + 4), (center + 3, center + 4)])
        self.pygame.draw.polygon(surface, (255, 160, 60),
                                 [(center, 2), (center - 2, center + 3), (center + 2, center + 3)])
        self.pygame.draw.circle(surface, (255, 220, 100, 150), (center, center + 5), 3)
        self._cache["rocket"] = surface

    def _build_mine_surface(self):
        size = 20
        surface = self.pygame.Surface((size, size), self.pygame.SRCALPHA)
        center = size // 2
        self.pygame.draw.circle(surface, (60, 60, 60), (center, center), 7)
        self.pygame.draw.circle(surface, (80, 80, 80), (center, center), 5)
        self.pygame.draw.circle(surface, (40, 40, 40), (center, center), 7, 1)
        for angle_deg in range(0, 360, 60):
            rad = math.radians(angle_deg)
            spike_x = center + int(math.cos(rad) * 9)
            spike_y = center + int(math.sin(rad) * 9)
            self.pygame.draw.circle(surface, (70, 70, 70), (spike_x, spike_y), 2)
        self._cache["mine_unarmed"] = surface
        armed = surface.copy()
        self.pygame.draw.circle(armed, (255, 50, 50), (center, center), 3)
        self._cache["mine_armed"] = armed

    def _build_powerup_surfaces(self):
        size = 24
        for power_type in entities.PowerUpType:
            surface = self.pygame.Surface((size, size), self.pygame.SRCALPHA)
            center = size // 2
            if power_type == entities.PowerUpType.HEALTH:
                bg_color = (50, 200, 80)
                self.pygame.draw.circle(surface, bg_color, (center, center), 9)
                self.pygame.draw.circle(surface, (30, 160, 60), (center, center), 9, 2)
                self.pygame.draw.rect(surface, (255, 255, 255), (center - 1, center - 5, 3, 10))
                self.pygame.draw.rect(surface, (255, 255, 255), (center - 5, center - 1, 10, 3))
            elif power_type == entities.PowerUpType.SPREAD_SHOT:
                bg_color = (80, 180, 220)
                self.pygame.draw.circle(surface, bg_color, (center, center), 9)
                self.pygame.draw.circle(surface, (60, 140, 180), (center, center), 9, 2)
                for angle_offset in [-20, 0, 20]:
                    rad = math.radians(angle_offset - 90)
                    ex = center + int(math.cos(rad) * 7)
                    ey = center + int(math.sin(rad) * 7)
                    self.pygame.draw.line(surface, (255, 255, 255), (center, center), (ex, ey), 2)
            elif power_type == entities.PowerUpType.ROCKET:
                bg_color = (220, 100, 40)
                self.pygame.draw.circle(surface, bg_color, (center, center), 9)
                self.pygame.draw.circle(surface, (180, 80, 30), (center, center), 9, 2)
                self.pygame.draw.polygon(surface, (255, 255, 255),
                                         [(center, center - 5), (center - 3, center + 3), (center + 3, center + 3)])
            elif power_type == entities.PowerUpType.RAPID_FIRE:
                bg_color = (240, 200, 40)
                self.pygame.draw.circle(surface, bg_color, (center, center), 9)
                self.pygame.draw.circle(surface, (200, 170, 30), (center, center), 9, 2)
                bolt_points = [(center - 2, center - 6), (center + 3, center - 1),
                               (center, center - 1), (center + 2, center + 6),
                               (center - 3, center + 1), (center, center + 1)]
                self.pygame.draw.polygon(surface, (255, 255, 255), bolt_points)
            elif power_type == entities.PowerUpType.RICOCHET:
                bg_color = (180, 80, 200)
                self.pygame.draw.circle(surface, bg_color, (center, center), 9)
                self.pygame.draw.circle(surface, (140, 60, 160), (center, center), 9, 2)
                self.pygame.draw.arc(surface, (255, 255, 255),
                                     (center - 6, center - 6, 12, 12),
                                     0.3, 2.5, 2)
                self.pygame.draw.arc(surface, (255, 255, 255),
                                     (center - 4, center - 4, 8, 8),
                                     3.5, 5.5, 2)
            elif power_type == entities.PowerUpType.MINE_LAYER:
                bg_color = (100, 100, 100)
                self.pygame.draw.circle(surface, bg_color, (center, center), 9)
                self.pygame.draw.circle(surface, (70, 70, 70), (center, center), 9, 2)
                self.pygame.draw.circle(surface, (255, 255, 255), (center, center), 4)
                self.pygame.draw.circle(surface, (70, 70, 70), (center, center), 4, 1)
            self._cache[f"powerup_{power_type.value}"] = surface

    def _build_powerup_pulse_frames(self):
        """Pre-compute scaled powerup surfaces at discrete pulse phases.

        Instead of calling pygame.transform.scale every frame, we
        pre-build a small number of frames and cycle through them.
        """
        num_frames = 8
        for power_type in entities.PowerUpType:
            base_key = f"powerup_{power_type.value}"
            base_surface = self._cache.get(base_key)
            if base_surface is None:
                continue
            frames = []
            for i in range(num_frames):
                # Mimic: pulse = 1.0 + 0.15 * sin(timer * 2.0)
                phase = i / num_frames * 2.0 * math.pi
                pulse = 1.0 + 0.15 * math.sin(phase)
                new_w = max(1, int(base_surface.get_width() * pulse))
                new_h = max(1, int(base_surface.get_height() * pulse))
                scaled = self.pygame.transform.scale(base_surface, (new_w, new_h))
                # Also pre-build the glow for this frame
                glow_w = new_w + 8
                glow_h = new_h + 8
                glow_surf = self.pygame.Surface((glow_w, glow_h), self.pygame.SRCALPHA)
                self.pygame.draw.circle(
                    glow_surf, (255, 255, 100, constants.POWERUP_GLOW_ALPHA),
                    (glow_w // 2, glow_h // 2), new_w // 2 + 3,
                )
                frames.append((scaled, glow_surf))
            self._cache[f"powerup_frames_{power_type.value}"] = frames

    def _build_hit_flash_surface(self):
        """Pre-build the hit-flash overlay surface."""
        radius = int(constants.TANK_HITBOX_RADIUS + 4)
        diameter = radius * 2
        surface = self.pygame.Surface((diameter, diameter), self.pygame.SRCALPHA)
        self.pygame.draw.circle(surface, (255, 255, 255, 120), (radius, radius),
                                int(constants.TANK_HITBOX_RADIUS + 2))
        self._cache["hit_flash"] = surface
        self._cache["hit_flash_radius"] = radius

    def _build_ricochet_glow_surface(self):
        """Pre-build the ricochet bullet glow surface."""
        surface = self.pygame.Surface((16, 16), self.pygame.SRCALPHA)
        self.pygame.draw.circle(surface, (180, 80, 220, 80), (8, 8), 6)
        self.pygame.draw.circle(surface, (220, 150, 255), (8, 8), 3)
        self._cache["ricochet_glow"] = surface

    def _build_destroyed_hull_surface(self):
        """Pre-build the destroyed tank hull surface."""
        surface = self.pygame.Surface((32, 32), self.pygame.SRCALPHA)
        self.pygame.draw.polygon(surface, (60, 60, 60, 180),
                                 [(16, 4), (4, 16), (10, 28), (22, 28), (28, 16)])
        self.pygame.draw.polygon(surface, (40, 40, 40, 150),
                                 [(16, 4), (4, 16), (10, 28), (22, 28), (28, 16)], 2)
        self._cache["destroyed_hull"] = surface

    def get(self, key):
        return self._cache.get(key)


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


class Renderer:
    """Draw world, tanks, menus, and state overlays with polished graphics."""

    # Lobby colour palette (matches networktest style)
    _LOB_COLOR_BG = (15, 15, 25)
    _LOB_COLOR_PANEL = (30, 40, 45)
    _LOB_COLOR_TEXT = (220, 220, 220)
    _LOB_COLOR_DIM = (120, 120, 140)
    _LOB_COLOR_HIGHLIGHT = (40, 100, 50)
    _LOB_COLOR_SUCCESS = (80, 200, 120)
    _LOB_COLOR_WARNING = (200, 180, 80)
    _LOB_COLOR_BORDER = (40, 100, 50)

    def __init__(self, pygame_module, screen):
        self.pygame = pygame_module
        self.screen = screen
        self.font_menu = pygame_module.font.Font(None, constants.MENU_FONT_SIZE)
        self.font_big = pygame_module.font.Font(None, constants.BIG_FONT_SIZE)
        self.font_small = pygame_module.font.Font(None, constants.SMALL_FONT_SIZE)
        self.font_lobby = pygame_module.font.Font(None, constants.HUD_FONT_SIZE)
        self.sprite_cache = SpriteCache(pygame_module)
        self.particles = ParticleSystem(pygame_module)
        self.terrain_surface = pygame_module.Surface(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        )
        self.terrain_surface.fill(constants.COLOR_BG)
        self._build_terrain_pattern()
        self.flash_timer = 0.0
        self.destroy_timers = {}
        self._powerup_frame_index = 0.0

    def _build_terrain_pattern(self):
        tile = self.sprite_cache.get("terrain_tile")
        if tile:
            for y in range(0, constants.SCREEN_HEIGHT, constants.TILE_SIZE):
                for x in range(0, constants.SCREEN_WIDTH, constants.TILE_SIZE):
                    self.terrain_surface.blit(tile, (x, y))

    def draw_world(self, game):
        self.screen.blit(self.terrain_surface, (0, 0))
        camera = game.arena.clamp_camera(game.local_tank.position)
        self._draw_obstacles(game, camera)
        self._draw_powerups(game, camera)
        self._draw_mines(game, camera)
        self._draw_bullets(game, camera)
        self._draw_tanks(game, camera)
        self.particles.draw(self.screen, camera)

    def _draw_obstacles(self, game, camera):
        for obstacle in game.arena.obstacles:
            if obstacle.is_destroyed:
                continue
            wx = obstacle.tile_x * constants.TILE_SIZE
            wy = obstacle.tile_y * constants.TILE_SIZE
            sx, sy = game.arena.world_to_screen((wx, wy), camera)
            if sx + constants.TILE_SIZE < 0 or sx > constants.SCREEN_WIDTH:
                continue
            if sy + constants.TILE_SIZE < 0 or sy > constants.SCREEN_HEIGHT:
                continue
            if obstacle.type == entities.ObstacleType.HARD_ROCK:
                tile = self.sprite_cache.get("hard_rock_tile")
            else:
                tile = self.sprite_cache.get("soft_obstacle_tile")
            if tile:
                self.screen.blit(tile, (int(sx), int(sy)))
            else:
                color = constants.COLOR_HARD
                if obstacle.type == entities.ObstacleType.SOFT:
                    color = constants.COLOR_SOFT
                self.pygame.draw.rect(self.screen, color,
                                      (int(sx), int(sy), constants.TILE_SIZE, constants.TILE_SIZE))

    def _draw_powerups(self, game, camera):
        """Draw powerups using pre-computed pulse frames."""
        for powerup in game.powerups:
            sx, sy = game.arena.world_to_screen(powerup.position, camera)
            isx, isy = int(sx), int(sy)
            if isx < -20 or isx > constants.SCREEN_WIDTH + 20:
                continue
            if isy < -20 or isy > constants.SCREEN_HEIGHT + 20:
                continue
            # Look up pre-computed frames
            frames_key = f"powerup_frames_{powerup.type.value}"
            frames = self.sprite_cache.get(frames_key)
            if frames:
                # Map pulse_timer to a frame index
                phase_index = int((powerup.pulse_timer * 2.0 / (2.0 * math.pi)) * len(frames)) % len(frames)
                scaled, glow_surf = frames[phase_index]
                self.screen.blit(glow_surf,
                                 (isx - glow_surf.get_width() // 2,
                                  isy - glow_surf.get_height() // 2))
                self.screen.blit(scaled,
                                 (isx - scaled.get_width() // 2,
                                  isy - scaled.get_height() // 2))
            else:
                # Fallback to base surface without pulse
                key = f"powerup_{powerup.type.value}"
                surface = self.sprite_cache.get(key)
                if surface:
                    self.screen.blit(surface,
                                     (isx - surface.get_width() // 2,
                                      isy - surface.get_height() // 2))
                else:
                    self.pygame.draw.circle(self.screen, constants.COLOR_YELLOW, (isx, isy), 8)

    def _draw_mines(self, game, camera):
        for mine in game.mines:
            sx, sy = game.arena.world_to_screen(mine.position, camera)
            isx, isy = int(sx), int(sy)
            key = "mine_armed" if mine.armed else "mine_unarmed"
            surface = self.sprite_cache.get(key)
            if surface:
                blink = mine.armed and (int(mine.arm_timer * 10) % 2 == 0 if mine.arm_timer > 0 else True)
                if mine.armed and blink:
                    glow = self.pygame.Surface((28, 28), self.pygame.SRCALPHA)
                    self.pygame.draw.circle(glow, (255, 0, 0, 50), (14, 14), 12)
                    self.screen.blit(glow, (isx - 14, isy - 14))
                self.screen.blit(surface, (isx - surface.get_width() // 2,
                                           isy - surface.get_height() // 2))
            else:
                color = constants.COLOR_ORANGE if mine.armed else constants.COLOR_GREY
                self.pygame.draw.circle(self.screen, color, (isx, isy), 6)

    def _draw_bullets(self, game, camera):
        ricochet_glow = self.sprite_cache.get("ricochet_glow")
        for bullet in game.bullets:
            sx, sy = game.arena.world_to_screen(bullet.position, camera)
            isx, isy = int(sx), int(sy)
            if isx < -10 or isx > constants.SCREEN_WIDTH + 10:
                continue
            if isy < -10 or isy > constants.SCREEN_HEIGHT + 10:
                continue
            if bullet.weapon_type == entities.WeaponType.ROCKET:
                surface = self.sprite_cache.get("rocket")
                if surface:
                    self.screen.blit(surface, (isx - surface.get_width() // 2,
                                               isy - surface.get_height() // 2))
                else:
                    self.pygame.draw.circle(self.screen, constants.COLOR_ORANGE, (isx, isy), 4)
            elif bullet.weapon_type == entities.WeaponType.RICOCHET:
                # Use pre-cached glow surface
                if ricochet_glow:
                    self.screen.blit(ricochet_glow, (isx - 8, isy - 8))
                else:
                    self.pygame.draw.circle(self.screen, (220, 150, 255), (isx, isy), 3)
            else:
                surface = self.sprite_cache.get("bullet")
                if surface:
                    self.screen.blit(surface, (isx - surface.get_width() // 2,
                                               isy - surface.get_height() // 2))
                else:
                    self.pygame.draw.circle(self.screen, constants.COLOR_WHITE, (isx, isy), 3)

    def _draw_tanks(self, game, camera):
        tank_color_keys = ["green", "red"]
        for idx, tank in enumerate(game.tanks):
            if not tank.is_alive:
                self._draw_destroyed_tank(game, tank, camera)
                continue
            self._draw_alive_tank(game, tank, camera, tank_color_keys[idx])

    def _draw_alive_tank(self, game, tank, camera, color_key):
        sx, sy = game.arena.world_to_screen(tank.position, camera)
        isx, isy = int(sx), int(sy)
        cached = self.sprite_cache.get(f"tank_{color_key}")
        total_size = self.sprite_cache.get(f"tank_{color_key}_size")
        if cached is None or total_size is None:
            self._draw_tank_fallback(game, tank, camera,
                                     constants.COLOR_GREEN if color_key == "green" else constants.COLOR_RED)
            return
        # Draw body (pre-cached surface, rotated)
        body_angle = tank.body_angle
        body_rotated = self.pygame.transform.rotate(cached, -body_angle)
        body_rect = body_rotated.get_rect(center=(isx, isy))
        self.screen.blit(body_rotated, body_rect)
        # Draw turret (pre-cached surface, rotated)
        turret_surface = self.sprite_cache.get(f"turret_{color_key}")
        if turret_surface:
            turret_angle = tank.turret_angle
            turret_rotated = self.pygame.transform.rotate(turret_surface, -turret_angle)
            turret_rect = turret_rotated.get_rect(center=(isx, isy))
            self.screen.blit(turret_rotated, turret_rect)
        # Draw hit flash (pre-cached surface with alpha modulation)
        if tank.hit_flash_timer > 0:
            flash_surface = self.sprite_cache.get("hit_flash")
            flash_radius = self.sprite_cache.get("hit_flash_radius")
            if flash_surface and flash_radius:
                flash_intensity = tank.hit_flash_timer / constants.TANK_HIT_FLASH_TIME
                # Scale alpha by modulating a copy — this is cheaper than
                # creating a new surface from scratch every frame.
                alpha = int(120 * flash_intensity)
                temp = flash_surface.copy()
                temp.set_alpha(alpha)
                self.screen.blit(temp,
                                 (isx - flash_radius, isy - flash_radius))

    def _draw_tank_fallback(self, game, tank, camera, color):
        screen_pos = game.arena.world_to_screen(tank.position, camera)
        draw_color = constants.COLOR_WHITE if tank.hit_flash_timer > 0.0 else color
        center = (int(screen_pos[0]), int(screen_pos[1]))
        self.pygame.draw.circle(self.screen, draw_color, center,
                                int(constants.TANK_HITBOX_RADIUS))
        dx_value, dy_value = utils.angle_to_vector(tank.turret_angle)
        end = (
            int(screen_pos[0] + dx_value * constants.TANK_BODY_HEIGHT),
            int(screen_pos[1] + dy_value * constants.TANK_BODY_HEIGHT),
        )
        self.pygame.draw.line(self.screen, constants.COLOR_BLACK, center, end,
                              constants.TANK_TURRET_WIDTH)

    def _draw_destroyed_tank(self, game, tank, camera):
        sx, sy = game.arena.world_to_screen(tank.position, camera)
        isx, isy = int(sx), int(sy)
        hull = self.sprite_cache.get("destroyed_hull")
        if hull:
            self.screen.blit(hull, (isx - 16, isy - 16))
        else:
            self.pygame.draw.circle(self.screen, (60, 60, 60), (isx, isy), 12)
        if random.random() < 0.1:
            self.particles.emit_smoke(tank.x, tank.y, 1)

    def register_destroy(self, tank):
        key = id(tank)
        if key not in self.destroy_timers:
            self.destroy_timers[key] = constants.TANK_DESTROY_ANIMATION_TIME
            self.particles.emit_explosion(tank.x, tank.y, constants.COLOR_ORANGE,
                                          count=20, speed=120.0, lifetime=0.8)
            self.particles.emit_explosion(tank.x, tank.y, (255, 255, 200),
                                          count=8, speed=60.0, lifetime=0.4)

    def register_hit(self, bullet):
        self.particles.emit_explosion(bullet.x, bullet.y, (255, 255, 150),
                                      count=5, speed=40.0, lifetime=0.2)

    def register_mine_explosion(self, mine):
        self.particles.emit_explosion(mine.x, mine.y, constants.COLOR_ORANGE,
                                      count=15, speed=100.0, lifetime=0.6)
        self.particles.emit_explosion(mine.x, mine.y, (100, 100, 100),
                                      count=8, speed=50.0, lifetime=0.8)

    def register_muzzle_flash(self, tank):
        dx, dy = utils.angle_to_vector(tank.turret_angle)
        x = tank.x + dx * constants.TANK_BODY_HEIGHT
        y = tank.y + dy * constants.TANK_BODY_HEIGHT
        self.particles.emit_muzzle_flash(x, y, tank.turret_angle)

    def update(self, dt):
        self.particles.update(dt)
        expired = []
        for key, timer in self.destroy_timers.items():
            self.destroy_timers[key] -= dt
            if self.destroy_timers[key] <= 0:
                expired.append(key)
        for key in expired:
            del self.destroy_timers[key]

    # ------------------------------------------------------------------
    # Menu drawing
    # ------------------------------------------------------------------

    def draw_menu(self, menu_index):
        self.screen.fill((15, 15, 25))
        border_size = 4
        border_color = (40, 100, 50)
        self.pygame.draw.rect(self.screen, border_color,
                              (0, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), border_size)
        title = self.font_big.render("TANK BATTLE", True, constants.COLOR_GREEN)
        title_shadow = self.font_big.render("TANK BATTLE", True, (20, 80, 30))
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title, title_rect)
        separator_y = 155
        self.pygame.draw.line(self.screen, (60, 130, 70),
                              (constants.SCREEN_WIDTH // 4, separator_y),
                              (3 * constants.SCREEN_WIDTH // 4, separator_y), 2)
        for index, item in enumerate(constants.MENU_ITEMS):
            y_pos = 210 + index * 48
            if index == menu_index:
                indicator_x = constants.SCREEN_WIDTH // 2 - 90
                self.pygame.draw.polygon(self.screen, constants.COLOR_YELLOW,
                                         [(indicator_x, y_pos - 6),
                                          (indicator_x + 10, y_pos),
                                          (indicator_x, y_pos + 6)])
                self.pygame.draw.rect(self.screen, (40, 60, 45),
                                      (constants.SCREEN_WIDTH // 2 - 100, y_pos - 16, 200, 36),
                                      border_radius=6)
                self.pygame.draw.rect(self.screen, constants.COLOR_GREEN,
                                      (constants.SCREEN_WIDTH // 2 - 100, y_pos - 16, 200, 36),
                                      2, border_radius=6)
                color = constants.COLOR_YELLOW
            else:
                color = constants.COLOR_LIGHT_GREY
            surface = self.font_menu.render(item, True, color)
            self.screen.blit(surface, surface.get_rect(center=(constants.SCREEN_WIDTH // 2, y_pos)))
        controls_text = self.font_small.render("Arrows/WASD: Move  |  Space: Fire  |  Ctrl: Mine  |  IJKL: Turret",
                                                True, constants.COLOR_GREY)
        self.screen.blit(controls_text,
                         controls_text.get_rect(center=(constants.SCREEN_WIDTH // 2,
                                                        constants.SCREEN_HEIGHT - 20)))

    # ------------------------------------------------------------------
    # Lobby drawing — enhanced with network info, symmetric visibility,
    # and bidirectional handshake indicators
    # ------------------------------------------------------------------

    def draw_lobby(self, game):
        """Draw the enhanced lobby screen with network information.

        Displays the host's IP address, WiFi network name, a list of
        discovered peers with connection/handshake status indicators,
        and the lobby action menu.  Both Host and Join lobbies now
        show each other symmetrically.

        Issue 1: Handshake-confirmed connections show a ✓ indicator.
        Issue 2: Join lobby shows available hosts with ability to
                 select one; Host lobby shows clients with join status.
        """
        sw = constants.SCREEN_WIDTH
        sh = constants.SCREEN_HEIGHT
        margin = 16
        row_h = 28

        # Background
        self.screen.fill(self._LOB_COLOR_BG)
        self.pygame.draw.rect(self.screen, self._LOB_COLOR_BORDER,
                              (0, 0, sw, sh), 4)

        y = margin

        # Title
        role_label = "HOST LOBBY" if game.lobby_is_host else "JOIN LOBBY"
        title_surf = self.font_big.render(role_label, True, constants.COLOR_GREEN)
        title_shadow = self.font_big.render(role_label, True, (20, 80, 30))
        title_rect = title_surf.get_rect(center=(sw // 2, y + 22))
        self.screen.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title_surf, title_rect)
        y += 58

        # Separator
        self.pygame.draw.line(self.screen, self._LOB_COLOR_HIGHLIGHT,
                              (margin, y), (sw - margin, y), 2)
        y += 10

        # Network information section
        ip_text = f"My IP: {game.lobby_local_ip}"
        ip_surf = self.font_lobby.render(ip_text, True, self._LOB_COLOR_SUCCESS)
        self.screen.blit(ip_surf, (margin + 8, y))
        y += row_h

        if game.lobby_wifi_ssid:
            wifi_text = f"WiFi: {game.lobby_wifi_ssid}"
            wifi_surf = self.font_lobby.render(wifi_text, True, self._LOB_COLOR_SUCCESS)
            self.screen.blit(wifi_surf, (margin + 8, y))
        else:
            wifi_text = "WiFi: (not detected)"
            wifi_surf = self.font_lobby.render(wifi_text, True, self._LOB_COLOR_DIM)
            self.screen.blit(wifi_surf, (margin + 8, y))
        y += row_h

        if game.lobby_is_host:
            port_text = f"Listening on port: {constants.HOST_PORT}"
            port_surf = self.font_lobby.render(port_text, True, self._LOB_COLOR_TEXT)
            self.screen.blit(port_surf, (margin + 8, y))
        y += row_h + 4

        # Separator
        self.pygame.draw.line(self.screen, self._LOB_COLOR_HIGHLIGHT,
                              (margin, y), (sw - margin, y), 1)
        y += 8

        # Discovered clients / hosts section
        header_label = "Discovered Clients:" if game.lobby_is_host else "Available Hosts:"
        header_surf = self.font_lobby.render(header_label, True, self._LOB_COLOR_TEXT)
        self.screen.blit(header_surf, (margin + 8, y))
        y += row_h

        discovered = game.lobby_discovered_clients
        connected = game.lobby_connected_clients
        handshake_confirmed = game.lobby_handshake_confirmed

        # Filter peers based on role for display
        if game.lobby_is_host:
            # Host sees all discovered peers (both hosts and clients)
            display_peers = discovered
        else:
            # Join lobby only shows hosts (peers with hosting=True)
            display_peers = [h for h in discovered if h.get("hosting")]

        if not display_peers:
            searching_text = "Searching for devices..." if game.lobby_is_host else "Searching for hosts..."
            search_surf = self.font_small.render(searching_text, True, self._LOB_COLOR_DIM)
            self.screen.blit(search_surf, (margin + 24, y))
            y += row_h
        else:
            for peer_idx, host_info in enumerate(display_peers):
                ip = host_info.get("address", "???")
                is_connected = ip in connected
                is_handshake = handshake_confirmed.get(ip, False)

                # Connection status dot with handshake indicator
                if is_handshake:
                    # Issue 1: Bidirectional handshake confirmed — green with ✓
                    dot_color = self._LOB_COLOR_SUCCESS
                    dot_x = margin + 24
                    dot_y_c = y + row_h // 2
                    self.pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y_c), 5)
                    # Draw checkmark inside the dot
                    self.pygame.draw.line(self.screen, constants.COLOR_BLACK,
                                          (dot_x - 2, dot_y_c), (dot_x - 1, dot_y_c + 2), 2)
                    self.pygame.draw.line(self.screen, constants.COLOR_BLACK,
                                          (dot_x - 1, dot_y_c + 2), (dot_x + 3, dot_y_c - 3), 2)
                elif is_connected:
                    # Connected but handshake not yet confirmed — yellow
                    dot_color = self._LOB_COLOR_WARNING
                    dot_x = margin + 24
                    dot_y_c = y + row_h // 2
                    self.pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y_c), 5)
                else:
                    # Discovered but not connected — dim
                    dot_color = self._LOB_COLOR_DIM
                    dot_x = margin + 24
                    dot_y_c = y + row_h // 2
                    self.pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y_c), 5)

                # IP address
                ip_surf = self.font_small.render(ip, True, self._LOB_COLOR_TEXT)
                self.screen.blit(ip_surf, (margin + 40, y))

                # Connection status text (Issue 1 & 2)
                if is_handshake:
                    status = "Connected \u2713"
                    status_color = self._LOB_COLOR_SUCCESS
                elif is_connected:
                    status = "Handshaking..."
                    status_color = self._LOB_COLOR_WARNING
                else:
                    status = "available"
                    status_color = self._LOB_COLOR_DIM
                status_surf = self.font_small.render(status, True, status_color)
                self.screen.blit(status_surf, (sw - margin - status_surf.get_width() - 8, y))

                # In the Join lobby, show selection highlight for the
                # currently highlighted host (Issue 2)
                if not game.lobby_is_host and peer_idx == game.lobby_index:
                    highlight_rect = (margin + 4, y - 2, sw - 2 * margin - 8, row_h)
                    self.pygame.draw.rect(self.screen, (40, 80, 50), highlight_rect, border_radius=3)
                    self.pygame.draw.rect(self.screen, constants.COLOR_GREEN, highlight_rect, 2, border_radius=3)
                    # Arrow indicator
                    arrow_x = margin + 8
                    arrow_y_c = y + row_h // 2
                    self.pygame.draw.polygon(self.screen, constants.COLOR_YELLOW,
                                             [(arrow_x, arrow_y_c - 4),
                                              (arrow_x + 6, arrow_y_c),
                                              (arrow_x, arrow_y_c + 4)])

                y += row_h

        # Separator
        y += 4
        self.pygame.draw.line(self.screen, self._LOB_COLOR_HIGHLIGHT,
                              (margin, y), (sw - margin, y), 1)
        y += 10

        # Lobby action menu
        if game.lobby_is_host:
            # Host lobby: standard action menu (Start / Manual IP / Back)
            for idx, item in enumerate(constants.LOBBY_ITEMS):
                item_y = y + idx * 38
                if idx == game.lobby_index:
                    # Selection highlight
                    highlight_rect = (margin + 4, item_y - 6, sw - 2 * margin - 8, 32)
                    self.pygame.draw.rect(self.screen, (40, 60, 45), highlight_rect, border_radius=5)
                    self.pygame.draw.rect(self.screen, constants.COLOR_GREEN, highlight_rect, 2, border_radius=5)

                    # Arrow indicator
                    arrow_x = margin + 12
                    self.pygame.draw.polygon(self.screen, constants.COLOR_YELLOW,
                                             [(arrow_x, item_y - 4),
                                              (arrow_x + 8, item_y + 8),
                                              (arrow_x, item_y + 20)])

                    color = constants.COLOR_YELLOW
                else:
                    color = self._LOB_COLOR_DIM

                item_surf = self.font_lobby.render(item, True, color)
                self.screen.blit(item_surf, item_surf.get_rect(center=(sw // 2, item_y + 10)))
        else:
            # Join lobby: action menu items are offset by the number of hosts
            hosts = [h for h in discovered if h.get("hosting")]
            num_hosts = len(hosts)
            for idx, item in enumerate(constants.LOBBY_ITEMS):
                item_index = num_hosts + idx
                item_y = y + idx * 38
                if item_index == game.lobby_index:
                    # Selection highlight
                    highlight_rect = (margin + 4, item_y - 6, sw - 2 * margin - 8, 32)
                    self.pygame.draw.rect(self.screen, (40, 60, 45), highlight_rect, border_radius=5)
                    self.pygame.draw.rect(self.screen, constants.COLOR_GREEN, highlight_rect, 2, border_radius=5)

                    # Arrow indicator
                    arrow_x = margin + 12
                    self.pygame.draw.polygon(self.screen, constants.COLOR_YELLOW,
                                             [(arrow_x, item_y - 4),
                                              (arrow_x + 8, item_y + 8),
                                              (arrow_x, item_y + 20)])

                    color = constants.COLOR_YELLOW
                else:
                    color = self._LOB_COLOR_DIM

                item_surf = self.font_lobby.render(item, True, color)
                self.screen.blit(item_surf, item_surf.get_rect(center=(sw // 2, item_y + 10)))

        # Bottom instructions
        if game.lobby_is_host:
            instructions = "D-pad/Arrows: Navigate  |  A/Enter: Select  |  B/ESC: Back"
        else:
            instructions = "D-pad: Select Host  |  A/Enter: Join  |  B/ESC: Back"
        inst_surf = self.font_small.render(instructions, True, self._LOB_COLOR_DIM)
        self.screen.blit(inst_surf, inst_surf.get_rect(center=(sw // 2, sh - 16)))

    # ------------------------------------------------------------------
    # Other screen drawing
    # ------------------------------------------------------------------

    def draw_center_text(self, message, color=constants.COLOR_WHITE):
        self.screen.fill((15, 15, 25))
        self.pygame.draw.rect(self.screen, (40, 100, 50),
                              (0, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), 4)
        text = self.font_menu.render(message, True, color)
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
        bg_rect = text_rect.inflate(40, 20)
        self.pygame.draw.rect(self.screen, (20, 30, 25), bg_rect, border_radius=8)
        self.pygame.draw.rect(self.screen, constants.COLOR_GREEN, bg_rect, 2, border_radius=8)
        self.screen.blit(text, text_rect)

    def draw_countdown(self, game):
        self.draw_world(game)
        overlay = self.pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
                                       self.pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))
        value = max(0, int(game.state_timer) + 1)
        label = "GO!" if value == 0 else str(value)
        text = self.font_big.render(label, True, constants.COLOR_YELLOW)
        shadow = self.font_big.render(label, True, (80, 80, 0))
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
        self.screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        self.screen.blit(text, text_rect)

    def draw_paused(self, game):
        game.draw_playing()
        overlay = self.pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
                                       self.pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        text = self.font_menu.render("PAUSED", True, constants.COLOR_YELLOW)
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 - 10))
        bg_rect = text_rect.inflate(60, 30)
        self.pygame.draw.rect(self.screen, (20, 30, 25), bg_rect, border_radius=8)
        self.pygame.draw.rect(self.screen, constants.COLOR_YELLOW, bg_rect, 2, border_radius=8)
        self.screen.blit(text, text_rect)
        hint = self.font_small.render("Press ESC or ENTER to resume", True, constants.COLOR_LIGHT_GREY)
        self.screen.blit(hint, hint.get_rect(center=(constants.SCREEN_WIDTH // 2,
                                                       constants.SCREEN_HEIGHT // 2 + 25)))

    def draw_round_over(self, game):
        self.draw_world(game)
        overlay = self.pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
                                       self.pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        text = self.font_menu.render("ROUND OVER", True, constants.COLOR_YELLOW)
        shadow = self.font_menu.render("ROUND OVER", True, (80, 80, 0))
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
        self.screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        self.screen.blit(text, text_rect)

    def draw_match_over(self, wins):
        self.screen.fill((15, 15, 25))
        self.pygame.draw.rect(self.screen, (40, 100, 50),
                              (0, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), 4)
        winner = 1 if wins[0] > wins[1] else 2
        winner_color = constants.COLOR_GREEN if winner == 1 else constants.COLOR_RED
        title = self.font_big.render("VICTORY!", True, winner_color)
        title_shadow = self.font_big.render("VICTORY!", True, (40, 40, 40))
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 120))
        self.screen.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title, title_rect)
        message = f"Player {winner} wins the match!"
        text = self.font_menu.render(message, True, constants.COLOR_YELLOW)
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)
        score_text = self.font_menu.render(f"{wins[0]}  -  {wins[1]}", True, constants.COLOR_WHITE)
        score_rect = score_text.get_rect(center=(constants.SCREEN_WIDTH // 2,
                                                   constants.SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(score_text, score_rect)
        hint = self.font_small.render("Press ENTER to return to menu", True, constants.COLOR_GREY)
        self.screen.blit(hint, hint.get_rect(center=(constants.SCREEN_WIDTH // 2,
                                                       constants.SCREEN_HEIGHT - 30)))
