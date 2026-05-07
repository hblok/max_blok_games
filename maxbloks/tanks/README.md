# Tanks

Top-down 2D tank shooter for handheld gaming devices (Anbernic R46H, etc.) and desktop.

Drive your tank around a large scrolling world, shoot waves of enemies, and collect weapon power-ups. Survive 50 kills to win.

## Controls

| Action | Keyboard | Gamepad |
|--------|----------|---------|
| Move / aim | Arrow keys or WASD | Left stick |
| Fire | Space | Button A |
| Restart (game over) | B | Button B |
| Quit | — | Select / back buttons |

## Weapons

Collect weapon pickups scattered around the world:

| Weapon | Description |
|--------|-------------|
| Default | Single bullet |
| Faster Shooter | Triple fire rate |
| Laser | Hold fire for continuous beam |
| Spray | 5-way spread shot |
| Bombs | Drop mines; explode on contact |

## Running

```bash
# From the repository root
python3 -m maxbloks.tanks.main

# Via the launch script
./maxbloks/tanks/Tanks.sh
```

## Requirements

- Python 3.8+
- pygame-ce (`pip install pygame-ce`)
