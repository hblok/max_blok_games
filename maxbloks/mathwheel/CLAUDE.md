# MathWheel

## Overview
MathWheel is an educational math practice game designed for children around age 6–7. Players solve arithmetic equations by selecting answers on a scrollable number wheel. The game focuses on addition and subtraction with optional multiplication and division, using progressive difficulty and encouraging feedback to maintain a positive learning experience.

## Purpose and Main Features

### Gameplay
- **Equation Solving**: Equations shown as `A + B = ?`, `? + B = C`, `A + ? = C` and similar forms for all operations
- **Number Wheel Input**: Scroll a vertical number picker to select the answer, then press a submit icon button
- **Progressive Difficulty**: Starts with easy problems (sums ≤ 10), gradually introduces harder ones
- **Endless Practice Mode**: Continuous question flow; structured for future rounds, timers, or mini-goals
- **Mixed Difficulty**: Easier questions are periodically mixed in to maintain confidence

### Operations
| Operation       | Default | Notes                           |
|-----------------|---------|----------------------------------|
| Addition (+)    | ON      | Primary learning focus           |
| Subtraction (−) | ON      | No negative results              |
| Multiplication (×) | OFF | Optional, toggle in settings     |
| Division (÷)   | OFF     | Optional, no fractional results  |

### Difficulty Levels
| Level  | Max Number | Max Result | Missing Positions     |
|--------|------------|------------|-----------------------|
| Easy   | 10         | 10         | First, Last           |
| Medium | 9          | 18         | First, Middle, Last   |
| Hard   | 20         | 30         | First, Middle, Last   |

### Reward System
- Star-based scoring: 2 stars for first-try correct, 1 star after retry
- No penalty for wrong answers
- Visual star animations and encouraging feedback
- Skip option available without punishment

## Dependencies

### External
- Python 3.7+
- pygame-ce 2.0+

### Internal (from maxbloks)
- `maxbloks.mathwheel.compat_sdl` — SDL display initialization (symlink to `../common/compat_sdl.py`)

## File Structure

```
mathwheel/
├── __init__.py           # Package marker
├── main.py               # Entry point
├── game.py               # MathWheelGame: state machine, rendering, input
├── game_framework.py     # Base framework with input handling
├── constants.py          # All constants: colors, layout, difficulty, scoring
├── utils.py              # Question generation, DifficultyManager, ScoreTracker
├── entities.py           # NumberWheel, FeedbackEffect, StarAnimation, UIFocus
├── compat_sdl.py         # SDL compatibility layer (symlink)
├── BUILD                 # Bazel build configuration
├── README.md             # User-facing documentation
├── CLAUDE.md             # This file — architecture & development notes
├── game.json             # Game metadata
├── version.json          # Version information
├── MathWheel.sh          # Launch script
└── tests/
    ├── __init__.py
    ├── BUILD
    ├── test_constants.py # Constant validation tests
    ├── test_entities.py  # NumberWheel, FeedbackEffect, StarAnimation, UIFocus tests
    └── test_utils.py     # Question generation, difficulty, scoring tests
```

## Architecture

### State Machine
The game uses a simple two-state machine:
- **MENU**: Settings screen for toggling operations on/off
- **PLAYING**: Main gameplay with equation display, number wheel, and submit/skip buttons

### Key Classes

1. **MathWheelGame** (`game.py`)
   - Main game class extending GameFramework
   - State machine: MENU ↔ PLAYING
   - Manages question lifecycle, rendering, and input dispatch
   - Pre-renders static surfaces (gradient background, star shapes)

2. **Question** (`utils.py`)
   - Data class for a single equation: operands, result, operation, missing position
   - Properties: `answer`, `display_values`, `wheel_range`

3. **DifficultyManager** (`utils.py`)
   - Tracks correct streaks and total progress
   - Advances difficulty after `QUESTIONS_PER_DIFFICULTY_UP` consecutive correct answers
   - Mixes easier questions back in via `EASY_MIX_RATIO`

4. **ScoreTracker** (`utils.py`)
   - Tracks stars earned; awards bonus for first-try correct answers
   - No punishment for wrong answers (configurable via `WRONG_ANSWER_PENALTY`)

5. **NumberWheel** (`entities.py`)
   - Scrollable number picker with smooth animation
   - Clamped to valid range; shows visible items centered on current value

6. **FeedbackEffect** (`entities.py`)
   - Timed visual feedback (✓ or ✗) with alpha fade-out

7. **StarAnimation** (`entities.py`)
   - Bounce-scale animation when a star is earned

8. **UIFocus** (`entities.py`)
   - Tracks which UI element (WHEEL, SUBMIT, SKIP) has keyboard/gamepad focus

9. **GameFramework** (`game_framework.py`)
   - Base class from fish game, adapted for discrete (non-continuous) input
   - Provides keyboard, gamepad, and joystick handling with edge detection
   - Hat and axis input converted to digital up/down/left/right events

### Question Generation

Each operation has a dedicated generator function that:
- Respects difficulty constraints (max_number, max_result)
- Retries up to 50 times to find valid operands within bounds
- Falls back to conservative values if retry limit is reached
- Picks a missing position based on difficulty config (easy: no middle position)

Constraints enforced:
- **Addition**: sum ≤ max_result
- **Subtraction**: result ≥ 0 (no negative answers)
- **Multiplication**: product ≤ max_result, operands ≥ 1
- **Division**: exact integer division only, divisor ≥ 1

### Input Model

The game uses **discrete input** (not continuous movement):
- Arrow keys / D-pad trigger single scroll steps per press
- Key repeat is handled manually with configurable delay and interval
- Left/right arrows move focus between WHEEL → SUBMIT → SKIP
- Enter/Space/A button activates the focused element
- Joystick axes are converted to digital events with edge detection

### Rendering

- **Background**: Pre-rendered vertical gradient surface (blitted each frame)
- **Equation**: Dynamically rendered text with highlighted `?` placeholder
- **Number Wheel**: Vertical list with highlighted center, scroll arrows, focus border
- **Buttons**: Circle buttons with checkmark (submit) and arrow (skip) icons
- **Stars**: Pre-rendered star polygon surfaces with bounce animation
- **Feedback**: Semi-transparent overlay with alpha fade

## How to Run

```bash
pip install pygame-ce
python -m maxbloks.mathwheel.main
```

## Controls

### Keyboard
| Key              | Action                    |
|------------------|---------------------------|
| ↑ / W            | Scroll wheel up           |
| ↓ / S            | Scroll wheel down         |
| ← / A            | Move focus left            |
| → / D            | Move focus right           |
| Enter / Space    | Confirm / Submit           |
| Escape           | Toggle settings menu       |

### Gamepad
| Button           | Action                    |
|------------------|---------------------------|
| D-pad Up/Down    | Scroll wheel              |
| D-pad Left/Right | Move focus                |
| A / B            | Confirm / Submit           |
| Y                | Back                      |
| Start            | Toggle settings menu       |

## Configuration

All constants are in `constants.py`. Key settings:

### Difficulty Tuning
```python
QUESTIONS_PER_DIFFICULTY_UP = 5   # Correct streak to advance
EASY_MIX_RATIO = 0.25            # Fraction of easier questions mixed in
```

### Scoring
```python
STARS_PER_CORRECT = 1
STAR_BONUS_FIRST_TRY = 1
WRONG_ANSWER_PENALTY = 0
```

### Wheel Behavior
```python
WHEEL_VISIBLE_ITEMS = 5
WHEEL_REPEAT_DELAY = 400    # ms before key repeat starts
WHEEL_REPEAT_INTERVAL = 80  # ms between repeated scrolls
```

### Animation Timing
```python
FEEDBACK_DURATION = 1200     # ms total feedback display
FEEDBACK_FADE_START = 800    # ms when fade begins
STAR_ANIM_DURATION = 600     # ms star bounce animation
```

## Development Notes

### Running Tests
```bash
python -m unittest discover -s maxbloks/mathwheel/tests -v
```

81 tests covering:
- Question generation for all four operations across all difficulty levels
- Constraint validation (no negatives, no fractions, bounds checking)
- Missing position selection logic
- DifficultyManager progression and reset
- ScoreTracker star calculation
- NumberWheel scrolling, clamping, range changes, visible items
- FeedbackEffect timing and alpha
- StarAnimation progress and scale
- UIFocus navigation
- Constant validation

### Adding New Operations
1. Define operation symbol in `constants.py`
2. Add generator function in `utils.py`
3. Add to `generate_question()` dispatcher
4. Add menu toggle in `game.py._init_state()` and `_activate_menu_item()`

### Future Extensions
The architecture supports adding:
- **Rounds/Timers**: Add state to DifficultyManager, new game states
- **Mini-goals**: Track per-session targets in ScoreTracker
- **Sound effects**: Add sound loading in `game.py.__init__` (pattern from fish game)
- **Themes/Skins**: Replace color constants or add theme selection
- **Statistics**: Extend DifficultyManager to track per-operation accuracy

## License
GPL-3.0-or-later