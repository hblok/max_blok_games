# Dog Rider - Motorbike Adventure

## Overview
Dog Rider is an exciting side-scrolling obstacle course game featuring a brave dog on his motorcycle. Navigate through challenging terrain, avoid dangerous rocks, use ramps to perform spectacular jumps, and clear all 75 obstacles to win. The game features physics-based movement, animated characters, and parallax scrolling backgrounds.

## Purpose and Main Features

### Gameplay
- **Physics-Based Movement**: Realistic motorcycle physics with gravity, momentum, and jump mechanics
- **Progressive Difficulty**: Game speed gradually increases as you progress
- **75 Obstacles**: Clear all obstacles to win the game
- **Ramp Mechanics**: Hit ramps to launch high into the air for extra distance

### Visual Features
- **Animated Dog Character**: Moving ears, tail, and tongue with dynamic animations
- **Detailed Motorcycle**: Rotating wheels, exhaust, and chrome details
- **Parallax Background**: Layered background with mountains, trees, and grass
- **Exhaust Particles**: Realistic exhaust smoke particles when riding

### Obstacle Types
| Type | Description | Effect |
|------|-------------|--------|
| Rock | Gray circular obstacles | Instant game over on collision |
| Ramp | Triangular launch ramps | Launches player into the air |

## Dependencies

### External
- Python 3.7+
- pygame 2.0+

### Internal (from maxbloks)
- `maxbloks.dogrider.compat_sdl` - SDL display initialization (symlink to `../common/compat_sdl.py`)

## File Structure

```
dogrider/
├── __init__.py           # Package marker
├── main.py               # Entry point
├── dog_rider_game.py     # Main game class with game loop
├── dog_rider.py          # DogRider player character class
├── obstacles.py          # Obstacle and ObstacleManager classes
├── background.py         # BackgroundManager for parallax scrolling
├── constants.py          # Game constants and configuration
├── game_framework.py     # Base game framework with input handling
├── compat_sdl.py         # SDL compatibility layer (symlink)
├── BUILD                 # Bazel build configuration
├── README.md             # Detailed documentation
├── game.json             # Game metadata
├── version.json          # Version information
├── Dogrider.png          # Game icon
├── DogRider.png          # Large icon
├── Dogrider.sh           # Launch script
└── tests/                # Unit tests
    ├── test_background.py
    ├── test_obstacles.py
    ├── test_constants.py
    ├── test_game_framework.py
    └── test_dog_rider.py
```

## Architecture

### Game States
- `start` - Title screen with instructions
- `playing` - Main gameplay
- `game_over` - Win/lose screen with final stats

### Key Classes

1. **DogRiderGame** (`dog_rider_game.py`)
   - Main game class inheriting from GameFramework
   - Manages game state, input handling, collisions
   - Implements win/lose conditions

2. **DogRider** (`dog_rider.py`)
   - Player character with physics-based movement
   - Handles ramp collisions, jumps, and animation
   - Manages exhaust particles

3. **ObstacleManager** (`obstacles.py`)
   - Manages spawning and despawning of rocks and ramps
   - Handles collision detection
   - Tracks progress toward 75 obstacles

4. **BackgroundManager** (`background.py`)
   - Multi-layer parallax scrolling background
   - Creates depth with mountains, trees, and ground layers

5. **GameFramework** (`game_framework.py`)
   - Base class providing common game functionality
   - Input handling (keyboard and gamepad)
   - Display management and timing

### Physics System

#### Movement Constants (from `constants.py`)
```python
GRAVITY = 0.8              # Downward acceleration
JUMP_POWER = -15           # Initial upward velocity
FORWARD_JUMP_BOOST = 4     # Forward momentum when jumping
GROUND_Y = 350             # Y position of ground
MAX_GAME_SPEED = 6.0       # Maximum scroll speed
SPEED_INCREASE_RATE = 0.0005  # Speed increase per frame
```

#### Ramp Physics
- Character follows ramp surface
- Launch power based on ramp height
- Character rotates to match ramp slope

## How to Run

```bash
# From the repository root:
pip install pygame

# Run the game:
python -m maxbloks.dogrider.main
```

Or use the provided script:
```bash
./Dogrider.sh
```

## Controls

### Keyboard
| Key | Action |
|-----|--------|
| ↑ / W | Steer up |
| ↓ / S | Steer down |
| ← / A | Steer left |
| → / D | Steer right |
| Space | Jump |
| ESC | Quit |

### Gamepad
| Button | Action |
|--------|--------|
| D-pad | Steering |
| A | Jump |
| B | Back to menu (game over screen) |
| Start | Start game (start screen) |

## Configuration

Key settings in `constants.py`:

### Screen Settings
```python
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
```

### Game Balance
```python
MAX_OBSTACLES = 75         # Total obstacles to win
GRAVITY = 0.8              # Fall speed
JUMP_POWER = -15           # Jump height
MAX_GAME_SPEED = 6.0       # Maximum scroll speed
```

### Difficulty Adjustment
For easier gameplay:
```python
MAX_OBSTACLES = 50         # Fewer obstacles
SPEED_INCREASE_RATE = 0.0002  # Slower speed increase
JUMP_POWER = -18           # Higher jumps
```

For harder gameplay:
```python
MAX_OBSTACLES = 100        # More obstacles
SPEED_INCREASE_RATE = 0.001  # Faster speed increase
JUMP_POWER = -12           # Lower jumps
```

## Scoring System
- Points based on game speed and time survived
- Base rate: 10 points × game speed per second
- Higher speed = more points but harder timing

## Development Notes

### Running Tests
```bash
python -m unittest discover -s maxbloks/dogrider/tests
```

### Adding New Obstacle Types
1. Add obstacle class in `obstacles.py`
2. Update `ObstacleManager` spawning logic
3. Add collision handling in `DogRider`
4. Update constants for new obstacle parameters

### Modifying Physics
Edit `constants.py` to adjust:
- Gravity strength
- Jump power
- Movement speeds
- Ground position

## Troubleshooting

### Character Moves Slowly
- Check `JOYSTICK_DEADZONE` in `constants.py`
- Increase deadzone for old/loose joysticks

### Can't Jump High Enough
- Increase `JUMP_POWER` (more negative = higher)
- Increase `FORWARD_JUMP_BOOST` for more distance

### Display Issues
- Game runs in fullscreen by default
- Modify `fullscreen=True` to `fullscreen=False` in `dog_rider_game.py`

## License
GPL-3.0-or-later