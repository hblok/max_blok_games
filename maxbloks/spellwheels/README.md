# SpellWheels

A handheld-first spelling game for first-grade children (ages 6–7) learning basic German. The gameplay is icon-driven and requires **no reading ability** to play — only the options / settings menu contains text.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)

## Concept

A big, colorful icon is displayed (dog, apple, sun, …). Below it, a row of vertical letter wheels appears — one wheel per letter of the target German word. Each wheel cycles through A–Z plus German umlauts (Ä, Ö, Ü). Spin the letters, move between wheels, submit when the spelled word matches the icon, and earn stars.

## Installation

```bash
pip install pygame-ce
```

## Running

```bash
python -m maxbloks.spellwheels.main
```

Or use the launch script:

```bash
./SpellWheels.sh
```

## Controls

### Keyboard

| Key              | Action                                 |
|------------------|----------------------------------------|
| Left / Right     | Move between wheels                    |
| Up / Down        | Spin the active wheel                  |
| Space / Enter    | Submit the current spelling            |
| Backspace        | Clear / reset the active wheel         |
| H                | Show a visual hint (first letter)      |
| Escape           | Pause menu                             |
| Tab              | Return to main / level map             |
| Q or Alt+F4      | Quit the game                          |

### Gamepad (Anbernic layout)

| Button              | Action                                 |
|---------------------|----------------------------------------|
| D-Pad Left / Right  | Move between wheels                    |
| D-Pad Up / Down     | Spin the active wheel                  |
| A                   | Submit the current spelling            |
| B                   | Clear / reset the active wheel         |
| Y                   | Show a visual hint                     |
| Start               | Pause menu                             |
| Select              | World / level map                      |
| Button 8 / 13       | System exit                            |

Analog sticks respect a **0.2 deadzone**, and diagonal input is normalized by `0.707`.

## Gameplay

1. **Look** at the big icon at the top of the screen.
2. **Spin** each wheel until the correct letter is centered.
3. **Move** between wheels with Left / Right.
4. **Submit** the word with A (or Space / Enter).
5. ✅ **Correct** — stars appear, and the icon celebrates.
6. ❌ **Wrong** — only the incorrect wheels gently shake; spin them and try again.

Need a nudge? Press Y (or H) to briefly flash the first correct letter above wheel 1.

## Scoring

- **3 stars** — solved with no wrong submissions.
- **2 stars** — solved after one wrong submission.
- **1 star** — solved after two or more wrong submissions.

Earning stars unlocks sticker rewards displayed on the level-complete screen.

## Word List

The starter word list ships with four themed levels:

| Icon   | Word    | Letters | Level        |
|:------:|---------|:-------:|--------------|
| 🐶     | HUND    | 4       | Animals      |
| 🐱     | KATZE   | 5       | Animals      |
| 🐟     | FISCH   | 5       | Animals      |
| 🍎     | APFEL   | 5       | Fruits       |
| 🌳     | BAUM    | 4       | Fruits       |
| ☀️     | SONNE   | 5       | Nature       |
| 🌙     | MOND    | 4       | Nature       |
| ⭐     | STERN   | 5       | Nature       |
| 🏠     | HAUS    | 4       | Household    |
| 🚗     | AUTO    | 4       | Household    |

Each level has 2–3 words, progressing from 3–4 letter to 5–6 letter words. Progress is **auto-saved** after every solved word so the child can turn off the device at any time and resume exactly where they left off.

## Running Tests

```bash
python -m unittest discover -s maxbloks/spellwheels/tests -v
```

## License

GPL-3.0-or-later