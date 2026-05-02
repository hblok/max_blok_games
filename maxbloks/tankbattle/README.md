# Tank Battle

Tank Battle is a two-player top-down tank combat game for the maxbloks collection. Each player runs the game on their own Anbernic handheld device and connects over local WiFi for short best-of-three matches across a large scrolling arena.

## Installation

Build or install the wheel from the maxbloks release package, then launch the game with the included `Tankbattle.sh` script. During development from the repository root, run:

```bash
python -m maxbloks.tankbattle.main
```

The game uses Python and SDL through the shared `maxbloks.common.compat_sdl` framework, with a logical resolution of 640×480 scaled to the physical display.

## Controls

Keyboard and gamepad work at the same time. Drive forward and backward with `W/S` or the up/down arrows, and rotate the tank body with `A/D` or the left/right arrows. Aim the turret independently with `I/K/J/L`. Fire the primary weapon with Space, fire the secondary or drop a mine with Left Ctrl, pause with Escape, navigate menus with arrows, and confirm with Enter.

On a gamepad, use the left analog stick to drive and rotate the tank, the right analog stick to aim the turret, Button A to fire the primary weapon, Button B to use the secondary weapon, Start to pause, and the D-pad for menu navigation. Both analog sticks use a 0.2 deadzone, and the turret keeps its last direction when the right stick returns to neutral.

## Hosting and Joining over WiFi

From the menu, choose **Host Game** on one device. The host opens TCP port 5555 for the reliable lobby connection and advertises itself with UDP beacons on port 5556. On the second device, choose **Join Game** to discover hosts on the local subnet. Manual IP entry is planned as a fallback for networks that block UDP broadcast.

The host generates the match map seed and sends it to the client so both devices use the same arena. During play, frequent tank state updates are sent over UDP at approximately 20 Hz, while reliable events such as round transitions and power-up spawns use TCP.

## Features

Tank Battle includes a large 6400×4800 world, a scrolling viewport centered on the local player, hard rock clusters, destructible soft obstacles, best-of-three round scoring, a 90-second round timer, sudden death on timeout ties, health packs, spread shot, rockets, rapid fire, ricochet rounds, mine laying, a compact HUD, and a bottom-right minimap showing both tanks and hard rock layout.
