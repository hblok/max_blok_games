# Project Guidelines

## Python Style
- Prefer custom classes and data structures over dictionaries
- Use `pathlib` instead of `os.path`
- Import modules, not classes (`import module` then `module.Class`, not `from module import Class`)
- Keep methods minimal; factor out logical sections into sub-methods
- Avoid importing inside methods
- Keep classes small, preferably under 400 lines

## Testing
- Use `unittest`
- One `TestCase` class per module
- No docstrings on test methods
- No `main()` or `unittest.main()` in test modules
- Run tests after each significant change: `python -m unittest`
- Maintain >80% code coverage for math and core modules
- Use `setUp()` and `tearDown()` for test fixtures

## Documentation
- Docstrings for complex logic only
- Use single-line docstrings where appropriate
- Avoid verbose docstrings on simple methods
- Avoid docstrings on test methods

---

# Creating a New Game

This section provides comprehensive instructions for adding a new game to the maxbloks collection. Follow these steps to ensure your game integrates properly with the existing project structure and conventions.

## Overview

The maxbloks collection is designed for handheld gaming devices (Anbernic, R46H, etc.) and desktop platforms. Each game is an independent project under the `maxbloks/` directory, sharing common utilities for display initialization and following consistent architectural patterns.

## Step 1: Planning Your Game

Before writing code, consider the following:

### Game Requirements
- **Target Platform**: Handheld devices with gamepad controls (primary) and desktop with keyboard (secondary)
- **Resolution**: Design for 640×480 or 800×600 logical resolution with scaling support
- **Controls**: Must support both gamepad (D-pad, A/B/X/Y buttons) and keyboard input
- **Performance**: Target 60 FPS on limited hardware

### Choose Your Architecture Pattern

The collection supports two main architectural patterns:

| Pattern | Used By | Best For |
|---------|---------|----------|
| **GameFramework** | Dog Rider, Fish | Simple arcade games with linear progression |
| **Custom State Machine** | Starfighter | Complex games with multiple states and entities |
| **Component-Based UI** | Terminal | Applications with complex UI interactions |

## Step 2: Creating the File Structure

### Directory Template

Create a new directory under `maxbloks/` with the following structure:

```
maxbloks/yourgame/
├── __init__.py           # Package marker (minimal content)
├── main.py               # Entry point
├── game.py               # Main game class (or game_framework.py)
├── constants.py          # Game constants and configuration
├── entities.py           # Game entities (player, enemies, etc.)
├── utils.py              # Utility functions
├── compat_sdl.py         # Symlink to ../common/compat_sdl.py
├── BUILD                 # Bazel build configuration
├── README.md             # Game documentation
├── CLAUDE.md             # AI assistant documentation
├── game.json             # Game metadata
├── version.json          # Version information
├── YourGame.png          # Game screenshot/icon
├── YourGame.sh           # Launch script
└── tests/                # Unit tests
    └── test_game.py
```

### Creating the Symlink

Create the symlink to the common SDL compatibility module:

```bash
cd maxbloks/yourgame
ln -s ../common/compat_sdl.py compat_sdl.py
```

## Step 3: Essential Files

### `__init__.py`

Minimal package marker:

```python
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Your Game - Brief description."""
```

### `main.py` - Entry Point

Using the GameFramework pattern:

```python
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

from maxbloks.yourgame.game import YourGame


if __name__ == "__main__":
    game = YourGame(title="Your Game Name")
    game.run()
```

Using custom initialization:

```python
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import pygame
from maxbloks.yourgame.compat_sdl import init_display
from maxbloks.yourgame.game import YourGame
from maxbloks.yourgame.settings import LOGICAL_WIDTH, LOGICAL_HEIGHT, FULLSCREEN


def main():
    pygame.init()
    pygame.font.init()
    
    screen, info = init_display(
        fullscreen=FULLSCREEN,
        vsync=True,
        size=(LOGICAL_WIDTH, LOGICAL_HEIGHT),
    )
    
    pygame.display.set_caption("YOUR GAME")
    
    clock = pygame.time.Clock()
    game = YourGame()
    
    running = True
    while running:
        # Game loop implementation
        running = game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
```

### `constants.py` - Configuration

```python
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Game constants and configuration."""

# Screen settings
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
LOGICAL_WIDTH = 640
LOGICAL_HEIGHT = 480
FULLSCREEN = False
TARGET_FPS = 60

# Colors (RGB tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
# Add game-specific colors...

# Game settings
PLAYER_SPEED = 5.0
GRAVITY = 0.8
# Add game-specific constants...

# Input settings
JOYSTICK_DEADZONE = 0.2
```

### `game.json` - Metadata

```json
{
    "name": "Your Game",
    "description": "Brief description of your game",
    "author": "Your Name",
    "version": "0.1.0"
}
```

### `version.json`

```json
{
    "version": "0.1.0"
}
```

## Step 4: Implementing the Game Class

### Option A: Using GameFramework (Recommended for Simple Games)

Create `game_framework.py` or extend the existing pattern:

```python
import pygame
import sys


class GameFramework:
    """Base class for games with common functionality."""
    
    def __init__(self, screen, display_info, title="Game", fps=60):
        pygame.init()
        pygame.joystick.init()
        
        self.screen = screen
        self.screen_width = display_info["width"]
        self.screen_height = display_info["height"]
        self.FPS = fps
        
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        
        # Joystick setup
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        
        # Game state
        self.running = True
        self.game_over = False
        self.game_won = False
        
        # Input state
        self.movement_x = 0
        self.movement_y = 0
        self.shoot_button_pressed = False
        self.action_button_pressed = False
        self.restart_button_pressed = False
        
        # Common colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
    
    def handle_input(self):
        """Handle input from keyboard and gamepad."""
        # Reset frame-based inputs
        self.movement_x = 0
        self.movement_y = 0
        self.shoot_button_pressed = False
        self.action_button_pressed = False
        self.restart_button_pressed = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.shoot_button_pressed = True
                elif event.key == pygame.K_r:
                    self.restart_button_pressed = True
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button in [0, 1]:  # A/B buttons
                    self.shoot_button_pressed = True
        
        # Continuous movement input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.movement_x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.movement_x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.movement_y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.movement_y += 1
        
        # Joystick input
        if self.joystick:
            axis_x = self.joystick.get_axis(0)
            axis_y = self.joystick.get_axis(1)
            if abs(axis_x) > 0.1:
                self.movement_x += axis_x
            if abs(axis_y) > 0.1:
                self.movement_y += axis_y
    
    def update(self):
        """Override this method with game logic."""
        pass
    
    def draw(self):
        """Override this method with drawing code."""
        self.screen.fill(self.BLACK)
        pygame.display.flip()
    
    def draw_text(self, text, x, y, size=24, color=None, center=False):
        """Helper to draw text on screen."""
        if color is None:
            color = self.WHITE
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, (x, y))
    
    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)
        
        pygame.quit()
        sys.exit()
```

Your game class then extends this:

```python
# game.py
import pygame
from maxbloks.yourgame import compat_sdl
from maxbloks.yourgame.game_framework import GameFramework
from maxbloks.yourgame.entities import Player, Enemy
from maxbloks.yourgame.constants import *


class YourGame(GameFramework):
    def __init__(self, title="Your Game Name", fps=60):
        screen, display_info = compat_sdl.init_display(
            size=(SCREEN_WIDTH, SCREEN_HEIGHT),
            fullscreen=FULLSCREEN,
            vsync=True
        )
        super().__init__(screen, display_info, title, fps)
        self.init_game()
    
    def init_game(self):
        """Initialize game state and entities."""
        self.score = 0
        self.player = Player(self.screen_width // 2, self.screen_height // 2)
        self.enemies = []
    
    def handle_input(self):
        """Extend base input handling."""
        super().handle_input()
        
        # Handle game-specific input
        if self.game_over and self.restart_button_pressed:
            self.init_game()
    
    def update(self):
        """Update game state."""
        if self.game_over:
            return
        
        # Update entities
        self.player.update(self.movement_x, self.movement_y)
        
        # Check collisions, update score, etc.
    
    def draw(self):
        """Draw game elements."""
        self.screen.fill(BLACK)
        
        # Draw entities
        self.player.draw(self.screen)
        
        # Draw UI
        self.draw_text(f"Score: {self.score}", 10, 10, 24, self.WHITE)
        
        pygame.display.flip()
```

### Option B: Custom State Machine (For Complex Games)

For games with multiple states (menu, playing, paused, game over):

```python
# game.py
from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class YourGame:
    """Game with state machine architecture."""
    
    def __init__(self):
        self.state = GameState.MENU
        self.score = 0
        # Initialize entities...
    
    def update(self, input_state):
        """Update based on current state."""
        if self.state == GameState.MENU:
            self._update_menu(input_state)
        elif self.state == GameState.PLAYING:
            self._update_playing(input_state)
        elif self.state == GameState.PAUSED:
            self._update_paused(input_state)
        elif self.state == GameState.GAME_OVER:
            self._update_gameover(input_state)
    
    def _update_menu(self, input_state):
        if input_state.confirm:
            self.state = GameState.PLAYING
            self._reset_game()
    
    def _update_playing(self, input_state):
        # Game logic
        if input_state.pause:
            self.state = GameState.PAUSED
    
    # ... more state handlers
```

## Step 5: Creating Entities

### Basic Entity Template

```python
# entities.py
import pygame
import math


class Player:
    """Player entity with movement and rendering."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.size = 20
        self.color = (0, 255, 255)
    
    def update(self, movement_x, movement_y, screen_width, screen_height):
        """Update player position based on input."""
        self.x += movement_x * 5
        self.y += movement_y * 5
        
        # Boundary checking
        self.x = max(self.size, min(screen_width - self.size, self.x))
        self.y = max(self.size, min(screen_height - self.size, self.y))
    
    def draw(self, screen):
        """Render the player."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
    
    def collides_with(self, other):
        """Check collision with another entity."""
        distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        return distance < self.size + other.size


class Enemy:
    """Enemy entity with basic AI."""
    
    def __init__(self, x, y, size=15):
        self.x = x
        self.y = y
        self.size = size
        self.speed = 2.0
        self.color = (255, 0, 0)
    
    def update(self, player_x, player_y):
        """Move toward player."""
        dx = player_x - self.x
        dy = player_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
    
    def draw(self, screen):
        """Render the enemy."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
```

## Step 6: Testing

### Unit Test Template

Create `tests/test_game.py`:

```python
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from maxbloks.yourgame.entities import Player, Enemy
from maxbloks.yourgame import constants


class TestEntities(unittest.TestCase):
    
    def setUp(self):
        self.player = Player(100, 100)
        self.enemy = Enemy(200, 200)
    
    def tearDown(self):
        pass
    
    def test_player_initial_position(self):
        self.assertEqual(self.player.x, 100)
        self.assertEqual(self.player.y, 100)
    
    def test_player_movement(self):
        self.player.update(1, 0, 800, 600)  # Move right
        self.assertGreater(self.player.x, 100)
    
    def test_collision_detection(self):
        # Place enemy at same position as player
        self.enemy.x = 100
        self.enemy.y = 100
        self.assertTrue(self.player.collides_with(self.enemy))
    
    def test_no_collision(self):
        # Enemy is far away
        self.assertFalse(self.player.collides_with(self.enemy))


class TestConstants(unittest.TestCase):
    
    def test_screen_dimensions(self):
        self.assertGreater(constants.SCREEN_WIDTH, 0)
        self.assertGreater(constants.SCREEN_HEIGHT, 0)
    
    def test_colors_are_tuples(self):
        self.assertIsInstance(constants.WHITE, tuple)
        self.assertEqual(len(constants.WHITE), 3)
```

### Running Tests

```bash
# Run all tests for your game
python -m unittest discover -s maxbloks/yourgame/tests

# Run specific test file
python -m unittest maxbloks.yourgame.tests.test_game

# Run with verbose output
python -m unittest -v maxbloks.yourgame.tests.test_game
```

## Step 7: Build Configuration

### Bazel BUILD File

```python
# BUILD
load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "yourgame",
    srcs = [
        "__init__.py",
        "main.py",
        "game.py",
        "entities.py",
        "constants.py",
        "utils.py",
    ],
    deps = [
        "//maxbloks/common",
        "@pip//pygame",
    ],
    visibility = ["//visibility:public"],
)
```

### Launch Script (`YourGame.sh`)

```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 -m maxbloks.yourgame.main "$@"
```

Make it executable:
```bash
chmod +x YourGame.sh
```

## Step 8: Documentation

### README.md Template

```markdown
# Your Game Name

Brief description of your game.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

\`\`\`bash
pip install pygame
\`\`\`

## Running

\`\`\`bash
python -m maxbloks.yourgame.main
\`\`\`

## Controls

### Keyboard
| Key | Action |
|-----|--------|
| Arrow Keys | Move |
| Space | Action |

### Gamepad
| Button | Action |
|--------|--------|
| D-pad | Move |
| A | Action |

## License
GPL-3.0-or-later
```

### CLAUDE.md Template

Create a CLAUDE.md file following the same structure as the existing games (see maxbloks/starfighter/CLAUDE.md for a complete example). Include:

- Overview and purpose
- Main features
- Dependencies
- File structure
- Architecture
- How to run
- Controls
- Configuration
- Development notes

## Naming Conventions

### Directory and File Names
- Use lowercase with underscores: `your_game/`
- Main files: `main.py`, `game.py`, `entities.py`, `constants.py`, `utils.py`
- Test directory: `tests/`
- Test files: `test_*.py`

### Python Naming
- **Classes**: PascalCase (`PlayerShip`, `EnemySpawner`)
- **Functions/Methods**: snake_case (`update_position`, `check_collision`)
- **Constants**: UPPER_SNAKE_CASE (`SCREEN_WIDTH`, `MAX_SPEED`)
- **Private methods**: Prefix with underscore (`_internal_update`)

### Module Structure
- Import order: standard library → third-party → local modules
- Use absolute imports: `from maxbloks.yourgame.entities import Player`

## Best Practices

### Performance
- Pre-render static surfaces when possible
- Use sprite groups for many similar objects
- Avoid creating new objects in the game loop
- Use `pygame.Surface.convert()` for faster blitting

### Input Handling
- Always support both keyboard and gamepad
- Implement dead zones for analog sticks
- Distinguish between button press and button hold
- Normalize diagonal movement (multiply by 0.707)

### Display
- Use logical resolution with scaling
- Support both fullscreen and windowed modes
- Implement vsync for smooth rendering
- Test on target resolution (640×480 or 800×600)

### Code Organization
- Keep game logic separate from rendering
- Use composition over inheritance for entities
- Implement proper state management
- Handle cleanup on exit

## Checklist for New Games

Before submitting your game, verify:

- [ ] Directory follows naming conventions
- [ ] All required files present
- [ ] Symlink to `compat_sdl.py` created
- [ ] Game runs with `python -m maxbloks.yourgame.main`
- [ ] Both keyboard and gamepad controls work
- [ ] Unit tests pass (`python -m unittest discover`)
- [ ] README.md documentation complete
- [ ] CLAUDE.md documentation complete
- [ ] game.json and version.json present
- [ ] Launch script (`YourGame.sh`) works
- [ ] Code follows project style guidelines
- [ ] No hardcoded personal paths or credentials
- [ ] License headers on all source files

## Integration Testing

Test your game on target platforms:

```bash
# Test on desktop
python -m maxbloks.yourgame.main

# Test with different resolutions
# Modify constants.py and verify scaling works

# Test with gamepad
# Connect gamepad and verify all controls work

# Test fullscreen mode
# Set FULLSCREEN = True in constants.py
```

## Getting Help

- Review existing games for implementation patterns
- Check `maxbloks/common/CLAUDE.md` for display initialization details
- Consult the main project README for general guidelines