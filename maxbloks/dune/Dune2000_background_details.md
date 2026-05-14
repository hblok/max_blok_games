# Dune 2000 — Game Analysis & Remake Design/Implementation Plan

*Refined edition. Heavy focus on analysis, mechanics, and look-and-feel. Phases listed as task sets, not schedules.*

---

## Part 1: Game Analysis

### 1.1 Overview

Dune 2000 (Westwood / Intelligent Games, 1998) is a 2D real-time strategy game set on the desert planet Arrakis from Frank Herbert's *Dune* universe. It is a remake of *Dune II: The Building of a Dynasty* (1992) rebuilt on a Command & Conquer–style engine with multi-unit selection, a vertical sidebar UI, FMV cutscenes, skirmish and multiplayer modes, and three playable houses (Atreides, Harkonnen, Ordos) competing for control of the planet's only resource: **spice (melange)**.

The core loop is short, addictive, and tight:

> **harvest spice → earn Solaris (credits) → power base with Wind Traps → tech up through factories → build army → destroy enemy base.**

What gives the game its identity is not the loop itself — it is the *feel* of the loop: the rumble of harvesters on sand, the distant boom of artillery, the dread of seeing a sandworm's wake heading for an unprotected harvester, the satisfying snap of a Construction Yard finishing a Heavy Factory placement, the deep ambient drone of Arrakis wind underneath everything.

---

### 1.2 Core Gameplay Mechanics

#### Resource System

- **Spice** is the only resource. It appears as orange/rust-coloured tiles on sand, in two density tiers: light spice (single layer) and heavy spice (double-layer, brighter, granular pattern). Heavy spice yields more per harvest visit.
- **Harvesters** are heavy tracked vehicles that drive onto spice, animate a downward "scoop" cycle that visibly shrinks the spice patch tile-by-tile, and return to a Refinery to unload. A full Harvester load is worth **700 Solaris**.
- **Refineries** dock the Harvester (it drives into a side ramp and disappears), play an unloading animation (steam vents, machinery), and add credits to the player's pool. A new Harvester is dispensed if the previous one was lost.
- **Carryalls** are unarmed VTOL aircraft that, once a High-Tech Factory exists, automatically airlift Harvesters from Refinery to spice and back, dramatically speeding up the economy.
- **Spice Silos** store overflow capacity. Without enough Silo storage, incoming spice is wasted (a "Spice Lost" message appears).
- **Spice Blooms** are buried spice deposits that visually appear as faint dark rings on sand. When a unit walks onto one, it erupts in an orange dust geyser, damaging nearby units and seeding a fresh spice field of 5–10 tiles.
- **Solaris** is the spendable currency. The HUD displays it in the top-right corner with a tick-up/down animation when changing.

#### Power System

- Wind Traps generate power; almost every other building consumes it.
- A **power bar** on the sidebar shows total output vs. total consumption.
- When in deficit:
  - Construction and unit production slows proportionally to the deficit.
  - Rocket Turrets shut down entirely.
  - Radar/minimap goes black (an Outpost requires power).
- Gun Turrets and the Construction Yard do **not** require power, providing a baseline of defence even when power-starved.

#### Terrain & Map

The map uses a tile-based 2D top-down view (not isometric). Three surface types matter for gameplay:

| Terrain | Visual | Buildable | Vehicle | Infantry | Worm Risk |
|---|---|---|---|---|---|
| Rock | Grey, cracked, patchy moss | Yes | Yes | Yes | No |
| Sand | Tan/beige with wind ripples | No | Yes | Yes | Yes |
| Dune Mountain | Dark brown, raised, jagged | No | No | Yes (some passes) | No |
| Spice (light) | Orange dust scatter | No | Yes | Yes | Yes |
| Spice (heavy) | Bright orange granular crust | No | Yes | Yes | Yes |
| Cliff edge | Distinct shadow line | No | No | No | No |

- **Shroud (fog of war)** covers the entire map at start as solid black. Units explored reveal terrain permanently for the session, but enemy units in revealed areas are only visible while a friendly unit has line of sight on them.
- **Day/night cycle:** none. Lighting is static, baked into sprites.
- **Wind effects:** subtle sand particles drift across the screen on sandy areas — a constant ambient detail.

#### Base Building

- All construction is queued from the **Construction Yard sidebar** on the right edge of the screen.
- When the player clicks a building icon, a timer/progress ring fills around the icon. When complete, the icon shows "READY" and the cursor becomes a **placement ghost** (a translucent green outline of the building's footprint).
- Hovering the ghost over the map shows green tiles (valid) and red tiles (invalid: not rock, not on owned territory, or occupied).
- A click places the building. It appears at 25% size from a build pit animation, scaffolding rises, then it expands to full size over ~2 seconds with construction dust particles.
- Buildings off concrete start at 50% HP and slowly bleed HP down to 50% (they do not die from sand alone, but become very vulnerable).
- **Multiple Construction Yards** can be built (via MCV) to provide redundancy and multiple build queues running in parallel.

#### Combat

- **Selection:** Left-click for single, left-drag for box, double-click for all of that type on screen, Ctrl-1..9 to bind a group.
- **Movement:** Right-click to move; right-click an enemy to attack; right-click a building to attack-move toward it. Engineers and Saboteurs trigger an "enter" cursor over capturable buildings.
- **Targeting:** Units auto-acquire enemies within range when idle. Player-issued targets override.
- **Crushing:** Tracked vehicles can crush infantry by driving over them — except Sardaukar, who explode when crushed, dealing damage to the crushing vehicle.
- **Inaccuracy:** All weapons have inherent inaccuracy. Shells and missiles can miss. Weapons in Dune 2000 deal AoE/splash damage and have inherent inaccuracy that cannot be turned off; damage dealt does not change with distance between attacker and victim. This is important — it means stationary clustered targets get destroyed quickly, while spread-out moving targets are hit less reliably.
- **Damage table:** weapons have a damage type (bullet, explosive, missile, sonic, plasma, gas), and units have an armour type (none, light, medium, heavy). Each combination has a multiplier (e.g., bullets vs. heavy armour = 25%, missiles vs. heavy armour = 100%).
- **Damaged units** move slower, fire slower, and turn slower as health drops below 50%.

#### Economy Flow Diagram

```
   ┌─────────────┐         ┌──────────────┐
   │  Wind Trap  ├────────▶│   POWER POOL │◀───── consumed by all production
   └─────────────┘         └──────┬───────┘
                                  │
   ┌───────────┐    spice  ┌──────▼────────┐    credits   ┌─────────────┐
   │ Harvester ├──────────▶│   Refinery    ├─────────────▶│ Solaris Pool│
   └─────▲─────┘           └───────────────┘              └──────┬──────┘
         │ Carryall ferry                                        │
         │                                                       ▼
   ┌─────┴─────┐                                       ┌──────────────────┐
   │   Spice   │                                       │ Buildings, Units │
   │  Fields   │                                       │  Repairs, Sales  │
   └───────────┘                                       └──────────────────┘
```

---

### 1.3 The Three Playable Houses

#### House Atreides — *The Noble*

- **Home:** Caladan (water world).
- **Colours:** Royal blue with gold trim.
- **Banner motif:** Red hawk on blue.
- **Architectural style:** Clean angular lines, slate-grey walls with blue panels, gold accents. Buildings feel "honourable" and military-ceremonial.
- **Voice acting tone:** Crisp, British-RP, formal acknowledgements ("Acknowledged.", "On the move.", "For House Atreides!").
- **Combat doctrine:** Balanced and ranged. Sonic Tanks at long range, ornithopter airstrikes for finishing moves, Fremen for ambush.
- **Unique units:** Sonic Tank, Fremen (from Palace), Grenadier (1.06 multiplayer), Ornithopter Airstrike (support power).

#### House Harkonnen — *The Brutal*

- **Home:** Giedi Prime (volcanic industrial waste).
- **Colours:** Blood red with black trim.
- **Banner motif:** Black ram's-head/serpent on red.
- **Architectural style:** Heavy, blocky, industrial. Cooling stacks, exposed pipes, scorched edges. Buildings look like they were forged in a smelter.
- **Voice acting tone:** Gruff, growling, Russian/Eastern European accents, snarled responses ("Yes!", "We kill them!", "Death to enemies!").
- **Combat doctrine:** Heavy push. Slow, tough Combat Tanks; absolutely brutal Devastators; saturation bombardment via Death Hand.
- **Unique units:** Devastator, Sardaukar (post-1.06 / late-campaign), Death Hand Missile (superweapon).

#### House Ordos — *The Insidious*

- **Home:** Sigma Draconis IV (frigid ice world).
- **Colours:** Sickly green and copper.
- **Banner motif:** Stylised serpent/eye on green.
- **Architectural style:** Sleek, alien-looking, asymmetric. Curved domes, exposed ribbing, a feeling of "wealthy paranoia."
- **Voice acting tone:** Whispery, smooth, sinister, vaguely Eastern-European mercantile ("As you wish.", "Affirmative.", "Proceeding…").
- **Combat doctrine:** Stealth, speed, subversion. Hit-and-run with Raiders; flip enemy tanks with Deviators; decapitate buildings with Saboteurs.
- **Unique units:** Deviator, Raider (replaces Trike), Saboteur (from Palace), Stealth Raider (1.06 multiplayer).
- **Quirk:** Cannot build Missile Tanks at Heavy Factory — must purchase them from Starport.

#### Non-Playable Subfactions

- **House Corrino / The Emperor:** Provides Sardaukar reinforcements (dropped by frigate) to the player's enemies in late campaign missions. Has a unique Sardaukar Castle structure.
- **Fremen:** Native warriors of Arrakis; allied to Atreides, cloaked.
- **Mercenaries / Smugglers:** Neutral parties on some maps; ally on contract, defect if overrun. Use a generic mixed-house unit set.
- **Sandworms:** A wild "third combatant" — not controlled by anyone but deadly to all.

---

### 1.4 Buildings — Complete Reference

All buildings have:
- A footprint in tiles (e.g., 2×2, 3×3).
- A health pool, an armour type, a cost in Solaris, a build time, a power draw (+ for generation, − for consumption), and a prerequisite chain.
- Three visual states: **fully operational**, **damaged** (cracks, smoke wisps), **critical** (heavy smoke, sparking, half-collapse).
- A destruction animation: collapse, dust cloud, brief flame burst, leaves a charred rubble tile that blocks placement for ~10 seconds.

| Building | Footprint | Cost | Power | Prerequisite | Function |
|---|---|---|---|---|---|
| Concrete Slab (2×2) | 2×2 | $20 | 0 | None | Foundation |
| Concrete Slab (4×4) | 4×4 | $50 | 0 | Upgraded Construction Yard | Larger foundation |
| Construction Yard | 3×3 | $2000 (MCV) | +5 | None | Builds all structures |
| Wind Trap | 2×2 | $225 | +120 | Construction Yard | Power |
| Spice Refinery | 3×2 | $1000 | −30 | Wind Trap | Spice → Credits; includes 1 Harvester |
| Spice Silo | 2×2 | $150 | −5 | Refinery | Spice storage |
| Barracks | 2×2 | $300 | −20 | Wind Trap | Infantry training |
| Light Factory | 2×2 | $500 | −20 | Refinery | Trike/Raider/Quad |
| Heavy Factory | 3×2 | $900 | −30 | Refinery | Tanks, Harvester, MCV |
| Outpost | 2×2 | $400 | −30 | Barracks | Radar / minimap |
| Wall (segment) | 1×1 | $50 | 0 | Barracks | Blocks movement/fire |
| Gun Turret | 1×1 | $250 | 0 | Barracks | Anti-vehicle/infantry defence |
| Rocket Turret | 1×1 | $500 | −30 | Upgraded CY + Outpost | Long-range defence |
| High-Tech Factory | 2×2 | $1150 | −30 | Outpost | Carryall; advanced infantry |
| Repair Pad | 3×3 | $1000 | −30 | Upgraded Heavy Factory | Repairs vehicles |
| Starport | 3×3 | $1500 | −50 | Outpost + Heavy Factory | Buy units from CHOAM |
| IX Research Center | 2×2 | $1000 | −50 | Upgraded Heavy + Outpost | Unlocks superweapon-tier units |
| Palace | 3×3 | $1600 | −60 | IX Research Center | House superweapon/unique unit |

#### Tech Tree

```
Construction Yard
│
├──▶ Wind Trap
│     │
│     ├──▶ Barracks ──▶ Outpost ──▶ High-Tech Factory ──▶ [unlocks airstrike when upgraded]
│     │     │              │
│     │     │              └──▶ Starport (needs Heavy Factory)
│     │     │
│     │     └──▶ Wall, Gun Turret
│     │
│     └──▶ Refinery
│           │
│           ├──▶ Light Factory ──▶ Trike/Raider, Quad
│           │
│           └──▶ Heavy Factory ──▶ Harvester, Tank, Siege Tank
│                 │
│                 └──▶ (UPGRADE) ──▶ Repair Pad, MCV
│                                     │
│                                     └──▶ IX Research Center
│                                            │
│                                            ├──▶ Missile Tank (not Ordos)
│                                            ├──▶ Sonic / Devastator / Deviator
│                                            └──▶ Palace ──▶ Fremen / Sardaukar / Saboteur / Death Hand
│
└──▶ (UPGRADE) ──▶ 4×4 Concrete + Rocket Turret
```

---

### 1.5 Units — Detailed Reference

This section is the heart of the design. Each unit is described with **role**, **stats**, **weapons**, **sprite/animation notes**, **audio cues**, and **behavioural quirks** important for faithful recreation.

#### Infantry

Infantry sprites are small (roughly 12×16 pixels in the original; recommend **32×32 for the remake** for clearer readability). Each infantry sprite has **8 facing directions** (N, NE, E, SE, S, SW, W, NW), each with:

- **Idle** (1 frame, slight bob)
- **Walk** (4–6 frame cycle, legs/arms swing)
- **Fire** (2–3 frame muzzle flash, recoil)
- **Death** (4 frames, ragdoll fall + blood pixel)
- **Crushed** (1 frame, flat splatter)

Footstep sound on rock vs. sand differs (firmer thump on rock, muffled crunch on sand).

##### Light Infantry — All houses
- **Role:** Cheap anti-infantry, scout.
- **Cost:** $50. **HP:** 60. **Speed:** Medium. **Armour:** None.
- **Weapon:** Assault rifle. Range: 3 tiles. RoF: ~1 shot every 0.6s. Damage: ~6 per shot (bullet).
- **Sprite notes:** House-coloured uniform with rifle held diagonally. Visible muzzle flash sprite layered on top during firing.
- **Audio:** Burst of three "tat-tat-tat" rifle sounds. Acknowledgements vary per house.
- **Behaviour:** Will scatter slightly when targeted by splash weapons (a small evasion AI).

##### Trooper — All houses
- **Role:** Anti-vehicle, anti-air infantry.
- **Cost:** $90. **HP:** 80. **Speed:** Slow. **Armour:** None.
- **Weapon:** Shoulder-launched rocket. Range: 4 tiles. RoF: ~one rocket every 2.5s. Damage: heavy vs. vehicles, light vs. infantry, with small splash.
- **Sprite notes:** Bulkier silhouette, launcher tube visible on shoulder. Distinct firing animation where they kneel briefly.
- **Audio:** Whoosh-bang. Acknowledgement: "Locked on."
- **Behaviour:** Slower turning. Can target Carryalls and Ornithopters (one of the only ground anti-air options).

##### Engineer — All houses
- **Role:** Capture or repair buildings.
- **Cost:** $400. **HP:** 60. **Speed:** Slow. **Armour:** None.
- **Weapon:** None.
- **Sprite notes:** Civilian-looking, hard hat, carries a tool case. Walks with one arm swinging.
- **Audio:** "Yes, sir." / "Building secured!" on successful capture.
- **Behaviour:** Right-click on a damaged friendly building to repair (consumes the engineer). Right-click on enemy building to capture (consumes engineer; building changes ownership and becomes operational immediately). If the building is at >50% HP, capture fails and the engineer dies (in some balance variants); in original behaviour, capture always succeeds if the engineer reaches the building.

##### Grenadier — Atreides (1.06 multiplayer)
- **Role:** Infantry artillery.
- **Cost:** $80. **HP:** 70. **Speed:** Slow.
- **Weapon:** Hand-thrown grenade. Range: 3.5 tiles. Arcing projectile with delay and AoE.
- **Sprite notes:** Throwing arm rears back; grenade lobs in a visible arc with shadow.
- **Quirk:** Explodes when killed, dealing AoE — never group them tightly.

##### Sardaukar — Harkonnen (1.06 / late campaign)
- **Role:** Elite heavy infantry.
- **Cost:** $120. **HP:** 180. **Speed:** Slow.
- **Weapons:** Machine gun (vs. infantry) + rocket launcher (vs. vehicles) — auto-switches based on target.
- **Sprite notes:** Distinct gold-trimmed dark uniform, helmet with face shield, bulky.
- **Quirk:** Explodes when run over by vehicles, damaging the crusher.

##### Fremen — Atreides (from Palace)
- **Role:** Elite stealth infantry.
- **Cost:** Free (cooldown-based spawn from Palace, typically 2 per spawn). **HP:** 160.
- **Weapons:** Machine gun + rocket launcher (auto-switch).
- **Sprite notes:** Stillsuit-clad, sand-coloured, with a faint translucent shimmer when cloaked.
- **Quirk:** Cloaked while idle and moving; uncloak when firing or within ~2 tiles of enemy infantry. Detected by turrets and infantry.

##### Saboteur — Ordos (from Palace)
- **Role:** Building demolisher.
- **Cost:** Free (cooldown spawn from Palace). **HP:** 50. **Speed:** Medium.
- **Weapon:** None — uses a single demolition action.
- **Sprite notes:** Hooded figure with backpack charge; sprite has a translucent overlay during cloak phase (~10s cooldown-recharged).
- **Behaviour:** Enter any enemy building → instant destruction of that building, saboteur dies. Detected by turrets if close.

##### Thumper (campaign only, non-combat)
- **Role:** Bait sandworms.
- **Weapon:** None. Deployed in place, "thumps" rhythmically, attracting sandworms in a radius.
- **Sprite notes:** Stationary jackhammer device with a small operator; produces visible ground ripples.

#### Light Vehicles

Vehicle sprites use **32 facing directions** in the original (smooth rotation); a remake should target at least **16 facing directions** or use vector rotation. Each vehicle has:

- **Body** (the chassis sprite, all rotations)
- **Turret** (separate sprite layer that rotates independently for tanks)
- **Tracks/wheels** (animated dust kick-up sprite layered behind)
- **Damaged variant** (cracks, smoke trail)
- **Wreck** (charred chassis remains for ~30s after death)
- **Death animation:** explosion sprite (8 frames), debris fly-up, sometimes spawns a single Light Infantry survivor (small chance).

##### Trike — Atreides, Harkonnen
- **Role:** Scout / anti-infantry harasser.
- **Cost:** $150. **HP:** 100. **Speed:** Very fast. **Armour:** Light.
- **Weapon:** Twin machine guns. Range: 3 tiles. Excellent vs. infantry; poor vs. armour.
- **Sprite notes:** Three-wheeled buggy, low profile, kicks up large dust trail.
- **Audio:** Whining high-pitched engine.

##### Raider — Ordos (replaces Trike)
- **Role:** Upgraded Trike: scout + harasser.
- **Cost:** $150. **HP:** 120. **Speed:** Faster than Trike. **Armour:** Light.
- **Weapon:** Twin machine guns, slightly higher damage and RoF.
- **Sprite notes:** Sleeker, four-wheeled, green/copper accent.

##### Stealth Raider — Ordos (1.06 multiplayer)
- **Role:** Cloaked harasser / infiltration.
- **Cost:** $250. **HP:** 100.
- **Sprite notes:** Permanent translucent shimmer overlay while cloaked; uncloaks on firing.
- **Behaviour:** Uncloaks when firing its machine guns.

##### Quad — All houses
- **Role:** Anti-light-vehicle, anti-tank-skirmisher.
- **Cost:** $200. **HP:** 150. **Speed:** Fast. **Armour:** Light.
- **Weapon:** Twin rocket launchers. Range: 4 tiles. Strong vs. vehicles, weak vs. infantry.
- **Sprite notes:** Four-wheeled, twin rocket pods angled outward, heavier than Trike.

#### Heavy Vehicles

##### Harvester — All houses
- **Role:** Spice collection.
- **Cost:** $1200 (or 1 free with each Refinery). **HP:** 700. **Speed:** Very slow. **Armour:** Heavy.
- **Weapon:** None — but can crush infantry.
- **Sprite notes:** Massive boxy chassis with a downward-extending intake mechanism. Animated suction beneath when harvesting (4-frame loop with dust plume and bright orange spice particles).
- **Behaviour:** AI seeks nearest spice patch. Once full, returns to nearest Refinery. Can be manually directed. Carryall picks them up automatically when one is available.

##### Combat Tank — All houses (house variants)
- **Role:** Core front-line tank.
- **Cost:** $700. **Armour:** Medium → Heavy.
- **House variants:**
  - **Atreides:** HP 400, balanced — medium speed, medium reload (~2s).
  - **Harkonnen:** HP 500, slow speed, slow reload (~2.5s), but tougher.
  - **Ordos:** HP 320, fast speed, fast reload (~1.5s), lighter armour.
- **Weapon:** Heavy cannon. Range: 4 tiles. Good vs. vehicles and buildings; mediocre vs. infantry. Splash radius ~0.5 tile.
- **Sprite notes:** Rotating turret on a tracked chassis. House-coloured panels. Muzzle flash + smoke puff when firing. Recoil pushes turret back 2 pixels for 4 frames.
- **Audio:** Deep cannon thunk.

##### Siege Tank — All houses
- **Role:** Anti-infantry, anti-building artillery.
- **Cost:** $600. **HP:** 300. **Speed:** Slow. **Armour:** Light.
- **Weapon:** Long-range artillery shell. Range: 6 tiles. High splash damage. Friendly fire active.
- **Sprite notes:** Long-barrelled gun visibly oversized for the chassis. Visible shell-arc projectile with shadow.
- **Behaviour:** Cannot fire at point-blank range (minimum range ~1 tile).

##### Missile Tank — Atreides, Harkonnen (Ordos buys from Starport only)
- **Role:** Long-range anti-armour, anti-air.
- **Cost:** $800. **HP:** 250. **Speed:** Medium. **Armour:** Medium.
- **Weapon:** Two-missile volley. Range: 7 tiles (longest in the game, exceeds even Rocket Turret range). Tracks airborne targets. Weak vs. infantry.
- **Sprite notes:** Boxy chassis with a tall twin-tube launcher on top. Missiles launch with visible smoke trails.
- **Quirk:** Has the longest firing range of all units and structures in the game, outdistancing even the rocket turret defence.

##### MCV (Mobile Construction Vehicle) — All houses
- **Role:** Deployable Construction Yard.
- **Cost:** $1500 ($2000 effective). **HP:** 1000. **Speed:** Very slow. **Armour:** Heavy.
- **Weapon:** None.
- **Sprite notes:** Massive boxy vehicle with retracted construction crane. Deploy animation: vehicle lowers stabilisers, panels unfold outward, crane rises, transforms into Construction Yard.

##### Sonic Tank — Atreides only
- **Role:** Long-range area-effect tank.
- **Cost:** $950. **HP:** 250. **Speed:** Medium. **Armour:** Light.
- **Weapon:** Sonic wave. Range: 6 tiles. Travels in a straight line, damaging *every* unit it passes through (including friendly).
- **Sprite notes:** Sleek angular hull with a circular dish/emitter. Firing produces a visible cyan/white shockwave sprite that scales as it travels.
- **Audio:** Distinctive high-pitched warble during firing.
- **Quirk:** Sonic Blasts deal damage during their move function, not their impact — the blast starts with 60 hitpoints and loses one hitpoint every gametic. In practice: closer targets take more damage; the wave dissipates over distance.

##### Devastator — Harkonnen only
- **Role:** Heaviest assault tank, suicide bomber.
- **Cost:** $1000. **HP:** 600. **Speed:** Very slow. **Armour:** Heavy.
- **Weapon:** Dual plasma cannons. Range: 4 tiles. Devastating vs. all ground.
- **Sprite notes:** Hulking, square-shouldered chassis with paired barrels venting orange plasma glow when firing. Heaviest tread animation.
- **Special ability:** **Self-destruct** — player-issued command starts a 3-second countdown, then the unit explodes in a massive AoE (~3 tile radius, ~250 damage).

##### Deviator — Ordos only
- **Role:** Vehicle subversion.
- **Cost:** $750. **HP:** 200. **Speed:** Medium. **Armour:** Light.
- **Weapon:** Nerve-gas rocket. Range: 5 tiles. Negligible damage; on hit, target enemy *vehicle* (not infantry, not buildings) switches to Deviator player's control for ~15 seconds, then reverts.
- **Sprite notes:** Tall narrow launcher with a green/yellow toxic-canister look. Gas cloud sprite on impact (semi-transparent green smoke).
- **Quirk:** Useless vs. infantry. Best used vs. Devastators and Sonic Tanks.

#### Aircraft

##### Carryall — All houses
- **Role:** Automatic transport for Harvesters and damaged vehicles.
- **Cost:** $800 (one auto-spawns per High-Tech Factory built). **HP:** 200. **Speed:** Very fast.
- **Weapon:** None.
- **Sprite notes:** Wing-tipped VTOL with central cargo bay. Pickup animation: hovers above target, lowers grapples, target rises into bay. Drop animation: hovers, opens bay, lowers target.
- **Behaviour:** Idles in the air above a friendly building when no task is queued. Auto-assigns to Harvesters → Refinery → spice, and to damaged vehicles → Repair Pad if instructed.

##### Ornithopter — Atreides only (support power, not a buildable unit)
- **Role:** Airstrike support power.
- **Trigger:** Player clicks the "Airstrike" sidebar button after upgraded High-Tech Factory; cooldown begins ~3 minutes between strikes.
- **Behaviour:** 3 Ornithopters fly in from the map edge, bomb the target area in a tight line, fly away.
- **Sprite notes:** Dragonfly-style flapping wings (8-frame wing cycle), distinct silhouette. Bombs are small dropping ovals with shadow.
- **Audio:** Wing-flap whirr + bomb whistle.

#### Special / Superweapons

##### Death Hand Missile — Harkonnen (Palace ability)
- **Trigger:** Player clicks "Launch Death Hand" sidebar button; charges over ~5 minutes.
- **Behaviour:** Massive missile rises from the Palace, arcs across the map, lands within a wide scatter circle around the targeted point (highly inaccurate). Detonates with massive AoE (~5 tile radius, ~400 damage to centre).
- **Sprite notes:** Visible missile trail across the screen as it travels. Mushroom-cloud explosion sprite.

##### Saboteur ability — see Ordos infantry above.

##### Fremen ability — see Atreides infantry above.

#### Sandworm — Neutral wild entity
- **Role:** Environmental threat.
- **HP:** 1000 (effectively invincible to small arms). **Speed:** Fast in sand.
- **Behaviour:** Patrols sand tiles. Detects ground vibration in a ~6-tile radius. Surfaces beneath the heaviest unit in range, devours it (insta-kill), submerges, then chooses a new patrol point. Cannot cross rock tiles. A sandworm disappears after it devours 3 units (in later patch versions), then a new worm spawns elsewhere after a delay.
- **Sprite notes:** Underground travel is shown as a moving "wake" of disturbed sand and shadow. Surfacing animation: massive segmented worm body rises in 6 frames, mouth opens, snatches unit, body sinks back in 4 frames. Dust geyser on emergence.
- **Audio:** Deep low-frequency rumble that grows as worm approaches.

---

### 1.6 Defensive Structures

| Structure | HP | Damage | Range | Power | Notes |
|---|---|---|---|---|---|
| Wall (1 segment) | 200 | — | — | 0 | Blocks all movement and most projectiles. Cannot be repaired. Different sprite per connection (T/L/cross/end-cap auto-tiling). |
| Gun Turret | 300 | Medium bullet | 4 | 0 | Detects cloaked units. No power required. Animated rotating turret head, fires in bursts. |
| Rocket Turret | 400 | Heavy missile | 5 | −30 | Anti-air capable. Shuts off in power deficit. Tall pillar with rotating launcher pod. |

---

### 1.7 Environmental Hazards

- **Sandworms** (see §1.5).
- **Spice Bloom eruption:** triggered by unit walking onto a buried bloom tile. Explodes with ~2 tile AoE, deals ~100 damage. Leaves behind a fresh 5–10 tile spice patch.
- **Sand damage** to buildings without concrete: −1 HP every ~3 seconds, capped at 50% HP minimum.

---

### 1.8 Victory Conditions

#### Campaign
- **9 missions per house**, branching map selection between missions (player picks one of two territories on a planet map screen).
- **Mission objectives:**
  - Destroy all enemy forces (most common).
  - Collect X Solaris worth of spice (early missions).
  - Destroy specific target building (e.g., a Sardaukar Castle).
  - Capture specific building (often a Starport or Palace).
  - Protect a building or unit for a duration.
  - Final mission: defeat both other houses plus Emperor's Sardaukar.
- **Difficulty modifiers:** Easy lowers player costs and raises AI costs; Hard reverses; Medium is neutral.

#### Skirmish & Multiplayer
- **Annihilation** only: destroy all enemy buildings and units (Construction Yard plus any unit-producing building).
- Map sizes range from small (1v1) to large (4 players).
- Starting credits configurable; starting unit set configurable (MCV-only vs. pre-built base).

---

### 1.9 Key Strategies (Summary)

- **Double Refinery economy:** open with two Refineries before any combat building.
- **Trike/Raider rush:** Ordos especially can win games before tanks even appear.
- **Engineer capture:** steal an enemy's Construction Yard for cross-faction unit access.
- **Starport tank-drop:** mass-order 6 Combat Tanks for instant delivery.
- **Concrete-everything turtle:** make all buildings invincible to sand wear; then mass Missile Tanks.
- **Devastator suicide rush:** drive 3 into the enemy base, self-destruct in sequence.
- **Sonic Tank firing line:** spread Sonic Tanks in a row; carefully micromanage to avoid friendly fire.
- **Sandworm-bait kiting:** lure enemy harvesters onto sand near a known worm path.

---

## Part 2: Remake Design

### 2.1 Design Goals

1. **Faithful gameplay** — preserve unit roles, building chain, and the feel of the economy/combat loop.
2. **Modern engine** — proper widescreen, scalable resolution, smooth 60+ fps, fluid camera.
3. **Improved AI** — the original AI was widely considered weak; a competent AI is the single highest-impact improvement.
4. **UX upgrades** — production queues, waypoints, rally points, smarter group movement, control groups.
5. **Look-and-feel preservation** — match the original's tone: gritty, brown/orange palette, weighty units, ambient desert wind.
6. **Data-driven & moddable** — every unit, building, weapon, and house definition in plain config files (JSON/YAML).
7. **Multiplayer ready** — LAN and online via deterministic lockstep.

---

### 2.2 Technology Stack

| Layer | Recommended | Why |
|---|---|---|
| Language | TypeScript (web) or C++/Rust (native) | TS for prototype; Rust/C++ for shipping perf |
| Rendering | Phaser 3 (web) or SDL2 + custom 2D renderer (native) | Mature, fast, sprite-friendly |
| ECS framework | bitECS (web) / EnTT (C++) / Bevy (Rust) | Performance for many entities |
| Pathfinding | A* + flow fields (group movement) | Handles 100+ unit moves efficiently |
| Audio | Web Audio API / OpenAL / FMOD | Positional audio, multiple channels |
| Networking | WebRTC DataChannels / ENet | Low-latency UDP for lockstep |
| Map format | Custom JSON, with optional Tiled import | Mod-friendly |
| Build tooling | Vite (web) / CMake or Cargo (native) | Standard |
| Sprite pipeline | Aseprite → texture atlas (TexturePacker) | Industry standard for pixel art |

A browser-first TypeScript prototype is recommended: feedback loop is fast, no platform issues, and porting to native later is straightforward once mechanics are correct.

---

### 2.3 System Architecture

```
┌────────────────────────────── Game Client ────────────────────────────────┐
│                                                                            │
│  ┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │  Input     │  │  UI System   │  │  Renderer  │  │  Audio Manager   │  │
│  │  Manager   │  │  (Sidebar,   │  │  (Sprite,  │  │  (SFX, Music,    │  │
│  │  (Mouse,   │  │  Minimap,    │  │  Tile,     │  │  Positional 2D)  │  │
│  │  Keyboard) │  │  Tooltips)   │  │  Particles)│  │                  │  │
│  └─────┬──────┘  └──────┬───────┘  └─────┬──────┘  └──────────────────┘  │
│        └────────────────┴─────────────────┘                                │
│                          │                                                 │
│                  ┌───────▼────────┐                                        │
│                  │   Game Loop    │  (fixed-step 30 Hz simulation,         │
│                  │                │   variable-step render)                │
│                  └───────┬────────┘                                        │
└──────────────────────────┼─────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼─────────── Game Simulation ─────────────────────┐
│                                                                            │
│  ┌─────────────┐ ┌────────────┐ ┌─────────────┐ ┌──────────────────┐     │
│  │ Entity /    │ │ Map &      │ │ Production  │ │ Combat System    │     │
│  │ Component   │ │ Terrain    │ │ Queue       │ │ (Targeting,      │     │
│  │ System (ECS)│ │ (Tiles,    │ │ (Build,     │ │  Damage,         │     │
│  │             │ │ Fog,Spice) │ │ Train,Rally)│ │  Projectile)     │     │
│  └─────────────┘ └────────────┘ └─────────────┘ └──────────────────┘     │
│                                                                            │
│  ┌─────────────┐ ┌────────────┐ ┌─────────────┐ ┌──────────────────┐     │
│  │ Pathfinding │ │ Economy    │ │ AI          │ │ Event /          │     │
│  │ (A*, Flow   │ │ (Spice,    │ │ Controller  │ │ Mission System   │     │
│  │ Fields,     │ │ Power,     │ │ (per-house  │ │ (Triggers,       │     │
│  │ Reservation)│ │ Credits)   │ │ behaviour)  │ │  Objectives)     │     │
│  └─────────────┘ └────────────┘ └─────────────┘ └──────────────────┘     │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │              Data Layer: JSON definitions for                       │ │
│  │   Units │ Buildings │ Weapons │ Houses │ Maps │ Missions │ AI       │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────── Network Layer (optional) ───────┐
│   Deterministic Lockstep │ Command Serialization │ Sync Verification      │
└────────────────────────────────────────────────────────────────────────────┘
```

**Key architectural decisions:**

- **ECS (Entity Component System):** every unit and building is an entity with composable components (Position, Sprite, Health, Weapon, Mover, Producer, Harvester, etc.). Systems operate over component sets each tick. This makes mod-adding new units trivial.
- **Fixed-step simulation:** 30 Hz simulation tick decouples logic from render frame rate, enables deterministic multiplayer.
- **Data-driven everything:** all unit stats, building definitions, weapon parameters live in JSON. No code changes needed to retune balance or add units.
- **Renderer is a thin layer:** reads ECS state and draws; no game logic in render code.

---

### 2.4 Implementation Phases — Task Lists

The work is grouped into eleven phases. Each phase is a coherent slice of functionality. The phases are roughly in dependency order, but several can overlap and run in parallel once foundations exist.

#### Phase 1 — Engine Foundation

- Set up project, build pipeline, and code organisation.
- Implement tile map renderer: rock, sand, dune, spice (light/heavy), cliff edges.
- Implement camera with pan (arrow keys, edge scroll, middle-mouse drag) and zoom.
- Implement entity/component system or chosen ECS.
- Implement input manager: left-click select, drag-box select, right-click action, double-click select-type, modifier keys.
- Implement fog-of-war tile state (hidden / explored / visible) with sprite-based shroud.
- Implement minimap renderer (full map at 1px per tile, with visibility shading).
- Implement HUD frame: top bar (Solaris, Power), right sidebar placeholder, bottom-left unit info panel.

#### Phase 2 — Pathfinding & Movement

- Implement A\* on the tile grid with terrain costs.
- Mark dune tiles impassable for vehicles, passable for infantry on designated passes.
- Implement unit collision and tile reservation to prevent overlap.
- Implement steering separation for adjacent units (avoid clumping).
- Implement flow-field pathfinding for groups (single field per destination, shared by group).
- Implement movement orders: move, attack-move, patrol, stop, hold position.
- Implement waypoints (shift-right-click chain).
- Implement smooth sprite rotation between facing directions (8 or 16 directions).

#### Phase 3 — Economy

- Implement spice tile types and visual tile depletion (heavy → light → empty).
- Implement Refinery entity with docking slot, harvester intake animation, credit deposit.
- Implement Harvester behaviour: seek nearest spice, harvest (multi-tick), return.
- Implement Carryall AI: idle, assign-to-harvester, pick-up, transport, drop-off.
- Implement Silo storage with overflow loss event.
- Implement Solaris HUD display with tick animation.
- Implement Wind Trap power output and global Power Pool.
- Implement power deficit effects: slow production, turn off Rocket Turrets, disable radar.
- Implement Spice Bloom trigger and AoE eruption with spice seeding.

#### Phase 4 — Base Building

- Implement Construction Yard sidebar UI with scrollable building list.
- Implement single-slot build queue with progress ring and cancel.
- Implement build placement mode with ghost preview, valid/invalid tile colouring.
- Implement concrete slab placement (2×2 and upgraded 4×4).
- Implement sand-wear damage for non-concrete buildings.
- Implement all universal buildings (Wind Trap, Refinery, Silo, Barracks, factories, Outpost, Repair Pad, High-Tech Factory, Starport, IX Research Center, Palace).
- Implement upgrade system per building (Construction Yard, Barracks, factories).
- Implement prerequisite resolution from JSON.
- Implement building construction animation (rise-from-pit) and damage states (3 stages: fine, smoking, critical).
- Implement Outpost-enabled radar/minimap activation.
- Implement multiple Construction Yards supporting parallel build queues.
- Implement building selling (refund partial cost over time).

#### Phase 5 — Combat System

- Implement Weapon component (damage, damage type, range, RoF, projectile, splash).
- Implement Armour component (none, light, medium, heavy) and damage multiplier table.
- Implement projectile entities: bullet (instant), shell (arc, splash), missile (homing), sonic wave (line, damage-over-distance), plasma (instant, glow).
- Implement weapon inaccuracy (target offset randomisation per shot).
- Implement targeting AI: auto-acquire nearest valid enemy in range when idle.
- Implement attack-move, target-priority overrides, hold-fire.
- Implement infantry crushing by vehicles.
- Implement Sardaukar/Grenadier explode-on-death.
- Implement engineer building capture (and friendly repair).
- Implement repair pad mechanics (cost-per-HP-restored, animation).
- Implement unit selling at Repair Pad.
- Implement Devastator self-destruct command and timer.
- Implement Deviator team-switch effect with revert timer.
- Implement Saboteur enter-building instant-demolish.
- Implement Sonic Tank linear AoE that fades with distance and damages friendlies.
- Implement Gun Turret (auto-fire, cloak-detection).
- Implement Rocket Turret (anti-air, power-gated).
- Implement Wall placement, auto-tiling sprite (T/L/cross/end), blocking behaviour.

#### Phase 6 — Faction Differentiation

- Load house data files (colours, banner, voice set, unit roster, building roster).
- Implement house-tinted sprite rendering (palette-swap or shader).
- Implement Atreides unit set (Combat Tank Atreides variant, Sonic Tank, Fremen, Grenadier, Ornithopter airstrike).
- Implement Harkonnen unit set (Combat Tank Harkonnen variant, Devastator, Sardaukar, Death Hand).
- Implement Ordos unit set (Combat Tank Ordos variant, Raider, Stealth Raider, Deviator, Saboteur).
- Implement Atreides Airstrike support power (target reticle, cooldown, ornithopter flight, bomb drop).
- Implement Death Hand superweapon (charge timer, launch animation, scatter inaccuracy, AoE).
- Implement Palace per-house production (auto-trains Fremen pair / Saboteur, or charges Death Hand).
- Implement Starport with CHOAM market: rotating stock, fluctuating prices, delivery via frigate sprite.
- Implement Ordos Starport exception (sells Missile Tank, sells Trike not Raider).
- Implement house-specific voice acknowledgements.

#### Phase 7 — Sandworms & Environment

- Implement Sandworm entity with patrol AI on sand.
- Implement vibration detection (sense moving units within radius).
- Implement surfacing animation, devour event, submerge.
- Implement worm despawn after N kills and respawn elsewhere.
- Implement underground "wake" indicator on shroud-revealed sand.
- Implement Thumper deployment and worm-attraction behaviour.
- Implement worm-blocked tiles (rock prevents traversal).
- Implement ambient sand particle drift, occasional small dust devils for atmosphere.

#### Phase 8 — AI Controller

- Implement AI state machine: Boot → Economy → Tech-Up → Pressure → All-Out.
- Implement base-building priority queue (Wind Trap when low power, Refinery when expanding, defences when threatened).
- Implement production loop (mix unit types per phase, scale with available power and credits).
- Implement Harvester management (assign per Refinery, escort with light units).
- Implement attack composition rules (size threshold before launching, prefer balanced army).
- Implement target selection (prefer Refinery > Construction Yard > production buildings > defences > units).
- Implement defence reaction (intercept incoming attackers, repair damaged buildings).
- Implement Engineer use (only at low risk; AI can capture enemy structures).
- Implement superweapon use (target densest building cluster).
- Implement difficulty modifiers (cost multipliers, build-speed multipliers).
- Implement AI personality presets per house (Atreides defensive-and-air, Harkonnen brute-push, Ordos hit-and-run-with-Saboteurs).

#### Phase 9 — Campaign System

- Implement mission file format (JSON: map ref, starting units, objectives, triggers, briefing text).
- Implement objective system (kill X, capture Y, collect Z credits, protect W, time-based).
- Implement trigger system (on-time, on-condition, spawn reinforcements, send chat from mentat).
- Implement Mentat briefing screen (FMV slot, animated portrait, scrolling text).
- Implement planet selection screen between missions (two-territory branching choice).
- Implement campaign save/load (per-house progress).
- Build all 27 campaign maps (9 per house) with original objectives, or generate a starter set procedurally for v1.
- Implement Emperor reinforcement system (Sardaukar drop trigger in late missions).
- Implement campaign-only units (Thumper, special heroes if desired).

#### Phase 10 — Multiplayer

- Implement deterministic lockstep simulation (fixed-point math; seeded RNG).
- Implement command serialization (player inputs → tagged commands with simulation tick).
- Implement transport layer (WebRTC or ENet) with reliable command delivery.
- Implement lobby system (host, join, ready, house pick, map pick, slot config).
- Implement sync verification (CRC of game state every N ticks; detect and report desync).
- Implement spectator/observer mode.
- Implement reconnect from disconnect (stretch).
- Implement multiplayer-only unit gating (Stealth Raider, post-1.06 Sardaukar / Grenadier).

#### Phase 11 — Polish, Audio, and Mod Support

- Implement full audio set: unit ack/move/attack/death per house, weapon impacts, ambient wind, music tracks.
- Implement positional audio (panning by screen position, volume by zoom).
- Implement particle systems: explosions, dust trails, spice plumes, sonic shockwaves, plasma glow, building damage smoke, missile trails.
- Implement damage-state sprite swapping on buildings and vehicles.
- Implement death animations (vehicle wreckage, infantry ragdoll, building collapse).
- Implement HUD polish: animated build progress, hover tooltips, structure power readouts, queue badges.
- Implement settings menu (resolution, fullscreen, audio mix, hotkey rebinding, scroll speed).
- Implement map editor (paint terrain, place spice, place units, set objectives, export JSON).
- Implement mod loader (override JSON files; override sprite atlases; add new units/houses).
- Implement save/load for skirmish and campaign.
- Implement replays (record command stream + initial seed; play back deterministically).

---

### 2.5 Look-and-Feel Reference

To make the remake *feel* like Dune 2000 — not just function like it — these details matter:

**Visual palette**
- Dominant: warm sand-tan (#C9A878), rust-orange (#B85C3A), dusty grey rock (#7A7568), deep night-black shroud.
- House accents pop against the desert: Atreides royal blue, Harkonnen blood red, Ordos sickly green.
- High contrast between UI (cool steel-grey panels with house-coloured trim) and the warm tan/orange game world.

**Sprite philosophy**
- Pixel art at native resolution (e.g., 64×64 sprites for vehicles), upscaled with pixel-perfect or HQ4x filtering depending on user setting.
- 8 facing directions minimum for infantry; 16+ for vehicles.
- Heavy emphasis on **weight**: vehicles take a half-second to start moving (acceleration), tracks kick up visible dust, turrets recoil visibly when firing.
- Buildings cast a soft drop shadow to the south-east for depth.

**Animation philosophy**
- Idle animations are subtle (infantry sway, harvesters vent steam, walls flicker dust).
- Construction is theatrical: scaffolding rises, sparks fly, the building "pops" into completion with a small puff.
- Death is satisfying: explosions are framed at multiple sizes, with debris arcs and lingering smoke pillars.

**Sound philosophy**
- A constant low-frequency wind bed underneath everything.
- Unit acknowledgements are short, distinct, and per-house (not just retinted clips).
- Music: the original soundtrack by Frank Klepacki uses driving percussion and Middle-Eastern instrumentation — a remake should commission tracks in the same idiom rather than reusing them. Tracks fade in during combat and fade to ambient during peace.
- Sandworm rumble grows louder and lower in pitch as it nears the screen edge — a primary tension generator.

**UI philosophy**
- Vertical right-side sidebar is non-negotiable; it is iconic.
- Tabs (Buildings / Units) with grid of icons; progress ring around the currently building icon; "Ready" pulse when complete.
- Top bar shows Solaris, Power, and mission objectives.
- Minimap in bottom-right with click-to-jump and right-click-move.
- All UI elements use the cool-steel-with-house-accent palette to contrast the warm desert below.

**Game feel touches**
- Camera shake on Death Hand impact and Devastator self-destruct.
- Brief screen flash on superweapon detonation.
- A subtle "tick" sound every Solaris milestone (every 1000 earned).
- Spice harvesting causes a small visible orange particle burst at the Harvester intake.
- When a sandworm appears, the music drops out for 2 seconds — only the rumble plays.

These details are the difference between a working clone and a remake that captures why people remember the original.

---

*Document for an educational/fan remake project. All Dune 2000 IP belongs to its original holders.*
