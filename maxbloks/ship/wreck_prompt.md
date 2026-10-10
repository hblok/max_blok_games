# Ship wreck SVG: drawing prompt

Draft v3. Describes what to draw and how. Edit this file, then render.

## Decisions
- Canvas: 1200x800.
- Style: cartoon, but not at all childish. Extremely polished, like a premium console/mobile game background or a feature-animation concept painting.
- Use: game background. Gameplay sprites will be drawn on top, so the image must support them, not compete with them.

## Output
- Single self-contained SVG, `viewBox="0 0 1200 800"`, no external assets, no raster images, no scripts.
- Layered `<g id="...">` groups in the paint order below, so each layer can be tweaked alone.
- Vector cartoon rendering: clean shapes, soft gradients, a few filters (blur for light shafts and depth haze, turbulence only for subtle sand/water texture).

## Style: polished cartoon, not childish
- Shape language: clean, confident silhouettes with slightly exaggerated proportions (chunky timbers, a nicely curved hull), but believable structure. No bubbly, rounded "toy" shapes.
- Shading: every mid-ground object gets at least 3 tones: base, shadow, highlight, plus a thin rim light on the side facing the sun. Single consistent light direction (upper left).
- Shadows are colour-tinted (deep teal/blue-violet), never black or grey.
- Outlines: thin (1.5 to 2.5px), coloured as a darker shade of the fill, never pure black. Distant layers have no outlines at all.
- Palette is restrained and harmonious: muted, slightly desaturated tones; no pure primaries, no candy colours.
- Detail is deliberate: fewer, well-placed details (a few nicely shaped planks, cracks, barnacle clusters) instead of noise everywhere.
- Avoid: faces or eyes on fish/crabs, smiles, googly eyes, sparkles/stars, rainbow colours, thick black outlines, clip-art look.

## Scene
A 17th-century war galleon, centuries on the seabed: huge, dark and broken, but still imposing. Seen from the side and slightly from below, so it towers over the viewer. Late afternoon sunlight falls from the upper left through the surface, but the wreck sits mostly in its own shadow; only its top edges catch a cold rim of light. Mood: ominous, ancient, heavy silence. Something you do not swim into. Ominous through scale, silhouette and darkness, never through cheap horror props (no skulls, ghosts or faces).

## Layers (back to front)

1. **Water background** (`#water`): vertical gradient, bright turquoise `#3fa9b5` at the top to deep blue `#0b2e4a` at the bottom.
2. **Light shafts** (`#rays`): 5 to 7 translucent white wedges from the top-left surface down to the seabed, opacity 0.08 to 0.18, Gaussian blur ~6. Surface edge at the top: a wavy lighter band.
3. **Distant seabed** (`#far-sand`): low dunes, desaturated blue-green, low contrast, faded as if by distance. A few far rock silhouettes.
4. **Seabed** (`#sand`): warm sand `#c9b27c` darkening to `#6e6244` at the edges. Ripple lines (thin, slightly curved, low opacity). Patches of darker sediment near the hull.
5. **Hull** (`#hull`), the focal point, about 65% of the width, centered slightly right:
   - Galleon profile: low forecastle and beakhead at the bow (left), a long waist, then a towering stern castle (quarterdeck + poop deck) on the right, the highest part of the ship.
   - Tilted ~7 degrees the other way than v2: bow nosed down and buried in a sand mound, stern rearing up and resting on a rock outcrop. The stern castle is the dominant shape.
   - Planking: dark, cold-tinted wood (`#3a2c22` to `#5a4632`), plank seams, butt joints, and a thick wale along each gun deck.
   - Two gun decks: a lower row and an upper row of gun ports. Most lids gone, a few hanging; a few cannon muzzles still poking out.
   - Quarter gallery on the stern castle: a bay with tall arched windows, the glass long gone, black inside.
   - Tarnished, once-gilded carved trim along the rails and around the gallery (dull ochre, barely readable).
   - A broken stern lantern hanging askew from its bracket at the very top of the stern.
   - Beakhead at the bow with a weathered, eroded figurehead stub (no recognisable face) and a snapped bowsprit.
   - A large jagged break amidships: ribs exposed like a rib cage, some snapped, a deck beam visible inside.
   - Faint eerie inner glow: a very low-opacity cold teal-green glow inside the break, a few gun ports and the gallery windows. Barely there, felt more than seen.
   - Weathering: heavy algae on the lower hull, barnacle clusters, long dark weed strands draping down from the rails.
6. **Masts and rigging** (`#masts`):
   - Main mast still stands, slightly leaning back, snapped at the top, with its fighting top (round platform) intact: the tallest silhouette in the image.
   - Foremast broken and leaning far forward; mizzen snapped, leaning back, with a slanted lateen yard.
   - Shrouds with ratlines (rope ladders) running from the main top down to the hull side, partly torn.
   - Long tattered sails hanging from the yards and drifting like shrouds, semi-transparent.
   - Loose ropes drifting upward.
7. **Debris** (`#debris`): broken planks half in sand, a barrel on its side, a fallen anchor with a chain trailing across the sand, a cannon, a few scattered crates, a couple of clay amphora shards.
8. **Life** (`#life`): sparse and low contrast so it is never mistaken for a gameplay sprite. A distant school of 10 to 15 tiny fish as hazy silhouettes in the upper background (bluish, low opacity); no large or brightly coloured fish; a crab by the anchor; a starfish; coral fans and sea fern growing on the hull and rocks in muted pinks and purples.
9. **Foreground** (`#fore`): dark kelp fronds at the far left and right edges only (max ~80px into the frame), slightly blurred, framing the scene. Rising bubbles (small circles with a light stroke) from the break in the hull.
10. **Atmosphere** (`#vignette`): radial dark vignette at the corners, ~30% opacity; faint floating particles (tiny white dots, opacity 0.2 to 0.4).

## Colour palette
| Role | Hex |
|------|-----|
| Water top | `#3fa9b5` |
| Water bottom | `#0b2e4a` |
| Sand light / dark | `#c9b27c` / `#6e6244` |
| Wood dark / mid | `#3a2c22` / `#5a4632` |
| Rim light (cold) | `#cfe8dc` |
| Inner glow | `#6fe3c6` at very low opacity |
| Tarnished gilt | `#8a7a4a` |
| Algae | `#4f7a3a` |
| Sail cloth | `#d8cfb8` |
| Fish silver / orange | `#cfd8dc` / `#e8863a` |
| Coral | `#d46a8a`, `#8e5fa8` |

## Composition rules
- Play area: the band y≈80 to 540 is mostly open water. Keep it low contrast, low detail and free of hard edges, so sprites read clearly on top.
- Only the stern castle, masts, rigging and sails may rise into the play area (up to y≈300), and only as hazy, low-contrast dark silhouettes fading into the water.
- The wreck is the most detailed element, but its contrast and saturation stay below what gameplay sprites will use. No pure white highlights except tiny glints.
- Hull is the focal point at the bottom; everything else supports it.
- Depth by contrast: distant elements are bluer and lower contrast.
- Keep important shapes clear of the edges, except the framing kelp.
- Deterministic output: no randomness at render time (if a generator script is used, fix the seed).

## Out of scope
Animation, text/labels, people or skeletons, treasure.
