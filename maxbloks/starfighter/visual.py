# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
visual.py — Drawing helpers, glow emulation, HUD rendering, starfield.

All drawing targets the *logical surface* (640×480 by default).
Glow is approximated with layered alpha circles / outlines.
"""

from __future__ import annotations

import math
import random
import pygame

from maxbloks.starfighter.settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, COLORS, STAR_COUNT,
    PLAYER_RADIUS, POWERUP_DURATION, SHIELD_HITS,
)
from maxbloks.starfighter.utils import dim_color


# ======================================================================
# Glow helpers
# ======================================================================

def _make_glow_circle(radius: int, color: tuple, alpha: int) -> pygame.Surface:
    """Return a small per-pixel-alpha surface with a soft filled circle."""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (radius, radius)
    # Outer soft halo
    for r in range(radius, 0, -1):
        a = int(alpha * (r / radius) ** 0.5 * 0.5)
        c = (color[0], color[1], color[2], max(0, min(255, a)))
        pygame.draw.circle(surf, c, center, r)
    return surf


# Pre-built glow cache (lazily populated)
_glow_cache: dict[tuple, pygame.Surface] = {}


def get_glow_sprite(radius: int, color: tuple, alpha: int = 80) -> pygame.Surface:
    """Cached glow sprite for a given radius + color."""
    key = (radius, color, alpha)
    if key not in _glow_cache:
        _glow_cache[key] = _make_glow_circle(radius, color, alpha)
    return _glow_cache[key]


def draw_glow_circle(surface: pygame.Surface, x: float, y: float,
                     radius: int, color: tuple, core_alpha: int = 255,
                     glow_radius: int | None = None,
                     glow_alpha: int = 60):
    """Draw a glowing circle: outer halo + bright core."""
    gr = glow_radius or int(radius * 2.5)
    # Outer halo
    glow = get_glow_sprite(gr, color, glow_alpha)
    surface.blit(glow, (int(x) - gr, int(y) - gr), special_flags=pygame.BLEND_RGBA_ADD)
    # Core
    pygame.draw.circle(surface, (*color, core_alpha), (int(x), int(y)), radius)


def draw_glow_polygon(surface: pygame.Surface, points: list[tuple],
                      color: tuple, line_width: int = 2,
                      glow_width: int = 4, glow_alpha: int = 60):
    """Draw a polygon outline with a glow pass underneath."""
    # Glow pass — thicker, translucent
    glow_color = (*color, glow_alpha)
    glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(glow_surf, glow_color, points, glow_width)
    surface.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    # Core pass
    pygame.draw.polygon(surface, color, points, line_width)


def draw_glow_lines(surface: pygame.Surface, points: list[tuple],
                    color: tuple, closed: bool = True,
                    line_width: int = 2, glow_width: int = 5,
                    glow_alpha: int = 50):
    """Draw connected lines with glow."""
    glow_color = (*color, glow_alpha)
    glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.lines(glow_surf, glow_color, closed, points, glow_width)
    surface.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.lines(surface, color, closed, points, line_width)


# ======================================================================
# Starfield
# ======================================================================

class Starfield:
    """Subtle twinkling background stars."""

    def __init__(self, width: int = LOGICAL_WIDTH, height: int = LOGICAL_HEIGHT):
        self.stars: list[dict] = []
        for _ in range(STAR_COUNT):
            self.stars.append({
                "x": random.random() * width,
                "y": random.random() * height,
                "size": random.random() * 1.5 + 0.5,
                "alpha": random.random() * 0.4 + 0.1,
            })

    def draw(self, surface: pygame.Surface, game_time: float):
        for s in self.stars:
            flicker = s["alpha"] + math.sin(game_time * 0.02 + s["x"]) * 0.1
            a = max(0, min(255, int(flicker * 255)))
            color = (255, 255, 255, a)
            sz = max(1, int(s["size"]))
            pygame.draw.rect(
                surface, color,
                (int(s["x"]), int(s["y"]), sz, sz),
            )


# ======================================================================
# Ship polygon (player)
# ======================================================================

# 12-point ship silhouette (same as JS version), facing right (angle 0)
_SHIP_POINTS_RAW = [
    (22, 0),
    (6, -5),
    (-4, -8),
    (-14, -16),
    (-10, -8),
    (-12, -4),
    (-10, 0),
    (-12, 4),
    (-10, 8),
    (-14, 16),
    (-4, 8),
    (6, 5),
]

_THRUST_POINTS_RAW = [
    (-10, -5),
    (-18, 0),   # tip — randomised at draw time
    (-10, 5),
]


def _rotate_points(points, angle, cx=0.0, cy=0.0):
    """Rotate a list of (x, y) tuples around (cx, cy)."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    out = []
    for px, py in points:
        rx = cos_a * px - sin_a * py + cx
        ry = sin_a * px + cos_a * py + cy
        out.append((rx, ry))
    return out


def draw_player_ship(surface: pygame.Surface, x: float, y: float,
                     angle: float, thrusting: bool, invincible_flash: bool):
    """Draw the player ship with glow."""
    if invincible_flash:
        return  # hidden frame during invincibility blink

    color = COLORS["player"]
    pts = _rotate_points(_SHIP_POINTS_RAW, angle, x, y)

    # Glow pass
    draw_glow_lines(surface, pts, color, closed=True,
                    line_width=2, glow_width=5, glow_alpha=50)

    # Thrust flame
    if thrusting:
        flame_tip_x = -18 - random.random() * 6
        flame_pts_raw = [(-10, -5), (flame_tip_x, 0), (-10, 5)]
        flame_pts = _rotate_points(flame_pts_raw, angle, x, y)
        thrust_color = COLORS["thrust"]
        draw_glow_lines(surface, flame_pts, thrust_color, closed=False,
                        line_width=2, glow_width=4, glow_alpha=60)


# ======================================================================
# Enemy shapes
# ======================================================================

def _diamond_points(x, y, r):
    return [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]


def _hexagon_points(x, y, r):
    pts = []
    for i in range(6):
        a = (math.pi / 3) * i - math.pi / 2
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
    return pts


def _dart_points(x, y, r, angle):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    raw = [(r + 4, 0), (-r, -r * 0.7), (-r * 0.4, 0), (-r, r * 0.7)]
    return [(cos_a * px - sin_a * py + x,
             sin_a * px + cos_a * py + y) for px, py in raw]


def _boss_outer(x, y, r):
    return _hexagon_points(x, y, r)


def _boss_inner(x, y, r):
    return [
        (x, y - r * 0.5),
        (x + r * 0.43, y + r * 0.25),
        (x - r * 0.43, y + r * 0.25),
    ]


def draw_enemy(surface: pygame.Surface, enemy) -> None:
    """Draw an enemy entity with glow and damage coloring."""
    x, y = enemy.x, enemy.y
    r = enemy.radius
    etype = enemy.enemy_type
    base_color = COLORS.get(etype, COLORS["drifter"])

    # Damage dimming
    if enemy.max_hp > 1 and enemy.hp < enemy.max_hp:
        ratio = enemy.hp / enemy.max_hp
        factor = 0.3 + ratio * 0.7
        color = dim_color(base_color, factor)
    else:
        color = base_color

    # Flash white on hit
    if enemy.flash_timer > 0:
        color = COLORS["white"]

    # Build points
    if etype == "drifter":
        pts = _diamond_points(x, y, r)
        draw_glow_lines(surface, pts, color, closed=True,
                        line_width=2, glow_width=4, glow_alpha=50)
    elif etype == "gunner":
        pts = _hexagon_points(x, y, r)
        draw_glow_lines(surface, pts, color, closed=True,
                        line_width=2, glow_width=4, glow_alpha=50)
    elif etype == "kamikaze":
        pts = _dart_points(x, y, r, enemy.angle)
        draw_glow_lines(surface, pts, color, closed=True,
                        line_width=2, glow_width=4, glow_alpha=50)
    elif etype == "boss":
        outer = _boss_outer(x, y, r)
        inner = _boss_inner(x, y, r)
        lw = 3
        gw = 6
        draw_glow_lines(surface, outer, color, closed=True,
                        line_width=lw, glow_width=gw, glow_alpha=60)
        draw_glow_lines(surface, inner, color, closed=True,
                        line_width=2, glow_width=4, glow_alpha=40)


# ======================================================================
# Bullets
# ======================================================================

def draw_player_bullet(surface: pygame.Surface, bullet) -> None:
    """Draw a player bullet (normal, homing, or big)."""
    x, y = int(bullet.x), int(bullet.y)

    if bullet.big:
        color = COLORS["bigshot"]
        draw_glow_circle(surface, x, y, bullet.radius, color,
                         glow_radius=bullet.radius * 3, glow_alpha=50)
        # White core
        pygame.draw.circle(surface, COLORS["white"],
                           (x, y), max(1, bullet.radius // 2))

    elif bullet.homing:
        color = COLORS["homing"]
        a = math.atan2(bullet.vy, bullet.vx)
        raw = [(7, 0), (-4, -4), (-2, 0), (-4, 4)]
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        pts = [(cos_a * px - sin_a * py + x,
                sin_a * px + cos_a * py + y) for px, py in raw]
        draw_glow_lines(surface, pts, color, closed=True,
                        line_width=2, glow_width=4, glow_alpha=60)
    else:
        color = COLORS["bullet"]
        draw_glow_circle(surface, x, y, bullet.radius, color,
                         glow_radius=bullet.radius * 3, glow_alpha=50)
        pygame.draw.circle(surface, COLORS["white"],
                           (x, y), max(1, int(bullet.radius * 0.6)))


def draw_enemy_bullet(surface: pygame.Surface, bullet) -> None:
    """Draw an enemy bullet."""
    x, y = int(bullet.x), int(bullet.y)
    color = bullet.color
    draw_glow_circle(surface, x, y, bullet.radius, color,
                     glow_radius=bullet.radius * 3, glow_alpha=50)
    pygame.draw.circle(surface, COLORS["white"],
                       (x, y), max(1, bullet.radius // 2))


# ======================================================================
# Power-ups
# ======================================================================

_POWERUP_ICONS = {
    "shield":     "S",
    "rapidfire":  "R",
    "spreadshot": "W",
    "speedboost": ">",
    "homing":     "H",
    "bigshot":    "O",
}


def draw_powerup(surface: pygame.Surface, pu, game_time: float) -> None:
    """Draw a floating power-up with pulsing glow."""
    pulse = 1.0 + math.sin(game_time * 0.1) * 0.15
    r = int(pu.radius * pulse)
    x, y = int(pu.x), int(pu.y)
    color = pu.color

    # Fading when about to expire
    alpha = 255
    if pu.life < 180:
        alpha = int(77 + 178 * (pu.life / 180))

    # Outer ring
    glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    ring_color = (*color, min(255, int(alpha * 0.7)))
    pygame.draw.circle(glow_surf, ring_color, (x, y), r + 4, 2)
    surface.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(surface, color, (x, y), r, 2)

    # Icon letter
    font = _get_small_font(max(8, r))
    icon = _POWERUP_ICONS.get(pu.powerup_type, "?")
    txt = font.render(icon, True, color)
    txt.set_alpha(alpha)
    tr = txt.get_rect(center=(x, y))
    surface.blit(txt, tr)


# ======================================================================
# Particles
# ======================================================================

def draw_particle(surface: pygame.Surface, p) -> None:
    """Draw a single fading particle."""
    alpha = max(0, min(255, int(255 * p.life / p.max_life)))
    x, y = int(p.x), int(p.y)
    color = (*p.color, alpha)
    # Small glow
    glow = get_glow_sprite(6, p.color, alpha // 3)
    surface.blit(glow, (x - 6, y - 6), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(surface, color, (x, y), 2)


# ======================================================================
# Shield indicator
# ======================================================================

def draw_shield(surface: pygame.Surface, x: float, y: float,
                hits: int) -> None:
    """Draw the shield bubble around the player."""
    alpha = int((0.2 + hits * 0.15) * 255)
    alpha = min(255, alpha)
    color = COLORS["shield"]
    r = PLAYER_RADIUS + 8
    glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*color, alpha // 2), (int(x), int(y)), r + 4, 3)
    surface.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    ring_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(ring_surf, (*color, alpha), (int(x), int(y)), r, 2)
    surface.blit(ring_surf, (0, 0))


# ======================================================================
# HUD
# ======================================================================

_font_cache: dict[tuple, pygame.Font] = {}


def _get_font(size: int) -> pygame.font.Font:
    if size not in _font_cache:
        _font_cache[size] = pygame.font.SysFont("Courier New", size, bold=True)
    return _font_cache[size]


def _get_small_font(size: int) -> pygame.font.Font:
    key = ("small", size)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont("Courier New", size)
    return _font_cache[key]


def draw_text_glow(surface: pygame.Surface, text: str, x: int, y: int,
                   color: tuple, size: int = 16, center: bool = False):
    """Render text with a simple glow behind it."""
    font = _get_font(size)
    # Glow pass
    glow_surf = font.render(text, True, color)
    glow_surf.set_alpha(60)
    gr = glow_surf.get_rect()
    if center:
        gr.center = (x, y)
    else:
        gr.topleft = (x, y)
    # Slight offset copies for glow
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -2), (0, 2)]:
        surface.blit(glow_surf, gr.move(dx, dy))
    # Core text
    core = font.render(text, True, color)
    surface.blit(core, gr)


def draw_hud(surface: pygame.Surface, score: int, lives: int,
             game_time_frames: int, high_score: int,
             active_powerups: dict) -> None:
    """Draw the in-game HUD overlay."""
    w = surface.get_width()
    hud_color = COLORS["hud"]

    # Title
    draw_text_glow(surface, "STARFIGHTER", w // 2, 8,
                   hud_color, size=14, center=True)

    # Score
    score_str = f"SCORE: {score:06d}"
    draw_text_glow(surface, score_str, 8, 24, hud_color, size=12)

    # High score
    hi_str = f"HI: {high_score:06d}"
    draw_text_glow(surface, hi_str, w - 8 - len(hi_str) * 8, 24,
                   hud_color, size=12)

    # Lives
    lives_str = "\u2666" * max(0, lives)
    draw_text_glow(surface, lives_str, 8, 40, hud_color, size=14)

    # Time
    total_sec = game_time_frames // 60
    m = total_sec // 60
    s = total_sec % 60
    time_str = f"TIME: {m}:{s:02d}"
    draw_text_glow(surface, time_str, w - 8 - len(time_str) * 8, 40,
                   hud_color, size=12)

    # Active power-up indicators at bottom
    _draw_powerup_indicators(surface, active_powerups)


def _draw_powerup_indicators(surface: pygame.Surface,
                             active_powerups: dict) -> None:
    """Draw small icons with timer arcs at the bottom of the screen."""
    if not active_powerups:
        return

    h = surface.get_height()
    w = surface.get_width()
    count = len(active_powerups)
    spacing = 32
    start_x = w // 2 - (count - 1) * spacing // 2
    y = h - 20

    for i, (ptype, pdata) in enumerate(active_powerups.items()):
        cx = start_x + i * spacing
        color = COLORS.get(ptype, COLORS["hud"])
        icon = _POWERUP_ICONS.get(ptype, "?")
        max_dur = POWERUP_DURATION.get(ptype, 600)
        timer = pdata.get("timer", 0)
        ratio = max(0.0, min(1.0, timer / max_dur))

        # Timer arc
        arc_rect = pygame.Rect(cx - 12, y - 12, 24, 24)
        if ratio > 0:
            start_angle = math.pi / 2
            end_angle = start_angle + ratio * 2 * math.pi
            arc_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.arc(arc_surf, (*color, 150), arc_rect,
                            start_angle, end_angle, 2)
            surface.blit(arc_surf, (0, 0))

        # Icon
        font = _get_small_font(10)
        txt = font.render(icon, True, color)
        tr = txt.get_rect(center=(cx, y))
        surface.blit(txt, tr)

        # Flash on expiration
        if timer < 60 and (timer // 6) % 2 == 0:
            flash_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (*color, 80), (12, 12), 12)
            surface.blit(flash_surf, (cx - 12, y - 12))


# ======================================================================
# Overlay screens
# ======================================================================

def draw_menu(surface: pygame.Surface, high_score: int,
              game_time: float, menu_enemies: list) -> None:
    """Draw the main menu screen."""
    w, h = surface.get_size()

    # Pulsing title
    pulse = 0.7 + 0.3 * abs(math.sin(game_time * 0.03))
    alpha = int(pulse * 255)
    title_color = COLORS["hud"]

    draw_text_glow(surface, "STARFIGHTER", w // 2, h // 3 - 20,
                   title_color, size=32, center=True)

    # Subtitle
    draw_text_glow(surface, "Survive. Destroy. Ascend.",
                   w // 2, h // 3 + 25,
                   COLORS["menu_sub"], size=14, center=True)

    # High score
    draw_text_glow(surface, f"HIGH SCORE: {high_score:06d}",
                   w // 2, h // 2 + 10,
                   COLORS["hud"], size=12, center=True)

    # Prompt (blinking)
    if (int(game_time) // 45) % 2 == 0:
        draw_text_glow(surface, "PRESS FIRE OR START TO PLAY",
                       w // 2, h * 2 // 3 + 10,
                       COLORS["white"], size=11, center=True)


def draw_pause_overlay(surface: pygame.Surface) -> None:
    """Semi-transparent pause overlay."""
    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    draw_text_glow(surface, "PAUSED", w // 2, h // 2 - 15,
                   COLORS["hud"], size=28, center=True)
    draw_text_glow(surface, "PRESS PAUSE TO RESUME",
                   w // 2, h // 2 + 20,
                   COLORS["white"], size=11, center=True)


def draw_gameover(surface: pygame.Surface, score: int,
                  high_score: int, is_new_high: bool) -> None:
    """Game over overlay."""
    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    draw_text_glow(surface, "GAME OVER", w // 2, h // 3,
                   COLORS["gameover"], size=30, center=True)

    draw_text_glow(surface, f"SCORE: {score:06d}",
                   w // 2, h // 2 - 10,
                   COLORS["hud"], size=14, center=True)

    if is_new_high:
        draw_text_glow(surface, "NEW HIGH SCORE!",
                       w // 2, h // 2 + 15,
                       COLORS["rapidfire"], size=14, center=True)
    else:
        draw_text_glow(surface, f"HIGH SCORE: {high_score:06d}",
                       w // 2, h // 2 + 15,
                       COLORS["hud"], size=12, center=True)

    draw_text_glow(surface, "PRESS FIRE TO PLAY AGAIN",
                   w // 2, h * 2 // 3,
                   COLORS["white"], size=11, center=True)
    draw_text_glow(surface, "PRESS BACK FOR MENU",
                   w // 2, h * 2 // 3 + 20,
                   COLORS["white"], size=10, center=True)