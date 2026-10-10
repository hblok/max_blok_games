"""Generate wreck.svg from wreck_prompt.md (v3). Deterministic (fixed seed).

Usage: python maxbloks/ship/gen_wreck.py maxbloks/ship/wreck.svg
"""
import math
import random
import sys

R = random.Random(16)
W, H = 1200, 800
out = []
o = out.append


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def pts(seq):
    return " ".join(f"{f(x)},{f(y)}" for x, y in seq)


# Hull placement (local coords: bow at -x, deck at -y), rotated so the stern castle rears up.
HX, HY, HROT = 640, 650, -7

o(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
o("""<defs>
  <linearGradient id="gWater" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3fa9b5"/><stop offset="0.45" stop-color="#1a6079"/>
    <stop offset="0.8" stop-color="#0f3854"/><stop offset="1" stop-color="#0b2e4a"/>
  </linearGradient>
  <radialGradient id="gSun" cx="0.12" cy="-0.05" r="0.75">
    <stop offset="0" stop-color="#b6efe4" stop-opacity="0.45"/><stop offset="1" stop-color="#b6efe4" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="gRay" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity="1"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="gFar1" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2f7682"/><stop offset="1" stop-color="#1b4f63"/>
  </linearGradient>
  <linearGradient id="gFar2" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#4f8a83"/><stop offset="1" stop-color="#2f5f63"/>
  </linearGradient>
  <radialGradient id="gSand" cx="600" cy="690" r="720" gradientUnits="userSpaceOnUse" gradientTransform="translate(0 -30) scale(1 0.6) translate(0 460)">
    <stop offset="0" stop-color="#c9b27c"/><stop offset="0.55" stop-color="#a8956a"/><stop offset="1" stop-color="#6e6244"/>
  </radialGradient>
  <linearGradient id="gSandHaze" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a7486" stop-opacity="0.55"/><stop offset="0.35" stop-color="#2a7486" stop-opacity="0.12"/>
    <stop offset="1" stop-color="#0b2e4a" stop-opacity="0.35"/>
  </linearGradient>
  <linearGradient id="gHull" x1="0" y1="-215" x2="0" y2="105" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#6a5a48"/><stop offset="0.25" stop-color="#5a4632"/>
    <stop offset="0.65" stop-color="#3a2c22"/><stop offset="1" stop-color="#1c1c1e"/>
  </linearGradient>
  <linearGradient id="gHullShade" x1="0" y1="-215" x2="0" y2="105" gradientUnits="userSpaceOnUse">
    <stop offset="0.3" stop-color="#0a2229" stop-opacity="0"/><stop offset="1" stop-color="#0a2229" stop-opacity="0.7"/>
  </linearGradient>
  <linearGradient id="gHullSide" x1="-405" y1="0" x2="400" y2="0" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#cfe8dc" stop-opacity="0.12"/><stop offset="0.35" stop-color="#cfe8dc" stop-opacity="0"/>
    <stop offset="1" stop-color="#0a2229" stop-opacity="0.35"/>
  </linearGradient>
  <linearGradient id="gMast" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#6f7568"/><stop offset="0.45" stop-color="#4a524a"/><stop offset="1" stop-color="#2c3434"/>
  </linearGradient>
  <linearGradient id="gHaze" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a7a8c" stop-opacity="0.65"/><stop offset="1" stop-color="#2a7a8c" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="gCannon" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#6d7a76"/><stop offset="0.4" stop-color="#3b4644"/><stop offset="1" stop-color="#1f2a2c"/>
  </linearGradient>
  <linearGradient id="gBarrel" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#9a7448"/><stop offset="0.5" stop-color="#6e5034"/><stop offset="1" stop-color="#3a2a1e"/>
  </linearGradient>
  <linearGradient id="gRock" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#6f8f8a"/><stop offset="0.5" stop-color="#435f63"/><stop offset="1" stop-color="#26404a"/>
  </linearGradient>
  <linearGradient id="gKelp" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1c4a45"/><stop offset="1" stop-color="#0b2328"/>
  </linearGradient>
  <radialGradient id="gVig" cx="0.5" cy="0.45" r="0.75">
    <stop offset="0.6" stop-color="#04121c" stop-opacity="0"/><stop offset="1" stop-color="#04121c" stop-opacity="0.38"/>
  </radialGradient>
  <filter id="fRay" x="-20%" y="-5%" width="140%" height="110%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="fSoft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
  <filter id="fGlow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="5"/></filter>
  <filter id="fFar" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="1.6"/></filter>
  <filter id="fKelp" x="-30%" y="-5%" width="160%" height="110%"><feGaussianBlur stdDeviation="2"/></filter>
  <filter id="fSandTex" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.25  0 0 0 0 0.2  0 0 0 0 0.12  0 0 0 0.35 0" result="c"/>
    <feComposite in="c" in2="SourceGraphic" operator="in"/>
  </filter>
  <path id="hullShape" d="M -405 -112 L -362 -104 L -358 -124 L -228 -122 L -224 -94 L 118 -92 L 122 -152 L 248 -154
    L 252 -206 L 392 -214 C 400 -150 394 -40 372 50 C 300 90 160 100 40 100 L -200 96 C -300 86 -360 40 -380 -40
    C -388 -70 -398 -95 -405 -112 Z"/>
  <clipPath id="cHull"><use href="#hullShape"/></clipPath>
</defs>""")

# 1. Water
o('<g id="water"><rect width="1200" height="800" fill="url(#gWater)"/><rect width="1200" height="800" fill="url(#gSun)"/>')
surf = "M0 0 H1200 V18 " + " ".join(
    f"Q {f(1200 - i * 60 - 30)} {f(30 if i % 2 else 10)} {f(1200 - (i + 1) * 60)} 18" for i in range(20)) + " Z"
o(f'<path d="{surf}" fill="#a9e6df" opacity="0.22"/>')
for yy, op in ((34, 0.12), (52, 0.07)):
    d = f"M0 {yy} " + " ".join(f"Q {f(i * 75 + 37)} {f(yy + (7 if i % 2 else -7))} {f((i + 1) * 75)} {yy}" for i in range(16))
    o(f'<path d="{d}" fill="none" stroke="#c9f2ec" stroke-width="2" opacity="{op}"/>')
o("</g>")

# 2. Light shafts
o('<g id="rays" filter="url(#fRay)">')
for x0, w, spread, op in ((60, 40, 70, 0.16), (170, 25, 50, 0.1), (250, 55, 90, 0.18),
                          (380, 30, 60, 0.11), (470, 45, 80, 0.14), (600, 22, 45, 0.08)):
    dx = 330
    o(f'<polygon points="{pts([(x0, 0), (x0 + w, 0), (x0 + w + dx + spread, 760), (x0 + dx, 760)])}" fill="url(#gRay)" opacity="{op}"/>')
o("</g>")

# 3. Distant seabed
o('<g id="far-sand">')
o('<path d="M0 560 C 120 540 230 548 330 566 C 450 588 560 548 700 552 C 820 556 900 530 1010 540 C 1090 548 1150 560 1200 556 V800 H0 Z" fill="url(#gFar1)" filter="url(#fFar)"/>')
for rx, ry, s in ((150, 552, 1.0), (205, 560, 0.6), (930, 538, 1.2), (1010, 545, 0.7), (560, 560, 0.5)):
    o(f'<path transform="translate({rx} {ry}) scale({s})" d="M -40 12 C -38 -6 -22 -22 -4 -24 C 14 -26 30 -14 38 2 C 42 10 40 14 36 16 Z" fill="#245e6c" opacity="0.9"/>')
o('<path d="M0 610 C 150 590 260 600 380 618 C 520 638 640 600 780 606 C 900 612 1000 596 1100 604 C 1150 608 1180 612 1200 610 V800 H0 Z" fill="url(#gFar2)" opacity="0.9"/>')
o("</g>")

# 4. Seabed (behind the wreck)
SAND_BACK = "M0 650 C 140 636 260 644 380 652 C 520 662 620 640 760 640 C 900 640 1020 628 1200 642 V800 H0 Z"
o('<g id="sand">')
o(f'<path d="{SAND_BACK}" fill="url(#gSand)"/>')
o(f'<path d="{SAND_BACK}" fill="#000" filter="url(#fSandTex)" opacity="0.6"/>')
o(f'<path d="{SAND_BACK}" fill="url(#gSandHaze)"/>')
o('<path d="M0 650 C 140 636 260 644 380 652 C 520 662 620 640 760 640 C 900 640 1020 628 1200 642" fill="none" stroke="#e4d3a0" stroke-width="2" opacity="0.35"/>')
o("</g>")

# Big soft shadow the wreck sits in, so it looms out of its own darkness
o('<g id="hull-shadow" filter="url(#fSoft)">')
o('<ellipse cx="640" cy="640" rx="480" ry="120" fill="#0a2430" opacity="0.35"/>')
o('<ellipse cx="700" cy="712" rx="380" ry="20" fill="#0e2a30" opacity="0.55"/>')
o("</g>")

def coral_fan(x, y, s, col, rot=0):
    """Branching fan: deterministic recursive strokes."""
    g = [f'<g transform="translate({f(x)} {f(y)}) rotate({rot}) scale({s})" stroke="{col}" fill="none" stroke-linecap="round">']

    def br(px, py, ang, ln, wd, depth):
        ex = px + ln * math.sin(math.radians(ang))
        ey = py - ln * math.cos(math.radians(ang))
        cx = (px + ex) / 2 + R.uniform(-3, 3)
        cy = (py + ey) / 2
        g.append(f'<path d="M{f(px)} {f(py)} Q{f(cx)} {f(cy)} {f(ex)} {f(ey)}" stroke-width="{f(wd)}"/>')
        if depth:
            for da in (-22, 20):
                br(ex, ey, ang + da + R.uniform(-6, 6), ln * 0.72, wd * 0.7, depth - 1)

    for a in (-30, 0, 28):
        br(0, 0, a, 16, 3.2, 3)
    g.append("</g>")
    return "".join(g)

# Galleon, in its own rotated frame: bow nosed down (left), stern castle rearing up (right)
o(f'<g id="wreck" transform="translate({HX} {HY}) rotate({HROT})">')

# 6. Masts, rigging, sails: drawn first so the hull overlaps their feet
o('<g id="masts">')
# main mast: still standing, leaning back, fighting top intact, snapped above it
o('<g transform="translate(60 -92) rotate(6)">')
o('<path d="M -8 30 L -6 -238 L -3 -252 L 0 -242 L 2 -256 L 4 -240 L 6 -246 L 8 30 Z" fill="url(#gMast)" stroke="#1e2a2c" stroke-width="1.5"/>')
o('<path d="M -3 26 L -3 -236" stroke="#cfe8dc" stroke-width="1.5" opacity="0.25"/>')
for y in (-60, -120):  # iron mast bands
    o(f'<rect x="-9" y="{y}" width="18" height="5" rx="1.5" fill="#2c3434"/>')
# fighting top: platform + cone underneath + rail
o('<path d="M -12 -178 L -28 -190 L 28 -190 L 12 -178 Z" fill="#3a443e" stroke="#1e2a2c" stroke-width="1.2"/>')
o('<rect x="-30" y="-196" width="60" height="7" rx="2" fill="#4a524a" stroke="#1e2a2c" stroke-width="1.2"/>')
o('<path d="M -28 -196 V -212 M -14 -196 V -212 M 14 -196 V -212 M 28 -196 V -212 M -30 -212 H 30" stroke="#3a443e" stroke-width="2.5"/>')
o('<path d="M -16 -212 V -218 L -10 -210" stroke="#3a443e" stroke-width="2.5" fill="none"/>')
o('<path d="M -30 -197 H 30" stroke="#cfe8dc" stroke-width="1" opacity="0.3"/>')
# main yard, askew, with a long tattered sail drifting with the current
o('<g transform="translate(0 -150) rotate(17)">')
o('<path fill-rule="evenodd" fill="#c8d2c4" opacity="0.32" stroke="#8c9a90" stroke-width="1" '
  'd="M -96 4 L 104 4 C 116 50 128 100 150 160 L 136 146 L 132 178 L 118 150 L 104 196 L 94 154 L 76 174 '
  'L 66 132 L 50 150 L 40 112 L 22 128 L 16 92 L -4 104 L -10 70 L -30 84 L -36 50 L -56 62 L -62 30 L -82 40 C -88 28 -94 16 -96 4 Z '
  'M 40 40 L 58 46 L 64 66 L 52 84 L 44 70 L 34 62 Z"/>')
o('<path d="M -60 10 C -50 30 -44 44 -40 60 M 0 8 C 14 40 22 70 30 100 M 60 10 C 74 50 88 90 100 140" stroke="#ffffff" stroke-width="1.2" fill="none" opacity="0.14"/>')
o('<path d="M -104 -4 L 112 -4 L 116 0 L 112 4 L -100 4 L -108 6 L -104 0 L -110 -6 Z" fill="url(#gMast)" stroke="#1e2a2c" stroke-width="1.2"/>')
o("</g>")
o("</g>")
# foremast: broken, leaning far forward, a rag still on its yard
o('<g transform="translate(-300 -122) rotate(-42)">')
o('<path d="M -6 10 L -5 -150 L -2 -158 L 1 -151 L 3 -161 L 6 -148 L 7 10 Z" fill="url(#gMast)" stroke="#1e2a2c" stroke-width="1.5"/>')
o('<g transform="translate(0 -118) rotate(30)">')
o('<path d="M -50 3 L 46 3 C 50 30 62 54 70 80 L 58 70 L 52 96 L 40 72 L 30 90 L 22 62 L 8 78 L 2 50 L -14 60 L -18 34 L -36 42 C -40 26 -46 14 -50 3 Z" fill="#c8d2c4" opacity="0.3" stroke="#8c9a90" stroke-width="1"/>')
o('<rect x="-56" y="-3" width="112" height="6" rx="2.5" fill="url(#gMast)" stroke="#1e2a2c" stroke-width="1.2"/>')
o("</g></g>")
# mizzen: snapped, leaning back, slanted lateen yard
o('<g transform="translate(220 -154) rotate(16)">')
o('<path d="M -6 10 L -5 -112 L -2 -120 L 0 -110 L 3 -124 L 6 -108 L 6 10 Z" fill="url(#gMast)" stroke="#1e2a2c" stroke-width="1.5"/>')
o('<g transform="translate(0 -84) rotate(-52)"><path d="M -96 -2 L 70 -3 L 66 0 L 74 3 L -96 3 Z" fill="url(#gMast)" stroke="#1e2a2c" stroke-width="1.2"/></g>')
o("</g>")
# bowsprit, snapped, jutting from the beakhead
o('<path d="M -392 -116 L -476 -168 L -480 -158 L -474 -176 L -468 -166 L -386 -108 Z" fill="url(#gMast)" stroke="#1e2a2c" stroke-width="1.2"/>')


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# shrouds + ratlines from the main top down to the channels (some ratlines torn away)
top_l, top_r = (55, -278), (95, -282)
feet = [(84, -96), (104, -96), (130, -146), (152, -148), (174, -150)]
o('<g fill="none" stroke="#1e2e30" stroke-linecap="round" opacity="0.8">')
shrouds = []
for i, foot in enumerate(feet):
    top = lerp(top_l, top_r, i / (len(feet) - 1))
    shrouds.append((top, foot))
    if i == 3:  # one shroud snapped, its end drifting
        mid = lerp(top, foot, 0.45)
        o(f'<path d="M {f(top[0])} {f(top[1])} L {f(mid[0])} {f(mid[1])} q 14 10 6 26 t 8 22" stroke-width="1.6"/>')
    else:
        o(f'<path d="M {f(top[0])} {f(top[1])} L {f(foot[0])} {f(foot[1])}" stroke-width="1.8"/>')
for k in range(1, 12):
    t = k / 12
    if k in (5, 6, 9):
        continue
    for i in range(len(shrouds) - 1):
        if 3 in (i, i + 1) and t > 0.45:
            continue
        a = lerp(*shrouds[i], t)
        b = lerp(*shrouds[i + 1], t)
        o(f'<path d="M {f(a[0])} {f(a[1])} L {f(b[0])} {f(b[1])}" stroke-width="1"/>')
# stays: forestay sagging to the bowsprit, backstay to the stern castle, loose ends drifting up
o('<path d="M 62 -280 C -100 -190 -300 -170 -470 -164" stroke-width="1.8"/>')
o('<path d="M 96 -282 C 200 -250 300 -230 384 -212" stroke-width="1.5"/>')
o('<path d="M 70 -286 C 60 -320 90 -340 76 -372 C 68 -390 84 -404 78 -420" stroke-width="1.3" opacity="0.6"/>')
o('<path d="M -330 -230 C -340 -260 -320 -280 -334 -306" stroke-width="1.2" opacity="0.6"/>')
o('<path d="M 232 -270 C 250 -296 236 -316 256 -338" stroke-width="1.2" opacity="0.6"/>')
o("</g>")
o("</g>")  # masts

# beakhead + eroded figurehead stub (no face), behind the bow planking
o('<path d="M -400 -116 L -446 -132 L -452 -124 L -404 -100 Z" fill="#3a2c22" stroke="#1a1410" stroke-width="1.5"/>')
o('<path d="M -444 -126 C -468 -138 -478 -164 -462 -186 L -458 -178 L -452 -190 L -446 -180 C -456 -164 -452 -148 -428 -132 Z" fill="#33281f" stroke="#140f0b" stroke-width="1.5" stroke-linejoin="round"/>')
o('<path d="M -446 -134 C -462 -146 -466 -164 -458 -178" fill="none" stroke="#8a7a4a" stroke-width="1.5" opacity="0.5"/>')
o('<path d="M -470 -150 C -472 -164 -468 -176 -462 -184" fill="none" stroke="#cfe8dc" stroke-width="1.2" opacity="0.35"/>')

# 5. Hull body
o('<g id="hull">')
o('<use href="#hullShape" fill="url(#gHull)"/>')
o('<g clip-path="url(#cHull)">')
for y in range(-220, 100, 14):  # plank colour variation
    shade = R.choice(["#000000", "#ffffff", "#1a1410", "#cfe8dc"])
    o(f'<path d="M -420 {y} Q 0 {y + 8} 420 {y} V {y + 14} Q 0 {y + 22} -420 {y + 14} Z" fill="{shade}" opacity="{f(R.uniform(0.03, 0.08))}"/>')
for y in range(-206, 100, 14):  # seams, plank top highlights, butt joints
    o(f'<path d="M -420 {y} Q 0 {y + 8} 420 {y}" fill="none" stroke="#17100a" stroke-width="1.6" opacity="0.75"/>')
    o(f'<path d="M -420 {y + 2} Q 0 {y + 10} 420 {y + 2}" fill="none" stroke="#cfe8dc" stroke-width="1" opacity="0.07"/>')
    for k in range(3):
        bx = R.uniform(-380, 380)
        by = y + 8 * (1 - (bx / 420) ** 2) + 7
        o(f'<path d="M {f(bx)} {f(by - 6)} L {f(bx)} {f(by + 6)}" stroke="#17100a" stroke-width="1.2" opacity="0.5"/>')
# wales along both gun decks and the castle
for d, w in (("M -390 -4 Q 0 8 400 -8", 8), ("M -370 -48 Q 0 -38 400 -54", 7), ("M 118 -112 Q 260 -108 400 -118", 6), ("M 250 -166 Q 320 -164 400 -170", 5)):
    o(f'<path d="{d}" fill="none" stroke="#1e150e" stroke-width="{w}"/>')
    o(f'<path d="{d}" fill="none" stroke="#8a7a4a" stroke-width="1.2" opacity="0.45" transform="translate(0 {-w / 2})"/>')
# missing planks near the keel
for x, y, w in ((-290, 46, 54), (-230, 66, 40), (150, 70, 46), (260, 52, 34)):
    o(f'<path d="M {x} {y} l {w} -2 l -3 13 l -{w - 6} 3 Z" fill="#0a161a"/>')
    o(f'<path d="M {x} {y} l {w} -2" stroke="#7a6a50" stroke-width="1.5" opacity="0.6"/>')
# algae + draping weed on the lower hull
o('<g fill="#3f6a3a">')
for _ in range(20):
    o(f'<ellipse cx="{f(R.uniform(-380, 370))}" cy="{f(R.uniform(30, 96))}" rx="{f(R.uniform(16, 44))}" ry="{f(R.uniform(5, 13))}" opacity="{f(R.uniform(0.25, 0.45))}"/>')
o("</g>")
o('<g>')
for cx in (-340, -290, -230, 110, 180, 250, 320):  # barnacle clusters
    for _ in range(9):
        bx = cx + R.gauss(0, 12)
        by = 34 + 0.0002 * bx * bx + R.gauss(0, 5)
        r = R.uniform(1.2, 2.8)
        o(f'<circle cx="{f(bx)}" cy="{f(by)}" r="{f(r)}" fill="#c9cfc2" opacity="0.6"/>')
        o(f'<circle cx="{f(bx + 0.3)}" cy="{f(by + 0.3)}" r="{f(r * 0.4)}" fill="#3e4a44" opacity="0.6"/>')
o("</g>")

# gun ports: two decks; some lids hanging, some muzzles, a few faintly glowing
HOLE_X = (-176, 66)
GLOW_PORTS = []
ports = [(x, -26) for x in range(-330, 380, 52)] + [(x, -72) for x in range(-200, 118, 52)] + [(x, -132) for x in (150, 200)]
for i, (x, y) in enumerate(ports):
    if HOLE_X[0] < x < HOLE_X[1]:
        continue
    y += 0.00007 * x * x
    o(f'<rect x="{x - 9}" y="{f(y - 8)}" width="18" height="16" rx="1.5" fill="#070f12" stroke="#6a5a44" stroke-width="1.6"/>')
    kind = i % 5
    if kind == 1:
        o(f'<g transform="translate({x - 9} {f(y + 8)}) rotate({20 + 9 * (i % 3)})"><rect width="18" height="16" rx="1.5" fill="#3e3024" stroke="#17100a" stroke-width="1.2"/>'
          '<path d="M2 5 H16 M2 11 H16" stroke="#17100a" stroke-width="1"/></g>')
    elif kind == 3:
        o(f'<circle cx="{x}" cy="{f(y)}" r="6" fill="#2a3436" stroke="#5a6a66" stroke-width="1.5"/><circle cx="{x}" cy="{f(y)}" r="3" fill="#050a0c"/>')
    elif kind in (0, 4) and len(GLOW_PORTS) < 4:
        GLOW_PORTS.append((x, y))

# quarter gallery on the stern castle: bay of tall arched windows, tarnished gilt trim
o('<path d="M 282 -200 L 376 -204 L 374 -116 C 352 -96 306 -96 284 -112 Z" fill="#2e241c" stroke="#17100a" stroke-width="2"/>')
o('<path d="M 282 -200 L 376 -204 M 284 -112 C 306 -96 352 -96 374 -116" fill="none" stroke="#8a7a4a" stroke-width="2.5" opacity="0.6"/>')
WINDOWS = [(298, -184), (322, -185), (346, -186)]
for x, y in WINDOWS:
    o(f'<path d="M {x - 8} {y + 44} V {y + 8} A 8 8 0 0 1 {x + 8} {y + 8} V {y + 44} Z" fill="#050d10" stroke="#8a7a4a" stroke-width="1.5" opacity="0.95"/>')
    o(f'<path d="M {x} {y + 2} V {y + 44} M {x - 8} {y + 24} H {x + 8}" stroke="#2e241c" stroke-width="1.5"/>')
# carved scrolls flanking the gallery
for x, y, s in ((278, -150, 1), (380, -152, -1)):
    o(f'<path d="M {x} {y - 30} C {x - 8 * s} {y - 10} {x - 8 * s} {y + 10} {x} {y + 22} C {x + 6 * s} {y + 26} {x + 8 * s} {y + 18} {x + 3 * s} {y + 14}" fill="none" stroke="#8a7a4a" stroke-width="2.5" opacity="0.55"/>')

# big jagged break amidships
HOLE = "M -156 -96 L -136 -66 L -154 -36 L -134 -6 L -148 30 L -120 66 L -80 56 L -50 74 L -10 62 L 26 50 L 18 18 L 40 -14 L 24 -46 L 48 -96 Z"
o(f'<path d="{HOLE}" fill="#08141a"/>')
o(f'<clipPath id="cHole"><path d="{HOLE}"/></clipPath>')
o('<g clip-path="url(#cHole)">')
o('<ellipse cx="-56" cy="10" rx="80" ry="60" fill="#6fe3c6" opacity="0.13" filter="url(#fSoft)"/>')
for y in (-50, 6):  # the two gun decks seen through the break
    o(f'<path d="M -170 {y} Q -50 {y + 6} 60 {y - 4}" stroke="#241a12" stroke-width="9" fill="none"/>')
    o(f'<path d="M -170 {y - 4} Q -50 {y + 2} 60 {y - 8}" stroke="#7a6a50" stroke-width="1.3" fill="none" opacity="0.5"/>')
o("</g>")
for x, frac in ((-142, 0), (-126, 1), (-110, 0.5), (-94, 1), (-78, 0.35), (-62, 1), (-46, 0.75), (-30, 1), (-14, 0.45), (2, 1), (18, 0.6)):
    top = 60 - 150 * frac if frac else 30
    d = f"M {x - 2} 62 Q {x - 10} {f((62 + top) / 2)} {x - 1} {f(top)}"
    o(f'<path d="{d}" fill="none" stroke="#17100a" stroke-width="10"/>')
    o(f'<path d="{d}" fill="none" stroke="#4e3e30" stroke-width="7"/>')
    o(f'<path d="M {x - 4} 60 Q {x - 12} {f((62 + top) / 2)} {x - 3} {f(top + 2)}" fill="none" stroke="#cfe8dc" stroke-width="1.2" opacity="0.25"/>')
    if frac < 1:
        o(f'<path d="M {x - 5} {f(top + 3)} L {x - 3} {f(top - 7)} L {x - 1} {f(top + 1)} L {x + 1} {f(top - 10)} L {x + 3} {f(top + 3)} Z" fill="#5a4632" stroke="#17100a" stroke-width="1"/>')
o(f'<path d="{HOLE}" fill="none" stroke="#6a5a44" stroke-width="2.5"/>')
for x, y, a in ((-156, -96, 200), (-136, -66, 160), (-154, -36, 200), (-148, 30, 210), (24, -46, -20), (40, -14, 10), (48, -96, -30), (18, 18, -10)):
    o(f'<path transform="translate({x} {y}) rotate({a})" d="M 0 -2 L 14 -1 L 5 0 L 16 1 L 0 3 Z" fill="#5a4632" stroke="#17100a" stroke-width="0.8"/>')
# keel
o('<path d="M -386 -40 C -364 44 -300 92 -200 102 L 40 106 C 160 106 300 96 378 54" fill="none" stroke="#17100a" stroke-width="12"/>')
# volume shading: cold light on the bow side, heavy shade low and aft
o('<rect x="-480" y="-240" width="960" height="360" fill="url(#gHullSide)"/>')
o('<rect x="-480" y="-240" width="960" height="360" fill="url(#gHullShade)"/>')
o("</g>")  # end clip

# faint inner glow: a few ports and the gallery windows, felt more than seen
o('<g fill="#6fe3c6" filter="url(#fGlow)">')
for x, y in GLOW_PORTS:
    o(f'<ellipse cx="{x}" cy="{f(y)}" rx="9" ry="7" opacity="0.32"/>')
for x, y in WINDOWS:
    o(f'<rect x="{x - 6}" y="{y + 10}" width="12" height="30" rx="5" opacity="0.22"/>')
o("</g>")

o('<use href="#hullShape" fill="none" stroke="#17100a" stroke-width="2.4" stroke-linejoin="round"/>')
# gilt rail trim + cold rim light along the top edges
o('<path d="M -362 -106 L -358 -124 L -228 -122 M 122 -152 L 248 -154 M 252 -206 L 392 -214" fill="none" stroke="#8a7a4a" stroke-width="2" opacity="0.55" transform="translate(0 6)"/>')
o('<path d="M -403 -114 L -362 -106 L -358 -126 L -228 -124 M -224 -96 L -156 -96 M 48 -96 L 118 -94 L 122 -154 L 248 -156 L 252 -208 L 392 -216" fill="none" stroke="#cfe8dc" stroke-width="2" opacity="0.6"/>')
o('<path d="M -403 -110 C -394 -80 -386 -60 -380 -40" fill="none" stroke="#cfe8dc" stroke-width="1.6" opacity="0.35"/>')
# rail posts along the waist and castle
o('<g stroke="#2e241c" stroke-width="3">')
for x in range(-216, 118, 26):
    if not (HOLE_X[0] - 6 < x < HOLE_X[1] - 10):
        o(f'<path d="M {x} -94 V -108"/>')
o('<path d="M -216 -108 H -162 M 62 -108 H 118" stroke-width="3"/>')
o("</g>")
# broken stern lantern hanging askew from its bracket
o('<path d="M 388 -214 L 404 -232 L 412 -230" fill="none" stroke="#2c3434" stroke-width="3"/>')
o('<g transform="translate(412 -230) rotate(24)">')
o('<path d="M 0 0 V 6" stroke="#2c3434" stroke-width="2"/>')
o('<path d="M -8 6 L 8 6 L 10 12 L 8 30 L -8 30 L -10 12 Z" fill="#0a1418" stroke="#6a5e3e" stroke-width="2"/>')
o('<path d="M 0 6 V 30 M -9 18 H 9" stroke="#6a5e3e" stroke-width="1.2"/>')
o('<path d="M -6 30 L 0 38 L 6 30" fill="#6a5e3e"/>')
o("</g>")
# long dark weed draping from the rails
o('<g fill="none" stroke="#2c4a34" stroke-linecap="round" opacity="0.75">')
for x, y0 in [(x, -94) for x in (-210, -190, 70, 96)] + [(x, -152) for x in (140, 170, 210)] + [(x, -206) for x in (262, 300, 360)] + [(-300, -122), (-262, -122)]:
    ln = R.uniform(30, 80)
    sw = R.uniform(1.6, 3)
    o(f'<path d="M {x} {y0} c 4 {f(ln * 0.3)} -6 {f(ln * 0.6)} -2 {f(ln)} s 6 {f(ln * 0.4)} 2 {f(ln * 0.6)}" stroke-width="{f(sw)}"/>')
o("</g>")
# coral + sea fern on the lower hull (muted)
o(coral_fan(-320, 40, 0.9, "#9a5a72", -8))
o(coral_fan(250, 64, 0.8, "#6e5a8a", 4))
o('<g fill="none" stroke="#4f7a4a" stroke-width="1.6" stroke-linecap="round" opacity="0.7">')
for x in (-250, -242, 190, 198):
    o(f'<path d="M {x} 80 C {x - 6} 64 {x + 6} 52 {x} 36"/>')
    for k in range(4):
        yy = 72 - k * 10
        o(f'<path d="M {x - 1} {yy} q -6 -3 -9 -8 M {x + 1} {yy - 4} q 6 -3 9 -8" stroke-width="1"/>')
o("</g>")
o("</g>")  # hull
o("</g>")  # wreck frame

# Rock outcrop the stern rests on
o('<g id="stern-rock">')
o('<path d="M 846 716 C 858 690 892 674 934 678 C 972 682 996 662 1040 658 C 1084 654 1116 678 1124 716 Z" fill="url(#gRock)" stroke="#1a3038" stroke-width="2"/>')
o('<path d="M 870 692 C 890 680 912 676 934 678 M 1000 666 C 1016 660 1030 658 1046 658" fill="none" stroke="#b9d6c9" stroke-width="2.5" stroke-linecap="round" opacity="0.35"/>')
o('<path d="M 960 690 C 980 698 996 706 1004 716" fill="none" stroke="#1a3038" stroke-width="1.5" opacity="0.6"/>')
o("</g>")

# Depth haze: everything above the play-area floor fades into the water.
o('<filter id="fWhite"><feFlood flood-color="#fff"/><feComposite in2="SourceAlpha" operator="in"/></filter>'
  '<mask id="mWreck" maskUnits="userSpaceOnUse" x="0" y="0" width="1200" height="800"><use href="#wreck" filter="url(#fWhite)"/></mask>')
o('<rect id="haze" x="0" y="280" width="1200" height="330" fill="url(#gHaze)" mask="url(#mWreck)"/>')

# Near sand in front of the wreck: buries the stern and the keel
SAND_FRONT = ("M0 700 C 80 690 170 650 260 640 C 320 634 360 660 420 690 C 480 708 560 714 640 714 "
              "C 740 714 820 712 880 710 C 960 708 1040 712 1120 706 C 1160 703 1185 702 1200 702 V800 H0 Z")
o('<g id="sand-front">')
o(f'<path d="{SAND_FRONT}" fill="url(#gSand)"/>')
o(f'<path d="{SAND_FRONT}" fill="#000" filter="url(#fSandTex)" opacity="0.6"/>')
o('<path d="M 80 690 C 170 650 260 640 260 640 C 320 634 360 660 420 690 C 480 708 560 714 640 714" fill="none" stroke="#e8d7a4" stroke-width="2.5" opacity="0.5"/>')
o('<path d="M 360 670 C 480 716 700 720 880 716" fill="none" stroke="#6e6244" stroke-width="10" opacity="0.25" filter="url(#fSoft)"/>')
# ripples
o('<g fill="none" stroke="#6e6244" stroke-linecap="round" opacity="0.35">')
for _ in range(34):
    x = R.uniform(0, 1150)
    y = R.uniform(735, 795)
    ln = R.uniform(40, 110)
    o(f'<path d="M {f(x)} {f(y)} q {f(ln / 2)} -6 {f(ln)} 0" stroke-width="{f(R.uniform(1.2, 2.2))}"/>')
o("</g>")
o('<g fill="none" stroke="#ead9a8" stroke-linecap="round" opacity="0.22">')
for _ in range(26):
    x = R.uniform(0, 1150)
    y = R.uniform(735, 795)
    ln = R.uniform(30, 80)
    o(f'<path d="M {f(x)} {f(y - 2)} q {f(ln / 2)} -6 {f(ln)} 0" stroke-width="1.2"/>')
o("</g>")
# caustic light blobs from the sun side
o('<g fill="#fff3c8" opacity="0.1" filter="url(#fFar)">')
for _ in range(22):
    x = R.uniform(0, 800)
    y = R.uniform(730, 790)
    o(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(R.uniform(12, 30))}" ry="{f(R.uniform(3, 6))}"/>')
o("</g>")
# darker sediment near the hull
o('<g fill="#4e4630" opacity="0.35" filter="url(#fSoft)">'
  '<ellipse cx="720" cy="722" rx="120" ry="10"/><ellipse cx="990" cy="680" rx="90" ry="10"/></g>')
o(f'<path d="{SAND_FRONT}" fill="url(#gSandHaze)" opacity="0.6"/>')
o("</g>")

# 7. Debris
o('<g id="debris">')
o('<g fill="#2e2a1c" opacity="0.45" filter="url(#fFar)">'
  '<ellipse cx="236" cy="764" rx="44" ry="6"/><ellipse cx="535" cy="752" rx="66" ry="6"/>'
  '<ellipse cx="984" cy="732" rx="30" ry="5"/><ellipse cx="1096" cy="760" rx="36" ry="5"/></g>')
# broken planks half in sand
for x, y, a, ln in ((300, 732, -18, 70), (612, 728, 12, 54), (880, 708, -8, 60), (160, 752, 22, 48)):
    o(f'<g transform="translate({x} {y}) rotate({a})"><path d="M 0 0 L {ln} 0 L {ln + 6} 4 L {ln - 2} 6 L {ln + 3} 9 L 0 9 Z" fill="#6e5034" stroke="#2a1c10" stroke-width="1.5"/>'
      f'<path d="M 2 2 H {ln - 4}" stroke="#d9b984" stroke-width="1" opacity="0.45"/></g>')
# barrel on its side
o('<g transform="translate(232 742) rotate(-6)">')
o('<path d="M -34 -20 C -26 -26 26 -26 34 -20 L 34 20 C 26 26 -26 26 -34 20 Z" fill="url(#gBarrel)" stroke="#24170c" stroke-width="2"/>')
for x in (-22, 22):
    o(f'<path d="M {x} -24 C {x + 3} -8 {x + 3} 8 {x} 24" fill="none" stroke="#3c4440" stroke-width="4"/>')
    o(f'<path d="M {x - 1} -23 C {x + 2} -10 {x + 2} 0 {x + 1} 8" fill="none" stroke="#a9b0a4" stroke-width="1" opacity="0.5"/>')
o('<ellipse cx="34" cy="0" rx="8" ry="20" fill="#4a3320" stroke="#24170c" stroke-width="2"/>')
o('<ellipse cx="34" cy="0" rx="4" ry="12" fill="none" stroke="#2a1c10" stroke-width="1"/>')
o('<path d="M -30 -18 C -20 -22 20 -22 30 -18" fill="none" stroke="#f6e2ad" stroke-width="1.5" opacity="0.4"/>')
o("</g>")
# cannon half buried
o('<g transform="translate(540 740) rotate(-8)">')
o('<path d="M -50 -9 L 40 -12 C 46 -12 48 -8 48 0 C 48 8 46 12 40 12 L -50 9 C -58 8 -60 4 -60 0 C -60 -4 -58 -8 -50 -9 Z" fill="url(#gCannon)" stroke="#162022" stroke-width="2"/>')
o('<ellipse cx="46" cy="0" rx="4" ry="11" fill="#0b1214"/>')
o('<path d="M -20 -10 V 10 M 20 -12 V 12" stroke="#162022" stroke-width="3"/>')
o('<path d="M -48 -6 L 38 -9" stroke="#b9c8c2" stroke-width="1.5" opacity="0.4"/>')
o('<circle cx="-62" cy="0" r="4" fill="#3b4644" stroke="#162022" stroke-width="1.5"/>')
o("</g>")
# crates
o('<g transform="translate(980 712) rotate(9)">')
o('<rect x="-22" y="-22" width="44" height="40" fill="#7a5a3a" stroke="#24170c" stroke-width="2"/>')
o('<path d="M -22 -8 H 22 M -22 6 H 22 M -18 -20 L 18 16" stroke="#3a2818" stroke-width="2"/>')
o('<path d="M -20 -20 H 20" stroke="#f6e2ad" stroke-width="1.3" opacity="0.4"/>')
o("</g>")
o('<g transform="translate(1036 724) rotate(-14)">'
  '<path d="M -16 -14 L 14 -16 L 18 6 L 6 2 L -2 10 L -14 4 Z" fill="#6e5034" stroke="#24170c" stroke-width="1.8"/>'
  '<path d="M -14 -4 L 16 -6" stroke="#3a2818" stroke-width="1.5"/></g>')
# anchor + chain trailing back to the stern
o('<g transform="translate(1100 738) rotate(-62)">')
o('<path d="M -3 -52 H 3 V 22 H -3 Z" fill="url(#gCannon)" stroke="#162022" stroke-width="1.5"/>')
o('<path d="M -22 -40 H 22" stroke="#3b4644" stroke-width="5" stroke-linecap="round"/>')
o('<path d="M -34 6 C -30 24 -14 32 0 32 C 14 32 30 24 34 6" fill="none" stroke="#2a3436" stroke-width="7" stroke-linecap="round"/>')
o('<path d="M -34 6 L -40 -2 L -28 2 Z M 34 6 L 40 -2 L 28 2 Z" fill="#2a3436" stroke="#162022" stroke-width="1"/>')
o('<circle cx="0" cy="-58" r="7" fill="none" stroke="#2a3436" stroke-width="4"/>')
o('<path d="M -32 4 C -26 20 -12 28 0 28" fill="none" stroke="#a9b8b2" stroke-width="1.2" opacity="0.4"/>')
o("</g>")
o('<g fill="none" stroke="#2a3436" stroke-width="2.4">')
for i in range(14):
    t = i / 13
    x = 1060 - t * 120
    y = 718 + 14 * math.sin(t * 3.0) - t * 10
    rot = -15 + 25 * math.cos(t * 3.0)
    o(f'<ellipse transform="translate({f(x)} {f(y)}) rotate({f(rot)})" rx="{5 if i % 2 else 3}" ry="{3 if i % 2 else 5}"/>')
o("</g>")
# amphora shards
for x, y, a in ((372, 748, 20), (392, 756, -30), (690, 760, 5)):
    o(f'<path transform="translate({x} {y}) rotate({a})" d="M -9 2 L -6 -5 L 3 -7 L 9 -2 L 4 0 L -2 -2 Z" fill="#a8603e" stroke="#4a2414" stroke-width="1.2"/>')
o("</g>")

# 8. Life
o('<g id="life">')
# distant school: hazy silhouettes, far behind everything gameplay will put on top
o('<g fill="#6fb3bf" opacity="0.32">')
for _ in range(14):
    x = R.uniform(820, 1010)
    y = R.uniform(200, 290) + (x - 820) * 0.12
    s = R.uniform(0.6, 1.0)
    o(f'<path transform="translate({f(x)} {f(y)}) scale({f(s)})" d="M -9 0 C -5 -4 4 -4 7 0 C 4 4 -5 4 -9 0 Z M 6 0 L 12 -4 L 11 0 L 12 4 Z"/>')
o("</g>")
# crab by the anchor (no face)
o('<g transform="translate(1150 754)" stroke="#5a2a1e" stroke-linecap="round" fill="none">')
for s in (-1, 1):
    for k in range(3):
        o(f'<path d="M {s * 6} {k * 2} q {s * 7} -4 {s * 12} {4 + k * 2}" stroke-width="1.8"/>')
    o(f'<path d="M {s * 8} -4 q {s * 6} -8 {s * 10} -10" stroke-width="2"/>')
    o(f'<path d="M {s * 18} -14 q {s * 6} 0 {s * 4} 6 q {s * -4} 0 {s * -4} -6 Z" fill="#9a4a32" stroke-width="1.2"/>')
o('<ellipse cx="0" cy="0" rx="11" ry="7" fill="#9a4a32" stroke-width="1.5"/>')
o('<path d="M -7 -3 Q 0 -7 7 -3" stroke="#e2a07c" stroke-width="1.2" opacity="0.6"/>')
o("</g>")
# starfish
o('<g transform="translate(820 772) rotate(12)">')
star = []
for k in range(10):
    r = 13 if k % 2 == 0 else 5
    a = math.radians(-90 + k * 36)
    star.append((r * math.cos(a), r * math.sin(a)))
o(f'<polygon points="{pts(star)}" fill="#b86a5a" stroke="#5a2a1e" stroke-width="1.5" stroke-linejoin="round"/>')
o('<circle r="2" fill="#e8b49a" opacity="0.6"/>')
o("</g>")
# coral and fern on the bow rock and sand
o(coral_fan(892, 684, 0.9, "#9a5a72", -12))
o(coral_fan(1086, 664, 0.6, "#6e5a8a", 10))
o(coral_fan(84, 728, 1.1, "#8e5fa8", -4))
o(coral_fan(1172, 712, 0.8, "#d46a8a", 8))
o("</g>")

# 9. Foreground kelp + bubbles
o('<g id="fore">')
o('<g filter="url(#fKelp)" fill="url(#gKelp)">')


def kelp(x0, lean, h, w):
    left, right = [], []
    for i in range(13):
        t = i / 12
        y = 800 - h * t
        x = x0 + lean * t * t + 10 * math.sin(t * 6)
        ww = w * (1 - t * 0.8)
        left.append((x - ww / 2, y))
        right.append((x + ww / 2, y))
    poly = left + right[::-1]
    return f'<polygon points="{pts(poly)}"/>'


for x0, lean, h, w in ((10, 40, 520, 26), (38, 20, 380, 20), (-6, 60, 300, 22)):
    o(kelp(x0, lean, h, w))
for x0, lean, h, w in ((1190, -40, 500, 26), (1162, -24, 360, 20), (1206, -62, 280, 22)):
    o(kelp(x0, lean, h, w))
o("</g>")
# bubbles from the break in the hull
bx, by = 588, 620
o('<g fill="#bfe8ec" fill-opacity="0.12" stroke="#d6f4f4" stroke-width="1" opacity="0.7">')
for i in range(11):
    y = by - i * 22 - R.uniform(0, 10)
    x = bx + 6 * math.sin(i * 1.3) + R.uniform(-4, 4)
    r = 1.6 + i * 0.25 + R.uniform(0, 1)
    o(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>')
o("</g>")
o("</g>")

# 10. Atmosphere
o('<g id="vignette">')
o('<rect width="1200" height="800" fill="url(#gVig)"/>')
o('<g fill="#ffffff">')
for _ in range(70):
    o(f'<circle cx="{f(R.uniform(0, 1200))}" cy="{f(R.uniform(0, 760))}" r="{f(R.uniform(0.6, 1.6))}" opacity="{f(R.uniform(0.2, 0.4))}"/>')
o("</g></g>")
o("</svg>")

open(sys.argv[1], "w").write("\n".join(out) + "\n")
