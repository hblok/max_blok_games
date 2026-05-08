# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Rendering helpers for TankBattle with polished visual effects."""

import math

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
        self._build_bullet_surface()
        self._build_rocket_surface()
        self._build_mine_surface()
        self._build_powerup_surfaces()

    def _build_terrain_tile(self):
        tile = self.pygame.Surface((constants.TILE_SIZE, constants.TILE_SIZE))
        base_r, base_g, base_b = constants.COLOR_BG
        for row in range(constants.TILE_SIZE):
            for col in range(constants.TILE_SIZE):
                noise = ((col * 7 + row * 13) % 17 - 8)
                r = max(0, min(255, base_r + noise))
                g = max(0, min(255, base_g + noise))
                b = max(0, min(255, base_b + noise // 2))
                tile.set_at((col, row), (r, g, b))
        for edge_x in range(0, constants.TILE_SIZE, 6):
            for edge_y in range(0, constants.TILE_SIZE, 6):
                if (edge_x + edge_y) % 12 < 3:
                    current = tile.get_at((min(edge_x, constants.TILE_SIZE - 1),
                                           min(edge_y, constants.TILE_SIZE - 1)))
                    darkened = (max(0, current[0] - 4), max(0, current[1] - 4), current[2])
                    tile.set_at((min(edge_x, constants.TILE_SIZE - 1),
                                 min(edge_y, constants.TILE_SIZE - 1)), darkened)
        self._cache["terrain_tile"] = tile

    def _build_hard_rock_tile(self):
        size = constants.TILE_SIZE
        tile = self.pygame.Surface((size, size))
        tile.fill(constants.COLOR_HARD)
        hr, hg, hb = constants.COLOR_HARD
        for row in range(size):
            for col in range(size):
                variation = ((col * 11 + row * 7 + col * row) % 13 - 6)
                r = max(0, min(255, hr + variation))
                g = max(0, min(255, hg + variation))
                b = max(0, min(255, hb + variation))
                tile.set_at((col, row), (r, g, b))
        highlight = tuple(min(255, c + 30) for c in constants.COLOR_HARD)
        self.pygame.draw.line(tile, highlight, (0, 0), (size - 1, 0), 1)
        self.pygame.draw.line(tile, highlight, (0, 0), (0, size - 1), 1)
        shadow = tuple(max(0, c - 25) for c in constants.COLOR_HARD)
        self.pygame.draw.line(tile, shadow, (size - 1, 1), (size - 1, size - 1), 1)
        self.pygame.draw.line(tile, shadow, (1, size - 1), (size - 1, size - 1), 1)
        self.pygame.draw.rect(tile, shadow, (0, 0, size, size), 1)
        self._cache["hard_rock_tile"] = tile

    def _build_soft_obstacle_tile(self):
        size = constants.TILE_SIZE
        tile = self.pygame.Surface((size, size))
        tile.fill(constants.COLOR_SOFT)
        sr, sg, sb = constants.COLOR_SOFT
        for row in range(size):
            for col in range(size):
                variation = ((col * 3 + row * 5) % 9 - 4)
                r = max(0, min(255, sr + variation))
                g = max(0, min(255, sg + variation))
                b = max(0, min(255, sb + variation // 2))
                tile.set_at((col, row), (r, g, b))
        darker_soft = tuple(max(0, c - 20) for c in constants.COLOR_SOFT)
        for crack_y in range(4, size - 2, 7):
            start_x = (crack_y * 3) % (size // 2)
            self.pygame.draw.line(tile, darker_soft, (start_x, crack_y),
                                  (min(start_x + 8, size - 1), crack_y + 2), 1)
        highlight = tuple(min(255, c + 25) for c in constants.COLOR_SOFT)
        self.pygame.draw.line(tile, highlight, (0, 0), (size - 1, 0), 1)
        self.pygame.draw.line(tile, highlight, (0, 0), (0, size - 1), 1)
        shadow = tuple(max(0, c - 20) for c in constants.COLOR_SOFT)
        self.pygame.draw.line(tile, shadow, (size - 1, 1), (size - 1, size - 1), 1)
        self.pygame.draw.line(tile, shadow, (1, size - 1), (size - 1, size - 1), 1)
        self._cache["soft_obstacle_tile"] = tile

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
                symbol_color = (255, 255, 255)
                self.pygame.draw.circle(surface, bg_color, (center, center), 9)
                self.pygame.draw.circle(surface, (30, 160, 60), (center, center), 9, 2)
                self.pygame.draw.rect(surface, symbol_color, (center - 1, center - 5, 3, 10))
                self.pygame.draw.rect(surface, symbol_color, (center - 5, center - 1, 10, 3))
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

    def get(self, key):
        return self._cache.get(key)


class ParticleSystem:
    """Simple particle system for explosions and effects."""

    def __init__(self, pygame_module):
        self.pygame = pygame_module
        self.particles = []

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
                surf = self.pygame.Surface((size * 2, size * 2), self.pygame.SRCALPHA)
                self.pygame.draw.circle(surf, (*color, alpha), (size, size), size)
                screen.blit(surf, (sx - size, sy - size))


import random

class Renderer:
    """Draw world, tanks, menus, and state overlays with polished graphics."""

    def __init__(self, pygame_module, screen):
        self.pygame = pygame_module
        self.screen = screen
        self.font_menu = pygame_module.font.Font(None, constants.MENU_FONT_SIZE)
        self.font_big = pygame_module.font.Font(None, constants.BIG_FONT_SIZE)
        self.font_small = pygame_module.font.Font(None, constants.SMALL_FONT_SIZE)
        self.sprite_cache = SpriteCache(pygame_module)
        self.particles = ParticleSystem(pygame_module)
        self.terrain_surface = pygame_module.Surface(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        )
        self.terrain_surface.fill(constants.COLOR_BG)
        self._build_terrain_pattern()
        self.flash_timer = 0.0
        self.destroy_timers = {}

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
        for powerup in game.powerups:
            sx, sy = game.arena.world_to_screen(powerup.position, camera)
            isx, isy = int(sx), int(sy)
            if isx < -20 or isx > constants.SCREEN_WIDTH + 20:
                continue
            if isy < -20 or isy > constants.SCREEN_HEIGHT + 20:
                continue
            pulse = 1.0 + 0.15 * math.sin(powerup.pulse_timer * 2.0)
            key = f"powerup_{powerup.type.value}"
            surface = self.sprite_cache.get(key)
            if surface:
                scaled = self.pygame.transform.scale(
                    surface,
                    (int(surface.get_width() * pulse), int(surface.get_height() * pulse)),
                )
                glow_surf = self.pygame.Surface(
                    (scaled.get_width() + 8, scaled.get_height() + 8), self.pygame.SRCALPHA
                )
                glow_color = (255, 255, 100, 40)
                self.pygame.draw.circle(
                    glow_surf, glow_color,
                    (glow_surf.get_width() // 2, glow_surf.get_height() // 2),
                    scaled.get_width() // 2 + 3,
                )
                self.screen.blit(glow_surf,
                                 (isx - glow_surf.get_width() // 2,
                                  isy - glow_surf.get_height() // 2))
                self.screen.blit(scaled,
                                 (isx - scaled.get_width() // 2,
                                  isy - scaled.get_height() // 2))
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
                    angle = bullet.weapon_type.value
                    self.screen.blit(surface, (isx - surface.get_width() // 2,
                                               isy - surface.get_height() // 2))
                else:
                    self.pygame.draw.circle(self.screen, constants.COLOR_ORANGE, (isx, isy), 4)
            elif bullet.weapon_type == entities.WeaponType.RICOCHET:
                glow = self.pygame.Surface((16, 16), self.pygame.SRCALPHA)
                self.pygame.draw.circle(glow, (180, 80, 220, 80), (8, 8), 6)
                self.pygame.draw.circle(glow, (220, 150, 255), (8, 8), 3)
                self.screen.blit(glow, (isx - 8, isy - 8))
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
        body_angle = tank.body_angle
        body_rotated = self.pygame.transform.rotate(cached, -body_angle)
        body_rect = body_rotated.get_rect(center=(isx, isy))
        self.screen.blit(body_rotated, body_rect)
        turret_angle = tank.turret_angle
        turret_surface = self._create_turret_surface(tank, color_key)
        turret_rotated = self.pygame.transform.rotate(turret_surface, -turret_angle)
        turret_rect = turret_rotated.get_rect(center=(isx, isy))
        self.screen.blit(turret_rotated, turret_rect)
        if tank.hit_flash_timer > 0:
            flash_intensity = tank.hit_flash_timer / constants.TANK_HIT_FLASH_TIME
            flash_alpha = int(120 * flash_intensity)
            flash_surf = self.pygame.Surface(
                (constants.TANK_HITBOX_RADIUS * 2 + 8,
                 constants.TANK_HITBOX_RADIUS * 2 + 8),
                self.pygame.SRCALPHA,
            )
            self.pygame.draw.circle(
                flash_surf, (255, 255, 255, flash_alpha),
                (int(constants.TANK_HITBOX_RADIUS + 4), int(constants.TANK_HITBOX_RADIUS + 4)),
                int(constants.TANK_HITBOX_RADIUS + 2),
            )
            self.screen.blit(flash_surf,
                             (isx - constants.TANK_HITBOX_RADIUS - 4,
                              isy - constants.TANK_HITBOX_RADIUS - 4))

    def _create_turret_surface(self, tank, color_key):
        base_color = constants.COLOR_GREEN if color_key == "green" else constants.COLOR_RED
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
        return surface

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
        hull = self.pygame.Surface((32, 32), self.pygame.SRCALPHA)
        self.pygame.draw.polygon(hull, (60, 60, 60, 180),
                                 [(16, 4), (4, 16), (10, 28), (22, 28), (28, 16)])
        self.pygame.draw.polygon(hull, (40, 40, 40, 150),
                                 [(16, 4), (4, 16), (10, 28), (22, 28), (28, 16)], 2)
        self.screen.blit(hull, (isx - 16, isy - 16))
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
