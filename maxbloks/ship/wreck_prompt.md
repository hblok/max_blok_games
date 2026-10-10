# Ship wreck SVG: drawing prompt

Draft v2. Describes what to draw and how. Edit this file, then render.

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
An old wooden three-masted sailing ship, broken and half buried on a sandy seabed, seen from the side in shallow, clear water. Late afternoon sunlight falls from the upper left through the surface. Mood: quiet, ancient, slightly eerie but not scary.

## Layers (back to front)

1. **Water background** (`#water`): vertical gradient, bright turquoise `#3fa9b5` at the top to deep blue `#0b2e4a` at the bottom.
2. **Light shafts** (`#rays`): 5 to 7 translucent white wedges from the top-left surface down to the seabed, opacity 0.08 to 0.18, Gaussian blur ~6. Surface edge at the top: a wavy lighter band.
3. **Distant seabed** (`#far-sand`): low dunes, desaturated blue-green, low contrast, faded as if by distance. A few far rock silhouettes.
4. **Seabed** (`#sand`): warm sand `#c9b27c` darkening to `#6e6244` at the edges. Ripple lines (thin, slightly curved, low opacity). Patches of darker sediment near the hull.
5. **Hull** (`#hull`), the focal point, about 55% of the width, centered slightly right, sitting in the bottom third (top of the hull no higher than y≈540):
   - Tilted about 15 degrees, bow raised on the left, stern sunk deeper in the sand on the right.
   - Planking: dark brown `#4a3320`, with horizontal plank seams as thin darker lines and uneven plank colour variation.
   - A large jagged break amidships: ribs (curved timbers) exposed like a rib cage, 8 to 10 ribs, some snapped.
   - Missing planks near the keel, showing dark interior. Keel visible as a thick beam at the bottom.
   - Row of 4 small gun ports on the intact side, some with open hatches hanging.
   - Green algae and brown weed stains on the lower half; white barnacle dots clustered along the waterline of the wreck.
6. **Masts and rigging** (`#masts`):
   - Masts are short broken stumps so they stay out of the play area: nothing rises above y≈380, and anything above y≈540 is drawn in the hazy distance tone.
   - Main mast snapped at about one third height, splintered top.
   - Foremast leaning at ~35 degrees, a yard arm still attached.
   - Mizzen mast missing; only a stump.
   - Torn sail remnants: a few pale, ragged cloth shapes drifting in the current, semi-transparent, with holes.
   - Ropes: thin curved dark lines sagging from the masts, some ending loose and floating.
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
| Wood dark / mid | `#4a3320` / `#7a5a3a` |
| Algae | `#4f7a3a` |
| Sail cloth | `#d8cfb8` |
| Fish silver / orange | `#cfd8dc` / `#e8863a` |
| Coral | `#d46a8a`, `#8e5fa8` |

## Composition rules
- Play area: the band y≈80 to 540 is mostly open water. Keep it low contrast, low detail and free of hard edges, so sprites read clearly on top.
- The wreck is the most detailed element, but its contrast and saturation stay below what gameplay sprites will use. No pure white highlights except tiny glints.
- Hull is the focal point at the bottom; everything else supports it.
- Depth by contrast: distant elements are bluer and lower contrast.
- Keep important shapes clear of the edges, except the framing kelp.
- Deterministic output: no randomness at render time (if a generator script is used, fix the seed).

## Out of scope for v1
Animation, text/labels, people or skeletons, treasure.
