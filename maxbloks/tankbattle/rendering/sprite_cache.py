# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Pre-rendered surface cache for TankBattle sprites and tiles."""

import math
import random

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities


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
