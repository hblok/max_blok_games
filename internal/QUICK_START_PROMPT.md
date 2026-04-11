Maxbloks Game Development Quick Reference

When creating a new game for the maxbloks collection, follow these guidelines:

Project Structure

maxbloks/yourgame/
├── __init__.py           # Package marker
├── main.py               # Entry point
├── game.py               # Main game class
├── constants.py          # All configuration constants
├── entities.py           # Player, enemies, and game objects
├── utils.py              # Helper functions
├── compat_sdl.py         # Symlink to ../common/compat_sdl.py
├── tests/                # Unit tests
├── BUILD                 # Bazel build config
├── README.md             # Documentation
├── CLAUDE.md             # AI assistant docs
├── game.json             # Metadata
└── version.json          # Version info

Architecture Patterns

Option A: GameFramework (Simple Games)
- Extend GameFramework base class
- Override: handle_input(), update(), draw()
- Use self.movement_x/y for input, self.draw_text() for UI

Option B: State Machine (Complex Games)
- States: MENU → PLAYING ↔ PAUSED → GAME_OVER
- Separate update/draw methods per state
- Use enum.Enum for state definitions

Python Style Guidelines
- Imports: import module then module.Class (not from module import Class)
- Paths: Use pathlib, not os.path
- Classes: Prefer custom classes over dictionaries; keep under 400 lines
- Methods: Keep minimal; factor out logical sections
- Naming: PascalCase for classes, snake_case for functions, UPPER_SNAKE_CASE for constants

Key Requirements
- Dual Input Support: Must work with both keyboard AND gamepad
- Display: Use compat_sdl.init_display() for SDL bootstrap; support fullscreen/windowed
- Resolution: Design for 640×480 or 800×600 logical resolution with scaling
- Performance: Target 60 FPS; pre-render static surfaces; avoid object creation in game loop
- Testing: Use unittest; one TestCase per module; maintain >80% coverage for core modules

Common Patterns

Display Initialization

from maxbloks.yourgame.compat_sdl import init_display
screen, info = init_display(size=(640, 480), fullscreen=True, vsync=True)

Game Loop

def run(self):
    while self.running:
        self.handle_input()
        self.update()
        self.draw()
        self.clock.tick(60)

Input Handling
- Keyboard: Arrow keys + WASD for movement, Space for action
- Gamepad: D-pad/Left stick for movement, A/B buttons for action
- Normalize diagonal movement (multiply by 0.707)
- Implement joystick deadzone (0.2 typical)

Documentation Requirements
- README.md: Installation, controls, features
- CLAUDE.md: Architecture, dependencies, configuration, development notes
- All files need GPL-3.0-or-later license headers

Pre-Submit Checklist
-  Runs via python -m maxbloks.yourgame.main
-  Both keyboard and gamepad work
-  Tests pass: python -m unittest discover
-  Documentation complete (README.md, CLAUDE.md)
-  game.json and version.json present
-  Symlink to compat_sdl.py created
-  License headers on all source files
