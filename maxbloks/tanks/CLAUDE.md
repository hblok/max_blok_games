# Tanks — Developer Guide

## Overview

Top-down 2D tank shooter targeting handheld gaming devices (Anbernic R46H) at 640×480. The player drives a tank around a large scrolling world (2400×1800), shoots waves of enemies, and collects weapon power-ups. Win condition: 50 kills.

## Purpose and Main Features

- Scrolling camera following the player across a world 3–4× the viewport size
- Progressive enemy difficulty (speed increases with each kill)
- Five weapon types including a continuous laser beam and deployable land mines
- Procedurally generated world: rock clusters, mountains, health packs, weapon pickups
- Full gamepad and keyboard support

## Dependencies

- `pygame-ce` — display, input, sprites
- `maxbloks.common.compat_sdl` — cross-platform SDL display init (via `compat_sdl.py` symlink)

## File Structure

```
maxbloks/tanks/
├── __init__.py         package marker
├── main.py             entry point
├── game.py             Game class (main loop + state machine)
├── constants.py        all config classes and color palette
├── position.py         Position dataclass (x, y, distance_to)
├── camera.py           Camera (viewport scrolling, world→screen transform)
├── collision.py        CollisionManager + CollisionHandler
├── enemy.py            Enemy sprite (chases player)
├── game_state.py       GameState enum + GameStats
├── input_handler.py    InputHandler + InputState (keyboard/gamepad)
├── obstacles.py        Rock, MountainFormation, HealthPack sprites
├── paths.py            GamePaths (asset path helpers)
├── projectile.py       Projectile sprite (base bullet)
├── render.py           Renderer (all drawing logic)
├── spawner.py          EnemySpawner (edge spawning, difficulty scaling)
├── tank.py             Tank sprite (movement, rotation, firing)
├── ui.py               UI (HUD, health bar, weapon bar, game-over screen)
├── weapon_manager.py   WeaponManager (switching, duration tracking)
├── weapons.py          Weapon classes + WeaponPickup + WeaponType
├── world.py            World (procedural generation, collision helpers)
├── compat_sdl.py       symlink → ../common/compat_sdl.py
├── game.json           game metadata
├── version.json        version
├── Tanks.sh            launch script
├── Tanks.png           screenshot / icon
└── tests/
    ├── __init__.py
    ├── BUILD
    └── test_*.py       (17 test modules, 48 tests)
```

## Architecture

```
main.py
  └─ game.Game
       ├─ constants.*Config / Colors
       ├─ input_handler.InputHandler  ← keyboard + gamepad
       ├─ ui.UI                       ← HUD overlay
       ├─ world.World                 ← static environment
       ├─ camera.Camera               ← viewport scroll
       ├─ tank.Tank                   ← player sprite
       ├─ weapon_manager.WeaponManager
       │    └─ weapons.*             (Weapon subclasses + LaserBeam + BombProjectile)
       ├─ spawner.EnemySpawner        ← wave / difficulty
       ├─ pygame.sprite.Group enemies / projectiles
       ├─ render.Renderer             ← all drawing
       └─ collision.CollisionHandler  ← all collision responses
```

**State machine** (inside `Game.run`):

```
PLAYING → GAME_OVER  (tank health reaches 0)
PLAYING → VICTORY    (50 enemies killed)
GAME_OVER / VICTORY → PLAYING  (B / restart button)
```

## How to Run

```bash
# Development (from repo root)
python3 -m maxbloks.tanks.main

# Tests
python3 -m unittest discover -s maxbloks/tanks/tests -v

# Full project tests
python3 -m unittest discover -s maxbloks

# Security lint
bandit -c bandit.yaml -r maxbloks/tanks/
```

## Controls

| Action | Keyboard | Gamepad |
|--------|----------|---------|
| Move / aim | Arrow / WASD | Left stick |
| Fire | Space | A (button 0) |
| Restart | B key | B (button 1) |
| Quit | — | Select (8) / Start (13) |

## Configuration

All tunable values live in `constants.py`:

| Class | Key constants |
|-------|--------------|
| `DisplayConfig` | `width=640`, `height=480`, `fps=60` |
| `WorldConfig` | `width=2400`, `height=1800`, `num_rock_clusters=8` |
| `TankConfig` | `speed=3.0`, `rotation_speed=200`, `max_health=300`, `fire_rate=500` |
| `EnemyConfig` | `base_speed=0.5`, `max_speed=3.0`, `max_enemies=15`, `spawn_interval=2000` |
| `GameConfig` | `enemies_to_win=50`, `joystick_deadzone=0.15` |

## Development Notes

### Adding a new weapon
1. Add a constant to `WeaponType` in `weapons.py`
2. Subclass `Weapon`, override `fire()` if needed
3. Add it to `WeaponManager.switch_weapon`'s `weapon_classes` dict
4. Add a color to `Colors` in `constants.py`
5. Add an icon to `UI._draw_weapon_icon` in `ui.py`
6. Add a `WeaponPickup` spawn entry in `World._generate_weapon_pickups`

### Camera coordinate system
World positions are in world-space (0..2400, 0..1800). `camera.apply(pos)` converts to screen-space for rendering. Never pass screen-space positions to game logic.

### Collision flow
`CollisionHandler.process_collisions` is the single entry point each frame. Order matters: bomb mines are resolved first (before regular projectile removal), then projectile–enemy, then tank–enemy, then pickups.

## Invariants / What NOT to Change

- `Position` is a mutable dataclass; do not freeze it — `Enemy.update_ai` mutates it in place
- `BombProjectile.is_expired` always returns `False`; landmine removal is handled by `CollisionHandler._bombs_vs_units`
- `Renderer.render_frame` must be called with `gs=` (keyword), not `game_state=` — the parameter was renamed to avoid shadowing the `game_state` module import
- `World.obstacles` is a `set`, not a sprite group — do not call `.update()` on it
