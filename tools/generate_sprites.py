# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate pixel-art PNG sprite assets for TankBattle.

Run from the repository root:
    python tools/generate_sprites.py

Writes PNG files to maxbloks/tankbattle/assets/sprites/.
SpriteCache loads them at startup; if a file is absent it falls back
to its built-in procedural drawing, so this script has no hard
dependency on being run first.
"""

import math
import os
import pathlib
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402  (env vars must be set first)

DEST = pathlib.Path(__file__).parent.parent / "maxbloks" / "tankbattle" / "assets" / "sprites"

# ---------------------------------------------------------------------------
# Palette — mirrors constants.py so sprites integrate with the game colours
# ---------------------------------------------------------------------------

COLOR_BG       = (38, 74, 42)
COLOR_SOFT     = (145, 105, 64)
COLOR_HARD     = (55, 55, 60)
COLOR_GREEN    = (40, 220, 80)
COLOR_RED      = (220, 60, 50)

TILE_SIZE      = 32
TANK_BW        = 28
TANK_BH        = 36
TANK_TW        = 8   # turret barrel width
TURRET_SIZE    = 48
TANK_SIZE      = max(TANK_BW, TANK_BH) + 16   # 52


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _darker(color, amount=30):
    return tuple(max(0, c - amount) for c in color[:3])

def _lighter(color, amount=30):
    return tuple(min(255, c + amount) for c in color[:3])

def _save(surface, name):
    path = DEST / name
    pygame.image.save(surface, str(path))
    print(f"  wrote {path.name}")


# ---------------------------------------------------------------------------
# Terrain tiles
# ---------------------------------------------------------------------------

def make_terrain_tile():
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(COLOR_BG)
    rng = random.Random(42)
    br, bg, bb = COLOR_BG
    # Scattered noise dots
    for _ in range(40):
        px, py = rng.randrange(TILE_SIZE), rng.randrange(TILE_SIZE)
        n = rng.randint(-8, 8)
        col = (max(0, min(255, br + n)), max(0, min(255, bg + n)), max(0, min(255, bb + n // 2)))
        pygame.draw.circle(s, col, (px, py), 1)
    # Short grass-blade strokes
    blade_dark  = _darker(COLOR_BG, 10)
    blade_light = _lighter(COLOR_BG, 18)
    for _ in range(14):
        x = rng.randrange(2, TILE_SIZE - 2)
        y = rng.randrange(2, TILE_SIZE - 2)
        length = rng.randint(2, 5)
        col = blade_light if rng.random() > 0.4 else blade_dark
        pygame.draw.line(s, col, (x, y), (x + rng.randint(-1, 1), y - length), 1)
    return s


def make_hard_rock_tile():
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(COLOR_HARD)
    hr, hg, hb = COLOR_HARD
    rng = random.Random(7)
    # Texture noise
    for _ in range(24):
        px, py = rng.randrange(1, TILE_SIZE - 1), rng.randrange(1, TILE_SIZE - 1)
        n = rng.randint(-8, 8)
        col = (max(0, min(255, hr + n)), max(0, min(255, hg + n)), max(0, min(255, hb + n)))
        pygame.draw.circle(s, col, (px, py), 1)
    # Diagonal crack across the tile
    crack_col = _darker(COLOR_HARD, 22)
    pygame.draw.line(s, crack_col, (22, 2), (10, 14), 1)
    pygame.draw.line(s, crack_col, (10, 14), (20, 28), 1)
    # Bevel edges
    hi = _lighter(COLOR_HARD, 28)
    sh = _darker(COLOR_HARD, 22)
    pygame.draw.line(s, hi, (0, 0), (TILE_SIZE - 1, 0), 1)
    pygame.draw.line(s, hi, (0, 0), (0, TILE_SIZE - 1), 1)
    pygame.draw.line(s, sh, (TILE_SIZE - 1, 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
    pygame.draw.line(s, sh, (1, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
    pygame.draw.rect(s, sh, (0, 0, TILE_SIZE, TILE_SIZE), 1)
    return s


def make_soft_obstacle_tile():
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(COLOR_SOFT)
    sr, sg, sb = COLOR_SOFT
    rng = random.Random(13)
    # Texture noise
    for _ in range(18):
        px, py = rng.randrange(1, TILE_SIZE - 1), rng.randrange(1, TILE_SIZE - 1)
        n = rng.randint(-6, 6)
        col = (max(0, min(255, sr + n)), max(0, min(255, sg + n)), max(0, min(255, sb + n // 2)))
        pygame.draw.circle(s, col, (px, py), 1)
    # Crate plank lines — horizontal separators
    plank = _darker(COLOR_SOFT, 24)
    plank_hi = _lighter(COLOR_SOFT, 18)
    for y in (10, 21):
        pygame.draw.line(s, plank, (1, y), (TILE_SIZE - 2, y), 1)
        pygame.draw.line(s, plank_hi, (1, y + 1), (TILE_SIZE - 2, y + 1), 1)
    # Vertical centre divider
    cx = TILE_SIZE // 2
    pygame.draw.line(s, plank, (cx, 1), (cx, TILE_SIZE - 2), 1)
    # Metal corner brackets
    bracket = _darker(COLOR_SOFT, 35)
    for bx, by in [(1, 1), (TILE_SIZE - 4, 1), (1, TILE_SIZE - 4), (TILE_SIZE - 4, TILE_SIZE - 4)]:
        pygame.draw.rect(s, bracket, (bx, by, 3, 3))
    # Bevel
    hi = _lighter(COLOR_SOFT, 22)
    sh = _darker(COLOR_SOFT, 18)
    pygame.draw.line(s, hi, (0, 0), (TILE_SIZE - 1, 0), 1)
    pygame.draw.line(s, hi, (0, 0), (0, TILE_SIZE - 1), 1)
    pygame.draw.line(s, sh, (TILE_SIZE - 1, 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
    pygame.draw.line(s, sh, (1, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
    return s


# ---------------------------------------------------------------------------
# Tank body
# ---------------------------------------------------------------------------

def make_tank_body(base_color):
    sz = TANK_SIZE   # 52
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy = sz // 2, sz // 2

    dark   = _darker(base_color, 55)
    mid    = _darker(base_color, 25)
    light  = _lighter(base_color, 50)
    bright = _lighter(base_color, 70)

    # Track dimensions (identical to SpriteCache)
    track_w = (TANK_BW - 6) // 2   # 11
    track_h = TANK_BH + 4           # 40
    lt = (cx - TANK_BW // 2 - 1, cy - track_h // 2, track_w, track_h)  # left track rect
    rt = (cx + TANK_BW // 2 - track_w + 1, cy - track_h // 2, track_w, track_h)

    # Track base
    track_dark = (35, 30, 30)
    track_mid  = (60, 55, 55)
    for tr in (lt, rt):
        pygame.draw.rect(s, track_dark, tr, border_radius=3)
        # Individual tread links every 5px
        for ty in range(tr[1] + 3, tr[1] + tr[3] - 2, 5):
            pygame.draw.line(s, track_mid, (tr[0] + 1, ty), (tr[0] + tr[2] - 2, ty), 1)
        # Wheel hubs at top and bottom
        for hub_y in (tr[1] + 5, tr[1] + tr[3] - 5):
            pygame.draw.circle(s, track_mid, (tr[0] + tr[2] // 2, hub_y), 3)
            pygame.draw.circle(s, (20, 20, 20), (tr[0] + tr[2] // 2, hub_y), 3, 1)

    # Drop shadow
    shadow_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    body_rect = (cx - TANK_BW // 2, cy - TANK_BH // 2, TANK_BW, TANK_BH)
    shadow_body = (body_rect[0] + 3, body_rect[1] + 3, body_rect[2], body_rect[3])
    pygame.draw.rect(shadow_surf, (0, 0, 0, 40), shadow_body, border_radius=3)
    s.blit(shadow_surf, (0, 0))

    # Hull base
    pygame.draw.rect(s, base_color, body_rect, border_radius=3)

    # Side skirts (narrow strips over track gap)
    skirt = mid
    for sk_rect in [
        (body_rect[0], body_rect[1] + 4, 3, body_rect[3] - 8),
        (body_rect[0] + body_rect[2] - 3, body_rect[1] + 4, 3, body_rect[3] - 8),
    ]:
        pygame.draw.rect(s, skirt, sk_rect)

    # Front armor plate (top of hull = forward)
    front_h = 8
    front_rect = (body_rect[0] + 2, body_rect[1] + 2, TANK_BW - 4, front_h)
    pygame.draw.rect(s, light, front_rect, border_radius=2)
    # Vision port slots on front armor
    slot_col = _darker(light, 40)
    for sx in (body_rect[0] + 6, body_rect[0] + 16):
        pygame.draw.rect(s, slot_col, (sx, body_rect[1] + 3, 4, 2))
    # Bright leading edge line
    pygame.draw.line(s, bright, (body_rect[0] + 3, body_rect[1] + 2),
                     (body_rect[0] + TANK_BW - 4, body_rect[1] + 2), 1)

    # Centre hull panel
    center_rect = (body_rect[0] + 3, body_rect[1] + front_h + 3,
                   TANK_BW - 6, TANK_BH - front_h - 12)
    pygame.draw.rect(s, mid, center_rect)
    # Rivet dots on hull sides
    rivet_col = _darker(base_color, 40)
    for ry in range(body_rect[1] + 6, body_rect[1] + TANK_BH - 4, 8):
        pygame.draw.circle(s, rivet_col, (body_rect[0] + 3, ry), 1)
        pygame.draw.circle(s, rivet_col, (body_rect[0] + TANK_BW - 4, ry), 1)

    # Rear engine panel
    rear_y = body_rect[1] + TANK_BH - 9
    pygame.draw.rect(s, dark, (body_rect[0] + 2, rear_y, TANK_BW - 4, 7), border_radius=2)
    # Exhaust ports
    exhaust_col = (15, 15, 15)
    for ex in (body_rect[0] + 5, body_rect[0] + TANK_BW - 10):
        pygame.draw.rect(s, exhaust_col, (ex, rear_y + 2, 5, 3))
    # Heat shimmer (bright pixel above exhaust)
    pygame.draw.rect(s, _lighter(dark, 40), (body_rect[0] + 6, rear_y - 1, 3, 1))
    pygame.draw.rect(s, _lighter(dark, 40), (body_rect[0] + TANK_BW - 9, rear_y - 1, 3, 1))

    # Hull outline
    pygame.draw.rect(s, dark, body_rect, 2, border_radius=3)

    # Turret mount ring
    pygame.draw.circle(s, dark, (cx, cy), 9)
    pygame.draw.circle(s, mid, (cx, cy), 7)
    pygame.draw.circle(s, (15, 15, 15), (cx, cy), 9, 2)
    # Inner ring detail
    pygame.draw.circle(s, _darker(mid, 10), (cx, cy), 5)
    pygame.draw.circle(s, mid, (cx, cy), 5, 1)

    # Hatch (right of turret ring)
    hx, hy = cx + 11, cy - 4
    pygame.draw.rect(s, dark, (hx, hy, 7, 7), border_radius=2)
    pygame.draw.rect(s, mid, (hx + 1, hy + 1, 5, 5), border_radius=1)
    pygame.draw.circle(s, _lighter(mid, 20), (hx + 3, hy + 3), 1)  # hatch bolt

    return s


# ---------------------------------------------------------------------------
# Turret
# ---------------------------------------------------------------------------

def make_turret(base_color):
    sz = TURRET_SIZE   # 48
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy = sz // 2, sz // 2

    light = _lighter(base_color, 50)
    barrel_col = (42, 42, 42)
    barrel_hi  = (88, 88, 88)

    turret_h = TANK_BH   # 36  — barrel length matches body height
    barrel_rect = (cx - TANK_TW // 2, cy - turret_h // 2, TANK_TW, turret_h)

    # Barrel
    pygame.draw.rect(s, barrel_col, barrel_rect, border_radius=2)
    # Highlight ridge left side
    pygame.draw.line(s, barrel_hi,
                     (barrel_rect[0] + 1, barrel_rect[1] + 4),
                     (barrel_rect[0] + 1, barrel_rect[1] + barrel_rect[3] - 4), 1)
    # Cooling slots on barrel
    for slot_y in range(barrel_rect[1] + 8, barrel_rect[1] + barrel_rect[3] - 8, 7):
        pygame.draw.line(s, (20, 20, 20),
                         (barrel_rect[0] + 2, slot_y),
                         (barrel_rect[0] + TANK_TW - 3, slot_y), 1)

    # Muzzle block
    muzzle_w = TANK_TW + 4
    muzzle_h = 5
    muzzle_rect = (cx - muzzle_w // 2, barrel_rect[1] - muzzle_h, muzzle_w, muzzle_h)
    pygame.draw.rect(s, barrel_col, muzzle_rect, border_radius=1)
    pygame.draw.line(s, barrel_hi, (muzzle_rect[0], muzzle_rect[1]),
                     (muzzle_rect[0] + muzzle_w - 1, muzzle_rect[1]), 1)

    # Muzzle tip glow
    tip_y = muzzle_rect[1] + 2
    pygame.draw.circle(s, (255, 245, 130), (cx, tip_y), 3)
    pygame.draw.circle(s, (255, 255, 230), (cx, tip_y), 1)

    # Turret dome — dark shell with team-colour inner ring
    dome_r = TANK_TW + 1   # 9
    pygame.draw.circle(s, (38, 38, 38), (cx, cy), dome_r)
    pygame.draw.circle(s, base_color, (cx, cy), dome_r - 3)
    pygame.draw.circle(s, (18, 18, 18), (cx, cy), dome_r, 2)
    # Dome rivet dots
    for angle_deg in (30, 150, 270):
        rad = math.radians(angle_deg)
        rx = cx + int(math.cos(rad) * (dome_r - 2))
        ry = cy + int(math.sin(rad) * (dome_r - 2))
        pygame.draw.circle(s, (18, 18, 18), (rx, ry), 1)
    # Glint
    pygame.draw.circle(s, light, (cx - 1, cy - 2), 2)
    return s


# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------

def make_bullet():
    sz = 12
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c = sz // 2
    pygame.draw.circle(s, (255, 255, 180, 170), (c, c), 4)
    pygame.draw.circle(s, (255, 255, 255), (c, c), 2)
    pygame.draw.circle(s, (255, 240, 120, 80), (c, c), 5)
    return s


def make_rocket():
    sz = 16
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c = sz // 2
    # Body
    pygame.draw.polygon(s, (200, 85, 25),
                         [(c, 1), (c - 3, c + 5), (c + 3, c + 5)])
    # Highlight
    pygame.draw.polygon(s, (240, 140, 55),
                         [(c, 3), (c - 2, c + 4), (c + 2, c + 4)])
    # Fins
    pygame.draw.polygon(s, (160, 65, 20),
                         [(c - 3, c + 5), (c - 5, c + 9), (c - 1, c + 8)])
    pygame.draw.polygon(s, (160, 65, 20),
                         [(c + 3, c + 5), (c + 5, c + 9), (c + 1, c + 8)])
    # Exhaust glow
    pygame.draw.circle(s, (255, 210, 90, 160), (c, c + 8), 3)
    pygame.draw.circle(s, (255, 140, 30, 100), (c, c + 9), 2)
    return s


# ---------------------------------------------------------------------------
# Mine
# ---------------------------------------------------------------------------

def make_mine(armed=False):
    sz = 20
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c = sz // 2
    # Body
    pygame.draw.circle(s, (55, 55, 55), (c, c), 7)
    pygame.draw.circle(s, (78, 78, 78), (c, c), 5)
    pygame.draw.circle(s, (38, 38, 38), (c, c), 7, 1)
    # Spikes / detonators
    for deg in range(0, 360, 60):
        rad = math.radians(deg)
        sx = c + int(math.cos(rad) * 9)
        sy = c + int(math.sin(rad) * 9)
        pygame.draw.circle(s, (68, 68, 68), (sx, sy), 2)
        pygame.draw.circle(s, (38, 38, 38), (sx, sy), 2, 1)
    # Top mounting bolt
    pygame.draw.circle(s, (90, 90, 90), (c, c - 6), 1)
    # Armed indicator
    if armed:
        pygame.draw.circle(s, (255, 45, 45), (c, c), 3)
        pygame.draw.circle(s, (255, 140, 140), (c - 1, c - 1), 1)
    return s


# ---------------------------------------------------------------------------
# Power-ups
# ---------------------------------------------------------------------------

def make_powerup(power_type):
    sz = 24
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c = sz // 2

    configs = {
        "health":      ((50, 200, 80),  (30, 160, 60)),
        "spread_shot": ((80, 180, 220), (60, 140, 180)),
        "rocket":      ((220, 100, 40), (180, 80, 30)),
        "rapid_fire":  ((240, 200, 40), (200, 170, 30)),
        "ricochet":    ((180, 80, 200), (140, 60, 160)),
        "mine_layer":  ((100, 100, 100),(70, 70, 70)),
    }
    bg, outline = configs.get(power_type, ((150, 150, 150), (100, 100, 100)))

    pygame.draw.circle(s, bg, (c, c), 9)
    pygame.draw.circle(s, outline, (c, c), 9, 2)
    # Glint
    pygame.draw.circle(s, tuple(min(255, v + 60) for v in bg), (c - 2, c - 3), 2)

    if power_type == "health":
        pygame.draw.rect(s, (255, 255, 255), (c - 1, c - 5, 3, 10))
        pygame.draw.rect(s, (255, 255, 255), (c - 5, c - 1, 10, 3))

    elif power_type == "spread_shot":
        for offset in (-22, 0, 22):
            rad = math.radians(offset - 90)
            ex = c + int(math.cos(rad) * 7)
            ey = c + int(math.sin(rad) * 7)
            pygame.draw.line(s, (255, 255, 255), (c, c), (ex, ey), 2)

    elif power_type == "rocket":
        pygame.draw.polygon(s, (255, 255, 255),
                             [(c, c - 5), (c - 3, c + 3), (c + 3, c + 3)])

    elif power_type == "rapid_fire":
        bolt = [(c - 2, c - 6), (c + 3, c - 1), (c, c - 1),
                (c + 2, c + 6), (c - 3, c + 1), (c, c + 1)]
        pygame.draw.polygon(s, (255, 255, 255), bolt)

    elif power_type == "ricochet":
        pygame.draw.arc(s, (255, 255, 255), (c - 6, c - 6, 12, 12), 0.3, 2.5, 2)
        pygame.draw.arc(s, (255, 255, 255), (c - 4, c - 4, 8, 8), 3.5, 5.5, 2)

    elif power_type == "mine_layer":
        pygame.draw.circle(s, (255, 255, 255), (c, c), 4)
        pygame.draw.circle(s, outline, (c, c), 4, 1)

    return s


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"Writing sprites to {DEST}")

    _save(make_terrain_tile(),        "terrain_tile.png")
    _save(make_hard_rock_tile(),      "hard_rock_tile.png")
    _save(make_soft_obstacle_tile(),  "soft_obstacle_tile.png")

    _save(make_tank_body(COLOR_GREEN), "tank_green.png")
    _save(make_tank_body(COLOR_RED),   "tank_red.png")

    _save(make_turret(COLOR_GREEN), "turret_green.png")
    _save(make_turret(COLOR_RED),   "turret_red.png")

    _save(make_bullet(), "bullet.png")
    _save(make_rocket(), "rocket.png")

    _save(make_mine(armed=False), "mine_unarmed.png")
    _save(make_mine(armed=True),  "mine_armed.png")

    for pt in ("health", "spread_shot", "rocket", "rapid_fire", "ricochet", "mine_layer"):
        _save(make_powerup(pt), f"powerup_{pt}.png")

    pygame.quit()
    print("Done.")


if __name__ == "__main__":
    main()
