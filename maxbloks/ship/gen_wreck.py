"""Generate wreck.svg from wreck_prompt.md (v2). Deterministic (fixed seed).

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


# Hull placement (local coords: bow at -x, deck at -y), rotated so the bow lifts.
HX, HY, HROT = 690, 640, 10

o(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
o("""<defs>
  <linearGradient id="gWater" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3fa9b5"/><stop offset="0.45" stop-color="#1d6a83"/>
    <stop offset="0.8" stop-color="#123f5c"/><stop offset="1" stop-color="#0b2e4a"/>
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
  <linearGradient id="gHull" x1="0" y1="-115" x2="0" y2="85" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#8a6842"/><stop offset="0.25" stop-color="#6e5034"/>
    <stop offset="0.7" stop-color="#4a3320"/><stop offset="1" stop-color="#2c2420"/>
  </linearGradient>
  <linearGradient id="gHullShade" x1="0" y1="-115" x2="0" y2="85" gradientUnits="userSpaceOnUse">
    <stop offset="0.35" stop-color="#0d2a33" stop-opacity="0"/><stop offset="1" stop-color="#0d2a33" stop-opacity="0.6"/>
  </linearGradient>
  <linearGradient id="gHullSide" x1="-345" y1="0" x2="335" y2="0" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#f3dca0" stop-opacity="0.18"/><stop offset="0.4" stop-color="#f3dca0" stop-opacity="0"/>
    <stop offset="1" stop-color="#0d2a33" stop-opacity="0.3"/>
  </linearGradient>
  <linearGradient id="gMast" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#8a8a72"/><stop offset="0.45" stop-color="#5f6656"/><stop offset="1" stop-color="#3a4a4a"/>
  </linearGradient>
  <linearGradient id="gHaze" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a7a8c" stop-opacity="0.5"/><stop offset="1" stop-color="#2a7a8c" stop-opacity="0"/>
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
    <stop offset="0.6" stop-color="#04121c" stop-opacity="0"/><stop offset="1" stop-color="#04121c" stop-opacity="0.3"/>
  </radialGradient>
  <filter id="fRay" x="-20%" y="-5%" width="140%" height="110%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="fSoft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
  <filter id="fFar" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="1.6"/></filter>
  <filter id="fKelp" x="-30%" y="-5%" width="160%" height="110%"><feGaussianBlur stdDeviation="2"/></filter>
  <filter id="fSandTex" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.25  0 0 0 0 0.2  0 0 0 0 0.12  0 0 0 0.35 0" result="c"/>
    <feComposite in="c" in2="SourceGraphic" operator="in"/>
  </filter>
  <path id="hullShape" d="M -345 -92 C -322 -82 -302 -72 -280 -68 L 170 -62 L 178 -106 L 336 -114 L 331 42
    C 300 72 200 80 100 82 L -150 80 C -262 72 -322 22 -345 -92 Z"/>
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

# Shadows the wreck casts on the sand
o('<g id="hull-shadow" filter="url(#fSoft)" opacity="0.55">')
o('<ellipse cx="520" cy="706" rx="150" ry="14" fill="#0e2a30"/>')
o('<ellipse cx="820" cy="690" rx="230" ry="18" fill="#0e2a30"/>')
o("</g>")

# Rock under the raised bow
o('<g id="bow-rock">')
o('<path d="M 400 712 C 404 688 424 668 452 662 C 482 656 512 664 528 682 C 538 694 540 708 536 716 Z" fill="url(#gRock)" stroke="#1f3940" stroke-width="2"/>')
o('<path d="M 418 684 C 432 670 452 664 474 664" fill="none" stroke="#b9d6c9" stroke-width="2.5" stroke-linecap="round" opacity="0.5"/>')
o('<path d="M 470 690 C 488 694 502 704 506 714" fill="none" stroke="#1f3940" stroke-width="1.5" opacity="0.6"/>')
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


# 5. Hull + 6. Masts (same rotated frame)
o(f'<g id="wreck" transform="translate({HX} {HY}) rotate({HROT})">')

# 6a. masts behind the hull side (drawn first so the hull overlaps the bases)
o('<g id="masts">')
# foremast leaning forward ~35 deg
o('<g transform="translate(-215 -64) rotate(-35)">')
o('<path d="M -6 0 L -5 -150 L 5 -150 L 6 0 Z" fill="url(#gMast)" stroke="#2c3a3c" stroke-width="1.5"/>')
o('<path d="M -2 -2 L -2 -146" stroke="#c9c6a6" stroke-width="1.5" opacity="0.35"/>')
o('<path d="M -6 -150 L -3 -158 L 0 -152 L 2 -161 L 5 -150 Z" fill="#6a705e" stroke="#2c3a3c" stroke-width="1"/>')
# yard arm, askew
o('<g transform="translate(0 -128) rotate(14)">')
o('<rect x="-62" y="-3.5" width="124" height="7" rx="3" fill="url(#gMast)" stroke="#2c3a3c" stroke-width="1.2"/>')
# torn sail hanging from yard (holes via evenodd)
o('<path fill-rule="evenodd" fill="#d8cfb8" opacity="0.5" stroke="#a9a08a" stroke-width="1" '
  'd="M -56 3 L 52 3 C 50 30 56 52 46 78 L 40 66 L 33 88 L 24 70 L 14 96 L 6 74 L -6 90 L -12 68 L -24 84 L -30 62 '
  'L -40 74 L -44 50 L -54 58 C -50 40 -58 20 -56 3 Z '
  'M 10 22 L 22 26 L 26 38 L 18 50 L 12 40 L 4 36 Z"/>')
o('<path d="M -40 10 C -38 30 -42 46 -40 60 M 0 8 C 4 30 0 50 4 70 M 34 10 C 36 30 32 48 36 62" stroke="#ffffff" stroke-width="1.2" fill="none" opacity="0.18"/>')
o("</g>")
o("</g>")
# main mast snapped at one third, splintered
o('<g transform="translate(-30 -62) rotate(-4)">')
o('<path d="M -8 0 L -7 -96 L -4 -110 L -1 -100 L 2 -114 L 4 -98 L 7 -104 L 8 0 Z" fill="url(#gMast)" stroke="#2c3a3c" stroke-width="1.5"/>')
o('<path d="M -3 -4 L -3 -94" stroke="#c9c6a6" stroke-width="1.5" opacity="0.35"/>')
o('<rect x="-11" y="-60" width="22" height="6" rx="2" fill="#4c564c" stroke="#2c3a3c" stroke-width="1"/>')
o("</g>")
# mizzen: just a stump
o('<path d="M 226 -110 L 227 -136 L 230 -130 L 233 -140 L 236 -128 L 238 -110 Z" fill="url(#gMast)" stroke="#2c3a3c" stroke-width="1.2"/>')
# bowsprit, snapped
o('<path d="M -330 -86 L -398 -124 L -402 -116 L -396 -131 L -393 -122 L -326 -80 Z" fill="url(#gMast)" stroke="#2c3a3c" stroke-width="1.2"/>')
# ropes: sagging rigging + loose drifting ends
o('<g fill="none" stroke="#24363a" stroke-linecap="round" opacity="0.75">')
o('<path d="M -38 -150 C -110 -100 -200 -80 -300 -78" stroke-width="1.6"/>')
o('<path d="M -36 -130 C -60 -96 -70 -80 -86 -64" stroke-width="1.3"/>')
o('<path d="M -24 -130 C 10 -100 40 -80 70 -64" stroke-width="1.3"/>')
o('<path d="M -300 -165 C -330 -140 -360 -120 -394 -120" stroke-width="1.4"/>')
o('<path d="M -296 -170 C -280 -200 -250 -210 -236 -236 C -228 -250 -240 -262 -230 -276" stroke-width="1.2" opacity="0.7"/>')
o('<path d="M 232 -132 C 260 -160 250 -190 276 -210 C 296 -226 286 -246 300 -258" stroke-width="1.2" opacity="0.6"/>')
o("</g>")
# haze over everything high up (masts are in the play area -> distance tone)
o("</g>")

# 5. Hull body
o('<g id="hull">')
o('<use href="#hullShape" fill="url(#gHull)"/>')
o('<g clip-path="url(#cHull)">')
# plank colour variation
for i, y in enumerate(range(-112, 86, 14)):
    shade = R.choice(["#000000", "#ffffff", "#2a1a0e", "#f0d9a8"])
    op = R.uniform(0.03, 0.09)
    o(f'<path d="M -360 {y} Q 0 {y + 8} 360 {y} V {y + 14} Q 0 {y + 22} -360 {y + 14} Z" fill="{shade}" opacity="{f(op)}"/>')
# plank seams + top highlights + plank butt joints
for y in range(-98, 86, 14):
    o(f'<path d="M -360 {y} Q 0 {y + 8} 360 {y}" fill="none" stroke="#24170c" stroke-width="1.6" opacity="0.7"/>')
    o(f'<path d="M -360 {y + 2} Q 0 {y + 10} 360 {y + 2}" fill="none" stroke="#e8c98f" stroke-width="1" opacity="0.13"/>')
    for k in range(3):
        bx = R.uniform(-320, 320)
        by = y + 8 * (1 - (bx / 360) ** 2) + 7
        o(f'<path d="M {f(bx)} {f(by - 6)} L {f(bx)} {f(by + 6)}" stroke="#24170c" stroke-width="1.2" opacity="0.5"/>')
# wale (thick rubbing strake) along the gun deck
o('<path d="M -330 -52 Q 0 -40 340 -58" fill="none" stroke="#2e1f12" stroke-width="7"/>')
o('<path d="M -330 -55 Q 0 -43 340 -61" fill="none" stroke="#b58e5c" stroke-width="1.5" opacity="0.45"/>')
# missing planks near the keel
for x, y, w in ((-205, 46, 52), (-150, 58, 38), (150, 52, 44), (232, 40, 30)):
    o(f'<path d="M {x} {y} l {w} -2 l -3 13 l -{w - 6} 3 Z" fill="#0f1e22"/>')
    o(f'<path d="M {x} {y} l {w} -2" stroke="#9a7a50" stroke-width="1.5" opacity="0.6"/>')
# algae + weed on lower half
o('<g fill="#4f7a3a">')
for _ in range(16):
    x = R.uniform(-300, 320)
    y = R.uniform(20, 75)
    rx, ry = R.uniform(14, 40), R.uniform(5, 12)
    o(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(ry)}" opacity="{f(R.uniform(0.25, 0.45))}"/>')
o("</g>")
o('<g fill="none" stroke="#6a6a2e" stroke-linecap="round" opacity="0.55">')
for _ in range(14):
    x = R.uniform(-290, 320)
    y = R.uniform(-30, 30)
    ln = R.uniform(10, 24)
    o(f'<path d="M {f(x)} {f(y)} q 3 {f(ln / 2)} -1 {f(ln)} t 1 {f(ln / 2)}" stroke-width="1.6"/>')
o("</g>")
# barnacle clusters along the wreck's waterline
o('<g>')
for cx in (-280, -230, -170, -120, 130, 190, 250, 300):
    for _ in range(9):
        bx = cx + R.gauss(0, 12)
        by = 24 + 0.0002 * bx * bx + R.gauss(0, 5)
        r = R.uniform(1.2, 2.8)
        o(f'<circle cx="{f(bx)}" cy="{f(by)}" r="{f(r)}" fill="#e2ddcb" opacity="0.75"/>')
        o(f'<circle cx="{f(bx + 0.3)}" cy="{f(by + 0.3)}" r="{f(r * 0.4)}" fill="#5e5a4a" opacity="0.6"/>')
o("</g>")
# gun ports (one hatch hanging open)
for i, x in enumerate((-250, -180, 118, 250)):
    y = -36 + 0.00007 * x * x - (8 if x > 170 else 0)
    o(f'<rect x="{x - 9}" y="{f(y - 8)}" width="18" height="16" rx="1.5" fill="#120d0a" stroke="#9a7a50" stroke-width="1.6"/>')
    if i == 1:
        o(f'<g transform="translate({x - 9} {f(y + 8)}) rotate(24)"><rect width="18" height="16" rx="1.5" fill="#5a4028" stroke="#2a1a0e" stroke-width="1.2"/>'
          '<path d="M2 5 H16 M2 11 H16" stroke="#2a1a0e" stroke-width="1"/></g>')
    elif i == 3:
        o(f'<g transform="translate({x - 9} {f(y + 8)}) rotate(68)"><rect width="18" height="16" rx="1.5" fill="#5a4028" stroke="#2a1a0e" stroke-width="1.2"/></g>')
# big jagged break amidships: dark interior, deck beam, ribs
HOLE = "M -78 -70 L -60 -48 L -76 -22 L -60 4 L -70 34 L -40 54 L -8 46 L 22 58 L 56 50 L 84 40 L 76 16 L 98 -8 L 82 -34 L 104 -72 Z"
o(f'<path d="{HOLE}" fill="#0c1a1e"/>')
o(f'<clipPath id="cHole"><path d="{HOLE}"/></clipPath>')
o('<g clip-path="url(#cHole)">')
o('<rect x="-100" y="-80" width="220" height="150" fill="#16343a" opacity="0.35"/>')
o('<path d="M -90 -4 Q 10 4 110 -6" stroke="#3a2a1c" stroke-width="9" fill="none"/>')
o('<path d="M -90 -8 Q 10 0 110 -10" stroke="#8a6a44" stroke-width="1.5" fill="none" opacity="0.5"/>')
o("</g>")
ribs = [(-56, 0), (-40, 1), (-24, 0.55), (-8, 1), (8, 0.4), (24, 1), (40, 0.7), (56, 1), (72, 0.5)]
for x, frac in ribs:
    top = 52 - 120 * frac
    d = f"M {x - 2} 52 Q {x - 9} {f((52 + top) / 2)} {x - 1} {f(top)}"
    o(f'<path d="{d}" fill="none" stroke="#2a1c10" stroke-width="9" stroke-linecap="butt"/>')
    o(f'<path d="{d}" fill="none" stroke="#6e5034" stroke-width="6"/>')
    o(f'<path d="M {x - 4} 50 Q {x - 11} {f((52 + top) / 2)} {x - 3} {f(top + 2)}" fill="none" stroke="#d9b984" stroke-width="1.3" opacity="0.5"/>')
    if frac < 1:  # snapped: splinter tip
        o(f'<path d="M {x - 5} {f(top + 3)} L {x - 3} {f(top - 6)} L {x - 1} {f(top + 1)} L {x + 1} {f(top - 9)} L {x + 3} {f(top + 3)} Z" fill="#7a5a3a" stroke="#2a1c10" stroke-width="1"/>')
# splintered plank ends around the break
o(f'<path d="{HOLE}" fill="none" stroke="#a07c4e" stroke-width="2.5" stroke-linejoin="miter"/>')
for x, y, a in ((-78, -70, 200), (-60, -48, 160), (-76, -22, 200), (-70, 34, 210), (82, -34, -20), (98, -8, 10), (104, -72, -30), (76, 16, -10)):
    o(f'<path transform="translate({x} {y}) rotate({a})" d="M 0 -2 L 12 -1 L 5 0 L 14 1 L 0 3 Z" fill="#9a7650" stroke="#2a1c10" stroke-width="0.8"/>')
# keel beam
o('<path d="M -330 -6 C -300 50 -240 82 -150 86 L 100 88 C 200 86 296 78 334 46" fill="none" stroke="#24170c" stroke-width="11"/>')
o('<path d="M -326 -8 C -296 46 -238 77 -150 81 L 100 83 C 200 81 294 73 330 42" fill="none" stroke="#7a5a3a" stroke-width="2" opacity="0.5"/>')
# volume shading: sunlit bow, shadowed stern, darker bottom
o('<rect x="-400" y="-130" width="800" height="230" fill="url(#gHullSide)"/>')
o('<rect x="-400" y="-130" width="800" height="230" fill="url(#gHullShade)"/>')
o("</g>")  # end clip
# outline + rim light on the sun-facing deck edge and bow
o('<use href="#hullShape" fill="none" stroke="#24170c" stroke-width="2.2" stroke-linejoin="round"/>')
o('<path d="M -343 -90 C -322 -80 -302 -70 -280 -66 L -78 -64" fill="none" stroke="#f6e2ad" stroke-width="2" opacity="0.7"/>')
o('<path d="M 104 -64 L 168 -62 M 180 -108 L 334 -116" fill="none" stroke="#f6e2ad" stroke-width="2" opacity="0.55"/>')
o('<path d="M -343 -88 C -322 20 -262 70 -160 78" fill="none" stroke="#f6e2ad" stroke-width="1.6" opacity="0.3"/>')
# coral fans + sea fern growing on the hull
o(coral_fan(-262, 54, 1.0, "#d46a8a", -8))
o(coral_fan(-214, 64, 0.7, "#8e5fa8", 6))
o(coral_fan(270, 30, 0.8, "#8e5fa8", 4))
o('<g fill="none" stroke="#5f8a4a" stroke-width="1.6" stroke-linecap="round" opacity="0.8">')
for x in (-120, -112, 214, 222):
    o(f'<path d="M {x} 62 C {x - 6} 46 {x + 6} 34 {x} 18"/>')
    for k in range(4):
        yy = 54 - k * 10
        o(f'<path d="M {x - 1} {yy} q -6 -3 -9 -8 M {x + 1} {yy - 4} q 6 -3 9 -8" stroke-width="1"/>')
o("</g>")
o("</g>")  # hull
o("</g>")  # wreck frame

# Depth haze: everything above the play-area floor fades into the water.
o('<filter id="fWhite"><feFlood flood-color="#fff"/><feComposite in2="SourceAlpha" operator="in"/></filter>'
  '<mask id="mWreck" maskUnits="userSpaceOnUse" x="0" y="0" width="1200" height="800"><use href="#wreck" filter="url(#fWhite)"/></mask>')
o('<rect id="haze" x="0" y="380" width="1200" height="200" fill="url(#gHaze)" mask="url(#mWreck)"/>')

# Near sand in front of the wreck: buries the stern and the keel
SAND_FRONT = ("M0 724 C 120 716 250 722 360 718 C 430 716 500 712 560 712 C 640 712 700 706 760 698 "
              "C 840 688 900 668 960 662 C 1030 656 1090 676 1140 690 C 1170 698 1190 700 1200 700 V800 H0 Z")
o('<g id="sand-front">')
o(f'<path d="{SAND_FRONT}" fill="url(#gSand)"/>')
o(f'<path d="{SAND_FRONT}" fill="#000" filter="url(#fSandTex)" opacity="0.6"/>')
o('<path d="M 560 712 C 640 712 700 706 760 698 C 840 688 900 668 960 662 C 1030 656 1090 676 1140 690" fill="none" stroke="#e8d7a4" stroke-width="2.5" opacity="0.55"/>')
o('<path d="M 600 716 C 700 712 860 690 980 676 C 1050 670 1100 690 1140 700" fill="none" stroke="#6e6244" stroke-width="10" opacity="0.25" filter="url(#fSoft)"/>')
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
o(coral_fan(440, 672, 0.9, "#d46a8a", -12))
o(coral_fan(510, 676, 0.6, "#8e5fa8", 10))
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
bx, by = 708, 600
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
