# Fish Feeding Frenzy

An engaging arcade-style survival game where you play as a fish in an underwater world. Eat smaller fish to grow, avoid the predator shark until you're big enough to challenge it, and dominate the ocean!

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-GPL--3.0--or--later-yellow.svg)

## Features

### 🎮 Addictive Gameplay
- **Growth Mechanic**: Start small and grow by eating fish smaller than you
- **Progressive Difficulty**: Face increasingly challenging scenarios as you level up
- **Strategic Survival**: Avoid the shark while building your size
- **Multiple Levels**: Advance through 3 levels as you grow larger

### 🦈 Shark Predator
- **Relentless Hunter**: The shark actively tracks and pursues you
- **Win Condition**: Grow larger than the shark to turn the tables
- **High Stakes**: One wrong move and it's game over!

### 🎨 Visual Effects
- **Animated Bubbles**: Dynamic underwater atmosphere
- **Colorful Fish**: Various fish species with different colors and sizes
- **Smooth Movement**: Fluid animations for all entities
- **Full Screen Support**: Immersive fullscreen experience

### 🔊 Sound Effects
- **Eat Sound**: Satisfying feedback when consuming fish
- **Level Up Sound**: Celebrate your growth milestones
- **Game Over Sound**: Dramatic ending when defeated
- **Generated Audio**: Works with or without external sound files

## Gameplay

### Objective
Start as a small fish and grow by eating smaller fish. Avoid the shark until you become large enough to eat it and win the game!

### Scoring
- **Points**: Earn points based on the size of fish you eat
- **Growth**: Your fish grows proportionally to the size of consumed fish
- **Levels**: 
  - **Level 1**: Starting size (size < 20)
  - **Level 2**: Medium fish (size ≥ 20)
  - **Level 3**: Large predator (size ≥ 40)

### Winning
Grow your fish to be larger than the shark, then collide with it to eat it and win!

### Losing
If the shark catches you while you're smaller, it's game over!

## Screenshots

```
╔═══════════════════════════════════════════════════════════╗
║  Score: 150    Size: 15    Level: 2                       ║
║                                                           ║
║        🐟      🐠                                        ║
║                                                           ║
║              🐡        🐟      🦈                         ║
║                    👆                                      ║
║                                                           ║
║        🐟           🐠                                    ║
║                                                           ║
║      ╭╮╭╮  (bubbles)                                     ║
║                                                           ║
║  WASD/Arrows: Move  Grow by eating smaller fish          ║
║  Avoid the shark until you're bigger!                    ║
╚═══════════════════════════════════════════════════════════╝
```

## Installation

### Prerequisites
- Python 3.7 or higher
- Pygame 2.0 or higher

### Install Dependencies

```bash
pip install pygame
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

### Running the Game

```bash
python main.py
```

Or use the provided script:

```bash
./Fish.sh
```

## Controls

### Keyboard Controls

| Key | Action |
|-----|--------|
| **W / Up Arrow** | Swim up |
| **S / Down Arrow** | Swim down |
| **A / Left Arrow** | Swim left |
| **D / Right Arrow** | Swim right |
| **R** | Restart game (after game over/win) |

### Gamepad Controls

| Button | Action |
|--------|--------|
| **D-pad** | Navigate (swim direction) |
| **A** | Restart game (after game over/win) |

## Game Mechanics

### Fish Spawning
- Fish spawn from left and right sides of the screen
- Smaller fish (5-15) are more common (70% chance)
- Larger fish (16-30) appear less frequently
- Fish swim at random speeds between screen edges

### Collision Detection
- **Player vs Fish**: 
  - If player size ≥ fish size: Player eats fish and grows
  - If player size < fish size: Fish passes by (can't eat)
- **Player vs Shark**:
  - If player size > shark size: Player wins!
  - If player size ≤ shark size: Game over!

### Growth System
- Growth is proportional to the size of eaten fish
- Formula: `player.size += fish.size * 0.1`
- Visual feedback: Your fish visibly grows as you eat

### Level System
- **Level 1**: Starting state (size < 20)
- **Level 2**: Medium fish (size ≥ 20) - Level up sound plays
- **Level 3**: Large predator (size ≥ 40) - Level up sound plays

### Shark AI
- The shark spawns on the right side of the screen
- Actively tracks and pursues the player
- Moves horizontally towards player's position
- Adjusts vertical position to intercept

## Project Structure

```
fish/
├── fish_game.py         # Main game class with game loop
├── entities.py          # Fish, PlayerFish, Shark, Bubble entities
├── game_framework.py    # Base game framework with input handling
├── utils.py             # Utility functions and constants
├── compat_sdl.py        # SDL compatibility layer (symlink)
├── main.py              # Entry point
├── game.json            # Game metadata
├── version.json         # Version information
├── Fish.sh              # Start script
├── requirements.txt     # Python dependencies
├── eat.wav              # Eat sound effect
├── game_over.wav        # Game over sound effect
├── level_up.wav         # Level up sound effect
├── Fish.png             # Game icon
├── Fish_small.png       # Small icon
└── tests/               # Test files
```

## Architecture

### Main Components

1. **FishGame** (`fish_game.py`)
   - Main game class inheriting from GameFramework
   - Manages game state, entities, and scoring
   - Handles collisions and level progression
   - Implements win/lose conditions

2. **Entities** (`entities.py`)
   - `PlayerFish`: The player's controllable fish
   - `Fish`: NPC fish with random properties
   - `Shark`: The predator AI
   - `Bubble`: Decorative underwater particles

3. **GameFramework** (`game_framework.py`)
   - Base class for game structure
   - Input handling (keyboard and gamepad)
   - Display management
   - Game loop and timing

4. **Utils** (`utils.py`)
   - Color constants
   - Fish color palettes
   - Sound generation functions
   - Game configuration

### Entity Classes

#### PlayerFish
- Controlled by player input
- Grows when eating smaller fish
- Starts at size 10
- Smooth movement with boundary checking

#### Fish
- Auto-moving NPCs
- Random size, color, speed, and spawn position
- Swim horizontally across screen
- Removed when off-screen

#### Shark
- AI-controlled predator
- Starts larger than player
- Tracks player position
- Moves horizontally towards player

#### Bubble
- Decorative particles
- Spawn randomly from bottom
- Float upward at varying speeds
- Removed when off-screen

## Customization

### Modifying Game Settings

Edit `utils.py` to customize:

```python
# Screen size
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Game settings
BUBBLE_SPAWN_RATE = 0.02  # Chance per frame
INITIAL_FISH_COUNT = 10
MIN_FISH_SIZE = 5
MAX_FISH_SIZE = 30

# Colors
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

```python
FISH_COLORS = [
    (255, 100, 100),  # Red
    (100, 255, 100),  # Green
    # Add your custom colors here:
    (255, 150, 0),    # Orange
    (200, 100, 255),  # Purple
    (0, 255, 255),    # Cyan
]
```

### Adjusting Difficulty

In `fish_game.py`, modify:

```python
# Growth rate (0.1 = 10% of fish size)
self.player.grow(fish.size * 0.1)

# Shark size (make it harder or easier)
self.shark = Shark(self.screen_width + 100, random.randint(50, self.screen_height - 50))
# Modify Shark class initial size

# Level thresholds
if self.player.size >= 20 and self.level == 1:
    self.level = 2
elif self.player.size >= 40 and self.level == 2:
    self.level = 3
```

## Troubleshooting

### Game Won't Start
- Ensure Python 3.7+ is installed
- Install pygame: `pip install pygame`
- Check that all files are in the correct directory

### No Sound
- Sound files are optional; the game generates sounds automatically
- Ensure your system audio is working
- Check pygame mixer initialization

### Display Issues
- The game runs in fullscreen by default
- Modify `fullscreen=True` to `fullscreen=False` in `fish_game.py` for windowed mode
- Adjust screen resolution in `compat_sdl.init_display()`

### Performance Issues
- Reduce frame rate: Change `fps=60` to `fps=30` in `FishGame.__init__()`
- Reduce number of fish: Modify `INITIAL_FISH_COUNT` and spawn rates

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Building for Distribution

```bash
# See BUILD file for build instructions
cat BUILD
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under GPL-3.0-or-later - see the LICENSE file for details.

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Inspired by classic arcade fish games
- Part of the max_blok_games collection for handheld gaming devices

## Version

Current version: See `version.json` for the latest version information.

---

Enjoy the underwater adventure! 🐠🦈