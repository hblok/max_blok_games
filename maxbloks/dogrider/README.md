# Dog Rider - Motorbike Adventure

An exciting side-scrolling obstacle course game featuring a brave dog on his motorcycle! Navigate through challenging terrain, avoid dangerous rocks, use ramps to perform spectacular jumps, and clear all obstacles to become the ultimate rider!

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-GPL--3.0--or--later-yellow.svg)

## Features

### 🏍️ Thrilling Gameplay
- **Physics-Based Movement**: Realistic motorcycle physics with gravity, momentum, and jump mechanics
- **Smooth Controls**: Responsive joystick/keyboard controls for precise movement
- **Progressive Difficulty**: Game speed gradually increases as you progress
- **75 Obstacles**: Clear all obstacles to win the game!

### 🎮 Controls & Mechanics
- **Jump**: Press SPACE or A button to jump over rocks
- **Steering**: Use arrow keys or joystick to move left/right
- **Ramps**: Hit ramps to launch high into the air for extra distance
- **Forward Boost**: Jumping while moving gives you extra forward momentum

### 🐕 Animated Character
- **Detailed Dog Rider**: Fully animated dog character with moving ears, tail, and tongue
- **Motorcycle Rendering**: Detailed motorcycle with rotating wheels, exhaust, and chrome details
- **Dynamic Animations**: Tail wagging increases when jumping, ears flap in the wind
- **Exhaust Particles**: Realistic exhaust smoke particles when riding

### 🌄 Visual Effects
- **Parallax Background**: Layered background with mountains, trees, and grass
- **Ground Texture**: Detailed ground with grass and dirt
- **Obstacle Varieties**: 
  - **Rocks**: Gray obstacles you must jump over or avoid
  - **Ramps**: Triangular ramps that launch you high into the air
- **Wheel Rotation**: Wheels spin realistically as you ride

### 🏆 Game States
- **Start Screen**: Title screen with instructions and controls
- **Playing**: Main gameplay with score and progress tracking
- **Game Over**: Win/lose screen with final stats

## Gameplay

### Objective
Control a dog on a motorcycle and navigate through a challenging obstacle course. Jump over rocks, use ramps to launch yourself, and clear all 75 obstacles to win!

### Scoring
- **Points**: Earn points based on game speed and time survived
- **Speed Bonus**: Faster gameplay = more points per second
- **Progress**: Track obstacles cleared out of 75 total

### Winning
Successfully clear all 75 obstacles without crashing into any rocks!

### Losing
Crash into a rock and it's game over!

### Obstacles

#### Rocks
- **Danger Level**: High - instant game over if hit
- **Strategy**: Jump over them or avoid by timing your jumps carefully
- **Appearance**: Gray circular obstacles on the ground

#### Ramps
- **Danger Level**: None - helpful obstacles
- **Strategy**: Hit ramps at full speed for maximum airtime and distance
- **Physics**: Follows the ramp surface and launches you at the end
- **Bonus**: Gives forward momentum boost and extra height

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
./Dogrider.sh
```

## Controls

### Keyboard Controls

| Key | Action |
|-----|--------|
| **↑ / W** | Steer up (move character up visually) |
| **↓ / S** | Steer down |
| **← / A** | Steer left |
| **→ / D** | Steer right |
| **SPACE** | Jump |
| **ESC** | Quit game |

### Gamepad Controls

| Button | Action |
|--------|--------|
| **D-pad** | Steering (up/down/left/right) |
| **A** | Jump |
| **B** | Back to menu (on game over screen) |
| **START** | Start game (on start screen) |

## Game Mechanics

### Movement Physics

#### Horizontal Movement
- **Left/Right**: Smooth acceleration with momentum
- **Max Speed**: 3 units/frame horizontally
- **Deceleration**: Gradual slowdown when not steering
- **Rotation**: Character tilts when turning

#### Vertical Movement
- **Gravity**: Constant downward acceleration (0.8 units/frame²)
- **Jump Power**: Initial upward velocity of -15 units/frame
- **Forward Boost**: Jumping adds +4 units/frame forward momentum

#### Ground Interaction
- **Ground Collision**: Character lands on ground at Y = 350
- **Ramp Physics**: Follows ramp surface and launches at end
- **Ramp Angle**: Character rotates to match ramp slope
- **Launch Power**: Depends on ramp height (taller = higher launch)

### Obstacle System

#### Spawning
- **Random Delays**: Obstacles spawn every 120-480 frames (varies with speed)
- **Speed Scaling**: Faster game = more frequent obstacles
- **Type Distribution**: 30% ramps, 70% rocks
- **Total Count**: Maximum 75 obstacles per game

#### Collision Detection
- **Rocks**: Collision causes instant game over
- **Ramps**: No collision penalty, enables jumping
- **Hitbox**: Rectangle-based collision detection

### Difficulty Progression

#### Speed Increase
- **Starting Speed**: 2.0 units/frame
- **Max Speed**: 6.0 units/frame
- **Rate**: +0.0005 units/frame per frame
- **Effect**: Faster game = more points but harder timing

#### Obstacle Frequency
- **Early Game**: Longer gaps between obstacles
- **Late Game**: Shorter gaps as speed increases
- **Formula**: Delay decreases as game speed increases

### Score System

#### Points Calculation
- **Base Rate**: 10 points × game speed per second
- **Speed Bonus**: Higher speed = more points
- **Example**: 
  - Speed 2.0 = 20 points/second
  - Speed 4.0 = 40 points/second
  - Speed 6.0 = 60 points/second

## Project Structure

```
dogrider/
├── dog_rider_game.py    # Main game class with game loop
├── dog_rider.py         # DogRider player character class
├── obstacles.py         # Obstacle and ObstacleManager classes
├── background.py        # BackgroundManager for parallax scrolling
├── constants.py         # Game constants and configuration
├── game_framework.py    # Base game framework with input handling
├── compat_sdl.py        # SDL compatibility layer (symlink)
├── main.py              # Entry point
├── game.json            # Game metadata
├── version.json         # Version information
├── Dogrider.sh          # Start script
├── Dogrider.png         # Game icon
├── DogRider.png         # Large icon
└── tests/               # Test files
```

## Architecture

### Main Components

1. **DogRiderGame** (`dog_rider_game.py`)
   - Main game class inheriting from GameFramework
   - Manages game state (start, playing, game_over)
   - Handles input, updates, and drawing
   - Implements win/lose conditions

2. **DogRider** (`dog_rider.py`)
   - Player character (dog on motorcycle)
   - Physics-based movement with gravity and momentum
   - Handles ramp collisions and jumps
   - Animated rendering with particles

3. **ObstacleManager** (`obstacles.py`)
   - Manages rocks and ramps
   - Handles spawning and despawning
   - Collision detection with player
   - Tracks progress and completion

4. **BackgroundManager** (`background.py`)
   - Parallax scrolling background
   - Multiple layers (mountains, trees, ground)
   - Creates depth and atmosphere

5. **GameFramework** (`game_framework.py`)
   - Base class for game structure
   - Input handling (keyboard and gamepad)
   - Display management
   - Game loop and timing

### Physics System

#### Gravity
```python
GRAVITY = 0.8  # Downward acceleration
velocity_y += GRAVITY
```

#### Jump Physics
```python
JUMP_POWER = -15  # Initial upward velocity
FORWARD_JUMP_BOOST = 4  # Forward momentum boost
velocity_y = JUMP_POWER
velocity_x += FORWARD_JUMP_BOOST
```

#### Ramp Launch
```python
# Launch power based on ramp height
launch_power = ramp.height / 20
velocity_y = -12 - launch_power
velocity_x += 3 + launch_power
```

## Customization

### Modifying Game Settings

Edit `constants.py` to customize:

```python
# Screen size
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Physics
GRAVITY = 0.8
JUMP_POWER = -15
FORWARD_JUMP_BOOST = 4

# Game balance
MAX_GAME_SPEED = 6.0
SPEED_INCREASE_RATE = 0.0005
MAX_OBSTACLES = 75

# Input sensitivity
JOYSTICK_DEADZONE = 0.2
```

### Adjusting Difficulty

#### Easier Game
```python
MAX_OBSTACLES = 50  # Fewer obstacles
SPEED_INCREASE_RATE = 0.0002  # Slower speed increase
JUMP_POWER = -18  # Higher jumps
```

#### Harder Game
```python
MAX_OBSTACLES = 100  # More obstacles
SPEED_INCREASE_RATE = 0.001  # Faster speed increase
JUMP_POWER = -12  # Lower jumps
```

### Modifying Colors

Edit `constants.py`:

```python
# Background colors
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)
MOUNTAIN_BLUE = (70, 130, 180)

# Character colors
BROWN = (139, 69, 19)
LIGHT_BROWN = (210, 180, 140)
```

### Adjusting Obstacle Spawning

In `obstacles.py`, modify:

```python
# Obstacle type distribution
obstacle_type = 'ramp' if random.random() < 0.3 else 'rock'
# Change 0.3 to adjust ramp frequency

# Spawn delays
min_delay = max(120, 300 - int(game_speed * 20))
max_delay = max(180, 480 - int(game_speed * 30))
# Adjust these formulas for different spacing
```

## Troubleshooting

### Game Won't Start
- Ensure Python 3.7+ is installed
- Install pygame: `pip install pygame`
- Check that all files are in the correct directory
- Verify `compat_sdl.py` symlink exists

### Character Moves Slowly
- Check joystick deadzone in `constants.py`
- Increase `JOYSTICK_DEADZONE` if using old/loose joysticks
- Decrease for more sensitive controls

### Can't Jump High Enough
- Increase `JUMP_POWER` in `constants.py`
- Increase `FORWARD_JUMP_BOOST` for more distance
- Ensure you're not in the air already when jumping

### Too Difficult
- Reduce `MAX_OBSTACLES`
- Decrease `SPEED_INCREASE_RATE`
- Increase `JUMP_POWER`
- Adjust obstacle spawn delays in `obstacles.py`

### Display Issues
- The game runs in fullscreen by default
- Modify `fullscreen=True` to `fullscreen=False` in `dog_rider_game.py`
- Adjust screen resolution in `compat_sdl.init_display()`

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

### Code Style

The project follows these conventions:
- PEP 8 style guide
- Docstrings for all classes and methods
- Type hints where appropriate
- Clear variable naming

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under GPL-3.0-or-later - see the LICENSE file for details.

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Inspired by classic side-scrolling obstacle games
- Part of the max_blok_games collection for handheld gaming devices

## Version

Current version: See `version.json` for the latest version information.

---

Ready to ride? 🏍️🐕 Jump in and start your motorbike adventure!