# Dune — AI Assistant Documentation

## Overview

Dune is a desert survival strategy game for the maxbloks collection.
Targets handheld devices (Anbernic, R46H) and desktop platforms.
Designed for gamepad-first input at 640×480.

## Purpose and Main Features

- Desert-themed survival/exploration gameplay (implementation TBD)
- Gamepad and keyboard controls
- 60 FPS target on limited hardware

## Dependencies

- **pygame-ce** — rendering and input
- **maxbloks.common.compat_sdl** — display initialisation via symlink

## File Structure

```
maxbloks/dune/
├── __init__.py
├── main.py          # Entry point
├── game.py          # DuneGame class (state machine)
├── constants.py     # Screen, color, and game constants
├── entities.py      # Player and future entity classes
├── utils.py         # Math helpers (clamp, distance, normalize)
├── compat_sdl.py    # Symlink → ../common/compat_sdl.py
├── BUILD
├── README.md
├── CLAUDE.md
├── game.json
├── version.json
├── Dune.sh
└── tests/
    ├── __init__.py
    ├── BUILD
    ├── test_constants.py
    ├── test_entities.py
    └── test_utils.py
```

## Architecture

Custom state machine (same pattern as Starfighter/SpellWheels):

```
DuneGame
  └── state: GameState (MENU → PLAYING ↔ PAUSED → GAME_OVER → MENU)
       └── Player (entities.py)
```

## How to Run

```bash
python -m maxbloks.dune.main
```

## Controls

| Action      | Keyboard          | Gamepad   |
|-------------|-------------------|-----------|
| Move        | W/A/S/D or arrows | D-pad     |
| Confirm     | Enter             | A button  |
| Pause/Back  | Escape            | Start     |

## Configuration

Key constants in `constants.py`:

| Constant        | Default | Purpose              |
|-----------------|---------|----------------------|
| LOGICAL_WIDTH   | 640     | Render width         |
| LOGICAL_HEIGHT  | 480     | Render height        |
| FULLSCREEN      | False   | Toggle fullscreen    |
| TARGET_FPS      | 60      | Frame rate cap       |
| PLAYER_SPEED    | 3.0     | Player movement speed|

## Development Notes

```bash
# Run tests
python -m unittest discover -s maxbloks/dune/tests -v

# Check coverage
tools/missing.sh

# Security lint
bandit -c bandit.yaml -r maxbloks/dune/
```

To extend the game: add new entity classes in `entities.py`, new game
states to `GameState`, and corresponding `_update_*` / `_draw_*` methods
in `game.py`.

## Invariants / What NOT to Change

- `compat_sdl.py` must remain a symlink to `../common/compat_sdl.py`, not a copy.
- All Python source files must carry the GPL-3.0-or-later SPDX header.
- `version.json` is the single source of truth for the version number; bump
  with `python tools/increment_version.py dune` before tagging a release.
