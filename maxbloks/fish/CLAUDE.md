# Fish Feeding Frenzy

## Overview
Fish Feeding Frenzy is an arcade-style survival game where you play as a fish in an underwater world. Eat smaller fish to grow, avoid the predator shark until you're big enough to challenge it, and dominate the ocean. The game features growth mechanics, progressive difficulty, and AI-controlled predator behavior.

## Purpose and Main Features

### Gameplay
- **Growth Mechanic**: Start small and grow by eating fish smaller than you
- **Progressive Difficulty**: Face increasingly challenging scenarios as you level up
- **Strategic Survival**: Avoid the shark while building your size
- **Multiple Levels**: Advance through 3 levels as you grow larger
- **Win Condition**: Grow larger than the shark and eat it to win

### Level System
| Level | Size Requirement | Description |
|-------|------------------|-------------|
| 1 | Starting | Initial size (size < 20) |
| 2 | size ≥ 20 | Medium fish |
| 3 | size ≥ 40 | Large predator |

### Visual Features
- **Animated Bubbles**: Dynamic underwater atmosphere
- **Colorful Fish**: Various fish species with different colors and sizes
- **Smooth Movement**: Fluid animations for all entities
- **Sound Effects**: Eat, level-up, and game-over sounds (with fallback generation)

## Dependencies

### External
- Python 3.7+
- pygame 2.0+

### Internal (from maxbloks)
- `maxbloks.fish.compat_sdl` - SDL display initialization (symlink to `../common/compat_sdl.py`)

## File Structure

```
fish/
├── __init__.py           # Package marker
├── main.py               # Entry point
├── fish_game.py          # Main game class with game loop
├── entities.py           # Fish, PlayerFish, Shark, Bubble entities
├── game_framework.py     # Base game framework with input handling
├── utils.py              # Utility functions and constants
├── compat_sdl.py         # SDL compatibility layer (symlink)
├── BUILD                 # Bazel build configuration
├── README.md             # Detailed documentation
├── game.json             # Game metadata
├── version.json          # Version information
├── Fish.png              # Game icon (large)
├── Fish_small.png        # Game icon (small)
├── Fish.sh               # Launch script
├── eat.wav               # Eat sound effect
├── game_over.wav         # Game over sound effect
├── level_up.wav          # Level up sound effect
└── tests/                # Unit tests
    └── test_fish_game.py
```

## Architecture

### Game States
- **Playing**: Main gameplay
- **Game Over**: Shark caught the player
- **Won**: Player ate the shark

### Key Classes

1. **FishGame** (`fish_game.py`)
   - Main game class inheriting from GameFramework
   - Manages game state, entities, collisions
   - Handles scoring and level progression

2. **PlayerFish** (`entities.py`)
   - Player-controlled fish
   - Grows when eating smaller fish
   - Smooth movement with boundary checking

3. **Fish** (`entities.py`)
   - NPC fish with random properties
   - Swim horizontally across screen
   - Various sizes and colors

4. **Shark** (`entities.py`)
   - AI-controlled predator
   - Tracks and pursues player
   - Starts larger than player

5. **Bubble** (`entities.py`)
   - Decorative particles
   - Float upward from bottom
   - Creates underwater atmosphere

6. **GameFramework** (`game_framework.py`)
   - Base class providing common game functionality
   - Input handling (keyboard and gamepad)
   - Display management and timing

### Entity Behavior

#### Fish Spawning
- Fish spawn from left and right sides
- Smaller fish (5-15) are more common (70% chance)
- Larger fish (16-30) appear less frequently
- Swim at random speeds between screen edges

#### Collision Detection
- **Player vs Fish**: 
  - Player size ≥ fish size: Player eats fish and grows
  - Player size < fish size: Fish passes by
- **Player vs Shark**:
  - Player size > shark size: Player wins
  - Player size ≤ shark size: Game over

### Growth System
- Growth proportional to eaten fish size
- Formula: `player.size += fish.size * 0.1`
- Visual feedback as fish grows

## How to Run

```bash
# From the repository root:
pip install pygame

# Run the game:
python -m maxbloks.fish.main
```

Or use the provided script:
```bash
./Fish.sh
```

## Controls

### Keyboard
| Key | Action |
|-----|--------|
| W / ↑ | Swim up |
| S / ↓ | Swim down |
| A / ← | Swim left |
| D / → | Swim right |
| R | Restart (after game over/win) |

### Gamepad
| Button | Action |
|--------|--------|
| D-pad | Swim direction |
| A | Restart (after game over/win) |

## Configuration

Key settings in `utils.py`:

### Screen Settings
```python
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
```

### Game Settings
```python
BUBBLE_SPAWN_RATE = 0.02   # Chance per frame
INITIAL_FISH_COUNT = 10    # Starting fish
MIN_FISH_SIZE = 5
MAX_FISH_SIZE = 30
```

### Colors
```python
BACKGROUND_COLOR = (30, 100, 150)  # Ocean blue
FISH_COLORS = [
    (255, 100, 100),  # Red
    (100, 255, 100),  # Green
    (100, 100, 255),  # Blue
    (255, 255, 100),  # Yellow
    # ... more colors
]
```

### Adding New Fish Colors
Edit `FISH_COLORS` in `utils.py`:
```python
FISH_COLORS = [
    (255, 100, 100),  # Red
    (255, 150, 0),    # Orange (new)
    (200, 100, 255),  # Purple (new)
]
```

## Sound System

The game supports both file-based and generated sounds:

### Sound Files
- `eat.wav` - Played when eating fish
- `game_over.wav` - Played on death
- `level_up.wav` - Played on level transition

### Fallback Generation
If sound files aren't available, the game generates sounds using:
- `generate_eat_sound()` - Short blip sound
- `generate_game_over_sound()` - Descending tone
- `generate_level_up_sound()` - Ascending arpeggio
- `create_beep(freq, duration)` - Basic beep fallback

## Development Notes

### Running Tests
```bash
python -m unittest discover -s maxbloks/fish/tests
```

### Modifying Difficulty
In `fish_game.py`:
```python
# Growth rate (0.1 = 10% of fish size)
self.player.grow(fish.size * 0.1)

# Level thresholds
if self.player.size >= 20 and self.level == 1:
    self.level = 2
elif self.player.size >= 40 and self.level == 2:
    self.level = 3
```

### Adding New Entity Types
1. Create entity class in `entities.py`
2. Add update/draw methods
3. Integrate with `FishGame` class
4. Add necessary constants to `utils.py`

## Troubleshooting

### No Sound
- Sound files are optional; game generates sounds automatically
- Check pygame mixer initialization
- Verify system audio is working

### Display Issues
- Game runs in fullscreen by default
- Modify `fullscreen=True` to `fullscreen=False` in `fish_game.py` for windowed mode

### Performance Issues
- Reduce frame rate: Change `fps=60` to `fps=30`
- Reduce fish count: Modify `INITIAL_FISH_COUNT`

## License
GPL-3.0-or-later