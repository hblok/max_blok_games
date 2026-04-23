# SpellWheels

## Overview

SpellWheels is an educational spelling game designed for first-grade children (ages 6–7) learning basic German. It is built handheld-first — the primary target platform is an Anbernic-style gamepad device, with full keyboard support for desktop play.

Gameplay screens are strictly **icon-only** — there is no prose or instructional text during play, because the target audience may not yet read confidently. Text appears exclusively on the options / settings / pause menus.

## Main Features

- **Icon-driven spelling puzzles** — a colorful cartoon icon represents the target German word.
- **Rotating letter wheels** — one vertical drum per letter, cycling through A–Z + Ä/Ö/Ü.
- **Four themed levels** — animals, fruits, nature, household — progressing from 4-letter to 5-letter words.
- **Gentle failure** — only wrong wheels shake; letters stay put so the child can correct them.
- **Visual hint** — flashes the first target letter above wheel 0 for 2 seconds.
- **Star rewards** — 1–3 stars per word based on number of wrong submissions.
- **Sticker / celebration screen** — after every completed level.
- **Auto-save** — progress persists across sessions to `~/.spellwheels_progress.json`.
- **Dual input** — keyboard and gamepad with joystick deadzone + diagonal normalization.

## Dependencies

### External
- Python 3.7+
- pygame-ce 2.0+

### Internal
- `maxbloks.spellwheels.compat_sdl` — SDL display bootstrap (symlink to `../common/compat_sdl.py`).

## File Structure

```
spellwheels/
├── __init__.py          # Package marker
├── main.py              # Entry point (python -m maxbloks.spellwheels.main)
├── game.py              # SpellWheelsGame: state machine, rendering
├── entities.py          # LetterWheel, PuzzleState, LevelRunner, feedback effects
├── input.py             # InputHandler -> InputState
├── utils.py             # Word / Level data, ScoreTracker, ProgressSaver
├── constants.py         # Colors, layout, timings, alphabet, mappings
├── compat_sdl.py        # Symlink to ../common/compat_sdl.py
├── BUILD                # Bazel build file
├── README.md            # User-facing documentation
├── CLAUDE.md            # This file
├── game.json            # Game catalog metadata
├── version.json         # Version info
├── SpellWheels.sh       # Launch script
└── tests/
    ├── __init__.py
    ├── BUILD
    ├── test_constants.py
    ├── test_entities.py
    ├── test_game.py
    └── test_utils.py
```

## Architecture

### State Machine (`enum.Enum`)

Defined in `game.py`:

```python
class GameState(enum.Enum):
    MENU = enum.auto()
    PLAYING = enum.auto()
    PAUSED = enum.auto()
    LEVEL_COMPLETE = enum.auto()
    GAME_OVER = enum.auto()
```

Transitions:

```
                +----------+
                |   MENU   |<----+---------+
                +----------+     |         |
                     |           |         |
                     v  (Play)   | (map)   | (confirm)
                +----------+-----+---------+
                | PLAYING  |<--(resume)-- PAUSED
                +----------+
                     |
              (last word solved)
                     |
                     v
                +----------------+
                | LEVEL_COMPLETE |---(auto/confirm)---> PLAYING
                +----------------+                         (next level)
                     |
               (no more levels)
                     |
                     v
                +-----------+
                | GAME_OVER |---(confirm)---> MENU
                +-----------+
```

Each state has dedicated `_update_<state>(input_state, dt)` and `_draw_<state>(screen)` methods in `SpellWheelsGame`.

### Core Entities (`entities.py`)

| Class           | Responsibility                                                     |
|-----------------|---------------------------------------------------------------------|
| `LetterWheel`   | One vertical drum cycling through the alphabet; supports spin_up / spin_down / set_letter with wrap-around. |
| `PuzzleState`   | A full word puzzle: N wheels + active cursor; detects correct / wrong positions; manages shake and hint timers. |
| `LevelRunner`   | Drives word-by-word progression through a `Level`.                  |
| `FeedbackEffect`| Timed visual feedback (correct flash, level-complete flash).        |
| `StarAnimation` | Bounce scale effect when a star is earned.                          |

### Data Model (`utils.py`)

| Class / Helper   | Role                                                             |
|------------------|------------------------------------------------------------------|
| `WordEntry`      | A single word plus its icon tag and theme.                       |
| `Level`          | A themed list of `WordEntry` objects.                            |
| `ScoreTracker`   | Session-wide star total + per-word mistake count.                |
| `ProgressSaver`  | JSON-backed auto-save / load to `~/.spellwheels_progress.json`.  |
| `build_default_levels()` | Ships the starter four-level word list.                  |
| `stars_for_mistakes()`   | Pure function mapping mistakes → stars (1–3).            |

### Input (`input.py`)

`InputHandler.update()` drains the pygame event queue once per frame and returns a frame-local `InputState` with **edge-triggered** booleans:

- `move_left`, `move_right` — wheel cursor
- `spin_up`, `spin_down` — wheel rotation
- `submit`, `clear`, `hint` — primary actions
- `pause`, `map_view` — state transitions
- `quit_requested` — application exit

Analog sticks apply a **0.2 deadzone**, emit events only on crossing the 0.5 threshold (edge detection), and diagonals are normalized via the `DIAGONAL_NORMALIZE = 0.707` constant exposed in `constants.py`.

### Rendering

All gameplay rendering happens at the **logical resolution** of 640×480. `main.py` creates a logical pygame `Surface`, passes it to `game.draw()`, and the result is letter-boxed / scaled onto the physical screen via `compat_sdl.init_display()`.

- `_render_gradient_bg()` — pre-rendered once into `self.bg_surface`.
- `_draw_icon()` — dispatches on `WordEntry.icon_tag` via the `_ICON_DRAWERS` table; each drawer is a small module-level function using only `pygame.draw` primitives (circles, rects, polygons) — no external images.
- `_draw_wheels()` — pygame-drawn rounded rectangles with three visible letters per drum and an animated glow border on the active wheel.
- `_draw_progress_bar()` — circle "footsteps" across the top.
- `_draw_stars_hud()` — polygon star in the top-left with the running total.

To add a new word, add its `WordEntry` to one of the levels in `utils.build_default_levels()` and register a drawer in `_ICON_DRAWERS` inside `game.py`.

## How to Run

```bash
pip install pygame-ce
python -m maxbloks.spellwheels.main
```

## Controls

See [`README.md`](README.md) for a complete keyboard + gamepad mapping.

## Configuration

Everything is in `constants.py`. Highlights:

```python
# Display
LOGICAL_WIDTH = 640
LOGICAL_HEIGHT = 480
FULLSCREEN = False
TARGET_FPS = 60

# Alphabet (A–Z + Ä, Ö, Ü)
ALPHABET = [...]

# Wheels
WHEEL_VISIBLE_LETTERS = 3
WHEEL_WIDTH = 60
WHEEL_HEIGHT = 180
WHEEL_REPEAT_DELAY = 400
WHEEL_REPEAT_INTERVAL = 90

# Feedback timings (ms)
CORRECT_FEEDBACK_DURATION = 1400
WRONG_SHAKE_DURATION = 600
LEVEL_COMPLETE_DISPLAY = 2500

# Scoring
MAX_STARS_PER_WORD = 3
STARS_BY_MISTAKES = [3, 2, 1]

# Input
JOYSTICK_DEADZONE = 0.2
DIAGONAL_NORMALIZE = 0.707
```

## Development Notes

### Running Tests

```bash
python -m unittest discover -s maxbloks/spellwheels/tests -v
```

Test coverage focuses on the headless, pygame-free modules (`utils`, `entities`, `constants`) which contain all game logic. The renderer (`game.py`'s drawing code) is smoke-tested to ensure imports and state transitions work.

### Adding New Words

1. Pick or add a theme.
2. Add a `WordEntry("WORD", "icon_tag", THEME)` inside `utils.build_default_levels()`.
3. If `icon_tag` is new, register a `_draw_icon_<tag>()` function in `game.py` and add it to `_ICON_DRAWERS`.
4. Word validation happens automatically — letters must all live in `ALPHABET`.

### Adding a New State

1. Extend `GameState` (keep the enum order intact for save-file compatibility).
2. Add `_update_<state>()` and `_draw_<state>()` methods.
3. Dispatch to them in `update()` and `draw()`.

### Future Extensions

- **Sound**: add optional audio cues for correct / wrong / star-earned (currently disabled per design spec).
- **Additional word lists**: pluggable via alternate `build_default_levels()` generators; could be loaded from a JSON file at runtime.
- **World map**: fleshed-out level selection screen (currently `map_view` routes back to menu).
- **Multi-profile**: multiple save slots for siblings.

## License

GPL-3.0-or-later