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

### Checking test and BUILD coverage
```bash
# Report source modules missing a test file, and test files missing a BUILD target
tools/missing.sh
```

### Running Bazel tests
```bash
# One game
bazel test //maxbloks/<game>/tests/...

# Whole project
bazel test //maxbloks/...
```

## Development Workflow

### Branching
- Any non-trivial change (new feature, refactor, bug fix that touches more than one file) **must** go on a new git branch and be pushed to GitHub before merging.
- Very minor fixes (single-line typo fix, constant tweak) may be committed directly to `main`.
- Branch names should be short and descriptive: `feature-name`, `fix-short-description`.

### Before merging a branch
1. All `unittest` tests pass: `python -m unittest discover -s maxbloks/<game>/tests`
2. Every new source module has a test file and a Bazel target — verified with `tools/missing.sh` (no output = clean).
3. `bazel test //maxbloks/<game>/tests/...` passes.
4. Security lint is clean: `bandit -c bandit.yaml -r maxbloks/`

### Claude instructions
- When running tests or logs, always pipe to `head -n 20` or use grep to filter for errors. Do not dump full logs.
- When starting work on a non-trivial task, create a new branch first: `git checkout -b <branch-name>`.
- After implementing a feature or fix, run `tools/missing.sh` and add any missing test files and BUILD targets before committing.

