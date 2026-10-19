"""Full-size (1:1) one-piece display replica of a bolt-action sniper rifle
(M40 / Remington 700 style with a tactical adjustable stock).

Solid prop: no internal mechanism, bore is blocked. Units: mm.
Axes: X = length (butt at 0, muzzle at +X), Z = up (bore axis at Z=0),
Y = width (shooter's right side is -Y).

Run:  python3 build.py   ->  sniper_replica.stl
"""
from build123d import *

OVERALL = 1130
STOCK_W = 44          # butt / forend width
GRIP_W = 34

# ---------------------------------------------------------------- stock
# Side profile of the stock (x, z), traced clockwise from the butt's bottom rear.
stock_pts = [
    (0, -150), (0, -8),            # recoil pad face
    (215, -8), (240, -22),         # cheek riser, drop to wrist
    (285, -24), (300, -14),        # wrist up to receiver tang
    (820, -14), (838, -26),        # top of forend (receiver/barrel bed)
    (838, -52), (820, -62),        # forend tip
    (470, -62), (440, -70),        # forend underside to magazine well
    (380, -70), (372, -60),        # floorplate, then front of grip
    (352, -150), (300, -158),      # near-vertical grip, grip base
    (290, -105), (262, -100),      # back of grip, hook notch
    (240, -150),                   # notch down to butt bottom
]
side = Polygon(*stock_pts, align=None)
# Round every corner of the outline: shrink/grow rounds convex corners,
# grow/shrink rounds concave ones.
side = offset(offset(side, -6, kind=Kind.ARC), 6, kind=Kind.ARC)
side = offset(offset(side, 4, kind=Kind.ARC), -4, kind=Kind.ARC)
stock = extrude(Plane.XZ * side, amount=STOCK_W / 2, both=True)
# Soften the long side edges for a moulded look.
side_faces = stock.faces().filter_by(Axis.Y)
stock = fillet(side_faces.edges(), 5)

# Slim the grip: cut material off both sides of the grip region.
# A rounded cutter keeps the step into the grip soft instead of a hard ledge.
grip_cut = fillet(Box(120, 30, 110).edges(), 12)
for s in (1, -1):
    stock -= Pos(326, s * (GRIP_W / 2 + 15), -122) * grip_cut

# Panel line separating the cheek riser and the butt pad
stock -= Pos(110, 0, -34) * Box(200, STOCK_W + 2, 1.2)
stock -= Pos(22, 0, -79) * Box(1.2, STOCK_W + 2, 160)

# Cheek riser / length-of-pull adjustment knobs on both sides
for s in (1, -1):
    y = s * (STOCK_W / 2)
    stock += Pos(150, y, -60) * Rot(90, 0, 0) * Cylinder(9, 8)
    stock += Pos(150, y + s * 6, -60) * Box(22, 4, 5)        # lever
    stock += Pos(95, y, -95) * Rot(90, 0, 0) * Cylinder(6, 4)
    # QD sling sockets
    stock -= Pos(60, y, -120) * Rot(90, 0, 0) * Cylinder(5, 6)
    stock -= Pos(780, y, -40) * Rot(90, 0, 0) * Cylinder(5, 6)

# ---------------------------------------------------------------- action
R_RCV = 17.5
receiver = Pos(410, 0, 0) * Rot(0, 90, 0) * Cylinder(R_RCV, 220)
receiver = fillet(receiver.edges(), 3)
shroud = Pos(290, 0, 0) * Rot(0, 90, 0) * Cone(10, 14, 22, align=(Align.CENTER, Align.CENTER, Align.MIN))
shroud = Pos(-11, 0, 0) * shroud
# ejection port recess on the right side
receiver -= Pos(430, -R_RCV, 4) * Box(70, 8, 16)

# Picatinny rail on the receiver
rail_len = 210
rail = Pos(410, 0, R_RCV + 3) * Box(rail_len, 21, 8)
for i in range(int(rail_len // 10)):
    rail -= Pos(410 - rail_len / 2 + 5 + i * 10, 0, R_RCV + 6.5) * Box(5.3, 24, 3)

# Bolt handle: stem angled down and back, ball knob
stem = Pos(318, -R_RCV, -2) * Rot(-30, 0, 0) * Rot(90, 0, 0) * Cylinder(5, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
knob = Pos(318, -R_RCV - 34, -22) * Sphere(10)

# Trigger guard loop and trigger
guard = Pos(398, 0, -74) * Box(60, 10, 26)
guard = fillet(guard.edges().filter_by(Axis.Y), 9)
guard -= Pos(398, 0, -74) * fillet(Box(46, 12, 14).edges().filter_by(Axis.Y), 5)
guard = Pos(0, 0, -6) * guard
trigger = Pos(396, 0, -76) * Rot(0, 15, 0) * Box(5, 7, 18)

# ---------------------------------------------------------------- barrel
B0, B1 = 520, OVERALL
barrel = Pos(B0, 0, 0) * Rot(0, 90, 0) * Cone(14, 10.5, B1 - B0, align=(Align.CENTER, Align.CENTER, Align.MIN))
barrel_nut = Pos(B0 + 6, 0, 0) * Rot(0, 90, 0) * Cylinder(R_RCV + 0.5, 12)
crown = Pos(B1 - 1, 0, 0) * Rot(0, 90, 0) * Cylinder(5, 6)   # shallow recessed muzzle

# Accessory rail and sling stud under the forend
fore_rail = Pos(745, 0, -66) * Box(70, 21, 8)
for i in range(6):
    fore_rail -= Pos(718 + i * 10, 0, -69.5) * Box(5.3, 24, 3)
stud = Pos(805, 0, -66) * Cylinder(4, 10)

# ---------------------------------------------------------------- assemble
rifle = stock + receiver + shroud + rail + stem + knob + guard + trigger \
        + barrel + barrel_nut + fore_rail + stud
rifle -= crown

print("bounding box (mm):", rifle.bounding_box().size)
export_stl(rifle, "sniper_replica.stl", tolerance=0.05, angular_tolerance=0.15)
print("wrote sniper_replica.stl")
