# MathWheel

A fun, low-text math practice game for children ages 6–7. Solve equations by scrolling a number wheel and pressing submit.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)

## Features

- **Addition & subtraction** enabled by default
- **Multiplication & division** available as optional toggles
- **Number wheel** input — scroll to pick an answer, then confirm
- **Missing-number equations** — unknown can appear in any position (e.g. `? + 3 = 7`, `5 + ? = 9`, `4 + 3 = ?`)
- **Progressive difficulty** — starts easy (sums ≤ 10), gradually introduces harder problems while mixing in easier ones
- **Star-based rewards** — earn bonus stars for first-try correct answers
- **Gentle wrong-answer handling** — encouraging feedback, retry allowed, skip available
- **Keyboard and gamepad** support
- **Endless practice mode** — structured for future rounds, timers, or mini-goals

## Installation

```bash
pip install pygame-ce
```

## Running

```bash
python -m maxbloks.mathwheel.main
```

Or use the launch script:

```bash
./MathWheel.sh
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
| Escape           | Open settings menu         |

### Gamepad

| Button       | Action                    |
|--------------|---------------------------|
| D-pad Up/Down| Scroll wheel              |
| D-pad Left/Right | Move focus             |
| A / B        | Confirm / Submit           |
| Start        | Open settings menu         |

## Difficulty Levels

| Level  | Numbers   | Max Result | Missing Positions     |
|--------|-----------|------------|-----------------------|
| Easy   | 0–10      | ≤ 10       | First, Last           |
| Medium | 0–9       | ≤ 18       | First, Middle, Last   |
| Hard   | 0–20      | ≤ 30       | First, Middle, Last   |

Difficulty advances automatically after a streak of correct answers. Easier questions are mixed in periodically to maintain confidence.

## Settings Menu

Press Escape (or Start on gamepad) to open the settings menu where you can:

- Toggle **addition** on/off
- Toggle **subtraction** on/off
- Toggle **multiplication** on/off (disabled by default)
- Toggle **division** on/off (disabled by default)

At least one operation must remain enabled.

## Scoring

- **First-try correct**: 2 stars
- **Correct after retry**: 1 star
- **Wrong answer**: 0 penalty (gentle feedback, can retry)
- **Skip**: no stars, moves to next question

## Running Tests

```bash
python -m unittest discover -s maxbloks/mathwheel/tests -v
```

## License

GPL-3.0-or-later