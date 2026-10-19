"""1:1 one-piece display replica of a VSR-10 style bolt-action airsoft rifle
with a sporter stock (see reference.png).

The stock's side outline is traced from the photo (trace_profile.py ->
stock_profile.json) and scaled to the VSR-10's published overall length of
1075 mm. Widths come from typical sporter-stock measurements, since the photo
is a single side view.

Solid prop: no internal mechanism, blocked muzzle. Units: mm.
Axes: X = length (butt at 0, muzzle at +X), Z = up (bore axis at Z=0),
Y = width (shooter's right side is -Y).

Run:  python3 trace_profile.py && python3 build.py   ->  vsr10_replica.stl
"""
import json
import math
from build123d import *

OVERALL = 1075


def simplify(pts, tol):
    """Ramer-Douglas-Peucker polyline simplification."""
    if len(pts) < 3:
        return pts
    (x0, z0), (x1, z1) = pts[0], pts[-1]
    dx, dz = x1 - x0, z1 - z0
    norm = (dx * dx + dz * dz) ** 0.5 or 1e-9
    dists = [abs(dz * (x - x0) - dx * (z - z0)) / norm for x, z in pts[1:-1]]
    i = max(range(len(dists)), key=dists.__getitem__)
    if dists[i] <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:i + 2], tol)[:-1] + simplify(pts[i + 1:], tol)


def rounded(face, convex, concave):
    """Round a 2D outline's convex then concave corners."""
    face = offset(offset(face, -convex, kind=Kind.ARC), convex, kind=Kind.ARC)
    return offset(offset(face, concave, kind=Kind.ARC), -concave, kind=Kind.ARC)


# ---------------------------------------------------------------- stock
profile = json.load(open("stock_profile.json"))
top = simplify([tuple(p) for p in profile["top"]], 0.4)
bottom = simplify([tuple(p) for p in profile["bottom"]], 0.4)
pts = top + bottom[::-1]          # butt top -> forend tip -> butt bottom
side = rounded(Polygon(*pts, align=None), 9, 12)
# Slab as wide as the widest part of the stock, with its long edges rounded
# first: that round survives wherever the plan below keeps full width.
side_body = extrude(Plane.XZ * side, amount=21, both=True)
for r_side in (9, 8, 7, 6, 5):     # largest round the outline accepts
    try:
        side_body = fillet(side_body.faces().filter_by(Axis.Y).edges(), r_side)
        break
    except ValueError:
        continue
print("stock section radius:", r_side)

# Top-view half-widths along the stock (x, half-width): full butt, narrow
# wrist and grip, wider action area and forend, slimmer forend tip.
half_w = [(0, 20.5), (205, 21), (236, 18.5), (256, 15.5), (300, 15.5),
          (322, 19.5), (520, 20), (680, 19), (705, 15)]
plan_pts = half_w + [(x, -w) for x, w in reversed(half_w)]
plan = rounded(Polygon(*plan_pts, align=None), 3, 30)
plan_body = extrude(plan, amount=200, both=True)

stock = side_body & plan_body
assert stock.volume > 0, "stock intersection failed"
# Soften the edges the plan cut left at the wrist and grip.
sharp = stock.edges().filter_by(lambda e: e.length > 1 and abs(e.center().Y) > 14)
for r in (6, 5, 4, 3, 2):          # largest round the geometry accepts
    try:
        stock = fillet(sharp, r)
        break
    except ValueError:
        continue
print("wrist edge radius:", r)

# Slim the lower grip (it shares X with the comb above it).
grip_cut = fillet(Box(110, 60, 110).edges(), 26)
for s in (1, -1):
    stock -= Pos(225, s * (15.5 + 30), -128) * grip_cut

# Butt pad parting line (pad is ~20 mm thick in the photo)
# A 1 mm groove around the section: a thin slice minus a rounded core.
pad_top, pad_bottom = -18.5, -136
core = fillet(Box(1.2, 2 * (20.5 - 1), pad_top - pad_bottom - 2).edges().filter_by(Axis.X), 8)
stock -= Pos(21, 0, (pad_top + pad_bottom) / 2) * (Box(1.0, 50, 170) - core)

# ---------------------------------------------------------------- action
R_RCV, Z_RCV = 13.5, -2.5
X_RCV0, X_RCV1 = 344, 500            # receiver rear (px 605) to front
receiver = Pos((X_RCV0 + X_RCV1) / 2, 0, Z_RCV) * Rot(0, 90, 0) * Cylinder(R_RCV, X_RCV1 - X_RCV0)
receiver = fillet(receiver.edges(), 2)
receiver -= Pos(425, -R_RCV, 2) * Box(60, 7, 13)                 # ejection port (right side)

# Bolt cocking piece behind the receiver (px 605-625 in the photo)
cocking = Pos(331, 0, Z_RCV + 1) * Rot(0, 90, 0) * Cylinder(7.5, 26)
cocking = fillet(cocking.edges().group_by(Axis.X)[0], 2)
cocking -= Pos(336, 0, Z_RCV + 1) * Rot(0, 90, 0) * (Cylinder(8, 1.2) - Cylinder(6.8, 1.2))

# Scope rail on the receiver (px 490-590)
rail_x0, rail_x1 = 363, 486
rail = Pos((rail_x0 + rail_x1) / 2, 0, 14) * Box(rail_x1 - rail_x0, 15, 7)
x = rail_x0 + 6
while x < rail_x1 - 3:
    rail -= Pos(x, 0, 16.5) * Box(5.3, 18, 2.5)
    x += 10

# Bolt handle on the right side: stem angled down, ball knob
stem = Pos(352, -R_RCV + 2, Z_RCV) * Rot(30, 0, 0) * Rot(90, 0, 0) \
    * Cylinder(4.5, 36, align=(Align.CENTER, Align.CENTER, Align.MIN))
knob = Pos(352, -R_RCV - 29, Z_RCV - 18) * Sphere(8.5)

# Trigger guard: thin round loop (X 317-371, Z -51..-83 in the photo)
loop = Pos(345, -66) * Ellipse(26, 17) - Pos(345, -66) * Ellipse(22, 13)   # sketch (x, z)
guard = extrude(Plane.XZ * loop, amount=4, both=True)
guard &= Pos(345, 0, -80) * Box(80, 20, 70)                        # top sinks into the stock
# Curved trigger blade built from short straight segments
trigger = Part()
blade = [(341, -50), (338, -56), (336, -62), (338, -68), (343, -73)]
for (xa, za), (xb, zb) in zip(blade, blade[1:]):
    angle = -math.degrees(math.atan2(zb - za, xb - xa))
    length = math.hypot(xb - xa, zb - za) + 2.4
    trigger += Pos((xa + xb) / 2, 0, (za + zb) / 2) * Rot(0, angle, 0) * Box(length, 5, 2.4)

# ---------------------------------------------------------------- barrel
barrel = Pos(X_RCV1 - 10, 0, 0) * Rot(0, 90, 0) \
    * Cylinder(11.2, OVERALL - X_RCV1 + 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
barrel = fillet(barrel.edges().group_by(Axis.X)[-1], 1)
barrel -= Pos(OVERALL - 10, 0, 0) * Rot(0, 90, 0) * (Cylinder(12, 0.8) - Cylinder(10.6, 0.8))  # orange tip line
barrel -= Pos(OVERALL - 2, 0, 0) * Rot(0, 90, 0) * Cylinder(5, 5)                              # recessed muzzle

# Accessory rail (X 594-675) with folding bipod post, rear sling swivel
fore_rail = Pos(634, 0, -42) * Box(80, 14, 7)
for i in range(7):
    fore_rail -= Pos(603 + i * 10, 0, -45) * Box(5.3, 18, 2.5)
bipod = Pos(676, 0, -45) * Cylinder(3, 19, align=(Align.CENTER, Align.CENTER, Align.MAX))
bipod += Pos(676, 0, -45) * Box(9, 10, 6)                          # hinge block
bipod += Pos(676, 0, -64) * fillet(Cylinder(4.5, 3).edges(), 1)    # foot
swivel = Pos(66, 0, -120) * Cylinder(4, 10, align=(Align.CENTER, Align.CENTER, Align.MAX))
swivel += Pos(66, 0, -128) * Box(10, 9, 4)
swivel += Pos(66, 0, -139) * Rot(90, 0, 0) * Torus(8, 1.8)

# ---------------------------------------------------------------- assemble
rifle = stock + receiver + cocking + rail + stem + knob + guard + trigger \
    + barrel + fore_rail + bipod + swivel

print("bounding box (mm):", rifle.bounding_box().size)
export_stl(rifle, "vsr10_replica.stl", tolerance=0.05, angular_tolerance=0.15)
print("wrote vsr10_replica.stl")
