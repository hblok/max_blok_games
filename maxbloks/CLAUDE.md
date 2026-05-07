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
- Run tests after each significant change:
  ```bash
  # Full project
  python -m unittest discover -s maxbloks

  # Single game
  python -m unittest discover -s maxbloks/<game>/tests -v
  ```
- Maintain >80% code coverage for math and core modules
- Use `setUp()` and `tearDown()` for test fixtures

## Documentation
- Docstrings for complex logic only
- Use single-line docstrings where appropriate
- Avoid verbose docstrings on simple methods
- Avoid docstrings on test methods

## Security Linting
Run [bandit](https://bandit.readthedocs.io/) before submitting:
```bash
bandit -c bandit.yaml -r maxbloks/
```

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

The collection supports three main architectural patterns:

| Pattern | Used By | Best For |
|---------|---------|----------|
| **GameFramework** | Dog Rider, Fish | Simple arcade games with linear progression |
| **Custom State Machine** | MathWheel, SpellWheels, Starfighter | Games with multiple distinct states (menu, playing, paused, game over) |
| **Component-Based UI** | Terminal | Applications with complex, multi-stage UI interactions |

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
└── tests/
    ├── __init__.py
    └── test_game.py
```

### Creating the Symlink

```bash
cd maxbloks/yourgame
ln -s ../common/compat_sdl.py compat_sdl.py
```

## Step 3: Essential Files

### `__init__.py`

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

from maxbloks.yourgame import game


if __name__ == "__main__":
    g = game.YourGame(title="Your Game Name")
    g.run()
```

Using custom initialization:

```python
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import pygame
from maxbloks.yourgame import compat_sdl, game, settings


def main():
    pygame.init()
    pygame.font.init()

    screen, info = compat_sdl.init_display(
        fullscreen=settings.FULLSCREEN,
        vsync=True,
        size=(settings.LOGICAL_WIDTH, settings.LOGICAL_HEIGHT),
    )

    pygame.display.set_caption("YOUR GAME")

    clock = pygame.time.Clock()
    g = game.YourGame()

    running = True
    while running:
        running = g.update()
        g.draw(screen)
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

# Game settings
PLAYER_SPEED = 5.0
GRAVITY = 0.8

# Input settings
JOYSTICK_DEADZONE = 0.2
```

### `game.json` - Metadata

```json
{
    "name": "Your Game",
    "description": "Brief description of your game",
    "author": "Your Name",
    "version": "0.0.1"
}
```

### `version.json`

```json
{
    "version": "0.0.1"
}
```

## Step 4: Implementing the Game Class

### Option A: Using GameFramework (Recommended for Simple Games)

Use `maxbloks/fish/game_framework.py` as the canonical starting point — copy it into your game directory and extend the base class:

```python
# game.py
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

from maxbloks.yourgame import compat_sdl, constants, entities
from maxbloks.yourgame import game_framework


class YourGame(game_framework.GameFramework):
    def __init__(self, title="Your Game Name", fps=60):
        screen, display_info = compat_sdl.init_display(
            size=(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
            fullscreen=constants.FULLSCREEN,
            vsync=True
        )
        super().__init__(screen, display_info, title, fps)
        self._init_game()

    def _init_game(self):
        self.score = 0
        self.player = entities.Player(self.screen_width // 2, self.screen_height // 2)
        self.enemies = []

    def handle_input(self):
        super().handle_input()
        if self.game_over and self.restart_button_pressed:
            self._init_game()

    def update(self):
        if self.game_over:
            return
        self.player.update(self.movement_x, self.movement_y)

    def draw(self):
        self.screen.fill(constants.BLACK)
        self.player.draw(self.screen)
        self.draw_text(f"Score: {self.score}", 10, 10, 24, self.WHITE)
        pygame.display.flip()
```

### Option B: Custom State Machine (For Complex Games)

```python
# game.py
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import enum


class GameState(enum.Enum):
    MENU = enum.auto()
    PLAYING = enum.auto()
    PAUSED = enum.auto()
    GAME_OVER = enum.auto()


class YourGame:
    """Game with state machine architecture."""

    def __init__(self):
        self.state = GameState.MENU
        self.score = 0

    def update(self, input_state):
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
        if input_state.pause:
            self.state = GameState.PAUSED

    # ... more state handlers
```

See `maxbloks/starfighter/game.py` and `maxbloks/spellwheels/game.py` for full examples.

## Step 5: Creating Entities

```python
# entities.py
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import math
import pygame


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
        self.x += movement_x * 5
        self.y += movement_y * 5
        self.x = max(self.size, min(screen_width - self.size, self.x))
        self.y = max(self.size, min(screen_height - self.size, self.y))

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

    def collides_with(self, other):
        distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        return distance < self.size + other.size
```

## Step 6: Testing

Create `tests/__init__.py` (empty) and `tests/test_game.py`:

```python
# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from maxbloks.yourgame import entities, constants


class TestEntities(unittest.TestCase):

    def setUp(self):
        self.player = entities.Player(100, 100)

    def test_player_initial_position(self):
        self.assertEqual(self.player.x, 100)
        self.assertEqual(self.player.y, 100)

    def test_player_movement(self):
        self.player.update(1, 0, 800, 600)
        self.assertGreater(self.player.x, 100)


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
python -m unittest discover -s maxbloks/yourgame/tests
python -m unittest discover -s maxbloks/yourgame/tests -v
python -m unittest discover -s maxbloks
```

## Step 7: Build Configuration

### Bazel BUILD File

```python
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

```bash
chmod +x YourGame.sh
```

## Step 8: Documentation

### CLAUDE.md

Create a CLAUDE.md following the same structure as existing games. Mandatory sections:

- [ ] **Overview** — what the game is and who it targets
- [ ] **Purpose and Main Features** — gameplay mechanics
- [ ] **Dependencies** — external and internal
- [ ] **File Structure** — directory tree
- [ ] **Architecture** — state machine or class hierarchy with ASCII diagram
- [ ] **How to Run** — exact commands
- [ ] **Controls** — keyboard and gamepad tables
- [ ] **Configuration** — key constants and how to tune them
- [ ] **Development Notes** — how to run tests, how to extend (add enemy types, etc.)
- [ ] **Invariants / What NOT to Change** — constraints that must be preserved

See `maxbloks/starfighter/CLAUDE.md` for a full example.

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
- Import modules, not classes: `from maxbloks.yourgame import entities` then `entities.Player()`

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
- Use logical resolution with scaling via `compat_sdl.init_display()`
- Support both fullscreen and windowed modes
- Implement vsync for smooth rendering
- Test on target resolution (640×480 or 800×600)

### Code Organization
- Keep game logic separate from rendering
- Use composition over inheritance for entities
- Implement proper state management
- Handle cleanup on exit

## Checklist for New Games

- [ ] Directory follows naming conventions
- [ ] All required files present (see directory template above)
- [ ] Symlink to `compat_sdl.py` created (must be a symlink, not a copy)
- [ ] `tests/__init__.py` present (required for test discovery)
- [ ] Game runs with `python -m maxbloks.yourgame.main`
- [ ] Both keyboard and gamepad controls work
- [ ] Unit tests pass (`python -m unittest discover -s maxbloks/yourgame/tests`)
- [ ] Full project tests still pass (`python -m unittest discover -s maxbloks`)
- [ ] Security lint passes (`bandit -c bandit.yaml -r maxbloks/yourgame/`)
- [ ] README.md documentation complete
- [ ] CLAUDE.md documentation complete (all mandatory sections present)
- [ ] game.json and version.json present
- [ ] Launch script (`YourGame.sh`) works and is executable
- [ ] Code follows project style guidelines (module imports, not class imports)
- [ ] License headers (`# SPDX-License-Identifier: GPL-3.0-or-later`) on all Python source files
- [ ] No hardcoded personal paths or credentials
- [ ] Bazel BUILD file lists all `.py` srcs
- [ ] Version bumped with `python tools/increment_version.py yourgame` before tagging a release

## Integration Testing

```bash
python -m maxbloks.yourgame.main
# Test with different resolutions — modify constants.py and verify scaling works
# Connect gamepad and verify all controls work
# Set FULLSCREEN = True in constants.py and test fullscreen mode
```

## Getting Help

- Review existing games for implementation patterns
- Check `maxbloks/common/CLAUDE.md` for display initialization details
- Consult the main project README for general guidelines
