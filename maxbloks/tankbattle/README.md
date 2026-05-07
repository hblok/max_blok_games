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

From the menu, choose **Host Game** on one device and **Join Game** on the other. Both devices immediately begin broadcasting `TANKBATTLE_BEACON` messages every 2 seconds to the Tank Battle multicast group (`239.255.190.20`, UDP port 5556) and listening for beacons from peers. When a beacon arrives from another instance, each device sends a direct unicast reply, so discovery is mutual and works within the first few seconds regardless of which device started first.

The game-specific multicast group and `TANKBATTLE_BEACON` / `TANKBATTLE_RESPONSE` message types prevent Tank Battle lobbies from appearing in the discovery lists of other maxbloks games running on the same network (such as networktest).

Once a host is found the client connects over TCP port 5555. The host generates the match map seed and sends it to the client so both devices use the same arena. During play, tank state updates are sent over UDP at approximately 20 Hz, while reliable events such as round transitions and power-up spawns use the TCP connection. Remote tank positions are smoothed between UDP packets using dead reckoning.

## Features

Tank Battle includes a large 6400×4800 world, a scrolling viewport centered on the local player, hard rock clusters, destructible soft obstacles, best-of-three round scoring, a 90-second round timer, sudden death on timeout ties, health packs, spread shot, rockets, rapid fire, ricochet rounds, mine laying, a compact HUD, and a bottom-right minimap showing both tanks and hard rock layout.
