# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate pixel-art PNG sprite assets for TankBattle.

Run from the repository root:
    python maxbloks/tankbattle/tools/generate_sprites.py

Writes PNG files to maxbloks/tankbattle/assets/sprites/.
SpriteCache loads them at startup; if a file is absent it falls back
to its built-in procedural drawing, so this script has no hard
dependency on being run first.

Every sprite in this file is defined using explicit pixel coordinates —
no random number generators.  This makes the source the authoritative
"source of truth" for each sprite, and makes each PNG reproducible.
"""

import math
import os
import pathlib

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

DEST = pathlib.Path(__file__).parent.parent / "assets" / "sprites"

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

COLOR_BG    = (34, 68, 38)
COLOR_SOFT  = (148, 108, 66)
COLOR_HARD  = (55, 55, 60)
COLOR_GREEN = (40, 220, 80)
COLOR_RED   = (220, 60, 50)

TILE_SIZE   = 32
TANK_BW     = 28
TANK_BH     = 36
TANK_TW     = 8
TURRET_SIZE = 48
TANK_SIZE   = max(TANK_BW, TANK_BH) + 16   # 52


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _d(c, n=30): return tuple(max(0, v - n) for v in c[:3])
def _l(c, n=30): return tuple(min(255, v + n) for v in c[:3])

def _px(s, coords, color):
    """Paint a list of (x, y) pixels onto surface s."""
    for x, y in coords:
        if 0 <= x < s.get_width() and 0 <= y < s.get_height():
            s.set_at((x, y), color)

def _save(surface, name):
    path = DEST / name
    pygame.image.save(surface, str(path))
    print(f"  wrote {path.name}")


# ---------------------------------------------------------------------------
# Terrain tile  (32×32)
#
# Design: dark-green base, deliberate grass tufts, subtle ground variation.
# Each tuft: shadow at base → two body pixels → bright tip pixel.
# ---------------------------------------------------------------------------

# Ground variation — explicit light/dark pixel positions
_TERRAIN_LIGHT = [
    (4,3),(9,7),(15,2),(20,5),(27,1),(31,8),
    (2,11),(8,14),(13,10),(18,13),(24,9),(30,12),
    (5,19),(11,22),(16,18),(22,21),(28,17),(1,23),
    (3,27),(10,29),(14,25),(21,28),(26,24),(29,30),
]
_TERRAIN_DARK = [
    (6,1),(12,4),(17,6),(23,3),(28,7),(0,9),
    (4,15),(9,18),(14,12),(20,16),(25,11),(31,17),
    (7,23),(13,26),(19,20),(25,24),(31,19),(2,28),
    (16,30),(8,31),(24,31),
]
# Grass tufts: (x, y_base, lean) — blade grows upward; lean ∈ {-1, 0, 1}
_TUFTS = [
    (2,6,0),(6,13,1),(10,5,-1),(14,11,0),(18,4,1),(22,12,-1),(26,6,0),(30,14,1),
    (1,18,-1),(5,25,0),(9,20,1),(13,26,-1),(17,19,0),(21,28,1),(25,17,-1),(29,23,0),
    (3,30,1),(7,9,-1),(11,29,0),(15,8,1),(19,31,-1),(23,7,0),(27,29,1),(31,10,-1),
]

def make_terrain_tile():
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(COLOR_BG)
    _px(s, _TERRAIN_LIGHT, _l(COLOR_BG, 12))
    _px(s, _TERRAIN_DARK,  _d(COLOR_BG, 10))
    SHADOW = _d(COLOR_BG, 18)
    BLADE  = _l(COLOR_BG, 20)
    TIP    = _l(COLOR_BG, 40)
    for x, yb, lean in _TUFTS:
        _px(s, [(x, yb)],          SHADOW)
        _px(s, [(x, yb-1)],        BLADE)
        _px(s, [(x+lean, yb-2)],   BLADE)
        _px(s, [(x+lean, yb-3)],   TIP)
    return s


# ---------------------------------------------------------------------------
# Hard rock tile  (32×32)
#
# Design: flat stone faces separated by deliberate crack lines; bevel edges.
# ---------------------------------------------------------------------------

# Primary crack — zigzag from top-centre down to bottom-right
_MAIN_CRACK = [
    (18,0),(18,1),(17,2),(17,3),(16,4),(15,5),(15,6),
    (14,7),(14,8),(13,9),(13,10),(12,11),(12,12),(12,13),
    (13,14),(13,15),(14,16),(14,17),(15,18),(15,19),(15,20),
    (16,21),(16,22),(17,23),(17,24),(17,25),(18,26),
    (18,27),(18,28),(18,29),(19,30),(19,31),
]
# Secondary crack — short branch on the left face
_BRANCH_CRACK = [
    (5,8),(6,9),(6,10),(7,11),(7,12),(8,13),(8,14),
]
# Face highlights — top-left stone face
_ROCK_HIGHLIGHT = [
    (1,1),(2,2),(4,1),(6,3),(8,1),(10,2),(1,4),(3,6),(5,4),(7,6),(9,4),(11,3),
    (1,7),(2,8),(4,9),(6,7),(3,10),(5,11),(7,9),(9,8),(11,10),(1,10),(2,12),
]
# Face shadows — bottom-right stone face
_ROCK_SHADOW = [
    (22,20),(24,22),(26,20),(28,22),(30,21),(22,24),(24,26),(26,24),(28,26),(30,24),
    (21,27),(23,28),(25,30),(27,28),(29,30),(22,30),(24,29),(26,31),(28,29),
]

def make_hard_rock_tile():
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(COLOR_HARD)
    _px(s, _ROCK_HIGHLIGHT, _l(COLOR_HARD, 22))
    _px(s, _ROCK_SHADOW,    _d(COLOR_HARD, 16))
    # Crack shadow (one pixel right of crack = slightly lighter to suggest depth)
    CRACK = _d(COLOR_HARD, 28)
    CRACK_EDGE = _d(COLOR_HARD, 14)
    for x, y in _MAIN_CRACK + _BRANCH_CRACK:
        _px(s, [(x, y)], CRACK)
        _px(s, [(x+1, y)], CRACK_EDGE)
    # Bevel edges
    BRIGHT = _l(COLOR_HARD, 30)
    SHADE  = _d(COLOR_HARD, 24)
    for x in range(TILE_SIZE):
        s.set_at((x, 0),            BRIGHT)
        s.set_at((x, TILE_SIZE-1),  SHADE)
    for y in range(TILE_SIZE):
        s.set_at((0, y),            BRIGHT)
        s.set_at((TILE_SIZE-1, y),  SHADE)
    return s


# ---------------------------------------------------------------------------
# Soft obstacle tile  (32×32)
#
# Design: wooden crate — three plank sections divided by dark lines,
# vertical centre divider, metal corner brackets, nail dots.
# ---------------------------------------------------------------------------

def make_soft_obstacle_tile():
    W = H = TILE_SIZE
    s = pygame.Surface((W, H))
    s.fill(COLOR_SOFT)

    PLANK_DARK  = _d(COLOR_SOFT, 28)
    PLANK_HI    = _l(COLOR_SOFT, 22)
    GRAIN       = _d(COLOR_SOFT, 10)
    METAL       = _d(COLOR_SOFT, 48)
    NAIL        = _l(COLOR_SOFT, 35)
    BORDER      = _d(COLOR_SOFT, 38)

    # Wood grain — subtle horizontal streaks in alternating planks
    for y in range(1, 10):
        if y % 2 == 0:
            for x in range(1, 15):
                s.set_at((x, y), GRAIN)
    for y in range(12, 21):
        if y % 2 == 1:
            for x in range(17, 31):
                s.set_at((x, y), GRAIN)
    for y in range(23, 31):
        if y % 2 == 0:
            for x in range(1, 15):
                s.set_at((x, y), GRAIN)
    for y in range(23, 31):
        if y % 2 == 1:
            for x in range(17, 31):
                s.set_at((x, y), GRAIN)

    # Horizontal plank dividers (dark line + highlight below)
    for x in range(1, 31):
        s.set_at((x, 10), PLANK_DARK)
        s.set_at((x, 11), PLANK_HI)
        s.set_at((x, 21), PLANK_DARK)
        s.set_at((x, 22), PLANK_HI)

    # Vertical centre divider
    for y in list(range(1, 10)) + list(range(12, 21)) + list(range(23, 31)):
        s.set_at((15, y), PLANK_DARK)
        s.set_at((16, y), PLANK_HI)

    # Metal corner L-brackets (3×3 squares)
    for bx, by in [(0,0),(29,0),(0,29),(29,29)]:
        pygame.draw.rect(s, METAL, (bx, by, 3, 3))

    # Nail heads (where planks intersect)
    _px(s, [
        (6,5),(22,5),(6,16),(22,16),(6,26),(22,26),
        (11,5),(26,5),(11,16),(26,16),(11,26),(26,26),
    ], NAIL)

    # Border
    pygame.draw.rect(s, BORDER, (0, 0, W, H), 1)
    return s


# ---------------------------------------------------------------------------
# Tank body  (52×52, SRCALPHA)
#
# Design: top-down tank facing UP (forward = top).
# Tracks with individual link plates; front armour band clearly marked;
# rear engine grille; turret ring; commander's hatch.
# ---------------------------------------------------------------------------

def make_tank_body(base_color):
    sz = TANK_SIZE   # 52
    s  = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy = sz // 2, sz // 2

    dark   = _d(base_color, 55)
    mid    = _d(base_color, 25)
    light  = _l(base_color, 45)
    bright = _l(base_color, 65)

    track_w = (TANK_BW - 6) // 2   # 11
    track_h = TANK_BH + 4           # 40
    lt = (cx - TANK_BW//2 - 1, cy - track_h//2, track_w, track_h)
    rt = (cx + TANK_BW//2 - track_w + 1, cy - track_h//2, track_w, track_h)

    TRACK_BASE  = (38, 34, 34)
    TRACK_LINK  = (58, 52, 52)
    TRACK_HI    = (72, 66, 66)
    WHEEL_HUB   = (50, 46, 46)

    # Track base
    for tr in (lt, rt):
        pygame.draw.rect(s, TRACK_BASE, tr, border_radius=3)
        # Individual tread link plates (5px tall each with a 1px dark gap)
        for ty in range(tr[1]+2, tr[1]+tr[3]-2, 5):
            plate_rect = (tr[0]+1, ty, tr[2]-2, 4)
            pygame.draw.rect(s, TRACK_LINK, plate_rect)
            pygame.draw.line(s, TRACK_HI,
                             (tr[0]+2, ty), (tr[0]+tr[2]-3, ty), 1)
        # Road wheels (circles at every 8px along track)
        for wy in range(tr[1]+5, tr[1]+tr[3]-4, 8):
            pygame.draw.circle(s, WHEEL_HUB, (tr[0]+tr[2]//2, wy), 3)
            pygame.draw.circle(s, TRACK_BASE, (tr[0]+tr[2]//2, wy), 3, 1)

    # Drop shadow
    sh = pygame.Surface((sz, sz), pygame.SRCALPHA)
    body_rect = (cx-TANK_BW//2, cy-TANK_BH//2, TANK_BW, TANK_BH)
    pygame.draw.rect(sh, (0,0,0,45),
                     (body_rect[0]+3, body_rect[1]+3, TANK_BW, TANK_BH),
                     border_radius=3)
    s.blit(sh, (0, 0))

    # Hull base
    pygame.draw.rect(s, base_color, body_rect, border_radius=3)

    # Hull side skirts (narrow strips covering track-hull gap)
    for sk in [
        (body_rect[0],                  body_rect[1]+5, 2, TANK_BH-10),
        (body_rect[0]+TANK_BW-2, body_rect[1]+5, 2, TANK_BH-10),
    ]:
        pygame.draw.rect(s, mid, (sk[0], sk[1], sk[2], sk[3]))

    # Front armour band (top of hull = forward direction)
    front_h = 7
    pygame.draw.rect(s, light,
                     (body_rect[0]+2, body_rect[1]+2, TANK_BW-4, front_h),
                     border_radius=2)
    # Bright leading edge (unmistakable forward indicator)
    pygame.draw.line(s, bright,
                     (body_rect[0]+3, body_rect[1]+2),
                     (body_rect[0]+TANK_BW-4, body_rect[1]+2), 1)
    # Vision port slots in front armour
    SLOT = _d(light, 50)
    for sx in (body_rect[0]+5, body_rect[0]+15):
        pygame.draw.rect(s, SLOT, (sx, body_rect[1]+4, 4, 2))

    # Centre hull panel
    pygame.draw.rect(s, mid,
                     (body_rect[0]+3, body_rect[1]+front_h+3,
                      TANK_BW-6, TANK_BH-front_h-12))

    # Hull rivet dots along both side edges
    RIVET = _d(base_color, 42)
    for ry in range(body_rect[1]+6, body_rect[1]+TANK_BH-6, 7):
        s.set_at((body_rect[0]+3, ry), RIVET)
        s.set_at((body_rect[0]+TANK_BW-4, ry), RIVET)

    # Rear engine grille
    rear_y = body_rect[1]+TANK_BH-9
    pygame.draw.rect(s, dark,
                     (body_rect[0]+2, rear_y, TANK_BW-4, 7), border_radius=2)
    # Exhaust ports (two rectangular slots)
    for ex in (body_rect[0]+5, body_rect[0]+TANK_BW-10):
        pygame.draw.rect(s, (15,15,15), (ex, rear_y+2, 5, 3))
    # Heat shimmer pixel above each exhaust port
    for ex in (body_rect[0]+7, body_rect[0]+TANK_BW-8):
        s.set_at((ex, rear_y-1), _l(dark, 35))

    # Hull outline
    pygame.draw.rect(s, dark, body_rect, 2, border_radius=3)

    # Turret mount ring
    pygame.draw.circle(s, dark,  (cx, cy), 9)
    pygame.draw.circle(s, mid,   (cx, cy), 7)
    pygame.draw.circle(s, _d(mid, 12), (cx, cy), 5)
    pygame.draw.circle(s, (18,18,18), (cx, cy), 9, 2)

    # Commander's hatch (right of turret ring)
    hx, hy = cx+11, cy-4
    pygame.draw.rect(s, dark, (hx, hy, 7, 7), border_radius=2)
    pygame.draw.rect(s, mid,  (hx+1, hy+1, 5, 5), border_radius=1)
    s.set_at((hx+3, hy+3), _l(mid, 25))   # hatch handle

    return s


# ---------------------------------------------------------------------------
# Turret  (48×48, SRCALPHA)
#
# Faces UP.  Dark charcoal barrel with cooling slots; team-colour dome;
# prominent muzzle tip for aim reading.
# ---------------------------------------------------------------------------

def make_turret(base_color):
    sz = TURRET_SIZE
    s  = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy = sz//2, sz//2

    BARREL  = (42, 42, 42)
    BARREL_HI = (86, 86, 86)
    MUZZLE  = (32, 32, 32)

    turret_h = TANK_BH   # 36
    barrel_rect = (cx-TANK_TW//2, cy-turret_h//2, TANK_TW, turret_h)

    # Barrel body
    pygame.draw.rect(s, BARREL, barrel_rect, border_radius=2)
    # Left highlight ridge
    pygame.draw.line(s, BARREL_HI,
                     (barrel_rect[0]+1, barrel_rect[1]+4),
                     (barrel_rect[0]+1, barrel_rect[1]+turret_h-4), 1)
    # Cooling slots (3 slots evenly spaced along barrel)
    SLOT = (20, 20, 20)
    for i in range(3):
        sy = barrel_rect[1] + 8 + i * 8
        pygame.draw.line(s, SLOT,
                         (barrel_rect[0]+2, sy),
                         (barrel_rect[0]+TANK_TW-3, sy), 1)

    # Muzzle block
    mw, mh = TANK_TW+4, 5
    mx = cx - mw//2
    my = barrel_rect[1] - mh
    pygame.draw.rect(s, MUZZLE, (mx, my, mw, mh), border_radius=1)
    pygame.draw.line(s, BARREL_HI, (mx, my), (mx+mw-1, my), 1)

    # Muzzle tip glow — clearly marks firing direction
    tip_y = my + 2
    pygame.draw.circle(s, (255, 245, 128), (cx, tip_y), 3)
    pygame.draw.circle(s, (255, 255, 230), (cx, tip_y), 1)

    # Dome — dark outer ring, team colour fill, inner shadow
    dome_r = TANK_TW + 1   # 9
    pygame.draw.circle(s, (36, 36, 36), (cx, cy), dome_r)
    pygame.draw.circle(s, base_color,   (cx, cy), dome_r-3)
    pygame.draw.circle(s, _d(base_color, 18), (cx, cy), dome_r-6)
    pygame.draw.circle(s, (18, 18, 18), (cx, cy), dome_r, 2)
    # Three rivet dots around dome equator
    for deg in (30, 150, 270):
        rad = math.radians(deg)
        rx = cx + int(math.cos(rad) * (dome_r-2))
        ry = cy + int(math.sin(rad) * (dome_r-2))
        s.set_at((rx, ry), (18, 18, 18))
    # Glint on dome
    s.set_at((cx-1, cy-2), _l(base_color, 55))

    return s


# ---------------------------------------------------------------------------
# Bullet  (12×12, SRCALPHA)
# ---------------------------------------------------------------------------

def make_bullet():
    sz = 12
    s  = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c  = sz // 2
    pygame.draw.circle(s, (255, 255, 170, 160), (c, c), 4)
    pygame.draw.circle(s, (255, 255, 255, 230), (c, c), 2)
    pygame.draw.circle(s, (255, 240, 100, 70),  (c, c), 5)
    return s


# ---------------------------------------------------------------------------
# Rocket  (16×16, SRCALPHA)
# ---------------------------------------------------------------------------

def make_rocket():
    sz = 16
    s  = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c  = sz // 2
    pygame.draw.polygon(s, (196, 82, 22),
                         [(c, 1),(c-3, c+5),(c+3, c+5)])
    pygame.draw.polygon(s, (238, 138, 52),
                         [(c, 3),(c-2, c+4),(c+2, c+4)])
    # Nose tip highlight
    s.set_at((c, 1), (255, 200, 120))
    # Fins
    pygame.draw.polygon(s, (158, 62, 18),
                         [(c-3,c+5),(c-5,c+10),(c-1,c+8)])
    pygame.draw.polygon(s, (158, 62, 18),
                         [(c+3,c+5),(c+5,c+10),(c+1,c+8)])
    # Exhaust flame
    pygame.draw.circle(s, (255, 208, 88, 155), (c, c+9), 3)
    pygame.draw.circle(s, (255, 138, 30, 100), (c, c+10), 2)
    return s


# ---------------------------------------------------------------------------
# Mine  (20×20, SRCALPHA)
# ---------------------------------------------------------------------------

def make_mine(armed=False):
    sz = 20
    s  = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c  = sz // 2
    # Body
    pygame.draw.circle(s, (52, 52, 52), (c, c), 7)
    pygame.draw.circle(s, (76, 76, 76), (c, c), 5)
    pygame.draw.circle(s, (36, 36, 36), (c, c), 7, 1)
    # Detonator spikes at 6 positions
    for deg in range(0, 360, 60):
        rad = math.radians(deg)
        sx = c + int(math.cos(rad) * 9)
        sy = c + int(math.sin(rad) * 9)
        pygame.draw.circle(s, (66, 66, 66), (sx, sy), 2)
        pygame.draw.circle(s, (36, 36, 36), (sx, sy), 2, 1)
    # Top mounting bolt
    s.set_at((c, c-6), (88, 88, 88))
    # Armed indicator — red LED
    if armed:
        pygame.draw.circle(s, (252, 44, 44), (c, c), 3)
        s.set_at((c-1, c-1), (255, 148, 148))
    return s


# ---------------------------------------------------------------------------
# Power-ups  (24×24, SRCALPHA)
# ---------------------------------------------------------------------------

def make_powerup(power_type):
    sz = 24
    s  = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c  = sz // 2

    CONFIGS = {
        "health":      ((50, 200, 80),  (28, 160, 58)),
        "spread_shot": ((80, 180, 220), (58, 138, 178)),
        "rocket":      ((220, 100, 40), (178, 78, 28)),
        "rapid_fire":  ((240, 200, 40), (198, 168, 28)),
        "ricochet":    ((178, 78, 200), (138, 58, 158)),
        "mine_layer":  ((100, 100, 100),(68, 68, 68)),
    }
    bg, outline = CONFIGS.get(power_type, ((150, 150, 150), (100, 100, 100)))

    pygame.draw.circle(s, bg,      (c, c), 9)
    pygame.draw.circle(s, outline, (c, c), 9, 2)
    # Glint (top-left of dome)
    s.set_at((c-2, c-3), tuple(min(255, v+65) for v in bg))

    if power_type == "health":
        pygame.draw.rect(s, (255,255,255), (c-1, c-5, 3, 10))
        pygame.draw.rect(s, (255,255,255), (c-5, c-1, 10, 3))

    elif power_type == "spread_shot":
        for offset in (-22, 0, 22):
            rad = math.radians(offset - 90)
            ex = c + int(math.cos(rad) * 7)
            ey = c + int(math.sin(rad) * 7)
            pygame.draw.line(s, (255,255,255), (c, c), (ex, ey), 2)

    elif power_type == "rocket":
        pygame.draw.polygon(s, (255,255,255),
                             [(c, c-5),(c-3, c+3),(c+3, c+3)])

    elif power_type == "rapid_fire":
        bolt = [(c-2,c-6),(c+3,c-1),(c,c-1),(c+2,c+6),(c-3,c+1),(c,c+1)]
        pygame.draw.polygon(s, (255,255,255), bolt)

    elif power_type == "ricochet":
        pygame.draw.arc(s, (255,255,255), (c-6, c-6, 12, 12), 0.3, 2.5, 2)
        pygame.draw.arc(s, (255,255,255), (c-4, c-4,  8,  8), 3.5, 5.5, 2)

    elif power_type == "mine_layer":
        pygame.draw.circle(s, (255,255,255), (c, c), 4)
        pygame.draw.circle(s, outline,       (c, c), 4, 1)

    return s


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"Writing sprites to {DEST}")

    _save(make_terrain_tile(),       "terrain_tile.png")
    _save(make_hard_rock_tile(),     "hard_rock_tile.png")
    _save(make_soft_obstacle_tile(), "soft_obstacle_tile.png")

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
