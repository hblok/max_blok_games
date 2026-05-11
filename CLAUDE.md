# Guidelines

See `maxbloks/CLAUDE.md` for Python style guidelines and the complete guide to adding a new game.

## Repository Layout

```
max_blok_games/
├── maxbloks/          # All games and shared utilities
│   ├── common/        # Shared SDL bootstrap (compat_sdl.py)
│   ├── dogrider/      # Side-scrolling motorcycle game
│   ├── fish/          # Arcade fish-growth survival game
│   ├── mathwheel/     # Educational math practice (ages 6-7)
│   ├── spellwheels/   # German spelling game (ages 6-7)
│   ├── starfighter/   # Neon space shoot-em-up
│   └── terminal/      # Gamepad-friendly Linux command launcher
├── tools/             # Developer utilities (increment_version.py)
├── docs/              # Project documentation
├── internal/          # Internal prompts and notes
├── BUILD              # Root Bazel build file
└── MODULE.bazel       # Bazel module definition
```

## Common Commands

### Running a game
```bash
python -m maxbloks.<game>.main
# e.g. python -m maxbloks.starfighter.main
```

### Running tests
```bash
# All tests across the whole project
python -m unittest discover -s maxbloks

# One game only
python -m unittest discover -s maxbloks/<game>/tests

# With verbose output
python -m unittest discover -s maxbloks/<game>/tests -v
```

### Building with Bazel
```bash
bazel build //maxbloks/<game>
# e.g. bazel build //maxbloks/starfighter
```

### Security linting
```bash
bandit -c bandit.yaml -r maxbloks/
```

### Bumping a game version before release
```bash
python tools/increment_version.py <game>
# e.g. python tools/increment_version.py spellwheels
```

### Claude instructions
- When running tests or logs, always pipe to head -n 20 or use grep to filter for errors. Do not dump full logs.

