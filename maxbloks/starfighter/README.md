# Starfighter — Pygame Port

A neon synthwave space combat game, ported from the web (Vue 3 + Canvas)
to **Python / Pygame**, targeting handheld consoles (Anbernic-style) and
desktop.

## Quick Start

```bash
# From the repository root:
pip install pygame

# Run the game:
python -m starfighter.main
```

## Resolution & Display

| Setting            | Default   | Location                  |
|--------------------|-----------|---------------------------|
| Logical resolution | 640 × 480 | `starfighter/settings.py` |
| Fullscreen         | Off       | `FULLSCREEN = True/False` |
| Integer scaling    | On        | `INTEGER_SCALING`         |

The game renders to a **logical surface** (640 × 480) and scales it to
the actual display, preserving aspect ratio with letterboxing.  On a
handheld, set `FULLSCREEN = True` in `settings.py`.

## Controls

| Action       | Keyboard       | Gamepad / D-pad          |
|--------------|----------------|--------------------------|
| Rotate left  | ← Arrow        | D-pad left / Stick left  |
| Rotate right | → Arrow        | D-pad right / Stick right|
| Thrust       | ↑ Arrow        | D-pad up / Stick up      |
| Fire         | Space          | A / B button             |
| Pause        | Escape         | Start / Select           |
| Confirm      | Space / Enter  | A / B button             |
| Back (menu)  | Backspace      | —                        |

Joystick deadzone and button mappings can be adjusted in `settings.py`.

## Game Overview

- **Inertial movement** — Asteroids-style thrust, rotation, and friction
- **Screen wrapping** — Player, enemies, and power-ups wrap; bullets do not
- **Difficulty ramp** — Four tiers over 90 seconds:
  - Tier 1 (0–30 s): Drifters only, max 3
  - Tier 2 (30–60 s): + Gunners, max 5
  - Tier 3 (60–90 s): + Kamikaze, multi-hit enemies, max 6
  - Tier 4 (90 s+): + Bosses, max 8

### Enemy Types

| Type     | Color   | Behaviour                          | HP     |
|----------|---------|------------------------------------|--------|
| Drifter  | Magenta | Random drift                       | 1      |
| Gunner   | Orange  | Tracks & shoots at player          | 1–3    |
| Kamikaze | Red     | Accelerates toward player          | 1      |
| Boss     | Gold    | Slow, fires 3-bullet spread        | 10     |

### Power-ups

| Power-up    | Color      | Effect                              | Duration |
|-------------|------------|-------------------------------------|----------|
| Shield      | Blue       | Absorbs 3 hits                      | 15 s     |
| Rapid Fire  | Yellow     | 3× fire rate, 10 bullet limit       | 10 s     |
| Spread Shot | Green      | 3-bullet cone                       | 10 s     |
| Speed Boost | Pink       | 1.5× speed and thrust               | 10 s     |
| Homing      | Orange-red | Slow tracking missiles (max 2)      | 10 s     |
| Big Shot    | Purple     | Large piercing bullets (max 2)      | 10 s     |

## Project Structure

```
starfighter/
├── __init__.py        # Package marker
├── main.py            # Entry point — Pygame loop & display scaling
├── settings.py        # All tuning constants & configuration
├── game.py            # StarfighterGame — main controller & state machine
├── entities.py        # Player, Bullet, PowerUp, Particle
├── enemies.py         # Drifter, Gunner, Kamikaze, Boss + spawning
├── visual.py          # Drawing helpers, glow emulation, HUD, overlays
├── input.py           # Keyboard & joystick → logical actions
├── utils.py           # Math helpers, vector functions, wrapping
├── compat_sdl.py      # Safe SDL/Pygame display bootstrap
└── README.md          # This file
```

## Known Limitations vs. Web Version

- **Glow rendering**: Pygame lacks shader-based `shadowBlur`, so glow is
  approximated with layered alpha circles and additive blitting.  The
  overall neon impression is preserved, but fine bloom is less smooth.
- **Font**: Uses system `Courier New` instead of the web's *Share Tech
  Mono*.  A TTF file can be dropped in and referenced in `visual.py`.
- **Touch controls**: Not implemented (web version has swipe/tap).
  Gamepad and keyboard are the target inputs.
- **Sound**: No audio (the web version is also silent).

## License

GPL-3.0-or-later — see repository root.