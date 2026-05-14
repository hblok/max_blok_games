# Dune 2000 Handheld — Simplified Design Plan

## Overview

A simplified 1v1 skirmish version of Dune 2000 designed for handheld devices (3" 640x480 screen, scalable) and playable by children. This version removes complex systems, reduces unit/building counts, and prioritizes controller-based input over on-screen buttons.

---

## Design Philosophy

### Core Simplifications

- **No power system** — Wind Traps removed entirely
- **No building upgrades** — All buildings available at base level
- **No concrete foundations** — Buildings don't degrade
- **No Silos** — Unlimited credit storage
- **No Carryalls** — Harvesters drive everywhere
- **No Starport** — All units built from factories
- **No Spice Blooms** — Simplified economy
- **No Sandworms** — Removed environmental hazard
- **No walls** — Simplified base defense
- **No engineers** — No building capture mechanic

### Target Audience Considerations

- Simple, intuitive controls using controller buttons
- Clear visual feedback for all actions
- Shorter game sessions (10-15 minutes)
- Forgiving gameplay (no harsh penalties)
- Immediate gratification (fast unit production)

---

## Screen Layout (640x480 Base)

```
┌─────────────────────────────────────────────────────────┐
│  [Solaris: 2500]  [House: Atreides]  [Time: 5:23]       │  ← Top Bar (40px)
├─────────────────────────────────────────────────────────┤
│                                                           │
│                                                           │
│                    GAME VIEW (360px)                      │
│                                                           │
│                                                           │
├─────────────────────────────────────────────────────────┤
│  [Minimap]  [Selected Unit Info]  [Quick Actions]       │  ← Bottom Bar (80px)
└─────────────────────────────────────────────────────────┘
```

**Scaling:** All UI elements scale proportionally to maintain visibility on different screen sizes.

---

## Controller Mapping

### Standard Controller Layout

```
     [L1] [R1]      [L2] [R2]
     [L3] [R3]      [Select] [Start]
     
     [D-Pad]        [Left Stick]  [Right Stick]
     
     [Y] [X]        [A] [B]
```

### Button Functions

| Button | Primary Function | Secondary Function (Hold) |
|--------|------------------|---------------------------|
| **A** | Select unit / Confirm action | Select all units of type |
| **B** | Move / Attack | Attack-move |
| **X** | Build menu | Cancel current action |
| **Y** | Unit production menu | Rally point mode |
| **L1** | Cycle building types | - |
| **R1** | Cycle unit types | - |
| **L2** | Previous unit in selection | - |
| **R2** | Next unit in selection | - |
| **D-Pad** | Camera pan | - |
| **Left Stick** | Camera pan (smooth) | - |
| **Right Stick** | Scroll minimap cursor | - |
| **Start** | Pause game | - |
| **Select** | Toggle minimap | - |
| **Menu** | Exit to main menu | - |

### Control Philosophy

- **No on-screen buttons** — All actions via controller
- **Context-sensitive menus** — Press X/Y to open radial menus
- **Quick actions** — Bottom bar shows 4 context-sensitive actions mapped to face buttons
- **Visual feedback** — Button prompts appear on screen for current context

---

## Two Houses Only

### House Atreides — "The Noble"

**Colors:** Blue and gold
**Playstyle:** Balanced, ranged combat

**Unique Unit:** Sonic Tank
- Long-range sonic wave
- Damages all units in line (including friendlies)
- Best used at distance

**Special Ability:** Fremen Warriors (spawn from Palace)
- Cloaked infantry
- Strong vs. vehicles

### House Harkonnen — "The Brutal"

**Colors:** Red and black
**Playstyle:** Heavy, slow, powerful

**Unique Unit:** Devastator
- Heaviest tank in game
- Self-destruct ability (hold B when selected)
- Very slow but devastating

**Special Ability:** Death Hand Missile (from Palace)
- Long-range superweapon
- Large area damage
- Long cooldown

---

## Simplified Buildings (8 Total)

### Building List

| Building | Cost | Function | Prerequisite |
|----------|------|----------|--------------|
| Construction Yard | 1500 | Builds all structures | Start with MCV |
| Spice Refinery | 800 | Converts spice to credits | Construction Yard |
| Barracks | 250 | Trains infantry | Construction Yard |
| Light Factory | 400 | Builds light vehicles | Refinery |
| Heavy Factory | 700 | Builds heavy vehicles | Refinery |
| Outpost | 300 | Provides radar/minimap | Barracks |
| Repair Pad | 600 | Repairs vehicles | Heavy Factory |
| Palace | 1200 | Unlocks special ability | Outpost + Heavy Factory |

### Simplified Tech Tree

```
Construction Yard (start)
├── Spice Refinery
│   ├── Light Factory
│   └── Heavy Factory → Repair Pad
├── Barracks → Outpost
└── Palace (requires Outpost + Heavy Factory)
```

### Building Changes from Original

- **No Wind Traps** — Power system removed
- **No Silos** — Unlimited credit storage
- **No Concrete Slabs** — Buildings don't degrade
- **No Walls** — Simplified defense
- **No High-Tech Factory** — No Carryalls needed
- **No Starport** — All units built from factories
- **No IX Research Center** — Simplified tech tree
- **No Gun/Rocket Turrets** — Defense relies on units

---

## Simplified Units (8 Total)

### Infantry (3 types)

| Unit | Cost | HP | Role | Produced From |
|------|------|-----|------|---------------|
| Light Infantry | 50 | 60 | Basic combat | Barracks |
| Trooper | 80 | 80 | Anti-vehicle | Barracks |
| Fremen | Free* | 120 | Elite cloaked | Palace (cooldown) |

*Fremen spawn in pairs every 60 seconds from Palace

### Light Vehicles (2 types)

| Unit | Cost | HP | Speed | Role | Produced From |
|------|------|-----|-------|------|---------------|
| Trike | 120 | 100 | Very Fast | Scout / harass | Light Factory |
| Quad | 180 | 150 | Fast | Anti-vehicle | Light Factory |

### Heavy Vehicles (3 types)

| Unit | Cost | HP | Speed | Role | Produced From |
|------|------|-----|-------|------|---------------|
| Harvester | 1000 | 600 | Very Slow | Collect spice | Heavy Factory |
| Combat Tank | 600 | 350 | Medium | Main battle tank | Heavy Factory |
| Sonic/Devastator | 850 | 300 | Medium | Unique unit | Heavy Factory |

### Unit Simplifications

- **No Siege Tank** — Simplified vehicle roster
- **No Missile Tank** — Simplified vehicle roster
- **No MCV** — Only one Construction Yard per game
- **No Engineers** — No building capture
- **No Grenadiers/Saboteurs** — Simplified infantry
- **No Sardaukar** — Simplified infantry
- **No Stealth Raider** — Simplified vehicles
- **No Carryalls** — Harvesters drive everywhere

---

## Simplified Economy

### Resource System

**Spice Only**
- Spice appears as orange patches on sand
- Two types: Light (single layer) and Heavy (double layer)
- Heavy spice yields 50% more per harvest

**Harvesting Loop**
1. Harvester automatically seeks nearest spice
2. Harvests for 5 seconds per tile
3. Returns to Refinery when full (700 credits)
4. Unloads and repeats

**No Power System**
- All buildings work at full speed immediately
- No power bars or management needed

**No Silos**
- Unlimited credit storage
- No "Spice Lost" messages

**No Carryalls**
- Harvesters drive to spice and back
- Slower economy but simpler to understand

### Starting Economy

- Start with: 1 Construction Yard, 1 Refinery, 1 Harvester, 500 credits
- First action: Build second Refinery for faster economy
- Recommended: 2-3 Harvesters per Refinery

---

## Simplified Combat

### Combat Mechanics

**Selection**
- A button: Select single unit
- Hold A + D-pad: Box select multiple units
- Double-tap A: Select all units of type on screen

**Movement**
- B button: Move selected units
- Hold B: Attack-move (attack enemies on path)

**Attacking**
- B on enemy: Attack specific target
- Units auto-attack enemies in range when idle

**Damage System**
- Simplified damage types: Bullet, Rocket, Sonic, Plasma
- No complex armor/damage tables
- Simple rule: Rockets > Vehicles, Bullets > Infantry

**Unit Behavior**
- Units don't slow down when damaged
- No friendly fire (except Sonic Tank)
- Vehicles can crush infantry

### Removed Combat Features

- **No crushing damage to vehicles** (Sardaukar explosion)
- **No unit self-destruct** (except Devastator ability)
- **No building capture** (no engineers)
- **No unit repair at Repair Pad** — simplified to auto-repair near base
- **No unit selling** — simplified economy

---

## Game Modes

### 1v1 Skirmish Only

**Victory Condition**
- Destroy all enemy buildings
- OR Destroy enemy Construction Yard

**Game Settings**
- Map size: Small (optimized for handheld)
- Starting credits: 500
- Game speed: Normal (can be adjusted)
- AI difficulty: Easy, Medium, Hard

**Map Features**
- Rock terrain for building
- Sand terrain for movement
- Spice fields scattered
- No dunes/mountains (simplified terrain)
- No cliffs (simplified navigation)

### AI Behavior

**Easy Mode**
- Slower unit production
- Smaller attack groups
- Defensive playstyle
- Ideal for learning

**Medium Mode**
- Balanced production
- Mixed attack groups
- Moderate aggression
- Standard challenge

**Hard Mode**
- Faster production
- Larger attack waves
- Aggressive expansion
- For experienced players

---

## UI Design

### Top Bar (40px height)

```
[Solaris: 2500]  [Atreides vs Harkonnen]  [Time: 5:23]
```

- Solaris counter with animated tick-up
- House indicators with colors
- Game timer

### Bottom Bar (80px height)

```
[Minimap 120x80]  [Unit Info]  [Action Buttons]
```

**Minimap**
- Shows explored terrain
- Shows units as colored dots
- Right stick moves cursor
- A button jumps camera

**Unit Info Panel**
- Shows selected unit type
- Health bar
- Simple stats (Attack/Defense)

**Action Buttons**
- 4 context-sensitive buttons
- Shows current button mappings
- Changes based on selection

### Build Menu (Radial)

Press X to open building menu:
- L1/R1: Cycle building types
- A: Build selected
- B: Cancel

Shows:
- Building icon
- Cost
- Prerequisite status (green/red)

### Unit Production Menu (Radial)

Press Y to open unit menu:
- L1/R1: Cycle unit types
- A: Train unit
- B: Cancel

Shows:
- Unit icon
- Cost
- Production time
- Queue status

---

## Visual Design

### Color Palette

**Terrain**
- Rock: #7A7568 (grey-brown)
- Sand: #C9A878 (tan)
- Spice Light: #D48A4E (orange)
- Spice Heavy: #E8A050 (bright orange)

**Houses**
- Atreides: #2E5C8E (blue)
- Harkonnen: #8B2E2E (red)

**UI**
- Background: #3A3A3A (dark grey)
- Text: #FFFFFF (white)
- Highlights: #FFD700 (gold)

### Sprite Guidelines

**Size**
- Infantry: 24x24 pixels
- Light vehicles: 32x32 pixels
- Heavy vehicles: 48x48 pixels
- Buildings: 64x64 to 96x96 pixels

**Directions**
- Infantry: 8 directions
- Vehicles: 16 directions

**Animations**
- Idle, Move, Attack, Death
- Simple 2-4 frame animations
- Clear visual feedback

### Effects

**Harvesting**
- Orange particles when collecting spice
- Visible spice depletion

**Combat**
- Muzzle flashes
- Explosion particles
- Damage numbers (optional)

**Building**
- Construction animation (rise from ground)
- Damage states (cracks, smoke)

---

## Audio Design

### Sound Effects

**Unit Responses**
- Short, clear acknowledgements
- Different per house
- "Yes", "Moving", "Attacking"

**Combat**
- Weapon sounds (cannons, rockets, sonic)
- Explosion sounds
- Impact sounds

**Economy**
- Harvester motor
- Spice collection sound
- Credit tick sound

**UI**
- Button clicks
- Menu opens/closes
- Error sounds

### Music

**Style**
- Driving, percussive
- Middle-Eastern influence
- Loops seamlessly

**Dynamic**
- Peaceful during economy phase
- Intensifies during combat
- Fades during superweapon

---

## Technical Specifications

### Performance Targets

- Frame rate: 30 FPS minimum
- Load time: < 5 seconds
- Save size: < 1 MB
- Memory: < 200 MB

### Screen Support

**Base Resolution:** 640x480
**Supported Resolutions:**
- 320x240 (very small screens)
- 640x480 (base)
- 800x600 (larger screens)
- 1024x768 (tablets)

All UI scales proportionally.

### Input Support

- Game controllers (primary)
- Touch fallback (optional)
- Keyboard fallback (for testing)

---

## Development Phases

### Phase 1: Core Engine (2 weeks)
- Tile map rendering
- Camera system
- Basic input handling
- Entity system

### Phase 2: Economy (1 week)
- Spice harvesting
- Credit system
- Building placement
- Unit production

### Phase 3: Combat (1 week)
- Unit movement
- Attack system
- Damage calculation
- AI basics

### Phase 4: UI (1 week)
- HUD implementation
- Menus
- Controller mapping
- Visual feedback

### Phase 5: Polish (1 week)
- Audio integration
- Visual effects
- Balance tuning
- Bug fixes

**Total: ~6 weeks for MVP**

---

## Balance Considerations

### Economy Balance

- Early game: Focus on 2 Refineries
- Mid game: 3-4 Harvesters total
- Late game: Expand to new spice fields

### Unit Balance

- Infantry: Cheap, weak vs. vehicles
- Light vehicles: Fast, weak armor
- Heavy vehicles: Slow, powerful
- Unique units: Situational but strong

### House Balance

- Atreides: Ranged advantage, Fremen support
- Harkonnen: Raw power, Devastator dominance

### Game Length

Target: 10-15 minutes per match
- Early game: 3-5 minutes (economy setup)
- Mid game: 5-8 minutes (unit production)
- Late game: 2-5 minutes (final battles)

---

## Educational Value

### Skills Developed

- **Resource Management** — Balancing economy and military
- **Strategic Thinking** — Planning attacks and defenses
- **Decision Making** — Quick choices under pressure
- **Spatial Awareness** — Map navigation and positioning
- **Pattern Recognition** — Understanding unit counters

### Age-Appropriate Features

- Simple controls (controller-based)
- Clear visual feedback
- Forgiving gameplay
- Short sessions
- No complex reading required

---

## Future Expansion Ideas

### Potential Additions (Post-Launch)

1. **Third House (Ordos)** — Stealth and speed focus
2. **Additional Maps** — More terrain variety
3. **Campaign Mode** — Simple mission progression
4. **Multiplayer** — Local 1v1 on same device
5. **Tutorial Mode** — Interactive learning
6. **Difficulty Settings** — More granular options
7. **Unit Skins** — Cosmetic customization
8. **Sound Options** — Music and SFX volume

### Not Recommended for Simplified Version

- Complex tech trees
- Building upgrades
- Power management
- Multiple resource types
- Large-scale battles (20+ units)
- Complex mission objectives
- Story campaigns

---

## Conclusion

This simplified Dune 2000 handheld version captures the essence of the original while making it accessible to young players on small screens. By removing complex systems (power, upgrades, capture) and focusing on core gameplay (harvest, build, fight), the game becomes approachable without losing strategic depth.

The controller-based interface eliminates touch-screen fatigue, while the simplified unit and building counts reduce cognitive load. The 1v1 skirmish format provides complete, satisfying game sessions in 10-15 minutes — perfect for handheld play.

**Key Success Metrics:**
- 8-year-old can learn basics in 5 minutes
- Complete match in 15 minutes
- Clear visual feedback for all actions
- Fun, engaging gameplay loop
- Stable 30 FPS performance

---

*Document created for simplified handheld adaptation of Dune 2000. Original game by Westwood/Intelligent Games (1998).*