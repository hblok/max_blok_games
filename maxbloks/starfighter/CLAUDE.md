# Starfighter

## Overview
Starfighter is a neon synthwave space combat game, ported from a web implementation (Vue 3 + Canvas) to Python/Pygame. The game targets handheld consoles (Anbernic-style) and desktop platforms, featuring Asteroids-style inertial movement, multiple enemy types, power-ups, and a progressive difficulty system.

## Purpose and Main Features

### Gameplay
- **Inertial Movement**: Asteroids-style thrust, rotation, and friction physics
- **Screen Wrapping**: Player, enemies, and power-ups wrap around screen edges (bullets do not)
- **Progressive Difficulty**: Four difficulty tiers over 90 seconds with increasing enemy variety and count
- **Multiple Enemy Types**: Drifters, Gunners, Kamikaze, and Boss enemies
- **Power-up System**: Six different power-ups with timed durations

### Enemy Types
| Type | Color | Behavior | HP |
|------|-------|----------|-----|
| Drifter | Magenta | Random drift | 1 |
| Gunner | Orange | Tracks & shoots at player | 1-3 |
| Kamikaze | Red | Accelerates toward player | 1 |
| Boss | Gold | Slow, fires 3-bullet spread | 10 |

### Power-ups
| Power-up | Color | Effect | Duration |
|----------|-------|--------|----------|
| Shield | Blue | Absorbs 3 hits | 15 s |
| Rapid Fire | Yellow | 3× fire rate, 10 bullet limit | 10 s |
| Spread Shot | Green | 3-bullet cone | 10 s |
| Speed Boost | Pink | 1.5× speed and thrust | 10 s |
| Homing | Orange-red | Slow tracking missiles (max 2) | 10 s |
| Big Shot | Purple | Large piercing bullets (max 2) | 10 s |

## Dependencies

### External
- Python 3.7+
- pygame 2.0+

### Internal (from maxbloks)
- `maxbloks.starfighter.compat_sdl` - SDL display initialization (symlink to `../common/compat_sdl.py`)

## File Structure

```
starfighter/
├── __init__.py        # Package marker
├── main.py            # Entry point — Pygame loop & display scaling
├── settings.py        # All tuning constants & configuration
├── game.py            # StarfighterGame — main controller & state machine
├── entities.py        # Player, Bullet, PowerUp, Particle classes
├── enemies.py         # Drifter, Gunner, Kamikaze, Boss + spawning logic
├── visual.py          # Drawing helpers, glow emulation, HUD, overlays
├── input.py           # Keyboard & joystick → logical actions
├── utils.py           # Math helpers, vector functions, wrapping
├── compat_sdl.py      # Safe SDL/Pygame display bootstrap (symlink)
├── BUILD              # Bazel build configuration
├── README.md          # Detailed documentation
├── game.json          # Game metadata
├── version.json       # Version information
├── Starfighter.png    # Game screenshot/icon
└── Starfighter.sh     # Launch script
```

## Architecture

### State Machine
The game uses a simple state machine:
- `MENU` → `PLAYING` → `PAUSED` ↔ `PLAYING` → `GAME_OVER` → `MENU`

### Key Classes

1. **StarfighterGame** (`game.py`)
   - Top-level controller managing state, entities, and game loop
   - Handles spawning, collisions, scoring, and power-up management

2. **Player** (`entities.py`)
   - Ship with position, velocity, angle, and invincibility state
   - Manages active power-ups and firing cooldowns

3. **Enemy Types** (`enemies.py`)
   - Base enemy class with type-specific behaviors
   - Tier-based spawning system

4. **InputHandler** (`input.py`)
   - Translates keyboard/joystick input to logical actions
   - Supports both keyboard and gamepad controls

5. **Starfield** (`visual.py`)
   - Background particle system for visual depth

### Display System
- Renders to a **logical surface** (640 × 480)
- Scales to actual display with aspect ratio preservation
- Supports integer scaling for pixel-perfect rendering
- Letterboxing for non-matching aspect ratios

## How to Run

```bash
# From the repository root:
pip install pygame

# Run the game:
python -m maxbloks.starfighter.main
```

Or use the provided script:
```bash
./Starfighter.sh
```

## Controls

### Keyboard
| Key | Action |
|-----|--------|
| ← Arrow | Rotate left |
| → Arrow | Rotate right |
| ↑ Arrow | Thrust |
| Space | Fire |
| Escape | Pause |

### Gamepad
| Button | Action |
|--------|--------|
| D-pad/Stick | Rotate/Thrust |
| A/B | Fire |
| Start/Select | Pause |

## Configuration

Key settings in `settings.py`:
- `LOGICAL_WIDTH`, `LOGICAL_HEIGHT` - Internal resolution (640×480)
- `FULLSCREEN` - Enable/disable fullscreen mode
- `INTEGER_SCALING` - Use integer scaling for pixel-perfect rendering
- `TARGET_FPS` - Target frame rate (default: 60)

### Difficulty Tuning
- `TIER_THRESHOLDS` - Time boundaries for difficulty tiers
- `TIER_MAX_ENEMIES` - Maximum enemies per tier
- Enemy-specific constants (speed, HP, score, drop chance)

## Known Limitations vs. Web Version
- **Glow rendering**: Approximated with layered alpha circles (no shader-based shadowBlur)
- **Font**: Uses system `Courier New` instead of web's Share Tech Mono
- **Touch controls**: Not implemented (gamepad/keyboard only)
- **Sound**: No audio (web version is also silent)

## Development Notes

### Testing
```bash
python -m unittest discover -s tests
```

### Adding New Enemy Types
1. Define constants in `settings.py`
2. Create enemy class in `enemies.py`
3. Add to `available_types` and spawn logic
4. Add drawing logic in `visual.py`

### Adding New Power-ups
1. Define duration in `POWERUP_DURATION` (settings.py)
2. Add color to `COLORS` dictionary
3. Implement effect in `Player` class
4. Add to `_POWERUP_DEFS` in `game.py`

## License
GPL-3.0-or-later